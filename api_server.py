"""
INTELLIGENT AI AGENT API v7.0
Smart tool orchestration like ChatGPT/Claude/Gemini
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import asyncio
import json
import time
from datetime import datetime
import sys
import os
import platform
import re
from pathlib import Path
import aiofiles
import traceback

if platform.system() == "Windows":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_code import UltimateAgent, AgentConfig, logger
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

class HealthCheckFilter(logging.Filter):
    """Filter out health check endpoint logs"""
    def filter(self, record: logging.LogRecord) -> bool:
        return not any(path in record.getMessage() for path in [
            "GET /health",
            "GET /stats",
            "GET /favicon.ico"
        ])

logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

app = FastAPI(
    title="Nexus AI - Production API",
    version="1.0.0",
    description="Production-ready AI agent with file upload, voice, and streaming"
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """FIXED: WebSocket with better Render compatibility"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Check if connection is still alive
            if websocket.client_state != WebSocketState.CONNECTED:
                logger.warning("WebSocket not connected, breaking")
                break
            
            try:
                # Set a reasonable timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=300.0  # 5 minutes
                )
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                    continue
                except:
                    break
            
            if not data:
                continue
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON"
                })
                continue
            
            message_text = message.get("message", "").strip()
            
            if not message_text:
                await websocket.send_json({
                    "type": "error", 
                    "content": "Empty message"
                })
                continue
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "status",
                "content": "Processing..."
            })
            
            # Process with council or ollama
            if agent.use_council:
                await process_with_council(
                    message_text,
                    websocket
                )
            else:
                await process_with_ollama(
                    message_text,
                    websocket
                )
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Error: {str(e)}"
            })
        except:
            pass
    finally:
        await manager.disconnect(websocket)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = None
start_time = time.time()
message_count = 0
tool_use_count = 0
response_times = []
active_connections: List[WebSocket] = []

class StatsResponse(BaseModel):
    totalMessages: int
    toolsUsed: int
    avgResponseTime: float
    uptime: str

class ConnectionManager:
    """Manage WebSocket connections - PATCHED"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_times: Dict[WebSocket, float] = {}
        self.timeout_seconds = 3600
        self._lock = asyncio.Lock()  
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:  
            self.active_connections.append(websocket)
            self.connection_times[websocket] = time.time()
        print(f" [SUCCESS] Client connected (total: {len(self.active_connections)})")
    
    async def disconnect(self, websocket: WebSocket):
        async with self._lock:  
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            if websocket in self.connection_times:
                del self.connection_times[websocket]
    
    async def cleanup_stale_connections(self):
        """Remove stale connections - PATCHED"""
        now = time.time()
        to_remove = []
        
        async with self._lock:
            connection_snapshot = list(self.connection_times.items())
        
        for ws, connect_time in connection_snapshot:
            if now - connect_time > self.timeout_seconds:
                to_remove.append(ws)
        
        for ws in to_remove:
            try:
                await ws.close()
            except:
                pass
            await self.disconnect(ws)
        
        if to_remove:
            logger.info(f" Cleaned up {len(to_remove)} stale connections")

manager = ConnectionManager()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter - PATCHED"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times: Dict[str, List[float]] = {}
        self.last_cleanup = time.time()
        
        self.excluded_paths = {
            "/health", "/stats", "/", "/docs", 
            "/openapi.json", "/council/stats"
        }
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        now = time.time()
        if now - self.last_cleanup > 300:  
            self._cleanup_old_ips()
            self.last_cleanup = now
        
        client_ip = request.client.host
        minute_ago = now - 60
        
        if client_ip not in self.request_times:
            self.request_times[client_ip] = []
        
        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip] 
            if t > minute_ago
        ]
        
        if len(self.request_times[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
        
        self.request_times[client_ip].append(now)
        
        response = await call_next(request)
        return response
    
    def _cleanup_old_ips(self):
        """Remove IPs with no recent activity - PATCHED"""
        now = time.time()
        to_remove = []
        
        for ip, times in self.request_times.items():
            if not times or max(times) < now - 300:  
                to_remove.append(ip)
        
        for ip in to_remove:
            del self.request_times[ip]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} inactive IPs")

app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# ============================================================================
# FILE UPLOAD ENDPOINT
# ============================================================================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads - PATCHED"""
    try:
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
        if safe_filename != file.filename:
            logger.warning(f" Sanitized filename: {file.filename} -> {safe_filename}")
        
        MAX_SIZE = 10 * 1024 * 1024
        content = await file.read()
        
        if len(content) > MAX_SIZE:
            raise HTTPException(400, "File too large (max 10MB)")
        
        allowed_types = {
            'text/plain', 'text/markdown', 'text/csv',
            'application/json', 'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(400, f"File type not supported: {file.content_type}")
        
        file_path = Path(AgentConfig.DATA_DIR) / safe_filename
        
        if file_path.exists():
            base = file_path.stem
            ext = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = Path(AgentConfig.DATA_DIR) / f"{base}_{counter}{ext}"
                counter += 1
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                file_content = await f.read(5000)
        except:
            file_content = "[Binary file - cannot preview]"
        
        logger.info(f" File uploaded: {safe_filename} ({len(content)} bytes)")
        
        return {
            "success": True,
            "filename": safe_filename,
            "size": len(content),
            "path": str(file_path),
            "content_preview": file_content[:500]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint - PATCHED"""
    await manager.connect(websocket)
    
    try:
        await safe_send_json(websocket, {
            "type": "connection",
            "status": "connected",
            "model": "Council Mode" if agent.use_council else AgentConfig.MODEL
        })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=300.0 
                )
            except asyncio.TimeoutError:
                if not await safe_send_json(websocket, {"type": "keepalive"}):
                    break
                continue
            except WebSocketDisconnect:
                logger.info(" Client disconnected gracefully")
                break
            except Exception as e:
                logger.error(f" Receive error: {e}")
                break
            
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f" Invalid JSON: {e}")
                await safe_send_json(websocket, {
                    "type": "error",
                    "message": "Invalid message format"
                })
                continue
            
            if message_data.get("type") != "message":
                continue
            
            user_message = message_data.get("content", "")
            
            if not user_message.strip():
                continue
            
            try:
                await intelligent_streaming(user_message, websocket)
            except Exception as e:
                logger.error(f" Streaming error: {e}")
                logger.error(traceback.format_exc())
                await safe_send_json(websocket, {
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logger.info(" WebSocket disconnected")
    except Exception as e:
        logger.error(f" WebSocket error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await manager.disconnect(websocket)

async def should_search_web(query: str) -> bool:
    """Determine if query needs web search"""
    current_indicators = ['today', 'now', 'current', 'latest', 'recent', 'news', 'weather']
    search_indicators = ['search', 'find', 'look up', 'what is', 'who is', 'when did', 'information about']
    
    query_lower = query.lower()
    return any(ind in query_lower for ind in current_indicators + search_indicators)

async def safe_send_json(websocket: WebSocket, data: dict) -> bool:
    """Send JSON with error handling - NEW HELPER"""
    try:
        await websocket.send_json(data)
        return True
    except RuntimeError as e:
        if "connection is closed" in str(e).lower():
            logger.warning(" Client disconnected")
            return False
        logger.error(f" WebSocket error: {e}")
        return False
    except Exception as e:
        logger.error(f" Unexpected WebSocket error: {e}")
        return False

async def smart_web_search(query: str, websocket: WebSocket) -> str:
    """Intelligent web search - PATCHED"""
    
    if not await safe_send_json(websocket, {
        "type": "response_chunk",
        "content": "*[SEARCH] Searching the web...*\n\n"
    }):
        return "[ERROR] Connection lost"
    
    loop = asyncio.get_event_loop()
    
    try:
        search_results = await loop.run_in_executor(
            None, 
            agent.tools.execute_tool, 
            'search_web', 
            [query]
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"[ERROR] Search failed: {e}"
    
    if "[ERROR]" in search_results:
        return search_results
    
    url_pattern = r'URL: (https?://[^\s]+)'
    urls = re.findall(url_pattern, search_results)
    
    comprehensive_info = f"SEARCH RESULTS:\n{search_results}\n\n"
    
    if not urls:
        return comprehensive_info
    
    if not await safe_send_json(websocket, {
        "type": "response_chunk",
        "content": "*Reading top sources...*\n\n"
    }):
        return comprehensive_info  
    
    async def fetch_url(url: str, index: int):
        try:
            content = await loop.run_in_executor(
                None,
                agent.tools.execute_tool,
                'fetch_webpage',
                [url]
            )
            if "[ERROR]" not in content:
                return (index, url, content[:3000])
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
        return None
    
    tasks = [fetch_url(url, i+1) for i, url in enumerate(urls[:3])]
    
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.warning("Fetch timeout, returning partial results")
        return comprehensive_info
    
    for result in results:
        if result and not isinstance(result, Exception):
            index, url, content = result
            comprehensive_info += f"\n\nSOURCE {index} - {url}:\n{content}\n"
    
    return comprehensive_info

def is_council_failure(response: str) -> bool:
    """Detect if council response indicates failure"""
    if not response:
        return True
    
    failure_indicators = [
        "both primary and backup councils",
        "both councils failed",
        "councils are unavailable",
        "please check api keys",
        "error:",
        "[error]",
        "failed to",
    ]
    
    response_lower = response.lower()
    return any(indicator in response_lower for indicator in failure_indicators)

async def intelligent_streaming(user_message: str, websocket: WebSocket):
    """Smart streaming - PATCHED"""
    global message_count, tool_use_count, response_times
    start = time.time()
    
    try:
        if len(user_message) > 10000:
            await safe_send_json(websocket, {
                "type": "error",
                "message": "Message too long (max 10000 chars)"
            })
            return
        
        agent.memory.add_conversation("user", user_message)
        
        context_msgs = agent.memory.get_recent_context(6)
        context_str = "\n".join([f"{m['role']}: {m['content']}" for m in context_msgs])
        
        if agent.use_council:
            await stream_with_council(user_message, context_str, websocket)
        else:
            await stream_with_ollama(user_message, websocket)
        
        message_count += 1
        response_times.append(time.time() - start)
        
    except Exception as e:
        logger.error(f" Streaming Error: {e}")
        logger.error(traceback.format_exc())
        await safe_send_json(websocket, {
            "type": "error", 
            "message": f"Error: {str(e)}"
        })

async def stream_response(websocket: WebSocket, text: str, chunk_size: int = 20) -> bool:
    """Stream text in chunks - NEW HELPER"""
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        if not await safe_send_json(websocket, {
            "type": "response_chunk", 
            "content": chunk
        }):
            return False
        await asyncio.sleep(0.005)
    return True

async def stream_with_council(user_message: str, context_str: str, websocket: WebSocket):
    """FIXED: Always send completion signal, even on timeout/error"""
    global tool_use_count
    
    max_iterations = 8
    current_context = context_str
    tool_history = []
    has_sent_final_response = False
    completion_sent = False  
    
    try:
        for iteration in range(max_iterations):
            if iteration == 0:
                if not await safe_send_json(websocket, {
                    "type": "response_chunk", 
                    "content": "*Consulting the Council...*\n\n"
                }):
                    return
            
            try:
                full_response = await asyncio.wait_for(
                    agent.orchestrator.convene(user_message, current_context),
                    timeout=120.0
                )
                
                if not full_response or is_council_failure(full_response):
                    logger.error(f"Council returned failure: {full_response}")
                    
                    if not has_sent_final_response:
                        error_msg = full_response if full_response else "Council failed to respond"
                        await safe_send_json(websocket, {
                            "type": "response_chunk",
                            "content": f"\n\n {error_msg}\n\n"
                        })
                        
                        if agent.orchestrator.backup_available:
                            await safe_send_json(websocket, {
                                "type": "response_chunk",
                                "content": "**Troubleshooting:**\n"
                                         "1. Check if GROQ_API_KEY or GOOGLE_API_KEY is set in .env\n"
                                         "2. Verify API keys are valid (not rate limited)\n"
                                         "3. Check agent_logs/agent.log for details\n"
                                         "4. Wait 60 seconds if rate limited\n"
                            })
                        
                        has_sent_final_response = True
                    
                    if not completion_sent:
                        await safe_send_json(websocket, {
                            "type": "response_complete",
                            "timestamp": datetime.now().isoformat(),
                            "status": "error"
                        })
                        completion_sent = True
                    break
                    
            except asyncio.TimeoutError:
                logger.error(f"Council timeout after {iteration + 1} iterations")
                
                if not has_sent_final_response:
                    timeout_msg = (
                        "⏱️ **Council Timeout**\n\n"
                        "The AI council took too long to respond. This usually means:\n\n"
                        "**Common Causes:**\n"
                        "- API rate limits (most likely)\n"
                        "- Network connectivity issues\n"
                        "- API keys may be invalid or expired\n\n"
                        "**Quick Fix:**\n"
                        "1. Add to your `.env` file:\n"
                        "   ```\n"
                        "   USE_BACKUP_ONLY=true\n"
                        "   ```\n"
                        "2. Restart the server\n"
                        "3. Try again\n\n"
                        "**Or wait 60 seconds** for rate limits to reset.\n"
                    )
                    
                    await safe_send_json(websocket, {
                        "type": "response_chunk",
                        "content": timeout_msg
                    })
                    has_sent_final_response = True
                
                if not completion_sent:
                    await safe_send_json(websocket, {
                        "type": "response_complete",
                        "timestamp": datetime.now().isoformat(),
                        "status": "timeout"
                    })
                    completion_sent = True
                return  
                
            except Exception as e:
                logger.error(f"Council exception: {e}")
                logger.error(traceback.format_exc())
                
                if not has_sent_final_response:
                    await safe_send_json(websocket, {
                        "type": "response_chunk",
                        "content": f"❌ **Council Error**\n\n{str(e)}\n\n"
                                 "Check agent_logs/agent.log for details.\n"
                    })
                    has_sent_final_response = True
                
                if not completion_sent:
                    await safe_send_json(websocket, {
                        "type": "response_complete",
                        "timestamp": datetime.now().isoformat(),
                        "status": "error"
                    })
                    completion_sent = True
                return  
            
            tool_pattern = r'TOOL\[(\w+)\]\((.*?)\)'
            tool_match = re.search(tool_pattern, full_response)
            
            if tool_match:
                tool_name = tool_match.group(1)
                args_str = tool_match.group(2).strip()
                args = [arg.strip().strip('"').strip("'") for arg in args_str.split(',') if arg.strip()]
                
                tool_sig = f"{tool_name}({','.join(args[:2])})"
                if tool_sig in tool_history:
                    logger.warning(f"Loop detected: {tool_sig}")
                    clean_response = re.sub(tool_pattern, '', full_response).strip()
                    if clean_response and not has_sent_final_response:
                        await stream_response(websocket, clean_response)
                        agent.memory.add_conversation("assistant", clean_response)
                        has_sent_final_response = True
                    
                    if not completion_sent:
                        await safe_send_json(websocket, {
                            "type": "response_complete",
                            "timestamp": datetime.now().isoformat(),
                            "status": "success"
                        })
                        completion_sent = True
                    break
                
                tool_history.append(tool_sig)
                tool_use_count += 1
                
                logger.info(f"🔧 Executing {tool_name}...")
                
                try:
                    if tool_name in ['search_web', 'smart_search']:
                        tool_result = await smart_web_search(args[0] if args else '', websocket)
                    else:
                        loop = asyncio.get_event_loop()
                        tool_result = await loop.run_in_executor(
                            None,
                            agent.tools.execute_tool,
                            tool_name,
                            args
                        )
                except Exception as e:
                    logger.error(f"Tool '{tool_name}' failed: {e}")
                    tool_result = f"[ERROR] Tool failed: {e}"
                
                current_context += f"\n\nTool: {tool_name}\nResult: {tool_result[:3000]}"
                continue  
            
            else:
                if not has_sent_final_response:
                    clean_response = re.sub(tool_pattern, '', full_response).strip()
                    
                    if not clean_response:
                        clean_response = "✅ Task completed."
                    
                    success = await stream_response(websocket, clean_response)
                    
                    if success:
                        agent.memory.add_conversation("assistant", clean_response)
                        has_sent_final_response = True
                
                if not completion_sent:
                    await safe_send_json(websocket, {
                        "type": "response_complete",
                        "timestamp": datetime.now().isoformat(),
                        "status": "success"
                    })
                    completion_sent = True
                break  
        
        if iteration >= max_iterations - 1 and not has_sent_final_response:
            await safe_send_json(websocket, {
                "type": "response_chunk",
                "content": "\n\n⚠️ Maximum iterations reached. Task may be incomplete.\n"
            })
            has_sent_final_response = True
        
        if not completion_sent:
            await safe_send_json(websocket, {
                "type": "response_complete",
                "timestamp": datetime.now().isoformat(),
                "status": "max_iterations" if iteration >= max_iterations - 1 else "success"
            })
            completion_sent = True
    
    except Exception as e:
        logger.error(f"Unexpected error in stream_with_council: {e}")
        logger.error(traceback.format_exc())
        
        if not has_sent_final_response:
            await safe_send_json(websocket, {
                "type": "response_chunk",
                "content": f"❌ Unexpected error: {str(e)}\n"
            })
        
        if not completion_sent:
            await safe_send_json(websocket, {
                "type": "response_complete",
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            })

async def stream_with_ollama(user_message: str, websocket: WebSocket):
    """Stream responses using Ollama mode"""
    
    system_prompt = agent._build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in agent.memory.get_recent_context(8):
        messages.append({
            "role": "user" if msg['role'] == 'user' else "assistant",
            "content": msg['content']
        })
    
    messages.append({"role": "user", "content": user_message})
    
    max_iterations = 5
    iteration = 0
    
    await websocket.send_json({
        "type": "response_chunk",
        "content": "*[THINK] Thinking...*\n\n"
    })
    
    while iteration < max_iterations:
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        lc_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                lc_messages.append(SystemMessage(content=msg['content']))
            elif msg['role'] == 'user':
                lc_messages.append(HumanMessage(content=msg['content']))
            else:
                lc_messages.append(AIMessage(content=msg['content']))
        
        response = agent.llm.invoke(lc_messages)
        content = response.content
        
        tool_call = agent._parse_tool_call(content)
        
        if not tool_call:
            clean_response = re.sub(
                r'TOOL\[.*?\]\(.*?\)', 
                '', 
                content, 
                flags=re.DOTALL
            ).strip()
            
            words = clean_response.split(' ')
            for i in range(0, len(words), 4):
                chunk = " ".join(words[i:i+4]) + " "
                await websocket.send_json({
                    "type": "response_chunk",
                    "content": chunk
                })
                await asyncio.sleep(0.01)
            
            agent.memory.add_conversation("assistant", clean_response)
            
            await websocket.send_json({
                "type": "response_complete",
                "timestamp": datetime.now().isoformat()
            })
            break
        
        tool_use_count += 1
        
        await websocket.send_json({
            "type": "response_chunk",
            "content": f"\n\n[TOOL]*Using {tool_call['tool']}...*\n\n"
        })
        
        if tool_call['tool'] in ['search_web', 'smart_search']:
            tool_result = await smart_web_search(
                tool_call['args'][0] if tool_call['args'] else '',
                websocket
            )
        else:
            tool_result = agent.tools.execute_tool(
                tool_call['tool'], 
                tool_call['args']
            )
        
        messages.append({"role": "assistant", "content": content})
        messages.append({
            "role": "user", 
            "content": f"Tool Result:\n{tool_result}"
        })
        
        iteration += 1
    
    if iteration >= max_iterations:
        await websocket.send_json({
            "type": "response_chunk",
            "content": "\n\n*[Task completed]*"
        })
        await websocket.send_json({
            "type": "response_complete",
            "timestamp": datetime.now().isoformat()
        })

@app.on_event("startup")
async def startup_event():
    """Startup - PATCHED"""
    global agent
    try:
        print(" Initializing Intelligent AI Agent...")
        
        try:
            agent = UltimateAgent()
        except SystemExit as e:
            print(f" FATAL: Agent initialization failed (SystemExit: {e})")
            print("\n Troubleshooting:")
            print("   1. Check if Ollama is running: curl http://localhost:11434")
            print("   2. Verify .env file has API keys")
            print("   3. Check logs in ./agent_logs/")
            sys.exit(1)
        except Exception as e:
            print(f" FATAL: {e}")
            print(traceback.format_exc())
            sys.exit(1)
        
        mode = "Council Mode" if agent.use_council else "Ollama Mode"
        print(f" [SUCCESS] Agent initialized in {mode}")
        
        asyncio.create_task(periodic_cleanup())
        
        print("\n" + "="*70)
        print(" SERVER READY")
        print("="*70)
        
    except Exception as e:
        print(f" [X] FATAL: {e}")
        print(traceback.format_exc())
        sys.exit(1)

async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        await asyncio.sleep(600)  
        await manager.cleanup_stale_connections()
        
        if agent:
            agent.memory.auto_cleanup()

@app.on_event("shutdown")
async def shutdown_event():
    if agent:
        agent.cleanup()

build_path = "frontend/build" 

app.mount("/static", StaticFiles(directory=f"{build_path}/static"), name="static")

@app.get("/")
async def serve_react_app():
    index_file = os.path.join(build_path, "index.html")
    return FileResponse(index_file)

@app.get("/{catchall:path}")
async def catch_all(catchall: str):
    index_file = os.path.join(build_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "online", "message": "Nexus API is running, but UI not found"}

@app.get("/health")
async def health_check():
    """Health check - PATCHED"""
    try:
        return {
            "status": "healthy",
            "mode": "council" if agent.use_council else "ollama",
            "model": AgentConfig.MODEL if not agent.use_council else "multi-model",
            "memory_loaded": len(agent.memory.conversation_history),
            "tools_available": len(agent.tools.tools),
            "uptime_seconds": int(time.time() - start_time),
            "active_connections": len(manager.active_connections),
            "council_stats": agent.orchestrator.get_stats() if agent.use_council else None
        }
    except Exception as e:
        logger.error(f" Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    uptime_seconds = time.time() - start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    
    return StatsResponse(
        totalMessages=message_count,
        toolsUsed=tool_use_count,
        avgResponseTime=round(avg_time, 2),
        uptime=f"{hours}h {minutes}m"
    )

@app.get("/test/gemini")
async def test_gemini():
    """Test Gemini API directly"""
    import aiohttp
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return {"error": "GOOGLE_API_KEY not set"}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": "Say 'Hello, I am working!'"}]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                status = response.status
                text = await response.text()
                
                return {
                    "status": status,
                    "response": text[:500],
                    "working": status == 200
                }
    except Exception as e:
        return {"error": str(e)}

@app.get("/history")
async def get_history():
    try:
        history = agent.memory.get_recent_context(50)
        return {"history": history, "total": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear")
async def clear_conversation():
    try:
        agent.memory.clear_conversation()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export")
async def export_conversation():
    try:
        history = agent.memory.get_recent_context(1000)
        return {
            "conversation": history,
            "exported_at": datetime.now().isoformat(),
            "total_messages": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - NEW"""
    logger.error(f" Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        NEXUS AI - PRODUCTION API v1.0                        ║
║                                                              ║
║  [SUCCESS] Real-time streaming                               ║
║  [SUCCESS] File upload & analysis                            ║
║  [SUCCESS] Web search with synthesis                         ║
║  [SUCCESS] Automatic tool usage                              ║
║  [SUCCESS] Persistent memory                                 ║
║  [SUCCESS] Voice input support                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🚀 Server starting...

  📡 API:        http://localhost:8000
  🔌 WebSocket:  ws://localhost:8000/ws
  📚 Docs:       http://localhost:8000/docs
  💚 Health:     http://localhost:8000/health

Make sure Ollama is running: ollama serve
""")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )