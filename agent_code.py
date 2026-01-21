"""
ULTIMATE AI AGENT SYSTEM v3.0 - PRODUCTION EDITION (BUGFIXED)
All critical bugs fixed and optimized.


Requirements:
pip install langchain-ollama chromadb sentence-transformers
pip install duckduckgo-search requests beautifulsoup4 lxml
pip install pyautogui pillow psutil cryptography pydantic
pip install SpeechRecognition pyttsx3 aiohttp diskcache python-dotenv
"""


import os
import json
import time
import requests
import subprocess
import threading
import sqlite3
import re
import gc
import asyncio
import shlex
import logging
import sys
import atexit
import warnings
import hashlib
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from pathlib import Path
from functools import wraps
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from collections import defaultdict


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

warnings.filterwarnings('ignore')


# ================================================================================
# CONSTANTS
# ================================================================================


class Constants:
    """Application constants"""
    MAX_WEBPAGE_LENGTH = 8000
    MAX_SEARCH_RESULTS = 5
    MAX_FILE_READ_SIZE = 50000
    MAX_LIST_FILES = 100
    MAX_TOOL_OUTPUT_LENGTH = 5000
    RATE_LIMIT_WINDOW = 60
    SYSTEM_INFO_CACHE_TTL = 5
    MAX_CONVERSATION_HISTORY = 30
    MAX_CONTEXT_CHARS = 32000
    DB_POOL_SIZE = 5
    REQUEST_TIMEOUT = 60
    COMMAND_TIMEOUT = 30
    MAX_INPUT_LENGTH = 10000
    MAX_ITERATIONS = 15
    CACHE_TTL_SEARCH = 600
    CACHE_TTL_WEBPAGE = 1800
    CACHE_TTL_SMART_SEARCH = 900
    ENABLE_AGGRESSIVE_CACHING = True
    MAX_SOURCES_TO_FETCH = 3
    
    DANGEROUS_PATTERNS = [
        r';\s*rm\s+-rf',
        r'&&\s*wget',
        r'\|\s*bash',
        r'`.*`',
        r'\$\(.*\)',
        r'<script',
        r'javascript:',
        r'eval\s*\(',
        r'exec\s*\(',
        r'\.\./',
        r'\.\.\\'
    ]
    
    SENSITIVE_OPERATIONS = [
        'delete', 'remove', 'format', 'shutdown', 'restart',
        'send_email', 'run_command', 'install', 'uninstall',
        'drop', 'truncate', 'kill', 'chmod', 'chown'
    ]
    
    ALLOWED_COMMANDS = {
        'ls', 'dir', 'pwd', 'whoami', 'date', 'echo', 'cat',
        'head', 'tail', 'grep', 'find', 'python', 'python3',
        'pip', 'git', 'curl', 'wget', 'which', 'type', 'tree',
        'df', 'du', 'free', 'top', 'ps', 'uname', 'hostname'
    }


# ================================================================================
# LOGGING CONFIGURATION
# ================================================================================


def setup_logging():
    """Configure comprehensive logging"""
    log_dir = Path("./agent_logs")
    log_dir.mkdir(exist_ok=True)
    
    main_log = log_dir / "agent.log"
    security_log = log_dir / "security.log"
    
    logger = logging.getLogger("Agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    main_handler = RotatingFileHandler(
        main_log, maxBytes=10*1024*1024, backupCount=5
    )
    main_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s'
    ))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(
        '[%(levelname)s] %(message)s'
    ))
    
    logger.addHandler(main_handler)
    logger.addHandler(console_handler)
    
    sec_logger = logging.getLogger("Security")
    sec_logger.setLevel(logging.INFO)
    sec_handler = RotatingFileHandler(
        security_log, maxBytes=5*1024*1024, backupCount=3
    )
    sec_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s'
    ))
    sec_logger.addHandler(sec_handler)
    
    return logger


logger = setup_logging()
sec_logger = logging.getLogger("Security")


# ================================================================================
# LAZY IMPORTS
# ================================================================================


class LazyLoader:
    """Lazy load heavy dependencies"""
    
    _instances: Dict[str, Any] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_embeddings(cls):
        """Lazy load embeddings model"""
        with cls._lock:
            if 'embeddings' not in cls._instances:
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    cls._instances['embeddings'] = HuggingFaceEmbeddings(
                        model_name="all-MiniLM-L6-v2",
                        cache_folder="./agent_cache/embeddings",
                        model_kwargs={'device': 'cpu'}
                    )
                    logger.info("Embeddings model loaded")
                except Exception as e:
                    logger.warning(f"Could not load embeddings: {e}")
                    cls._instances['embeddings'] = None
            return cls._instances['embeddings']
    
    @classmethod
    def get_voice_recognizer(cls):
        """Lazy load voice recognizer"""
        with cls._lock:
            if 'voice_recognizer' not in cls._instances:
                try:
                    import speech_recognition as sr
                    cls._instances['voice_recognizer'] = sr.Recognizer()
                except ImportError:
                    cls._instances['voice_recognizer'] = None
            return cls._instances['voice_recognizer']
    
    @classmethod
    def get_voice_engine(cls):
        """Lazy load TTS engine"""
        with cls._lock:
            if 'voice_engine' not in cls._instances:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 150)
                    engine.setProperty('volume', 0.9)
                    cls._instances['voice_engine'] = engine
                except Exception as e:
                    logger.warning(f"TTS unavailable: {e}")
                    cls._instances['voice_engine'] = None
            return cls._instances['voice_engine']


try:
    from langchain_ollama import ChatOllama
except ImportError:
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError:
        logger.error("Install langchain-ollama: pip install langchain-ollama")
        sys.exit(1)


from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


try:
    from diskcache import Cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("diskcache not available - caching disabled")


# ================================================================================
# PERFORMANCE UTILITIES
# ================================================================================


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start
            if elapsed > 1.0:
                logger.debug(f"[PERF] {func.__name__}: {elapsed:.2f}s")
    return wrapper


class PerformanceMonitor:
    """Thread-safe performance monitor"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record(self, operation: str, duration: float) -> None:
        """Record operation duration"""
        with self._lock:
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration)
            
            if len(self.metrics[operation]) > 100:
                self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_report(self) -> str:
        """Generate performance report"""
        lines = [
            "\n" + "="*70,
            "PERFORMANCE REPORT".center(70),
            "="*70
        ]
        
        with self._lock:
            metrics_copy = self.metrics.copy()
        
        if not metrics_copy:
            return "\n".join(lines + ["No metrics recorded yet"])
        
        for op, durations in sorted(metrics_copy.items()):
            if durations:
                avg = sum(durations) / len(durations)
                lines.append(
                    f"{op:<25} | Avg: {avg:.3f}s | "
                    f"Min: {min(durations):.3f}s | Max: {max(durations):.3f}s"
                )
        
        uptime = time.time() - self.start_time
        lines.append("="*70)
        lines.append(f"Uptime: {uptime:.1f}s")
        
        return "\n".join(lines)


perf_monitor = PerformanceMonitor()


# ================================================================================
# CONFIGURATION
# ================================================================================


class AgentConfig:
    """Configuration with validation"""
    
    MODEL = os.getenv("AGENT_MODEL", "llama3.1:8b")
    TEMPERATURE = float(os.getenv("AGENT_TEMP", "0.7"))
    MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITER", "15"))
    
    MEMORY_DIR = "./agent_memory"
    LOGS_DIR = "./agent_logs"
    DATA_DIR = "./agent_data"
    SECURE_DIR = "./agent_secure"
    CACHE_DIR = "./agent_cache"
    
    _cache: Optional['Cache'] = None
    _cache_lock = threading.Lock()
    
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    
    @classmethod
    def setup(cls) -> None:
        """Create directories and initialize cache"""
        dirs = [
            cls.MEMORY_DIR, cls.LOGS_DIR, cls.DATA_DIR,
            cls.SECURE_DIR, cls.CACHE_DIR
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(exist_ok=True, parents=True)
        
        if CACHE_AVAILABLE:
            with cls._cache_lock:
                if cls._cache is None:
                    try:
                        cls._cache = Cache(cls.CACHE_DIR, size_limit=500*1024*1024)
                        logger.info("Cache initialized")
                    except Exception as e:
                        logger.warning(f"Cache init failed: {e}")
    
    @classmethod
    def get_cache(cls) -> Optional['Cache']:
        """Get cache instance (thread-safe)"""
        with cls._cache_lock:
            if cls._cache is None and CACHE_AVAILABLE:
                try:
                    cls._cache = Cache(cls.CACHE_DIR)
                except Exception:
                    pass
            return cls._cache
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        for dir_path in [cls.MEMORY_DIR, cls.LOGS_DIR, cls.DATA_DIR]:
            if not Path(dir_path).exists():
                return False
        return True
    
    @classmethod
    def cleanup(cls) -> None:
        """Cleanup resources"""
        with cls._cache_lock:
            if cls._cache:
                try:
                    cls._cache.close()
                except Exception:
                    pass


AgentConfig.setup()
atexit.register(AgentConfig.cleanup)


# ================================================================================
# FIXED CONNECTION POOL
# ================================================================================


class ConnectionPool:
    """Thread-safe database connection pooling - FIXED VERSION"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool: List[sqlite3.Connection] = []
        self.in_use: set = set()
        self._lock = threading.Lock()
        self._closed = False
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection retrieval - FIXED"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        conn = None
        try:
            with self._lock:
                if self.pool:
                    conn = self.pool.pop()
                else:
                    conn = sqlite3.connect(
                        self.db_path,
                        check_same_thread=False,
                        timeout=10.0
                    )
                self.in_use.add(conn)
            
            yield conn
            
        except Exception as e:
            if conn:
                with self._lock:
                    self.in_use.discard(conn)
                try:
                    conn.close()
                except:
                    pass
            raise e
            
        finally:
            if conn:
                with self._lock:
                    if conn in self.in_use:
                        self.in_use.discard(conn)
                        if len(self.pool) < self.pool_size and not self._closed:
                            self.pool.append(conn)
                        else:
                            try:
                                conn.close()
                            except:
                                pass
    
    def close_all(self) -> None:
        """Close all connections - FIXED"""
        with self._lock:
            self._closed = True
            all_conns = list(self.pool) + list(self.in_use)
            for conn in all_conns:
                try:
                    conn.close()
                except Exception:
                    pass
            self.pool.clear()
            self.in_use.clear()


# ================================================================================
# ENHANCED SECURITY MANAGER
# ================================================================================


class SecurityManager:
    """Hardened security manager with advanced protection"""
    
    def __init__(self):
        self.config_dir = Path(AgentConfig.SECURE_DIR)
        self.config_dir.mkdir(exist_ok=True, parents=True)
        
        self.key_file = self.config_dir / "encryption.key"
        self.cipher = self._init_encryption()
        
        self.permissions = {
            "web_access": True,
            "file_read": True,
            "file_write": True,
            "file_delete": False,
            "system_commands": True,
            "email_send": True,
            "external_apis": True
        }
        
        self.rate_limits: Dict[str, List[float]] = {}
        self.max_requests_per_minute = 60
        self._rate_limit_lock = threading.Lock()
        self._last_cleanup = time.time()
        
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        self.blocked_operations: set = set()
        
        self.audit_db = self.config_dir / "audit.db"
        self.db_pool = ConnectionPool(str(self.audit_db), AgentConfig.DB_POOL_SIZE)
        self._init_audit_db()
        
        atexit.register(self.cleanup)
    
    def _init_encryption(self):
        """Initialize encryption"""
        from cryptography.fernet import Fernet
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                cipher = Fernet(key)
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                try:
                    os.chmod(self.key_file, 0o600)
                except:
                    pass
                cipher = Fernet(key)
            return cipher
        except Exception as e:
            logger.error(f"Encryption init error: {e}")
            raise RuntimeError("Failed to initialize encryption") from e
    
    def _init_audit_db(self) -> None:
        """Initialize audit database"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        success BOOLEAN NOT NULL,
                        user_approved BOOLEAN NOT NULL,
                        risk_level TEXT NOT NULL,
                        ip_hash TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON audit_log(timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_action 
                    ON audit_log(action)
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Audit DB init error: {e}")
            raise
    
    def encrypt(self, data: str) -> bytes:
        try:
            return self.cipher.encrypt(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes) -> str:
        try:
            return self.cipher.decrypt(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    @staticmethod
    def check_injection_patterns(text: str) -> bool:
        """Detect injection attempts"""
        for pattern in Constants.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                sec_logger.warning(f"Injection pattern detected: {pattern}")
                return True
        return False
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """Enhanced input sanitization"""
        if not user_input:
            return ""
        
        if len(user_input) > Constants.MAX_INPUT_LENGTH:
            logger.warning("Input truncated (too long)")
            user_input = user_input[:Constants.MAX_INPUT_LENGTH]
        
        if SecurityManager.check_injection_patterns(user_input):
            sec_logger.warning(f"Blocked malicious input: {user_input[:100]}")
            return ""
        
        sanitized = user_input.strip()
        
        return sanitized
    
    @staticmethod
    def validate_path(filepath: str, base_dir: str) -> Optional[Path]:
        """Validate path and prevent traversal attacks"""
        try:
            if not os.path.isabs(filepath):
                filepath = str(Path(base_dir) / filepath)
            
            resolved = Path(filepath).resolve()
            base = Path(base_dir).resolve()
            
            try:
                resolved.relative_to(base)
            except ValueError:
                sec_logger.warning(f"Path traversal blocked: {filepath}")
                return None
            
            return resolved
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return None
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Thread-safe rate limiting"""
        now = time.time()
        
        with self._rate_limit_lock:
            if now - self._last_cleanup > Constants.RATE_LIMIT_WINDOW:
                self._cleanup_rate_limits_internal()
            
            minute_ago = now - Constants.RATE_LIMIT_WINDOW
            
            if identifier in self.rate_limits:
                self.rate_limits[identifier] = [
                    t for t in self.rate_limits[identifier] if t > minute_ago
                ]
            else:
                self.rate_limits[identifier] = []
            
            if len(self.rate_limits[identifier]) >= self.max_requests_per_minute:
                logger.warning(f"Rate limit exceeded: {identifier}")
                return False
            
            self.rate_limits[identifier].append(now)
            return True
    
    def _cleanup_rate_limits_internal(self) -> None:
        now = time.time()
        minute_ago = now - Constants.RATE_LIMIT_WINDOW
        for identifier in list(self.rate_limits.keys()):
            self.rate_limits[identifier] = [
                t for t in self.rate_limits[identifier] if t > minute_ago
            ]
            if not self.rate_limits[identifier]:
                del self.rate_limits[identifier]
        self._last_cleanup = now
    
    def requires_user_confirmation(self, action: str, details: str = "") -> bool:
        """Check if action requires user confirmation"""
        action_lower = action.lower()
        
        for keyword in Constants.SENSITIVE_OPERATIONS:
            if keyword in action_lower:
                print(f"\n{'='*70}")
                print(f"[!] SECURITY WARNING - CONFIRMATION REQUIRED")
                print(f"{'='*70}")
                print(f"Action: {action}")
                if details:
                    print(f"Details: {details}")
                print(f"{'='*70}")
                
                try:
                    response = input("Approve this action? (yes/no): ").strip().lower()
                    approved = response == 'yes'
                    self.log_audit(action, details, approved, "HIGH", approved)
                    return approved
                except (KeyboardInterrupt, EOFError):
                    self.log_audit(action, details, False, "HIGH", False)
                    return False
        
        return True
    
    def check_permission(self, permission_type: str) -> bool:
        return self.permissions.get(permission_type, False)
    
    @timing_decorator
    def log_audit(
        self,
        action: str,
        details: str,
        success: bool,
        risk_level: str = "LOW",
        user_approved: bool = True
    ) -> None:
        """Thread-safe audit logging"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO audit_log 
                    (timestamp, action, details, success, user_approved, risk_level, ip_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        datetime.now().isoformat(),
                        action[:100],
                        details[:500],
                        success,
                        user_approved,
                        risk_level,
                        hashlib.sha256(b"localhost").hexdigest()
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Audit log error: {e}")
    
    def get_audit_report(self, days: int = 7) -> str:
        """Generate audit report"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                since = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute(
                    '''
                    SELECT timestamp, action, risk_level, success, user_approved
                    FROM audit_log
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                    ''',
                    (since,)
                )
                
                results = cursor.fetchall()
            
            if not results:
                return f"\nNo audit entries in the last {days} days"
            
            lines = [
                "\n" + "="*70,
                f"SECURITY AUDIT REPORT (Last {days} days)".center(70),
                "="*70
            ]
            
            for row in results:
                ts, action, risk, success, approved = row
                status = "[OK]" if success else "[FAIL]"
                approval = "USER" if approved else "AUTO"
                lines.append(
                    f"{status} [{risk:4}] [{approval:4}] {ts[:19]} - {action}"
                )
            
            lines.append("="*70)
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error generating report: {e}"
    
    def cleanup(self) -> None:
        try:
            self.db_pool.close_all()
        except Exception as e:
            logger.error(f"Security cleanup error: {e}")


security = SecurityManager()


# ================================================================================
# CREDENTIAL MANAGER
# ================================================================================


class CredentialManager:
    """Secure credential manager"""
    
    def __init__(self):
        self.creds_file = security.config_dir / "credentials.enc"
        self._credentials: Optional[Dict] = None
        self._dirty = False
        self._lock = threading.Lock()
    
    @property
    def credentials(self) -> Dict:
        """Thread-safe lazy load credentials"""
        with self._lock:
            if self._credentials is None:
                self._credentials = self._load_credentials()
            return self._credentials
    
    def _load_credentials(self) -> Dict:
        if not self.creds_file.exists():
            return {}
        
        try:
            with open(self.creds_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                return {}
            
            decrypted = security.decrypt(encrypted_data)
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Credential load error: {e}")
            return {}
    
    def _save_credentials(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            try:
                encrypted = security.encrypt(json.dumps(self.credentials))
                with open(self.creds_file, 'wb') as f:
                    f.write(encrypted)
                try:
                    os.chmod(self.creds_file, 0o600)
                except:
                    pass
                self._dirty = False
                logger.info("Credentials saved securely")
            except Exception as e:
                logger.error(f"Credential save error: {e}")
    
    def store(self, service: str, username: str, password: str) -> None:
        with self._lock:
            if service not in self.credentials:
                self.credentials[service] = {}
            
            self.credentials[service][username] = {
                'password': password,
                'created': datetime.now().isoformat()
            }
            self._dirty = True
        
        self._save_credentials()
        logger.info(f"Credentials stored: {service}/{username}")
    
    def retrieve(self, service: str, username: str) -> Optional[str]:
        try:
            with self._lock:
                return self.credentials[service][username]['password']
        except KeyError:
            return None


credentials = CredentialManager()


# ================================================================================
# FIXED MEMORY SYSTEM
# ================================================================================


class MemorySystem:
    """Enhanced memory system - FIXED CLEANUP"""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.conversation_history: List[Dict] = []
        self._initialized = False
        self._init_failed = False
        self._lock = threading.Lock()
        
        self.memory_db = Path(AgentConfig.MEMORY_DIR) / "conversations.db"
        self.db_pool = ConnectionPool(str(self.memory_db), 3)
        
        self.persist_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="memory-persist"
        )
        
        self._init_persistent_storage()
        self._load_recent_history()
        
        atexit.register(self.cleanup)
    
    def _init_persistent_storage(self):
        """Initialize persistent storage"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        session_id TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON conversations(timestamp DESC)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_role 
                    ON conversations(role)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_session_timestamp 
                    ON conversations(session_id, timestamp DESC)
                ''')
                
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA synchronous=NORMAL')
                cursor.execute('PRAGMA cache_size=10000')
                cursor.execute('PRAGMA temp_store=MEMORY')
                
                conn.commit()
                logger.info("Database optimized with indexes and WAL mode")


        except Exception as e:
            logger.error(f"Failed to initialize persistent storage: {e}")
            raise
    
    def auto_cleanup(self) -> None:
        """Automatic memory cleanup"""
        with self._lock:
            if len(self.conversation_history) > Constants.MAX_CONVERSATION_HISTORY:
                old_count = len(self.conversation_history)
                self.conversation_history = self.conversation_history[-Constants.MAX_CONVERSATION_HISTORY:]
                logger.info(f"Cleaned up {old_count - len(self.conversation_history)} old messages")
            
            gc.collect()
    
    def add_conversation(self, role: str, content: str) -> None:
        """Add to conversation with auto-cleanup"""
        timestamp = datetime.now().isoformat()
        
        with self._lock:
            self.conversation_history.append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })
            
            if len(self.conversation_history) % 10 == 0:
                self.auto_cleanup()
        
        if self.persist_executor:
            self.persist_executor.submit(self._persist_sync, timestamp, role, content)
    
    def _persist_sync(self, timestamp: str, role: str, content: str) -> None:
        """Sync database persistence"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations (timestamp, role, content)
                    VALUES (?, ?, ?)
                ''', (timestamp, role, content[:5000]))
                conn.commit()
        except Exception as e:
            logger.error(f"Persist error: {e}")
    
    def _load_recent_history(self):
        """Load recent conversation history"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT role, content, timestamp
                    FROM conversations
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (Constants.MAX_CONVERSATION_HISTORY,))
                
                rows = cursor.fetchall()
            
            for role, content, ts in reversed(rows):
                self.conversation_history.append({
                    "role": role,
                    "content": content,
                    "timestamp": ts
                })
            
            if rows:
                logger.info(f"Loaded {len(rows)} conversation entries")
        except Exception as e:
            logger.error(f"History load error: {e}")
    
    def _lazy_init(self) -> bool:
        """Lazy init vector store"""
        with self._lock:
            if self._initialized or self._init_failed:
                return self._initialized
            
            try:
                self.embeddings = LazyLoader.get_embeddings()
                
                if self.embeddings is None:
                    logger.warning("Embeddings unavailable - using simple memory")
                    self._init_failed = True
                    return False
                
                try:
                    from langchain_chroma import Chroma
                except ImportError:
                    from langchain_community.vectorstores import Chroma
                
                self.vectorstore = Chroma(
                    persist_directory=AgentConfig.MEMORY_DIR,
                    embedding_function=self.embeddings,
                    collection_name="agent_memory"
                )
                logger.info("Vector memory initialized")
                self._initialized = True
                return True
                
            except Exception as e:
                logger.warning(f"Vector memory init failed: {e}")
                self._init_failed = True
                return False
    
    def store_long_term(self, content: str) -> str:
        """Store in vector memory"""
        if not self._lazy_init():
            return "[WARN] Vector memory unavailable"
        
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'type': 'user_stored'
            }
            self.vectorstore.add_texts([content], metadatas=[metadata])
            logger.info(f"Stored to vector memory: {content[:50]}...")
            return "[SUCCESS] Memory stored successfully"
            
        except Exception as e:
            logger.error(f"Storage error: {e}")
            return "[ERROR] Memory storage failed"
    
    def recall(self, query: str, k: int = 5) -> str:
        """Recall from vector memory"""
        if not self._lazy_init():
            return "[WARN] Vector memory unavailable"
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            if not docs:
                return "No relevant memories found"
            
            results = [f"{i+1}. {doc.page_content}" for i, doc in enumerate(docs)]
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Recall error: {e}")
            return "[ERROR] Memory recall failed"
    
    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """Get recent conversation context"""
        with self._lock:
            return self.conversation_history[-n:] if self.conversation_history else []
    
    def clear_conversation(self) -> None:
        """Clear current session conversation"""
        with self._lock:
            self.conversation_history.clear()
        gc.collect()
        logger.info("Conversation cleared")
    
    def cleanup(self):
        """Cleanup resources - FIXED"""
        try:
            if self.persist_executor:
                self.persist_executor.shutdown(wait=True)
            
            self.db_pool.close_all()
            
            logger.info("Memory system cleaned up")
            
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")


# ================================================================================
# ENHANCED WEB TOOLS
# ================================================================================


class WebTools:
    """Web tools with improved error handling and caching"""
    
    _session: Optional[requests.Session] = None
    _session_lock = threading.Lock()
    
    @classmethod
    def get_session(cls) -> requests.Session:
        with cls._session_lock:
            if cls._session is None:
                cls._session = requests.Session()
                cls._session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=10,
                    pool_maxsize=20,
                    max_retries=3
                )
                cls._session.mount('http://', adapter)
                cls._session.mount('https://', adapter)
            return cls._session
    
    @staticmethod
    @timing_decorator
    def search_web(query: str) -> str:
        """Search the web"""
        try:
            if not security.check_permission("web_access"):
                return "[ERROR] Web access disabled"
            
            cache = AgentConfig.get_cache()
            cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
            
            if cache:
                cached = cache.get(cache_key)
                if cached:
                    logger.info("Using cached search results")
                    return cached
            
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return "[ERROR] duckduckgo-search not installed"
            
            sanitized = SecurityManager.sanitize_input(query)
            if not sanitized:
                return "[ERROR] Invalid query"
            
            logger.info(f"Searching: {sanitized}")
            
            with DDGS() as ddgs:
                results = list(ddgs.text(sanitized, max_results=Constants.MAX_SEARCH_RESULTS))
            
            if not results:
                return "No results found"
            
            output = ["Search Results:", "="*60]
            for i, r in enumerate(results, 1):
                title = r.get('title', 'No Title')
                body = r.get('body', '')[:300]
                href = r.get('href', '')
                output.append(f"\n{i}. {title}")
                output.append(f"   {body}")
                output.append(f"   URL: {href}")
            
            result_str = "\n".join(output)
            
            if cache:
                cache.set(cache_key, result_str, expire=Constants.CACHE_TTL_SEARCH)
            
            return result_str
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return "[ERROR] Search failed"
    
    @staticmethod
    @timing_decorator
    def fetch_webpage(url: str) -> str:
        """Fetch webpage content"""
        try:
            if not security.check_permission("web_access"):
                return "[ERROR] Web access disabled"
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if not re.match(r'https?://[^\s]+', url):
                return "[ERROR] Invalid URL"
            
            cache = AgentConfig.get_cache()
            cache_key = f"webpage:{hashlib.md5(url.encode()).hexdigest()}"
            
            if cache:
                cached = cache.get(cache_key)
                if cached:
                    return cached
            
            session = WebTools.get_session()
            response = session.get(url, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            text = soup.get_text(separator=' ', strip=True)[:Constants.MAX_WEBPAGE_LENGTH]
            result = f"Content from {url}:\n{'='*60}\n{text}"
            
            if cache:
                cache.set(cache_key, result, expire=Constants.CACHE_TTL_WEBPAGE)
            
            return result
            
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return "[ERROR] Failed to fetch webpage"
    
    @staticmethod
    def open_website(url: str) -> str:
        """Open website in browser"""
        try:
            import webbrowser
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return f"[SUCCESS] Opened {url}"
        except Exception as e:
            return "[ERROR] Failed to open browser"
        
    @staticmethod
    @timing_decorator
    def smart_search(query: str) -> str:
        """OPTIMIZED: Parallel fetching for 3x faster results"""
        try:
            if not security.check_permission("web_access"):
                return "[ERROR] Web access disabled"
            
            logger.info(f"[SMART SEARCH] Query: {query}")
            start_time = time.time()
            
            search_results = WebTools.search_web(query)
            
            if "[ERROR]" in search_results or "No results found" in search_results:
                return search_results
            
            url_pattern = r'URL: (https?://[^\s]+)'
            urls = re.findall(url_pattern, search_results)
            
            if not urls:
                return search_results
            
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            comprehensive = f"SEARCH RESULTS:\n{search_results}\n\nDETAILED CONTENT:\n{'='*60}\n"
            
            def fetch_with_index(url_tuple):
                """Helper to fetch with index"""
                idx, url = url_tuple
                try:
                    content = WebTools.fetch_webpage(url)
                    if "[ERROR]" not in content:
                        return (idx, url, content[:3000])
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                return None
            
            urls_to_fetch = list(enumerate(urls[:Constants.MAX_SOURCES_TO_FETCH], 1))
            sources = []
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(fetch_with_index, url_tuple): url_tuple for url_tuple in urls_to_fetch}
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        sources.append(result)
            
            for idx, url, content in sorted(sources):
                comprehensive += f"\n\nSOURCE {idx} - {url}:\n{content}\n"
            
            elapsed = time.time() - start_time
            logger.info(f"[SMART SEARCH] Completed in {elapsed:.2f}s ({len(sources)} sources)")
            
            return comprehensive
            
        except Exception as e:
            logger.error(f"Smart search error: {e}")
            return f"[ERROR] Smart search failed: {e}"


# ================================================================================
# FIXED SYSTEM TOOLS
# ================================================================================


class SystemTools:
    """System tools with command whitelisting"""
    
    _system_info_cache = None
    _system_info_time = 0
    _cache_lock = threading.Lock()
    
    @staticmethod
    def open_application(app_name: str) -> str:
        """Open application safely - FIXED VERSION"""
        try:
            app_map = {
                "chrome": ["chrome"] if os.name != 'nt' else ["cmd", "/c", "start", "chrome"],
                "firefox": ["firefox"],
                "notepad": ["notepad"] if os.name == 'nt' else ["gedit"],
                "calculator": ["calc"] if os.name == 'nt' else ["gnome-calculator"],
            }
            
            command = app_map.get(app_name.lower())
            if not command:
                return f"[ERROR] Unknown application: {app_name}"
            
            subprocess.Popen(command, shell=False)
            return f"[SUCCESS] Opened {app_name}"
            
        except Exception as e:
            logger.error(f"App open error: {e}")
            return "[ERROR] Failed to open application"
    
    @staticmethod
    @timing_decorator
    def run_command(command: str) -> str:
        """Execute system command with strict security"""
        try:
            if not security.check_permission("system_commands"):
                return "[ERROR] System commands disabled"
            
            if not security.requires_user_confirmation("run_command", command):
                return "[CANCELLED] User denied permission"
            
            try:
                args = shlex.split(command)
            except ValueError:
                return "[ERROR] Invalid command syntax"
            
            if not args:
                return "[ERROR] Empty command"
            
            base_cmd = os.path.basename(args[0])
            if base_cmd not in Constants.ALLOWED_COMMANDS:
                return f"[ERROR] Command not allowed: {base_cmd}\nAllowed: {', '.join(sorted(Constants.ALLOWED_COMMANDS))}"
            
            logger.warning(f"Executing: {command}")
            sec_logger.warning(f"Command executed: {command}")
            
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=Constants.COMMAND_TIMEOUT,
                cwd=os.getcwd()
            )
            
            output = [f"Exit Code: {result.returncode}"]
            if result.stdout:
                output.append(f"\nOutput:\n{result.stdout[:2000]}")
            if result.stderr:
                output.append(f"\nErrors:\n{result.stderr[:1000]}")
            
            security.log_audit("run_command", command, result.returncode == 0, "HIGH", True)
            return "\n".join(output)
            
        except subprocess.TimeoutExpired:
            return f"[ERROR] Command timeout (>{Constants.COMMAND_TIMEOUT}s)"
        except Exception as e:
            logger.error(f"Command error: {e}")
            return "[ERROR] Command execution failed"
    
    @staticmethod
    def get_system_info() -> str:
        """Get system information with caching"""
        with SystemTools._cache_lock:
            now = time.time()
            if (SystemTools._system_info_cache and 
                now - SystemTools._system_info_time < Constants.SYSTEM_INFO_CACHE_TTL):
                return SystemTools._system_info_cache
            
            try:
                import psutil
                
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                
                info = f"""System Information:
{'='*60}
CPU Usage: {cpu}%
Memory: {mem.percent}% used ({mem.used/1e9:.1f}GB / {mem.total/1e9:.1f}GB)
Disk: {disk.percent}% used ({disk.used/1e9:.1f}GB / {disk.total/1e9:.1f}GB)
Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
Platform: {sys.platform}
{'='*60}
"""
                SystemTools._system_info_cache = info
                SystemTools._system_info_time = now
                return info
            except ImportError:
                return "[ERROR] psutil not installed"
            except Exception as e:
                logger.error(f"System info error: {e}")
                return "[ERROR] Could not retrieve system info"
    
    @staticmethod
    def take_screenshot(filename: str = "") -> str:
        """Take screenshot"""
        try:
            import pyautogui
            
            if not filename:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            if not filename.endswith(('.png', '.jpg', '.jpeg')):
                filename += '.png'
            
            filepath = security.validate_path(filename, AgentConfig.DATA_DIR)
            if not filepath:
                return "[ERROR] Invalid file path"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return f"[SUCCESS] Screenshot saved: {filepath.name}"
        except ImportError:
            return "[ERROR] pyautogui not installed (pip install pyautogui pillow)"
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return "[ERROR] Screenshot failed"


# ================================================================================
# FILE TOOLS
# ================================================================================


class FileTools:
    """File tools with enhanced validation"""
    
    @staticmethod
    def create_file(filepath: str, content: str = "") -> str:
        """Create file with validation"""
        try:
            if not security.check_permission("file_write"):
                return "[ERROR] File write permission denied"
            
            validated_path = security.validate_path(filepath, AgentConfig.DATA_DIR)
            if not validated_path:
                return "[ERROR] Invalid file path"
            
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(validated_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            security.log_audit("create_file", str(validated_path), True, "MEDIUM")
            logger.info(f"File created: {validated_path.name}")
            return f"[SUCCESS] File created: {validated_path.name} ({len(content)} bytes)"
            
        except Exception as e:
            logger.error(f"File create error: {e}")
            security.log_audit("create_file", filepath, False, "MEDIUM")
            return f"[ERROR] Failed to create file: {str(e)}"
    
    @staticmethod
    def read_file(filepath: str) -> str:
        """Read file with size limits"""
        try:
            if not security.check_permission("file_read"):
                return "[ERROR] File read permission denied"
            
            validated_path = security.validate_path(filepath, AgentConfig.DATA_DIR)
            if not validated_path:
                validated_path = Path(filepath).resolve()
            
            if not validated_path.exists():
                return f"[ERROR] File not found: {filepath}"
            
            file_size = validated_path.stat().st_size
            
            try:
                with open(validated_path, 'r', encoding='utf-8') as f:
                    content = f.read(Constants.MAX_FILE_READ_SIZE)
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 decode failed for {filepath}, trying latin-1")
                with open(validated_path, 'r', encoding='latin-1', errors='replace') as f:
                    content = f.read(Constants.MAX_FILE_READ_SIZE)
                content = f"[Warning: File contained non-UTF-8 characters]\n\n{content}"
            
            result = [
                f"File: {validated_path.name}",
                f"Size: {file_size} bytes",
                "="*60,
                content
            ]
            
            if file_size > Constants.MAX_FILE_READ_SIZE:
                result.append("\n... [truncated]")
            
            logger.info(f"File read: {validated_path.name}")
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"File read error: {e}")
            return f"[ERROR] Failed to read file: {str(e)}"
    
    @staticmethod
    def list_files(directory: str = ".") -> str:
        """List directory contents"""
        try:
            if directory == ".":
                directory = AgentConfig.DATA_DIR
            
            validated_path = security.validate_path(directory, AgentConfig.DATA_DIR)
            if not validated_path:
                validated_path = Path(directory).resolve()
            
            if not validated_path.exists():
                return f"[ERROR] Directory not found: {directory}"
            
            if not validated_path.is_dir():
                return f"[ERROR] Not a directory: {directory}"
            
            items = sorted(validated_path.glob("*"), key=lambda x: (not x.is_dir(), x.name))
            items = items[:Constants.MAX_LIST_FILES]
            
            file_list = [f"Directory: {validated_path}", "="*60]
            
            for item in items:
                if item.is_dir():
                    file_list.append(f"[DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    file_list.append(f"[FILE] {item.name} ({size:,} bytes)")
            
            total_items = len(list(validated_path.glob("*")))
            if total_items > Constants.MAX_LIST_FILES:
                file_list.append(f"\n... ({total_items - Constants.MAX_LIST_FILES} more items)")
            
            logger.info(f"Listed directory: {validated_path}")
            return "\n".join(file_list)
            
        except Exception as e:
            logger.error(f"List files error: {e}")
            return f"[ERROR] Failed to list directory: {str(e)}"
    
    @staticmethod
    def delete_file(filepath: str) -> str:
        """Delete file with confirmation"""
        try:
            if not security.check_permission("file_delete"):
                return "[ERROR] File delete permission denied"
            
            if not security.requires_user_confirmation("delete_file", filepath):
                security.log_audit("delete_file", filepath, False, "HIGH", False)
                return "[CANCELLED] User denied deletion"
            
            validated_path = security.validate_path(filepath, AgentConfig.DATA_DIR)
            if not validated_path or not validated_path.exists():
                return "[ERROR] File not found"
            
            validated_path.unlink()
            
            security.log_audit("delete_file", str(validated_path), True, "HIGH", True)
            logger.info(f"File deleted: {validated_path.name}")
            return f"[SUCCESS] Deleted: {validated_path.name}"
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            security.log_audit("delete_file", filepath, False, "HIGH", True)
            return f"[ERROR] Failed to delete file: {str(e)}"
    
    @staticmethod
    def append_to_file(filepath: str, content: str) -> str:
        """Append to existing file"""
        try:
            if not security.check_permission("file_write"):
                return "[ERROR] File write permission denied"
            
            validated_path = security.validate_path(filepath, AgentConfig.DATA_DIR)
            if not validated_path:
                return "[ERROR] Invalid file path"
            
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(validated_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            security.log_audit("append_file", str(validated_path), True, "MEDIUM")
            logger.info(f"Appended to file: {validated_path.name}")
            return f"[SUCCESS] Appended {len(content)} bytes to {validated_path.name}"
            
        except Exception as e:
            logger.error(f"Append error: {e}")
            return f"[ERROR] Failed to append to file: {str(e)}"


# ================================================================================
# EMAIL MANAGER
# ================================================================================


class EmailManager:
    """Email manager with security"""
    
    @staticmethod
    def send_email(to_addr: str, subject: str, body: str, from_addr: str = "") -> str:
        """Send email with validation"""
        try:
            if not security.check_permission("email_send"):
                return "[ERROR] Email permission denied"
            
            if not security.requires_user_confirmation("send_email", f"To: {to_addr}"):
                return "[CANCELLED] User denied email send"
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'


            if not re.match(email_pattern, to_addr):
                return f"[ERROR] Invalid email: {to_addr}"
            
            if not from_addr:
                from_addr = input("Your email address: ").strip()
            
            password = credentials.retrieve("email", from_addr)
            if not password:
                password = input(f"Password for {from_addr}: ").strip()
                if input("Save password? (yes/no): ").lower() == 'yes':
                    credentials.store("email", from_addr, password)
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                server.starttls()
                server.login(from_addr, password)
                server.send_message(msg)
            
            security.log_audit("send_email", f"To: {to_addr}", True, "MEDIUM", True)
            return f"[SUCCESS] Email sent to {to_addr}"
        except Exception as e:
            logger.error(f"Email error: {e}")
            return "[ERROR] Email failed to send"


# ================================================================================
# VOICE INTERFACE
# ================================================================================


class VoiceInterface:
    """Voice interface with non-blocking TTS"""
    
    def __init__(self):
        self.enabled = False
        self.recognizer = None
        self.engine = None
        self._init_attempted = False
        self._speech_lock = threading.Lock()
    
    def _lazy_init(self) -> bool:
        if self._init_attempted:
            return self.enabled
        
        self._init_attempted = True
        try:
            self.recognizer = LazyLoader.get_voice_recognizer()
            self.engine = LazyLoader.get_voice_engine()
            self.enabled = (self.recognizer is not None and self.engine is not None)
            if self.enabled:
                logger.info("Voice interface enabled")
            return self.enabled
        except Exception:
            return False
    
    def listen(self, timeout: int = 5) -> Optional[str]:
        """Listen for voice input"""
        if not self._lazy_init():
            return None
        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                print("[LISTEN] Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)
                text = self.recognizer.recognize_google(audio)
                print(f"Heard: {text}")
                return text
        except Exception as e:
            logger.debug(f"Voice input failed: {e}")
            return None
    
    def _speak_thread(self, text: str):
        """Internal speech thread"""
        with self._speech_lock:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS error: {e}")


    def speak(self, text: str) -> None:
        """Non-blocking text-to-speech"""
        if not self._lazy_init():
            return
        
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'\[.*?\]', '', text)
        text = text[:500]
        
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()


# ================================================================================
# TOOL REGISTRY
# ================================================================================


class ToolRegistry:
    """Enhanced tool registry with argument validation"""
    
    def __init__(self, memory: MemorySystem):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.memory = memory
        self._register_all_tools()
        self._description_cache: Optional[str] = None
    
    def _register_all_tools(self) -> None:
        """Register all available tools"""
        self.tools = {
            'search_web': {
                'func': WebTools.search_web,
                'description': 'Search the internet for information',
                'args': ['query'],
                'required_args': 1,
                'validator': lambda q: isinstance(q, str) and len(q) > 0
            },
            'smart_search': {
                'func': WebTools.smart_search,
                'description': 'Intelligent search that reads multiple sources and synthesizes information',
                'args': ['query'],
                'required_args': 1,
                'validator': lambda q: isinstance(q, str) and len(q) > 0
            },
            'fetch_webpage': {
                'func': WebTools.fetch_webpage,
                'description': 'Fetch and extract content from a webpage',
                'args': ['url'],
                'required_args': 1,
                'validator': lambda u: isinstance(u, str) and len(u) > 0
            },
            'open_website': {
                'func': WebTools.open_website,
                'description': 'Open a website in the default browser',
                'args': ['url'],
                'required_args': 1,
                'validator': lambda u: len(u) > 0
            },
            'open_app': {
                'func': SystemTools.open_application,
                'description': 'Open an application (chrome, firefox, notepad, etc.)',
                'args': ['app_name'],
                'required_args': 1,
                'validator': lambda a: len(a) > 0
            },
            'system_info': {
                'func': SystemTools.get_system_info,
                'description': 'Get current system information (CPU, memory, disk)',
                'args': [],
                'required_args': 0,
                'validator': None
            },
            'screenshot': {
                'func': SystemTools.take_screenshot,
                'description': 'Take a screenshot and save it',
                'args': ['filename'],
                'required_args': 0,
                'validator': None
            },
            'run_command': {
                'func': SystemTools.run_command,
                'description': 'Run a system command (whitelisted commands only)',
                'args': ['command'],
                'required_args': 1,
                'validator': lambda c: len(c) > 0
            },
            'create_file': {
                'func': FileTools.create_file,
                'description': 'Create a new file with content',
                'args': ['filepath', 'content'],
                'required_args': 1,
                'validator': lambda f: '..' not in f
            },
            'read_file': {
                'func': FileTools.read_file,
                'description': 'Read the contents of a file',
                'args': ['filepath'],
                'required_args': 1,
                'validator': lambda f: len(f) > 0
            },
            'list_files': {
                'func': FileTools.list_files,
                'description': 'List files in a directory',
                'args': ['directory'],
                'required_args': 0,
                'validator': None
            },
            'delete_file': {
                'func': FileTools.delete_file,
                'description': 'Delete a file (requires confirmation)',
                'args': ['filepath'],
                'required_args': 1,
                'validator': lambda f: len(f) > 0
            },
            'append_file': {
                'func': FileTools.append_to_file,
                'description': 'Append content to an existing file',
                'args': ['filepath', 'content'],
                'required_args': 2,
                'validator': lambda f: len(f) > 0
            },
            'store_memory': {
                'func': self.memory.store_long_term,
                'description': 'Store information in long-term memory',
                'args': ['content'],
                'required_args': 1,
                'validator': lambda c: len(c) > 0
            },
            'recall_memory': {
                'func': self.memory.recall,
                'description': 'Search and recall from long-term memory',
                'args': ['query'],
                'required_args': 1,
                'validator': lambda q: len(q) > 0
            },
            'send_email': {
                'func': EmailManager.send_email,
                'description': 'Send an email (requires confirmation)',
                'args': ['to_addr', 'subject', 'body'],
                'required_args': 3,
                'validator': lambda e: '@' in e
            }
        }
    
    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions"""
        if self._description_cache is None:
            descriptions = ["Available Tools:", "="*60]
            for name, info in sorted(self.tools.items()):
                args_str = ", ".join(info['args']) if info['args'] else "none"
                descriptions.append(f"- {name}({args_str})")
                descriptions.append(f"  {info['description']}")
            self._description_cache = "\n".join(descriptions)
        return self._description_cache
    
    @timing_decorator
    def execute_tool(self, tool_name: str, args: List[str]) -> str:
        """Execute tool with validation"""
        if tool_name not in self.tools:
            return f"[ERROR] Unknown tool: {tool_name}"
        
        tool = self.tools[tool_name]
        
        if len(args) < tool['required_args']:
            return f"[ERROR] {tool_name} requires {tool['required_args']} arguments"
        
        if tool['validator'] and args:
            try:
                if not tool['validator'](args[0]):
                    return f"[ERROR] Invalid argument for {tool_name}"
            except Exception:
                return f"[ERROR] Argument validation failed"
        
        try:
            func = tool['func']
            
            padded_args = args + [''] * (len(tool['args']) - len(args))
            actual_args = padded_args[:len(tool['args'])]
            
            result = func() if not tool['args'] else func(*actual_args)
            
            result_str = str(result)
            if len(result_str) > Constants.MAX_TOOL_OUTPUT_LENGTH:
                result_str = result_str[:Constants.MAX_TOOL_OUTPUT_LENGTH] + "\n... [output truncated]"
            
            return result_str
            
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return "[ERROR] Tool execution failed"


# ================================================================================
# VALIDATION AND MAIN AGENT CLASS
# ================================================================================


def validate_council_setup() -> bool:
    """Validate council setup"""
    has_primary = bool(os.getenv('OPENROUTER_API_KEY'))
    has_backup = (bool(os.getenv('GROQ_API_KEY')) or 
                 bool(os.getenv('GOOGLE_API_KEY')))
    
    if not has_primary and not has_backup:
        logger.error("No councils available!")
        return False
    
    if has_primary:
        logger.info("[OK] Primary Council (OpenRouter) available")
    else:
        logger.warning("[!] Primary Council unavailable - will use backup only")
    
    if has_backup:
        logger.info("[OK] Backup Council available")
    else:
        logger.warning("[!] No backup council - primary is single point of failure")
    
    return True


def validate_environment():
    """Validate required environment variables"""
    has_ollama = True
    has_council = False
    
    if os.getenv("OPENROUTER_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        has_council = True
        logger.info("Council mode available")
        
        panels = ["PANEL_STRATEGIST", "PANEL_LIBRARIAN", "PANEL_ARCHITECT", 
                  "PANEL_OBSERVER", "PANEL_AUDITOR"]
        missing_panels = [p for p in panels if not os.getenv(p)]
        
        if missing_panels:
            logger.warning(f"Missing panel configs: {', '.join(missing_panels)}")
            logger.warning("Set these in .env for full Council functionality")
    
    if not has_council:
        try:
            response = requests.get("http://localhost:11434", timeout=2)
            logger.info("Ollama available as fallback")
        except:
            has_ollama = False
            logger.error("Neither Council nor Ollama available!")
    
    if not has_council and not has_ollama:
        print("\n[X] FATAL ERROR: No AI backend available!")
        print("\nOptions:")
        print("1. Set OPENROUTER_API_KEY in .env for Council mode")
        print("2. Start Ollama: ollama serve")
        sys.exit(1)
    
    return has_council, has_ollama


# ================================================================================
# FIXED DUAL COUNCIL ORCHESTRATOR
# ================================================================================


class DualCouncilMember:
    """Council member supporting multiple providers"""
    
    def __init__(self, model_spec: str, role: str):
        """
        model_spec can be:
        - "model/name:free" (OpenRouter, default)
        - "provider:model_name" (Groq/Gemini/Ollama)
        """
        if ':' in model_spec and '/' not in model_spec.split(':')[0]:
            self.provider, self.model = model_spec.split(':', 1)
        else:
            self.provider = 'openrouter'
            self.model = model_spec
        
        self.role = role
        self.name = f"{role}[{self.provider.upper()}]"


class DualCouncilOrchestrator:
    """
    FIXED VERSION: Manages two councils with internal consensus
    - Primary: OpenRouter free models
    - Backup: Groq + Gemini + Ollama
    """
    
    def __init__(self):
        self.primary_failures = 0
        self.primary_cooldown_until = None
        self.using_backup = False
        
        self.has_openrouter = bool(os.getenv('OPENROUTER_API_KEY'))
        self.has_groq = bool(os.getenv('GROQ_API_KEY'))
        self.has_gemini = bool(os.getenv('GOOGLE_API_KEY'))
        self.has_ollama = self._check_ollama()
        
        self.backup_available = (self.has_groq or self.has_gemini or self.has_ollama)
        
        logger.info(f"Primary Council (OpenRouter): {self.has_openrouter}")
        logger.info(f"Backup Council Available: {self.backup_available}")
        logger.info(f"  - Groq: {self.has_groq}")
        logger.info(f"  - Gemini: {self.has_gemini}")
        logger.info(f"  - Ollama: {self.has_ollama}")
        
        self.primary_panels = self._recruit_council('PANEL_')
        self.backup_panels = self._recruit_council('BACKUP_PANEL_')
        
        primary_chair = os.getenv("CHAIRPERSON_MODEL", "tngtech/deepseek-r1t2-chimera:free")
        self.primary_chairperson = DualCouncilMember(primary_chair, "Chairperson")
        
        backup_chair = os.getenv("BACKUP_CHAIRPERSON_MODEL", "gemini:gemini-2.5-flash")
        self.backup_chairperson = DualCouncilMember(backup_chair, "Backup-Chairperson")
        
        self.rate_limiters = {
            'openrouter': {'requests': [], 'rpm': 10},
            'groq': {'requests': [], 'rpm': 30, 'daily': 0, 'daily_limit': 14400},
            'gemini': {'requests': [], 'rpm': 15, 'daily': 0, 'daily_limit': 1500},
            'ollama': {'requests': [], 'rpm': 999}
        }
        self.daily_reset = datetime.now()
        self._rate_lock = threading.Lock()
        
        self.stats = {
            'primary_calls': 0,
            'backup_calls': 0,
            'primary_failures': 0,
            'backup_failures': 0,
            'total_fallbacks': 0,
            'primary_consensus_score': 0,
            'backup_consensus_score': 0,
            'primary_has_disagreement': False,
            'primary_disagreement_severity': 'low',
            'quality_checks': 0,
            'quality_fallbacks': 0
        }
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _recruit_council(self, prefix: str) -> Dict[str, List[DualCouncilMember]]:
        """Recruit a council (primary or backup)"""
        panels = defaultdict(list)
        
        role_vars = {
            "Strategist": f"{prefix}STRATEGIST",
            "Librarian": f"{prefix}LIBRARIAN",
            "Architect": f"{prefix}ARCHITECT",
            "Observer": f"{prefix}OBSERVER",
            "Auditor": f"{prefix}AUDITOR"
        }
        
        for role, env_var in role_vars.items():
            config = os.getenv(env_var, "")
            if config:
                members_config = [m.strip() for m in config.split(',') if m.strip()]
                for member_spec in members_config:
                    try:
                        member = DualCouncilMember(member_spec, role)
                        panels[role].append(member)
                    except Exception as e:
                        logger.error(f"Failed to create member from {member_spec}: {e}")
        
        council_type = "Primary" if prefix == "PANEL_" else "Backup"
        logger.info(f"{council_type} Council: {sum(len(p) for p in panels.values())} members")
        
        return panels
    
    def _should_use_backup(self) -> bool:
        """Determine if we should use backup council"""
        if not os.getenv('ENABLE_BACKUP_COUNCIL', 'true').lower() == 'true':
            return False
        
        if not self.backup_available:
            return False
        
        if self.primary_cooldown_until:
            if datetime.now() < self.primary_cooldown_until:
                logger.info("Primary council in cooldown, using backup")
                return True
            else:
                self.primary_cooldown_until = None
                self.primary_failures = 0
                logger.info("Primary council cooldown expired, retrying")
        
        failures_threshold = int(os.getenv('FAILURES_BEFORE_BACKUP', '2'))
        if self.primary_failures >= failures_threshold:
            cooldown = int(os.getenv('PRIMARY_COOLDOWN', '60'))
            self.primary_cooldown_until = datetime.now() + timedelta(seconds=cooldown)
            logger.warning(f"Primary council failed {self.primary_failures} times, "
                         f"switching to backup for {cooldown}s")
            return True
        
        return False
    
    def _can_call_provider(self, provider: str) -> bool:
        """FIXED: Thread-safe rate limit check"""
        with self._rate_lock:
            limiter = self.rate_limiters[provider]
            now = time.time()
            
            if datetime.now().date() > self.daily_reset.date():
                limiter['daily'] = 0
                self.daily_reset = datetime.now()
            
            if 'daily_limit' in limiter and limiter['daily'] >= limiter['daily_limit']:
                return False
            
            limiter['requests'] = [t for t in limiter['requests'] if t > now - 60]
            
            return len(limiter['requests']) < limiter['rpm']
    
    def _record_call(self, provider: str):
        """FIXED: Thread-safe call recording"""
        with self._rate_lock:
            limiter = self.rate_limiters[provider]
            limiter['requests'].append(time.time())
            if 'daily' in limiter:
                limiter['daily'] += 1
    
    async def _call_member(
        self,
        session: aiohttp.ClientSession,
        member: DualCouncilMember,
        prompt: str
    ) -> Dict:
        """Call a single council member with aggressive timeout"""
        
        if not self._can_call_provider(member.provider):
            return {
                "name": member.name,
                "text": f"[Rate limited: {member.provider}]",
                "success": False
            }
        
        self._record_call(member.provider)
        
        timeout_map = {
            'openrouter': 30.0,  
            'groq': 20.0,        
            'gemini': 25.0,      
            'ollama': 45.0       
        }
        
        call_timeout = timeout_map.get(member.provider, 30.0)
        
        try:
            if member.provider == 'openrouter':
                result = await asyncio.wait_for(
                    self._call_openrouter(session, member, prompt),
                    timeout=call_timeout
                )
            elif member.provider == 'groq':
                result = await asyncio.wait_for(
                    self._call_groq(session, member, prompt),
                    timeout=call_timeout
                )
            elif member.provider == 'gemini':
                result = await asyncio.wait_for(
                    self._call_gemini(session, member, prompt),
                    timeout=call_timeout
                )
            elif member.provider == 'ollama':
                result = await asyncio.wait_for(
                    self._call_ollama(member, prompt),
                    timeout=call_timeout
                )
            else:
                raise ValueError(f"Unknown provider: {member.provider}")
            
            if 'name' not in result:
                result['name'] = member.name
            
            result['success'] = True
            return result
        
        except asyncio.TimeoutError:
            logger.warning(f"{member.name} timeout ({call_timeout}s)")
            return {
                "name": member.name,
                "text": f"[Timeout after {call_timeout}s]",
                "success": False
            }
            
        except Exception as e:
            logger.error(f"{member.name} failed: {e}")
            return {
                "name": member.name,
                "text": f"[Error: {str(e)[:100]}]",
                "success": False
            }
    
    async def _call_openrouter(
        self,
        session: aiohttp.ClientSession,
        member: DualCouncilMember,
        prompt: str
    ) -> Dict:
        """FIXED: Call OpenRouter API with proper retry"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        if not api_key:
            raise Exception("OPENROUTER_API_KEY not set")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Agent Council"
        }
        
        payload = {
            "model": member.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.5
        }
        
        last_error = None
        for attempt in range(3):
            try:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 429:
                        if attempt < 2:
                            wait_time = (attempt + 1) * 2
                            logger.warning(f"Rate limit hit. Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        raise Exception("Rate limited after retries")
                    
                    if response.status == 402:
                        raise Exception("Credits required")
                    
                    if response.status != 200:
                        logger.error(f"OpenRouter error: {response_text[:200]}")
                        raise Exception(f"HTTP {response.status}")
                    
                    data = json.loads(response_text)
                    
                    if 'error' in data:
                        raise Exception(data['error'].get('message', 'Unknown error'))
                    
                    return {
                        "name": member.name,
                        "text": data['choices'][0]['message']['content']
                    }
                    
            except asyncio.TimeoutError as e:
                last_error = e
                if attempt < 2:
                    logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)
                    continue
                raise Exception("Request timeout after retries")
            except Exception as e:
                last_error = e
                if attempt < 2 and "rate limit" in str(e).lower():
                    await asyncio.sleep((attempt + 1) * 2)
                    continue
                raise
        
        raise Exception(f"All retries failed: {last_error}")
    
    async def _call_groq(
        self,
        session: aiohttp.ClientSession,
        member: DualCouncilMember,
        prompt: str
    ) -> Dict:
        """Call Groq API"""
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            raise Exception("GROQ_API_KEY not set")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        valid_groq_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile", 
            "llama-3.1-8b-instant",
            "llama-3.2-90b-vision-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        
        if member.model not in valid_groq_models:
            raise Exception(f"Invalid Groq model: {member.model}")
        
        payload = {
            "model": member.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 4096
        }
        
        try:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_text = await response.text()
                
                if response.status == 429:
                    raise Exception("Rate limited")
                
                if response.status != 200:
                    logger.error(f"Groq error: {response_text[:200]}")
                    raise Exception(f"HTTP {response.status}")
                
                data = json.loads(response_text)
                
                if 'error' in data:
                    raise Exception(data['error'].get('message', 'Unknown error'))
                
                return {
                    "name": member.name,
                    "text": data['choices'][0]['message']['content']
                }
        except asyncio.TimeoutError:
            raise Exception("Request timeout")
    
    async def _call_gemini(
        self,
        session: aiohttp.ClientSession,
        member: DualCouncilMember,
        prompt: str
    ) -> Dict:
        """FIXED: Call Google Gemini API"""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            raise Exception("GOOGLE_API_KEY not set")
        
        model_name = member.model
        
        if model_name.startswith('models/'):
            model_name = model_name[7:]
        
        valid_models = {
            "gemini-2.5-flash": "models/gemini-2.5-flash",
            "gemini-2.5-pro": "models/gemini-2.5-pro",
            "gemini-2.0-flash": "models/gemini-2.0-flash",
            "gemini-flash-latest": "models/gemini-flash-latest",
            "gemini-pro-latest": "models/gemini-pro-latest",
        }
        
        if model_name not in valid_models:
            logger.warning(f"Unknown Gemini model '{model_name}', using gemini-2.5-flash")
            model_name = "gemini-2.5-flash"
        
        full_model_name = valid_models[model_name]
        url = f"https://generativelanguage.googleapis.com/v1beta/{full_model_name}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 8192,
                "topP": 0.95,
            }
        }
        
        last_error = None
        for attempt in range(3):
            try:
                async with session.post(
                    url, 
                    json=payload, 
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 429:
                        if attempt < 2:
                            wait_time = (attempt + 1) * 3
                            logger.warning(f"Gemini rate limit, retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        raise Exception("Rate limited")
                    
                    if response.status != 200:
                        logger.error(f"Gemini error {response.status}: {response_text[:500]}")
                        raise Exception(f"HTTP {response.status}")
                    
                    data = json.loads(response_text)
                    
                    if 'error' in data:
                        error_msg = data['error'].get('message', 'Unknown error')
                        raise Exception(error_msg)
                    
                    if 'candidates' in data and data['candidates']:
                        text = data['candidates'][0]['content']['parts'][0]['text']
                        return {"name": member.name, "text": text}
                    else:
                        raise Exception("Empty response from Gemini")
                        
            except asyncio.TimeoutError:
                last_error = Exception("Request timeout")
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                raise last_error
            except Exception as e:
                last_error = e
                if attempt < 2 and "rate" in str(e).lower():
                    await asyncio.sleep((attempt + 1) * 2)
                    continue
                raise
        
        raise Exception(f"All retries failed: {last_error}")
    
    async def _call_ollama(self, member: DualCouncilMember, prompt: str) -> Dict:
        """Call local Ollama"""
        loop = asyncio.get_event_loop()
        
        def _sync_call():
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": member.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code}")
            return response.json()['response']
        
        text = await loop.run_in_executor(None, _sync_call)
        return {"name": member.name, "text": text}
    
    async def _convene_council(
        self,
        session: aiohttp.ClientSession,
        panels: Dict[str, List[DualCouncilMember]],
        chairperson: DualCouncilMember,
        user_query: str,
        context: str,
        council_name: str
    ) -> Optional[str]:
        """
        ORIGINAL CONSENSUS LOGIC RESTORED:
        1. Each role's AIs debate internally -> produce single best response per role
        2. Roles debate with each other -> final consensus
        3. Separate consensus quality tracking for Primary vs Backup
        """
        
        active_roles = ["Strategist", "Librarian"]
        query_lower = user_query.lower()
        if any(w in query_lower for w in ["code", "python", "script", "program", "implement"]):
            active_roles.append("Architect")
        if any(w in query_lower for w in ["verify", "check", "validate", "accurate", "correct"]):
            active_roles.append("Auditor")
        if any(w in query_lower for w in ["analyze", "observe", "assess", "evaluate"]):
            active_roles.append("Observer")
        
        is_primary = council_name == "Primary"
        logger.info(f"[*] Convening {council_name} Council with roles: {', '.join(active_roles)}")
        
        consensus_scores = {}
        role_consensus_responses = {}
        
        # ===================================================================
        # PHASE 1: INTERNAL CONSENSUS WITHIN EACH ROLE
        # ===================================================================
        
        for role in active_roles:
            if role not in panels or not panels[role]:
                logger.warning(f"[!] {council_name} - No {role} members available")
                continue
            
            members = panels[role]
            logger.info(f"[>] {council_name} {role} panel: {len(members)} experts deliberating...")
            
            role_prompt = f"""Role: {role}
Context: {context}
Query: {user_query}


As a {role}, provide your expert analysis. Be specific, detailed, and accurate."""
            
            tasks = [self._call_member(session, member, role_prompt) for member in members]
            
            max_retries = 2 if is_primary else 1
            retry_count = 0
            responses = None
            
            while retry_count <= max_retries:
                try:
                    responses = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=90.0
                    )
                    break
                except asyncio.TimeoutError:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"[T] {council_name} {role}: Timeout, retry {retry_count}/{max_retries}")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"[X] {council_name} {role}: All retries exhausted")
                        responses = []
            
            if not responses:
                logger.warning(f"[X] {council_name} {role}: No responses after retries")
                continue
            
            valid_responses = []
            for r in responses:
                if isinstance(r, Exception):
                    logger.warning(f"[!] {council_name} {role}: Member error: {str(r)[:100]}")
                elif r and r.get('success', False):
                    valid_responses.append(r)
            
            if not valid_responses:
                logger.warning(f"[X] {council_name} {role} panel: All members failed")
                continue
            
            logger.info(f"[+] {council_name} {role} panel: {len(valid_responses)}/{len(members)} responses succeeded")
            
            # ===============================================================
            # INTERNAL ROLE CONSENSUS (ORIGINAL LOGIC)
            # ===============================================================
            
            if len(valid_responses) == 1:
                role_consensus_responses[role] = valid_responses[0]['text']
                consensus_scores[role] = {'score': 300, 'method': 'single'}
                logger.info(f"[OK] {council_name} {role} (single expert): Response accepted")
            
            else:
                logger.info(f"[~] {council_name} {role} panel: Running internal consensus...")
                
                ranking_prompt = f"""You are evaluating {role} expert responses for quality.


Query: {user_query}


{role} Expert Responses:
{chr(10).join([f"{chr(10)}Expert {i+1} ({r['name']}):{chr(10)}{r['text'][:1000]}" for i, r in enumerate(valid_responses)])}


Rate each response on:
- Accuracy (0-100)
- Completeness (0-100)
- Depth of {role} expertise (0-100)
- Relevance (0-100)


Respond ONLY with JSON:
{{
  "rankings": [
    {{"id": 1, "scores": {{"accuracy": 95, "completeness": 90, "depth": 95, "relevance": 100}}, "total": 380}},
    {{"id": 2, "scores": {{"accuracy": 85, "completeness": 80, "depth": 85, "relevance": 95}}, "total": 345}}
  ],
  "quality_gap": 35,
  "strategy": "use_best/enhance_best/merge_all"
}}"""
                
                ranker = members[0]
                if is_primary and len(members) > 1:
                    ranking_attempts = [self._call_member(session, m, ranking_prompt) for m in members[:2]]
                    ranking_results = await asyncio.gather(*ranking_attempts, return_exceptions=True)
                    ranking_result = next((r for r in ranking_results if not isinstance(r, Exception) and r.get('success')), None)
                else:
                    ranking_result = await self._call_member(session, ranker, ranking_prompt)
                
                if ranking_result and ranking_result.get('success'):
                    try:
                        json_match = re.search(r'\{.*\}', ranking_result['text'], re.DOTALL)
                        if json_match:
                            ranking_data = json.loads(json_match.group())
                            rankings = ranking_data.get('rankings', [])
                            quality_gap = ranking_data.get('quality_gap', 0)
                            
                            ranked = sorted(
                                zip(valid_responses, rankings),
                                key=lambda x: x[1].get('total', 0),
                                reverse=True
                            )
                            
                            best = ranked[0][0]
                            best_score = ranked[0][1].get('total', 0)
                            
                            logger.info(f"[#] {council_name} {role} best: {best['name']} (score: {best_score}, gap: {quality_gap})")
                            
                            significant_gap = int(os.getenv('PRIMARY_ROLE_GAP' if is_primary else 'BACKUP_ROLE_GAP', '50' if is_primary else '40'))
                            
                            if quality_gap > significant_gap:
                                logger.info(f"[*] {council_name} {role}: Enhancing best response")
                                
                                others = [r[0] for r in ranked[1:]]
                                
                                enhance_prompt = f"""You are the {role} creating the definitive {role} perspective.


QUERY: {user_query}


BEST {role.upper()} RESPONSE (score: {best_score}):
{best['text']}


OTHER {role.upper()} PERSPECTIVES:
{chr(10).join([f"{i+1}. {o['text'][:600]}" for i, o in enumerate(others)])}


TASK:
1. The best response is your foundation - keep its core
2. Extract ANY valuable {role}-specific insights from other perspectives
3. Add missing details, facts, or considerations they caught
4. Integrate seamlessly as one unified {role} opinion
5. Remove nothing unless incorrect


Provide the ENHANCED {role} perspective:"""
                                
                                enhanced = await self._call_member(session, ranker, enhance_prompt)
                                if enhanced.get('success'):
                                    role_consensus_responses[role] = enhanced['text']
                                    consensus_scores[role] = {'score': best_score + 10, 'method': 'enhanced'}
                                    logger.info(f"[OK] {council_name} {role}: Enhanced response complete")
                                else:
                                    role_consensus_responses[role] = best['text']
                                    consensus_scores[role] = {'score': best_score, 'method': 'best_only'}
                            
                            else:
                                logger.info(f"[~] {council_name} {role}: Merging similar-quality responses")
                                
                                top_responses = [r[0] for r in ranked[:min(3, len(ranked))]]
                                
                                merge_prompt = f"""You are the {role} synthesizing multiple expert {role} perspectives.


QUERY: {user_query}


{role.upper()} EXPERT RESPONSES:
{chr(10).join([f"{chr(10)}Expert {i+1} (score: {ranked[i][1].get('total', 0)}):{chr(10)}{r['text']}" for i, r in enumerate(top_responses)])}


TASK:
1. Identify the BEST {role}-specific insights from each
2. Combine into ONE superior {role} perspective
3. Resolve contradictions (favor higher scores)
4. Ensure merged is BETTER than any individual
5. Make it flow as one unified {role} opinion


Provide the UNIFIED {role} perspective:"""
                                
                                merged = await self._call_member(session, ranker, merge_prompt)
                                
                                if merged.get('success'):
                                    eval_prompt = f"""Compare merged vs best original {role} response.


QUERY: {user_query}


ORIGINAL BEST (score: {best_score}):
{best['text'][:800]}


MERGED:
{merged['text'][:800]}


JSON only:
{{
  "merged_better": true/false,
  "merged_score": 0-400,
  "improvement": 0-50,
  "use": "merged/original"
}}"""
                                    
                                    eval_result = await self._call_member(session, ranker, eval_prompt)
                                    
                                    use_merged = True
                                    merged_score = best_score + 15
                                    
                                    if eval_result.get('success'):
                                        try:
                                            eval_json = re.search(r'\{.*\}', eval_result['text'], re.DOTALL)
                                            if eval_json:
                                                eval_data = json.loads(eval_json.group())
                                                use_merged = eval_data.get('use', 'merged') == 'merged'
                                                merged_score = eval_data.get('merged_score', merged_score)
                                                improvement = eval_data.get('improvement', 15)
                                                logger.info(f"[=] {council_name} {role}: Merged={merged_score} vs Best={best_score} (+{improvement})")
                                        except Exception as e:
                                            logger.warning(f"Eval parse error: {e}")
                                    
                                    if use_merged:
                                        role_consensus_responses[role] = merged['text']
                                        consensus_scores[role] = {'score': merged_score, 'method': 'merged'}
                                        logger.info(f"[OK] {council_name} {role}: Using merged (improved)")
                                    else:
                                        role_consensus_responses[role] = best['text']
                                        consensus_scores[role] = {'score': best_score, 'method': 'best_original'}
                                        logger.info(f"[OK] {council_name} {role}: Using best original")
                                else:
                                    role_consensus_responses[role] = best['text']
                                    consensus_scores[role] = {'score': best_score, 'method': 'best_fallback'}
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"{council_name} {role} consensus JSON error: {e}")
                        role_consensus_responses[role] = valid_responses[0]['text']
                        consensus_scores[role] = {'score': 250, 'method': 'fallback'}
                    except Exception as e:
                        logger.error(f"{council_name} {role} consensus error: {e}")
                        role_consensus_responses[role] = valid_responses[0]['text']
                        consensus_scores[role] = {'score': 250, 'method': 'error_fallback'}
                else:
                    logger.warning(f"[!] {council_name} {role}: Ranking failed, using first response")
                    role_consensus_responses[role] = valid_responses[0]['text']
                    consensus_scores[role] = {'score': 250, 'method': 'no_ranking'}
        
        if not role_consensus_responses:
            logger.error(f"[X] {council_name} Council: No role consensus achieved")
            return None
        
        avg_score = sum(s['score'] for s in consensus_scores.values()) / len(consensus_scores) if consensus_scores else 0
        logger.info(f"[OK] {council_name} Phase 1 complete: {len(role_consensus_responses)} roles, avg score: {avg_score:.0f}")
        
        if is_primary:
            self.stats['primary_consensus_score'] = avg_score
        else:
            self.stats['backup_consensus_score'] = avg_score
        
        # ===================================================================
        # PHASE 2: INTER-ROLE COUNCIL DEBATE (ORIGINAL)
        # ===================================================================
        
        logger.info(f"[*] {council_name} Phase 2: Council debate between roles...")
        
        council_debate = "\n\n".join([
            f"### {role} (Consensus: {consensus_scores.get(role, {}).get('method', 'unknown')}, Score: {consensus_scores.get(role, {}).get('score', 0)}):\n{opinion}"
            for role, opinion in role_consensus_responses.items()
        ])
        
        if len(role_consensus_responses) >= 2:
            logger.info(f"[?] {council_name}: Analyzing inter-role consensus...")
            
            agreement_prompt = f"""Analyze if the different roles agree or disagree.


QUERY: {user_query}


ROLE OPINIONS:
{council_debate}


JSON only:
{{
  "roles_agree": true/false,
  "confidence": 0-100,
  "disagreement_areas": ["area1", "area2"] or [],
  "severity": "low/medium/high",
  "action": "proceed/resolve_conflicts/need_clarification"
}}"""
            
            agreement_check = await self._call_member(session, chairperson, agreement_prompt)
            
            if agreement_check.get('success'):
                try:
                    agree_json = re.search(r'\{.*\}', agreement_check['text'], re.DOTALL)
                    if agree_json:
                        agree_data = json.loads(agree_json.group())
                        roles_agree = agree_data.get('roles_agree', True)
                        confidence = agree_data.get('confidence', 100)
                        disagreements = agree_data.get('disagreement_areas', [])
                        severity = agree_data.get('severity', 'low')
                        
                        logger.info(f"[=] {council_name} inter-role agreement: {roles_agree} (confidence: {confidence}%, severity: {severity})")
                        
                        if not roles_agree and disagreements:
                            logger.warning(f"[!] {council_name} roles disagree on: {', '.join(disagreements)}")
                            
                            if is_primary:
                                self.stats['primary_has_disagreement'] = True
                                self.stats['primary_disagreement_severity'] = severity
                except Exception as e:
                    logger.warning(f"{council_name} agreement analysis failed: {e}")
        
        # ===================================================================
        # PHASE 3: CHAIRPERSON FINAL SYNTHESIS (ORIGINAL)
        # ===================================================================
        
        logger.info(f"[>] {council_name} Phase 3: Chairperson synthesizing final answer...")
        
        chair_prompt = f"""You are the {council_name} Council Chairperson synthesizing expert role opinions.


QUERY: {user_query}


EXPERT ROLE CONSENSUS OPINIONS (with quality scores):
{council_debate}


Each role has already reached internal consensus - these are their BEST perspectives.


INSTRUCTIONS:
1. Synthesize into ONE definitive answer
2. Integrate insights from all roles
3. If roles disagree, note it and provide balanced view
4. Prioritize accuracy over completeness
5. If tool needed: TOOL[tool_name](args)
6. Be clear, complete, and authoritative
7. Weight higher-scored roles more heavily


FINAL ANSWER:"""
        
        final = None
        attempts = 0
        max_attempts = 3 if is_primary else 1
        
        while attempts < max_attempts and not final:
            try:
                final = await asyncio.wait_for(
                    self._call_member(session, chairperson, chair_prompt),
                    timeout=60.0
                )
                if final and final.get('success'):
                    break
            except asyncio.TimeoutError:
                attempts += 1
                logger.warning(f"[T] {council_name} Chairperson timeout, attempt {attempts}/{max_attempts}")
                await asyncio.sleep(1)
            except Exception as e:
                attempts += 1
                logger.error(f"[X] {council_name} Chairperson error: {e}")
                await asyncio.sleep(1)
        
        if not final or not final.get('success'):
            logger.error(f"[X] {council_name} Chairperson synthesis failed after {attempts} attempts")
            return None
        
        logger.info(f"[OK] {council_name} Council decision complete (consensus score: {avg_score:.0f})")
        return final['text']
    
    async def convene(self, user_query: str, context: str = "") -> str:
        """FIXED: Better timeout handling with faster fallback"""
        
        try:
            async with aiohttp.ClientSession() as session:
                
                use_backup_immediately = self._should_use_backup()
                
                if use_backup_immediately:
                    logger.info("[~] PRIMARY IN COOLDOWN - Using BACKUP Council")
                    self.stats['backup_calls'] += 1
                    
                    result = await asyncio.wait_for(
                        self._convene_council(
                            session,
                            self.backup_panels,
                            self.backup_chairperson,
                            user_query,
                            context,
                            "Backup"
                        ),
                        timeout=90.0  
                    )
                    
                    if result:
                        backup_score = self.stats.get('backup_consensus_score', 0)
                        logger.info(f"[OK] Backup Council succeeded (consensus: {backup_score:.0f})")
                        
                        if os.getenv('SHOW_COUNCIL_MODE', 'true').lower() == 'true':
                            result = f"[BACKUP COUNCIL - Consensus: {backup_score:.0f}] {result}"
                        return result
                    else:
                        self.stats['backup_failures'] += 1
                        return "[!] Backup Council unavailable. Please check API keys and Ollama status."
                
                # ============================================================
                # TRY PRIMARY FIRST (WITH TIMEOUT)
                # ============================================================
                logger.info("[>] Trying PRIMARY Council (OpenRouter)")
                self.stats['primary_calls'] += 1
                
                try:
                    primary_result = await asyncio.wait_for(
                        self._convene_council(
                            session,
                            self.primary_panels,
                            self.primary_chairperson,
                            user_query,
                            context,
                            "Primary"
                        ),
                        timeout=60.0 
                    )
                except asyncio.TimeoutError:
                    logger.error("[X] Primary Council TIMEOUT (60s)")
                    primary_result = None
                    self.primary_failures += 1
                    self.stats['primary_failures'] += 1
                
                # ============================================================
                # CHECK IF PRIMARY SUCCEEDED
                # ============================================================
                
                if not primary_result:
                    logger.error("[X] Primary Council failed")
                    if self.primary_failures == 0:  
                        self.primary_failures += 1
                        self.stats['primary_failures'] += 1
                    self.stats['total_fallbacks'] += 1
                    
                    logger.warning("[~] FALLBACK: Switching to Backup Council...")
                    
                    try:
                        result = await asyncio.wait_for(
                            self._convene_council(
                                session,
                                self.backup_panels,
                                self.backup_chairperson,
                                user_query,
                                context,
                                "Backup"
                            ),
                            timeout=90.0 
                        )
                    except asyncio.TimeoutError:
                        logger.error("[X] Backup Council also timed out")
                        return "[X] Both councils timed out. Please check your network connection."
                    
                    if result:
                        backup_score = self.stats.get('backup_consensus_score', 0)
                        logger.info(f"[OK] Backup recovered from Primary failure (consensus: {backup_score:.0f})")
                        
                        if os.getenv('SHOW_COUNCIL_MODE', 'true').lower() == 'true':
                            result = f"[BACKUP COUNCIL - Primary failed - Consensus: {backup_score:.0f}] {result}"
                        return result
                    else:
                        logger.error("[X] Both Primary and Backup failed")
                        return "[X] Both councils failed. Please check your configuration."
                
                # ============================================================
                # PRIMARY SUCCEEDED
                # ============================================================
                
                primary_score = self.stats.get('primary_consensus_score', 0)
                logger.info(f"[OK] Primary Council succeeded (consensus: {primary_score:.0f})")
                
                enable_quality_fallback = os.getenv('ENABLE_QUALITY_FALLBACK', 'false').lower() == 'true'
                
                if enable_quality_fallback:
                    low_threshold = int(os.getenv('LOW_CONSENSUS_THRESHOLD', '250'))
                    has_disagreement = self.stats.get('primary_has_disagreement', False)
                    disagreement_severity = self.stats.get('primary_disagreement_severity', 'low')
                    
                    should_quality_check = False
                    quality_reason = ""
                    
                    if primary_score < low_threshold:
                        should_quality_check = True
                        quality_reason = f"low consensus ({primary_score:.0f} < {low_threshold})"
                    elif has_disagreement and disagreement_severity == 'high':
                        should_quality_check = True
                        quality_reason = "high-severity disagreement"
                    
                    if should_quality_check:
                        logger.warning(f"[!] Quality concern: {quality_reason}")
                        logger.info("[?] Running Backup for comparison...")
                        
                        self.stats['quality_checks'] = self.stats.get('quality_checks', 0) + 1
                        
                        try:
                            backup_result = await asyncio.wait_for(
                                self._convene_council(
                                    session,
                                    self.backup_panels,
                                    self.backup_chairperson,
                                    user_query,
                                    context,
                                    "Backup"
                                ),
                                timeout=90.0
                            )
                        except asyncio.TimeoutError:
                            logger.warning("[!] Backup quality check timed out, using primary")
                            backup_result = None
                        
                        if backup_result:
                            backup_score = self.stats.get('backup_consensus_score', 0)
                            logger.info(f"[=] Comparison: Primary={primary_score:.0f} vs Backup={backup_score:.0f}")
                            
                            min_improvement = int(os.getenv('MIN_BACKUP_IMPROVEMENT', '30'))
                            if backup_score > primary_score + min_improvement:
                                logger.info(f"[OK] Using Backup (better quality: {backup_score:.0f} vs {primary_score:.0f})")
                                self.stats['quality_fallbacks'] = self.stats.get('quality_fallbacks', 0) + 1
                                
                                if os.getenv('SHOW_COUNCIL_MODE', 'true').lower() == 'true':
                                    backup_result = f"[BACKUP COUNCIL - Better quality: {backup_score:.0f} vs {primary_score:.0f}] {backup_result}"
                                return backup_result
                            else:
                                logger.info(f"[OK] Using Primary (backup not significantly better)")
                
                self.primary_failures = 0
                
                if os.getenv('SHOW_COUNCIL_MODE', 'true').lower() == 'true':
                    primary_result = f"[PRIMARY COUNCIL - Consensus: {primary_score:.0f}] {primary_result}"
                
                return primary_result
        
        except Exception as e:
            logger.error(f"Critical council error: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                logger.warning("[~] Exception fallback - trying Backup Council...")
                async with aiohttp.ClientSession() as session:
                    result = await asyncio.wait_for(
                        self._convene_council(
                            session,
                            self.backup_panels,
                            self.backup_chairperson,
                            user_query,
                            context,
                            "Backup"
                        ),
                        timeout=60.0  
                    )
                    if result:
                        return f"[BACKUP - Emergency fallback] {result}"
            except asyncio.TimeoutError:
                logger.error("[X] Emergency backup timed out")
            except Exception:
                pass
            
            return f"[X] Critical error: {str(e)}"
    
    def get_stats(self) -> str:
        """ORIGINAL: Get council statistics with consensus scores and fallback tracking"""
        lines = [
            "\n" + "="*70,
            "DUAL COUNCIL STATISTICS WITH CONSENSUS TRACKING".center(70),
            "="*70,
            "",
            "PRIMARY COUNCIL (OpenRouter):",
            f"  Total Calls:                 {self.stats['primary_calls']}",
            f"  Complete Failures:           {self.stats['primary_failures']}",
            f"  Avg Consensus Score:         {self.stats.get('primary_consensus_score', 0):.0f}/400",
            f"  Has Disagreements:           {self.stats.get('primary_has_disagreement', False)}",
            "",
            "BACKUP COUNCIL (Groq/Gemini/Ollama):",
            f"  Total Calls:                 {self.stats['backup_calls']}",
            f"  Complete Failures:           {self.stats['backup_failures']}",
            f"  Avg Consensus Score:         {self.stats.get('backup_consensus_score', 0):.0f}/400",
            "",
            "FALLBACK STATISTICS:",
            f"  Total Fallbacks:             {self.stats['total_fallbacks']}",
            f"  Quality-Based Fallbacks:     {self.stats.get('quality_fallbacks', 0)}",
            ""
        ]
        
        if self.primary_cooldown_until:
            remaining = (self.primary_cooldown_until - datetime.now()).total_seconds()
            if remaining > 0:
                lines.append(f"PRIMARY COOLDOWN: {int(remaining)}s remaining")
                lines.append("")
        
        primary_score = self.stats.get('primary_consensus_score', 0)
        backup_score = self.stats.get('backup_consensus_score', 0)
        
        if primary_score > 0 or backup_score > 0:
            lines.append("QUALITY ASSESSMENT:")
            if primary_score > 350:
                lines.append("  Primary: [OK] EXCELLENT")
            elif primary_score > 300:
                lines.append("  Primary: [+] GOOD")
            elif primary_score > 250:
                lines.append("  Primary: [!] ACCEPTABLE")
            elif primary_score > 0:
                lines.append("  Primary: [X] LOW QUALITY")
            
            if backup_score > 350:
                lines.append("  Backup:  [OK] EXCELLENT")
            elif backup_score > 300:
                lines.append("  Backup:  [+] GOOD")
            elif backup_score > 250:
                lines.append("  Backup:  [!] ACCEPTABLE")
            elif backup_score > 0:
                lines.append("  Backup:  [X] LOW QUALITY")
            lines.append("")
        
        lines.append("="*70)
        return "\n".join(lines)


class UltimateAgent:
    """FIXED: Main agent class with proper initialization"""
    
    def __init__(self):
        logger.info("Initializing Ultimate AI Agent v3.0...")


        self.memory = MemorySystem()
        self.tools = ToolRegistry(self.memory)
        self.voice = VoiceInterface()
        self.autonomous_mode = False
        
        if validate_council_setup():
            try:
                self.orchestrator = DualCouncilOrchestrator()
                self.use_council = True
                self.llm = None
                logger.info("[OK] Council mode enabled")
                print("[OK] Using Dual Council mode")
            except Exception as e:
                logger.error(f"Council init failed: {e}")
                logger.info("Falling back to Ollama mode")
                self.use_council = False
                self._init_ollama()
        else:
            self.orchestrator = None
            self.use_council = False
            logger.info("Using Ollama mode")
            self._init_ollama()
        
        atexit.register(self.cleanup)
        logger.info("[OK] Agent Ready")
        print("[OK] Agent initialized successfully\n")
    
    def _init_ollama(self):
        """Initialize Ollama LLM"""
        try:
            response = requests.get("http://localhost:11434", timeout=2)
            logger.info("Ollama connection verified")
        except requests.exceptions.RequestException:
            logger.error("Cannot connect to Ollama")
            print("\n[X] FATAL ERROR: Ollama is not running!")
            print("Please start Ollama first:")
            print("  - Download from: https://ollama.ai")
            print("  - Start with: ollama serve")
            print(f"  - Pull model: ollama pull {AgentConfig.MODEL}")
            sys.exit(1)
        
        try:
            self.llm = ChatOllama(
                model=AgentConfig.MODEL,
                temperature=AgentConfig.TEMPERATURE,
                num_ctx=8192
            )
            test_response = self.llm.invoke([HumanMessage(content="test")])
            logger.info(f"LLM initialized: {AgentConfig.MODEL}")
        except Exception as e:
            logger.critical(f"LLM initialization failed: {e}")
            print(f"\n[X] FATAL ERROR: Could not initialize {AgentConfig.MODEL}")
            print(f"  - Make sure you've pulled the model: ollama pull {AgentConfig.MODEL}")
            sys.exit(1)


    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt"""
        return f"""You are an advanced AI assistant with access to powerful tools.


Available Tools:
{self.tools.get_tool_descriptions()}


MATHEMATICAL FORMATTING (MANDATORY):
1. For all mathematical expressions, symbols, or formulas, use LaTeX syntax.
2. For inline math (within a sentence), wrap it in \\( ... \\). 
   Example: The value of \\( x \\) is \\( \\sqrt{{25}} \\).
3. For block math (centered on its own line), wrap it in \\[ ... \\].
   Example: \\[ x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}} \\]
4. Ensure complex characters like infinity ( \\infty ), set notation ( \\in ), or subscripts are always inside these delimiters.


CRITICAL INSTRUCTIONS:
1. When you need to use a tool, output: TOOL[tool_name](arg1, arg2, ...)
2. Use tools proactively when they would help answer the user's question
3. You can use multiple tools in sequence
4. After receiving tool results, provide a natural response to the user
5. Be concise but thorough
6. If a task requires confirmation, ask the user first


Current date: {datetime.now().strftime('%Y-%m-%d')}


Think step by step and use tools when appropriate."""


    def _parse_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from LLM response"""
        pattern = r'TOOL\[(\w+)\]\((.*?)\)'
        match = re.search(pattern, content)
        
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        
        args = []
        if args_str:
            args = [
                arg.strip().strip('"').strip("'") 
                for arg in args_str.split(',') 
                if arg.strip()
            ]
        
        return {
            'tool': tool_name,
            'args': args
        }
    
    
    async def execute_async(self, user_input: str, use_voice: bool = False) -> str:
        """FIXED: Async execution using Council"""
        try:
            if not security.check_rate_limit("main"):
                return "[!] Rate limit exceeded. Please wait a moment."
            
            user_input = SecurityManager.sanitize_input(user_input)
            if not user_input:
                return "[!] Input rejected by security filter"
            
            self.memory.add_conversation("user", user_input)
            
            context_msgs = self.memory.get_recent_context(8)
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context_msgs
            ])
            
            print("[COUNCIL] Consulting expert panels...", flush=True)
            
            response = await self.orchestrator.convene(user_input, context_str)
            
            tool_pattern = r'TOOL\[(\w+)\]\((.*?)\)'
            max_iterations = 5
            iteration = 0
            
            while iteration < max_iterations:
                tool_match = re.search(tool_pattern, response)
                
                if not tool_match:
                    break
                
                tool_name = tool_match.group(1)
                args_str = tool_match.group(2).strip()
                args = [arg.strip().strip('"').strip("'") 
                       for arg in args_str.split(',') if arg.strip()]
                
                print(f"[TOOL] Using: {tool_name}", flush=True)
                tool_result = self.tools.execute_tool(tool_name, args)
                
                context_str += f"\n\nTool: {tool_name}\nResult: {tool_result[:1000]}"
                
                response = await self.orchestrator.convene(user_input, context_str)
                iteration += 1
            
            clean_response = re.sub(tool_pattern, '', response).strip()
            
            if not clean_response:
                clean_response = "[OK] Task completed successfully."
            
            self.memory.add_conversation("assistant", clean_response)
            
            if use_voice:
                self.voice.speak(clean_response)
            
            return clean_response
            
        except Exception as e:
            logger.error(f"Async execution error: {e}")
            return f"[X] Error: {str(e)}"
    
    @timing_decorator
    def execute(self, user_input: str, use_voice: bool = False) -> str:
        """FIXED: Execute user request - supports both Council and Ollama modes"""
        
        if self.use_council:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(
                    self.execute_async(user_input, use_voice)
                )
            except Exception as e:
                logger.error(f"Council execution error: {e}")
                return f"[X] Council error: {str(e)}"
        else:
            return self._execute_with_ollama(user_input, use_voice)
    
    def _execute_with_ollama(self, user_input: str, use_voice: bool = False) -> str:
        """Original Ollama execution logic"""
        try:
            if not security.check_rate_limit("main"):
                return "[!] Rate limit exceeded. Please wait a moment."
            
            user_input = SecurityManager.sanitize_input(user_input)
            if not user_input:
                return "[!] Input rejected by security filter"
            
            self.memory.add_conversation("user", user_input)
            
            system_prompt = self._build_system_prompt()
            messages = [SystemMessage(content=system_prompt)]
            
            for msg in self.memory.get_recent_context(8):
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                else:
                    messages.append(AIMessage(content=msg['content']))
            
            messages.append(HumanMessage(content=user_input))
            
            iterations = 0
            final_response = ""
            
            print("[THINK] Processing", end="", flush=True)
            
            while iterations < Constants.MAX_ITERATIONS:
                response = self.llm.invoke(messages)
                content = response.content
                
                tool_call = self._parse_tool_call(content)
                
                if not tool_call:
                    final_response = content
                    print(" [OK]")
                    break
                
                print(f"\n[TOOL] Using: {tool_call['tool']}", end="", flush=True)
                result = self.tools.execute_tool(tool_call['tool'], tool_call['args'])
                print(" [OK]")
                
                messages.append(AIMessage(content=content))
                messages.append(HumanMessage(content=f"Tool Result:\n{result}"))
                
                iterations += 1
                
                print("[THINK] Processing", end="", flush=True)
            
            clean_response = re.sub(r'TOOL\[.*?\]\(.*?\)', '', final_response, flags=re.DOTALL).strip()
            
            if not clean_response and iterations > 0:
                clean_response = "[OK] Task completed successfully."
            
            self.memory.add_conversation("assistant", clean_response)
            
            if use_voice:
                self.voice.speak(clean_response)
            
            return clean_response
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return f"[X] Error: {str(e)}"
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.memory.cleanup()
            gc.collect()
            logger.info("Agent shutdown complete")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# ================================================================================
# INTERACTIVE SHELL
# ================================================================================


class InteractiveShell:
    """Enhanced interactive shell"""
    
    def __init__(self, agent: UltimateAgent):
        self.agent = agent
        self.running = True
        self.voice_mode = False
    
    def print_banner(self):
        """Print welcome banner"""
        mode = "Council Mode" if self.agent.use_council else "Ollama Mode"
        banner = f"""
{'='*70}
{'ULTIMATE AI AGENT v3.0 - BUGFIXED'.center(70)}
{'Production Edition - All Critical Bugs Fixed'.center(70)}
{'='*70}


Mode: {mode}
Model: {AgentConfig.MODEL if not self.agent.use_council else "Multi-Provider Council"}
Commands:
  - Type your request naturally
  - 'help' - Show all commands
  - 'tools' - List available tools
  - 'council' - Show council statistics (if in council mode)
  - 'voice' - Toggle voice mode
  - 'perf' - Performance report
  - 'audit' - Security audit report
  - 'clear' - Clear conversation history
  - 'quit' - Exit


{'='*70}
"""
        print(banner)
    
    def print_help(self):
        """Print help information"""
        help_text = """
Available Commands:
{'='*70}
help          - Show this help message
tools         - List all available tools
voice         - Toggle voice input/output mode
listen        - Listen for voice input once
perf          - Show performance metrics
audit         - Show security audit log
council       - Show council statistics (if using council mode)
memory        - Show conversation history
clear         - Clear conversation history
config        - Show current configuration
quit/exit     - Exit the agent


Tool Usage:
  Just ask naturally! The agent will use tools automatically.
  Examples:
    - "Search for recent AI news"
    - "List files in my data folder"
    - "What's my system memory usage?"
    - "Create a file called notes.txt"


{'='*70}
"""
        print(help_text)
    
    def handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if command was handled."""
        cmd = user_input.lower().strip()
        
        if cmd in ('quit', 'exit'):
            print("\n[BYE] Goodbye!")
            self.running = False
            return True
        
        elif cmd == 'help':
            self.print_help()
            return True
        
        elif cmd == 'tools':
            print("\n" + self.agent.tools.get_tool_descriptions())
            return True
        
        elif cmd == 'voice':
            self.voice_mode = not self.voice_mode
            status = "enabled" if self.voice_mode else "disabled"
            print(f"[VOICE] Voice mode {status}")
            return True
        
        elif cmd == 'listen':
            print("\n[LISTEN] Listening for voice input...")
            text = self.agent.voice.listen(timeout=10)
            if text:
                print(f"Heard: {text}\n")
                response = self.agent.execute(text, use_voice=self.voice_mode)
                print(f"\n[AGENT] {response}\n")
            else:
                print("[X] No voice input detected")
            return True
        
        elif cmd == 'perf':
            print(perf_monitor.get_report())
            return True
        
        elif cmd == 'audit':
            print(security.get_audit_report())
            return True
        
        elif cmd == 'council':
            if self.agent.use_council and self.agent.orchestrator:
                print(self.agent.orchestrator.get_stats())
            else:
                print("\n[INFO] Council mode not active. Using Ollama mode.")
            return True
        
        elif cmd == 'memory':
            history = self.agent.memory.get_recent_context(10)
            if history:
                print("\nRecent Conversation:")
                print("="*70)
                for msg in history:
                    role = msg['role'].upper()
                    content = msg['content'][:200]
                    print(f"{role}: {content}")
                print("="*70)
            else:
                print("\nNo conversation history")
            return True
        
        elif cmd == 'clear':
            self.agent.memory.clear_conversation()
            print("[OK] Conversation history cleared")
            return True
        
        elif cmd == 'config':
            config_info = f"""
Current Configuration:
{'='*70}
Model: {AgentConfig.MODEL}
Temperature: {AgentConfig.TEMPERATURE}
Max Iterations: {Constants.MAX_ITERATIONS}
Data Directory: {AgentConfig.DATA_DIR}
Memory Directory: {AgentConfig.MEMORY_DIR}
Voice Mode: {'Enabled' if self.voice_mode else 'Disabled'}
{'='*70}
"""
            print(config_info)
            return True
        
        return False
    
    def run(self):
        """Run interactive shell"""
        self.print_banner()
        
        while self.running:
            try:
                if self.voice_mode:
                    print("\n[LISTEN] Listening...")
                    user_input = self.agent.voice.listen(timeout=10)
                    if not user_input:
                        continue
                    print(f"You: {user_input}")
                else:
                    user_input = input("\n[YOU] > ").strip()
                
                if not user_input:
                    continue
                
                if self.handle_command(user_input):
                    continue
                
                response = self.agent.execute(user_input, use_voice=self.voice_mode)
                print(f"\n[AGENT] {response}")
                
            except KeyboardInterrupt:
                print("\n\n[!] Interrupted (Ctrl+C)")
                print("Type 'quit' to exit or continue with another request")
                
            except EOFError:
                print("\n[BYE] Goodbye!")
                break
                
            except Exception as e:
                logger.error(f"Shell error: {e}")
                print(f"\n[X] Error: {e}")


# ================================================================================
# MAIN ENTRY POINT
# ================================================================================


def main():
    """Main entry point"""
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')
    
    validate_environment()


    try:
        agent = UltimateAgent()
    except SystemExit:
        return
    except Exception as e:
        print(f"\n[X] FATAL ERROR: {e}")
        logger.critical(f"Fatal error: {e}")
        return
    
    try:
        shell = InteractiveShell(agent)
        shell.run()
    except Exception as e:
        print(f"\n[X] Shell error: {e}")
        logger.error(f"Shell error: {e}")
    finally:
        print("\n[SHUTDOWN] Shutting down...")
        agent.cleanup()
        print("[OK] Shutdown complete")


if __name__ == "__main__":
    main()
