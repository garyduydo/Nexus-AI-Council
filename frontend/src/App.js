import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, Sparkles, Upload, Mic, StopCircle, Paperclip, X, 
  MoreVertical, RefreshCw, Zap, Plus, 
  Copy, Trash2, Moon, Sun, Settings, AlertCircle, Loader,
  Download, FileText, GitBranch
} from 'lucide-react';

// Default Config
const DEFAULT_API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const DEFAULT_WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

/* ========================================================================== */
/* DYNAMIC THEMES                                                             */
/* ========================================================================== */

const THEME = {
  dark: {
    bg: '#0a0e1a',
    surface: '#141829',
    surfaceHover: '#1a1f35',
    accent: '#ff6b9d',
    accentDark: '#c74d7a',
    secondary: '#4ecdc4',
    warning: '#ffd93d',
    text: '#e8eaed',
    textMuted: '#8892a6',
    border: '#252b3f',
    success: '#26de81',
  },
  light: {
    bg: '#f8f9fa',
    surface: '#ffffff',
    surfaceHover: '#f1f3f5',
    accent: '#ff6b9d',
    accentDark: '#c74d7a',
    secondary: '#4ecdc4',
    warning: '#ffc107',
    text: '#212529',
    textMuted: '#6c757d',
    border: '#dee2e6',
    success: '#26de81',
  }
};

let globalMessageId = 0;

/* ========================================================================== */
/* MARKDOWN RENDERER                                                         */
/* ========================================================================== */

const MarkdownRenderer = ({ text, theme }) => {
  const renderMarkdown = (content) => {
    if (!content) return null;

    // Split by lines
    const lines = content.split('\n');
    const elements = [];
    let listItems = [];
    let codeBlock = null;
    let codeLines = [];

    const flushList = () => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-${elements.length}`} style={{ marginLeft: '20px', marginBottom: '12px' }}>
            {listItems.map((item, i) => (
              <li key={i} style={{ marginBottom: '6px' }}>{item}</li>
            ))}
          </ul>
        );
        listItems = [];
      }
    };

    const flushCodeBlock = () => {
      if (codeLines.length > 0) {
        elements.push(
          <pre key={`code-${elements.length}`} style={{
            backgroundColor: theme.bg,
            border: `1px solid ${theme.border}`,
            borderRadius: '8px',
            padding: '12px',
            overflowX: 'auto',
            marginBottom: '12px',
            fontSize: '13px',
            fontFamily: 'monospace'
          }}>
            <code>{codeLines.join('\n')}</code>
          </pre>
        );
        codeLines = [];
        codeBlock = null;
      }
    };

    lines.forEach((line, idx) => {
      // Code blocks
      if (line.startsWith('```')) {
        if (codeBlock) {
          flushCodeBlock();
        } else {
          flushList();
          codeBlock = line.slice(3);
        }
        return;
      }

      if (codeBlock) {
        codeLines.push(line);
        return;
      }

      // ✅ FIX: Headers - handle #### before ###
      if (line.startsWith('#### ')) {
        flushList();
        const text = line.slice(5).replace(/\*\*/g, '');
        elements.push(
          <h4 key={`h4-${idx}`} style={{ 
            fontSize: '16px', 
            fontWeight: '700', 
            marginTop: '16px', 
            marginBottom: '8px',
            color: theme.accent 
          }}>
            {text}
          </h4>
        );
        return;
      }

      if (line.startsWith('### ')) {
        flushList();
        const text = line.slice(4).replace(/\*\*/g, '');
        elements.push(
          <h3 key={`h3-${idx}`} style={{ 
            fontSize: '18px', 
            fontWeight: '700', 
            marginTop: '20px', 
            marginBottom: '10px',
            color: theme.accent 
          }}>
            {text}
          </h3>
        );
        return;
      }

      if (line.startsWith('## ')) {
        flushList();
        const text = line.slice(3).replace(/\*\*/g, '');
        elements.push(
          <h2 key={`h2-${idx}`} style={{ 
            fontSize: '20px', 
            fontWeight: '700', 
            marginTop: '24px', 
            marginBottom: '12px',
            color: theme.accent 
          }}>
            {text}
          </h2>
        );
        return;
      }

      if (line.startsWith('# ')) {
        flushList();
        const text = line.slice(2).replace(/\*\*/g, '');
        elements.push(
          <h1 key={`h1-${idx}`} style={{ 
            fontSize: '24px', 
            fontWeight: '800', 
            marginTop: '24px', 
            marginBottom: '12px',
            color: theme.accent 
          }}>
            {text}
          </h1>
        );
        return;
      }

      // List items
      if (line.match(/^[\s]*[-*•]\s/)) {
        const text = line.replace(/^[\s]*[-*•]\s/, '');
        const rendered = renderInlineFormatting(text);
        listItems.push(rendered);
        return;
      }

      if (line.match(/^[\s]*\d+\.\s/)) {
        const text = line.replace(/^[\s]*\d+\.\s/, '');
        const rendered = renderInlineFormatting(text);
        listItems.push(rendered);
        return;
      }

      // Regular paragraphs
      if (line.trim()) {
        flushList();
        elements.push(
          <p key={`p-${idx}`} style={{ marginBottom: '12px', lineHeight: '1.6' }}>
            {renderInlineFormatting(line)}
          </p>
        );
      } else {
        flushList();
      }
    });

    flushList();
    flushCodeBlock();

    return elements;
  };

  const renderInlineFormatting = (text) => {
    const parts = [];
    let currentText = text;
    let key = 0;

    // Remove TOOL[...] artifacts
    currentText = currentText.replace(/TOOL\[[^\]]+\]\([^)]+\)/g, '');

    // Process text with both bold and italic
    let lastIndex = 0;
    
    // Combined regex: (**bold**) or (*italic*)
    const formattingRegex = /(\*\*([^*]+)\*\*)|(\*([^*]+)\*)/g;
    let match;

    while ((match = formattingRegex.exec(currentText)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        parts.push(currentText.slice(lastIndex, match.index));
      }

      // Check if it's bold (**text**) or italic (*text*)
      if (match[1]) {
        // Bold: **text**
        parts.push(
          <strong key={`bold-${key++}`} style={{ fontWeight: '700', color: theme.text }}>
            {match[2]}
          </strong>
        );
      } else if (match[3]) {
        // Italic: *text*
        parts.push(
          <em key={`italic-${key++}`} style={{ fontStyle: 'italic', color: theme.textMuted }}>
            {match[4]}
          </em>
        );
      }

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < currentText.length) {
      parts.push(currentText.slice(lastIndex));
    }

    return parts.length > 0 ? parts : currentText;
  };

  return <div>{renderMarkdown(text)}</div>;
};

/* ========================================================================== */
/* SETTINGS MODAL COMPONENT                                                  */
/* ========================================================================== */

const SettingsModal = ({ isOpen, onClose, config, onSave, onClearHistory, activeTheme }) => {
  const [localConfig, setLocalConfig] = useState(config);

  useEffect(() => {
    if (isOpen) setLocalConfig(config);
  }, [isOpen, config]);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 5000,
      backdropFilter: 'blur(8px)'
    }}>
      <div style={{
        width: '500px', backgroundColor: activeTheme.surface,
        border: `1px solid ${activeTheme.border}`, borderRadius: '24px',
        padding: '32px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '700', color: activeTheme.text, margin: 0 }}>System Configuration</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: activeTheme.textMuted, cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: activeTheme.textMuted, marginBottom: '8px' }}>API ENDPOINT</label>
            <input 
              type="text" value={localConfig.apiUrl}
              onChange={(e) => setLocalConfig({...localConfig, apiUrl: e.target.value})}
              style={{ width: '100%', padding: '12px', backgroundColor: activeTheme.bg, border: `1px solid ${activeTheme.border}`, borderRadius: '12px', color: activeTheme.text, outline: 'none' }} 
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: activeTheme.textMuted, marginBottom: '8px' }}>WEBSOCKET TUNNEL</label>
            <input 
              type="text" value={localConfig.wsUrl}
              onChange={(e) => setLocalConfig({...localConfig, wsUrl: e.target.value})}
              style={{ width: '100%', padding: '12px', backgroundColor: activeTheme.bg, border: `1px solid ${activeTheme.border}`, borderRadius: '12px', color: activeTheme.text, outline: 'none' }} 
            />
          </div>

          <div style={{ marginTop: '10px', paddingTop: '20px', borderTop: `1px solid ${activeTheme.border}` }}>
            <button 
              onClick={() => {
                if (window.confirm('Clear all conversation history? This cannot be undone.')) {
                  onClearHistory();
                }
              }}
              style={{
                width: '100%', padding: '12px', backgroundColor: 'transparent',
                border: `1px solid ${activeTheme.accent}50`, borderRadius: '12px',
                color: activeTheme.accent, cursor: 'pointer', display: 'flex',
                alignItems: 'center', justifyContent: 'center', gap: '10px', fontWeight: '600'
              }}
            >
              <Trash2 size={16} /> Purge All Memory
            </button>
          </div>
        </div>

        <div style={{ marginTop: '32px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button onClick={onClose} style={{ padding: '12px 24px', borderRadius: '12px', border: `1px solid ${activeTheme.border}`, background: 'transparent', color: activeTheme.text, cursor: 'pointer' }}>Cancel</button>
          <button 
            onClick={() => onSave(localConfig)}
            style={{ padding: '12px 24px', borderRadius: '12px', border: 'none', background: activeTheme.accent, color: 'white', cursor: 'pointer', fontWeight: '600' }}
          >
            Apply Sync
          </button>
        </div>
      </div>
    </div>
  );
};

/* ========================================================================== */
/* WEBSOCKET HOOK                                                            */
/* ========================================================================== */

const useWebSocket = (url, apiUrl, onMessage) => {
  const [ws, setWs] = useState(null);
  const [status, setStatus] = useState('disconnected');
  const [councilMode, setCouncilMode] = useState('unknown');
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    // Validate URL
    if (!url || url.trim() === '') {
      console.error('Invalid WebSocket URL');
      setStatus('error');
      return;
    }
    
    // If already connected to the same URL, skip
    if (wsRef.current?.readyState === WebSocket.OPEN && wsRef.current.url === url) return;
    
    // Close existing connection if URL changed
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const websocket = new WebSocket(url);
      wsRef.current = websocket;

      websocket.onopen = () => {
        console.log('✅ Connected to backend');
        setStatus('connected');
        setWs(websocket);
        reconnectAttempts.current = 0;
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };

      websocket.onclose = () => {
        console.log('❌ Disconnected');
        setStatus('disconnected');
        setWs(null);
        
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;
        
        reconnectRef.current = setTimeout(connect, delay);
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setStatus('error');
    }
  }, [url, onMessage]);

  useEffect(() => {
    connect();
    
    // Fetch health status
    if (apiUrl && apiUrl.trim() !== '') {
      fetch(`${apiUrl}/health`)
        .then(res => res.json())
        .then(data => {
          setCouncilMode(data.mode || 'unknown');
        })
        .catch(err => console.error('Health check failed:', err));
    }

    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect, apiUrl]);

  const send = useCallback((data) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, [ws]);

  return { ws, status, councilMode, send };
};

/* ========================================================================== */
/* VOICE RECOGNITION                                                         */
/* ========================================================================== */

const useVoiceRecognition = () => {
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
    }
  }, []);

  const startRecording = (onResult, onError) => {
    if (!recognitionRef.current) {
      onError?.('Speech recognition not supported');
      return;
    }

    recognitionRef.current.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult?.(transcript);
      setIsRecording(false);
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech error:', event.error);
      onError?.(event.error);
      setIsRecording(false);
    };

    recognitionRef.current.onend = () => setIsRecording(false);

    try {
      recognitionRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
      onError?.('Failed to start recording');
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
    }
  };

  return { isRecording, startRecording, stopRecording };
};

/* ========================================================================== */
/* LOCAL STORAGE PERSISTENCE                                                 */
/* ========================================================================== */

const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  };

  return [storedValue, setValue];
};

/* ========================================================================== */
/* MAIN COMPONENT                                                             */
/* ========================================================================== */

const NexusAI = () => {
  // Theme state (must be declared first)
  const [theme, setTheme] = useLocalStorage('nexus_theme', 'dark');
  const activeTheme = THEME[theme] || THEME.dark;
  
  // Persistent storage
  const [allChats, setAllChats] = useLocalStorage('nexus_chats', []);
  const [config, setConfig] = useLocalStorage('nexus_config', {
    apiUrl: DEFAULT_API_URL,
    wsUrl: DEFAULT_WS_URL,
    systemPrompt: 'You are a helpful AI assistant.'
  });
  
  // Core state
  const [chatInput, setChatInput] = useState('');
  const [activeChat, setActiveChat] = useState(null);
  const [thinking, setThinking] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [leftOpen, setLeftOpen] = useState(true);
  const [err, setErr] = useState(null);
  const [view, setView] = useState('chat');
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  
  // Refs
  const bottom = useRef(null);
  const inputBox = useRef(null);
  const fileBtn = useRef(null);

  // WebSocket connection
  const handleWSMessage = useCallback((data) => {
    switch (data.type) {
      case 'connection':
        console.log('Connection status:', data.status);
        break;


      case 'response_chunk':
        setStreamingMessage(prev => ({
          id: prev?.id || globalMessageId++,
          role: 'ai',
          txt: (prev?.txt || '') + data.content,
          when: new Date(),
          streaming: true
        }));
        break;


      case 'response_complete':
        // ✅ FIX: Set streaming to null BEFORE adding to chat
        setStreamingMessage(prev => {
          if (prev) {
            const finalMsg = { ...prev, streaming: false };
            // ✅ Use setTimeout to ensure state update order
            setTimeout(() => {
              setActiveChat(current => {
                if (!current) return current;
                return {
                  ...current,
                  msgs: [...current.msgs, finalMsg]
                };
              });
            }, 0);
          }
          return null;  // ✅ Clear streaming immediately
        });
        setThinking(false);
        break;


      case 'error':
        setErr(data.message);
        setThinking(false);
        setStreamingMessage(null);
        break;


      default:
        console.log('Unknown message type:', data.type);
    }
  }, []);


  const { status, councilMode, send } = useWebSocket(config.wsUrl, config.apiUrl, handleWSMessage);

  // Voice recognition
  const { isRecording, startRecording, stopRecording } = useVoiceRecognition();

  // Auto-scroll
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeChat?.msgs, streamingMessage]);

  // Save chats when they change
  useEffect(() => {
    if (activeChat) {
      setAllChats(prev => 
        prev.map(c => c.id === activeChat.id ? activeChat : c)
      );
    }
  }, [activeChat, setAllChats]);

  // Chat management
  const spawnChat = () => {
    const chat = {
      id: `chat_${Date.now()}`,
      name: 'Untitled',
      msgs: [],
      made: new Date(),
      tags: [],
      mode: view
    };
    setAllChats(prev => [chat, ...prev]);
    setActiveChat(chat);
  };

  const killChat = (id) => {
    setAllChats(prev => prev.filter(c => c.id !== id));
    if (activeChat?.id === id) setActiveChat(null);
  };

  const forkChat = (msgId) => {
    if (!activeChat) return;
    
    const msgIndex = activeChat.msgs.findIndex(m => m.id === msgId);
    if (msgIndex === -1) return;

    const forkedChat = {
      id: `chat_${Date.now()}`,
      name: `Fork: ${activeChat.name}`,
      msgs: activeChat.msgs.slice(0, msgIndex + 1),
      made: new Date(),
      tags: [...activeChat.tags, 'forked'],
      mode: activeChat.mode
    };

    setAllChats(prev => [forkedChat, ...prev]);
    setActiveChat(forkedChat);
  };

  // File upload to backend
  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${config.apiUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Upload error:', error);
      setErr(`Failed to upload ${file.name}`);
      return null;
    }
  };

  // Send message
  const blast = async () => {
    if (!chatInput.trim() && !attachments.length) return;
    if (status !== 'connected') {
      setErr('Not connected to server. Reconnecting...');
      return;
    }

    // Create chat if needed
    let currentChat = activeChat;
    if (!currentChat) {
      const newChat = {
        id: `chat_${Date.now()}`,
        name: chatInput.slice(0, 30) || 'New Chat',
        msgs: [],
        made: new Date(),
        tags: [],
        mode: view
      };
      setAllChats(prev => [newChat, ...prev]);
      setActiveChat(newChat);
      currentChat = newChat;
    }

    // Upload files first
    const fileInfos = [];
    for (const file of attachments) {
      const result = await uploadFile(file);
      if (result) fileInfos.push(result);
    }

    // Create user message
    const userMsg = {
      id: globalMessageId++,
      role: 'user',
      txt: chatInput,
      files: fileInfos,
      when: new Date(),
    };

    // Update chat
    const updatedChat = {
      ...currentChat,
      msgs: [...currentChat.msgs, userMsg],
      name: currentChat.name === 'Untitled' ? chatInput.slice(0, 30) : currentChat.name
    };

    setActiveChat(updatedChat);
    setAllChats(prev => prev.map(c => c.id === updatedChat.id ? updatedChat : c));

    // Send to backend
    const sent = send({
      type: 'message',
      content: chatInput,
      conversation_id: currentChat.id,
      files: fileInfos,
      mode: view,
      system_prompt: config.systemPrompt
    });

    if (sent) {
      setChatInput('');
      setAttachments([]);
      setThinking(true);
      // Reset textarea height
      if (inputBox.current) {
        inputBox.current.style.height = 'auto';
      }
    } else {
      setErr('Failed to send message. Check connection.');
    }
  };

  // Voice input
  const toggleVoice = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording(
        (transcript) => {
          setChatInput(prev => prev + (prev ? ' ' : '') + transcript);
        },
        (error) => {
          setErr(`Voice recognition error: ${error}`);
        }
      );
    }
  };

  // File handling
  const grabFiles = (e) => {
    const files = Array.from(e.target.files);
    setAttachments(prev => [...prev, ...files]);
  };

  const dropFile = (idx) => {
    setAttachments(prev => prev.filter((_, i) => i !== idx));
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Copied to clipboard');
    }).catch(err => {
      console.error('Failed to copy:', err);
      setErr('Failed to copy to clipboard');
    });
  };

  // Regenerate response
  const regenerate = (msgId) => {
    if (!activeChat) return;
    
    const msgIndex = activeChat.msgs.findIndex(m => m.id === msgId);
    if (msgIndex === -1 || msgIndex === 0) return;

    // Find the user message before this AI response
    const userMsg = activeChat.msgs[msgIndex - 1];
    if (userMsg.role !== 'user') return;

    // Remove messages after the user message
    const trimmedMsgs = activeChat.msgs.slice(0, msgIndex);
    setActiveChat(prev => ({ ...prev, msgs: trimmedMsgs }));

    // Resend the user message
    const sent = send({
      type: 'message',
      content: userMsg.txt,
      conversation_id: activeChat.id,
      files: userMsg.files || [],
      mode: view,
      system_prompt: config.systemPrompt
    });

    if (sent) {
      setThinking(true);
    }
  };

  // Export chat
  const exportChat = async () => {
    if (!activeChat) return;

    try {
      const response = await fetch(`${config.apiUrl}/export`);
      const data = await response.json();
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat_${activeChat.name}_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setErr('Export failed');
    }
  };

  // Clear history
  const clearHistory = async () => {
    try {
      await fetch(`${config.apiUrl}/clear`, { method: 'POST' });
      setActiveChat(null);
      setAllChats([]);
      setShowSettings(false);
    } catch (error) {
      setErr('Failed to clear history');
    }
  };

  // Get all messages including streaming
  const allMessages = activeChat?.msgs || [];
  const displayMessages = streamingMessage 
    ? [...allMessages, streamingMessage]
    : allMessages;

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      width: '100vw',
      backgroundColor: activeTheme.bg,
      color: activeTheme.text,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      overflow: 'hidden'
    }}>
      
      {/* Left sidebar */}
      {leftOpen && (
        <div style={{
          width: '280px',
          backgroundColor: activeTheme.surface,
          borderRight: `1px solid ${activeTheme.border}`,
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.2s ease'
        }}>
          
          <div style={{ padding: '16px', borderBottom: `1px solid ${activeTheme.border}` }}>
            <button
              onClick={spawnChat}
              style={{
                width: '100%',
                padding: '14px',
                background: `linear-gradient(135deg, ${activeTheme.accent} 0%, ${activeTheme.accentDark} 100%)`,
                border: 'none',
                borderRadius: '12px',
                color: 'white',
                fontWeight: '600',
                fontSize: '15px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transform: 'rotate(-0.5deg)',
                boxShadow: '0 4px 12px rgba(255, 107, 157, 0.25)',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.transform = 'rotate(0deg) scale(1.02)'}
              onMouseLeave={(e) => e.target.style.transform = 'rotate(-0.5deg) scale(1)'}
            >
              <Plus size={18} />
              New Chat
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
            {allChats.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: activeTheme.textMuted,
                fontSize: '14px'
              }}>
                No chats yet.<br/>Start one above! ↑
              </div>
            ) : (
              allChats.map(chat => (
                <div
                  key={chat.id}
                  onClick={() => setActiveChat(chat)}
                  style={{
                    padding: '12px 14px',
                    marginBottom: '6px',
                    backgroundColor: activeChat?.id === chat.id ? activeTheme.surfaceHover : 'transparent',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    border: activeChat?.id === chat.id ? `1px solid ${activeTheme.accent}` : '1px solid transparent',
                    position: 'relative',
                    transition: 'all 0.15s',
                    transform: activeChat?.id === chat.id ? 'translateX(3px)' : 'translateX(0)'
                  }}
                  onMouseEnter={(e) => {
                    if (activeChat?.id !== chat.id) {
                      e.currentTarget.style.backgroundColor = activeTheme.surfaceHover;
                      e.currentTarget.style.transform = 'translateX(2px)';
                    }
                    const deleteBtn = e.currentTarget.querySelector('.delete-btn');
                    if (deleteBtn) deleteBtn.style.opacity = '1';
                  }}
                  onMouseLeave={(e) => {
                    if (activeChat?.id !== chat.id) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }
                    const deleteBtn = e.currentTarget.querySelector('.delete-btn');
                    if (deleteBtn) deleteBtn.style.opacity = '0';
                  }}
                >
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '500',
                    marginBottom: '4px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {chat.name}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: activeTheme.textMuted
                  }}>
                    {chat.msgs.length} messages
                  </div>
                  
                  <button
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      killChat(chat.id);
                    }}
                    style={{
                      position: 'absolute',
                      right: '8px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      padding: '6px',
                      backgroundColor: activeTheme.surface,
                      border: 'none',
                      borderRadius: '6px',
                      color: activeTheme.textMuted,
                      cursor: 'pointer',
                      opacity: 0,
                      transition: 'opacity 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = activeTheme.accent;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = activeTheme.textMuted;
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>

          <div style={{
            padding: '12px',
            borderTop: `1px solid ${activeTheme.border}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <button 
              onClick={exportChat}
              disabled={!activeChat}
              style={{
                padding: '10px',
                backgroundColor: 'transparent',
                border: `1px solid ${activeTheme.border}`,
                borderRadius: '8px',
                color: activeChat ? activeTheme.textMuted : activeTheme.border,
                cursor: activeChat ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (activeChat) {
                  e.target.style.borderColor = activeTheme.accent;
                  e.target.style.color = activeTheme.accent;
                }
              }}
              onMouseLeave={(e) => {
                if (activeChat) {
                  e.target.style.borderColor = activeTheme.border;
                  e.target.style.color = activeTheme.textMuted;
                }
              }}
            >
              <Download size={16} />
              Export Chat
            </button>
            
            <div style={{ display: 'flex', gap: '6px' }}>
              <button style={{
                flex: 1,
                padding: '10px',
                backgroundColor: 'transparent',
                border: `1px solid ${activeTheme.border}`,
                borderRadius: '8px',
                color: activeTheme.textMuted,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onClick={() => setShowSettings(true)}
              >
                <Settings size={16} />
              </button>
              <button 
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                style={{
                  flex: 1,
                  padding: '10px',
                  backgroundColor: 'transparent',
                  border: `1px solid ${activeTheme.border}`,
                  borderRadius: '8px',
                  color: activeTheme.textMuted,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        
        {/* Header */}
        <div style={{
          height: '64px',
          borderBottom: `1px solid ${activeTheme.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          backgroundColor: activeTheme.surface,
          position: 'relative'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              onClick={() => setLeftOpen(!leftOpen)}
              style={{
                padding: '8px',
                backgroundColor: 'transparent',
                border: 'none',
                color: activeTheme.textMuted,
                cursor: 'pointer',
                borderRadius: '6px',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = activeTheme.surfaceHover}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              <MoreVertical size={20} />
            </button>
            
            <div>
              <div style={{
                fontSize: '18px',
                fontWeight: '700',
                background: `linear-gradient(90deg, ${activeTheme.accent}, ${activeTheme.secondary})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.5px'
              }}>
                nexus
              </div>
              <div style={{
                fontSize: '11px',
                color: activeTheme.textMuted,
                marginTop: '2px',
                fontWeight: '500',
                letterSpacing: '1px'
              }}>
                {status === 'connected' ? `${councilMode} • ${view}` : 'CONNECTING...'}
              </div>
            </div>
          </div>

          {/* Mode switcher */}
          <div style={{
            display: 'flex',
            gap: '6px',
            backgroundColor: activeTheme.bg,
            padding: '4px',
            borderRadius: '10px',
            border: `1px solid ${activeTheme.border}`
          }}>
            {['chat', 'code', 'research'].map(mode => (
              <button
                key={mode}
                onClick={() => setView(mode)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: view === mode ? activeTheme.accent : 'transparent',
                  border: 'none',
                  borderRadius: '7px',
                  color: view === mode ? 'white' : activeTheme.textMuted,
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: '600',
                  textTransform: 'lowercase',
                  transition: 'all 0.2s',
                  transform: view === mode ? 'scale(1.05)' : 'scale(1)'
                }}
              >
                {mode}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: status === 'connected' ? activeTheme.success : activeTheme.accent,
              animation: status === 'connected' ? 'pulse 2s ease-in-out infinite' : 'none'
            }} />
            <span style={{ fontSize: '12px', color: activeTheme.textMuted }}>
              {status}
            </span>
          </div>
        </div>

        {/* Error banner */}
        {err && (
          <div style={{
            padding: '12px 24px',
            backgroundColor: `${activeTheme.accent}20`,
            borderBottom: `1px solid ${activeTheme.accent}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <AlertCircle size={18} color={activeTheme.accent} />
              <span style={{ fontSize: '14px' }}>{err}</span>
            </div>
            <button
              onClick={() => setErr(null)}
              style={{
                padding: '4px',
                backgroundColor: 'transparent',
                border: 'none',
                color: activeTheme.accent,
                cursor: 'pointer'
              }}
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '32px',
          backgroundColor: activeTheme.bg
        }}>
          {displayMessages.length === 0 ? (
            <div style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '24px'
            }}>
              <div style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                background: `radial-gradient(circle at 30% 30%, ${activeTheme.accent}, ${activeTheme.secondary})`,
                position: 'relative',
                animation: 'float 3s ease-in-out infinite',
                boxShadow: `0 20px 60px ${activeTheme.accent}40`
              }}>
                <Sparkles size={48} style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  color: 'white'
                }} />
              </div>

              <div style={{ textAlign: 'center', maxWidth: '500px' }}>
                <h1 style={{
                  fontSize: '42px',
                  fontWeight: '800',
                  marginBottom: '12px',
                  letterSpacing: '-1px'
                }}>
                  Ready when you are
                </h1>
                <p style={{
                  fontSize: '16px',
                  color: activeTheme.textMuted,
                  lineHeight: '1.6'
                }}>
                  Ask me anything. I've got council reasoning, web search, code execution, and more tricks up my sleeve.
                </p>
              </div>

              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '12px',
                justifyContent: 'center',
                maxWidth: '600px'
              }}>
                {[
                  'Explain quantum computing',
                  'Write a Python script',
                  'Search latest AI news',
                  'Analyze this data'
                ].map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setChatInput(prompt)}
                    style={{
                      padding: '12px 20px',
                      backgroundColor: activeTheme.surface,
                      border: `1px solid ${activeTheme.border}`,
                      borderRadius: '20px',
                      color: activeTheme.text,
                      cursor: 'pointer',
                      fontSize: '14px',
                      transition: 'all 0.2s',
                      transform: `rotate(${Math.random() * 4 - 2}deg)`
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = activeTheme.surfaceHover;
                      e.target.style.borderColor = activeTheme.accent;
                      e.target.style.transform = 'rotate(0deg) scale(1.05)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = activeTheme.surface;
                      e.target.style.borderColor = activeTheme.border;
                      e.target.style.transform = `rotate(${Math.random() * 4 - 2}deg) scale(1)`;
                    }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
              {displayMessages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={msg.id}
                    style={{
                      marginBottom: '28px',
                      display: 'flex',
                      gap: '16px',
                      alignItems: 'flex-start',
                      animation: 'slideIn 0.3s ease-out',
                      animationDelay: `${idx * 0.05}s`,
                      opacity: 0,
                      animationFillMode: 'forwards'
                    }}
                  >
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: isUser ? '12px' : '50%',
                      background: isUser 
                        ? `linear-gradient(135deg, ${activeTheme.warning}, ${activeTheme.accent})`
                        : `linear-gradient(135deg, ${activeTheme.secondary}, ${activeTheme.accent})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px',
                      fontWeight: '700',
                      color: 'white',
                      flexShrink: 0,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      transform: isUser ? 'rotate(-3deg)' : 'rotate(0deg)'
                    }}>
                      {isUser ? 'Y' : <Zap size={20} />}
                    </div>

                    <div style={{ flex: 1 }}>
                      {msg.files?.length > 0 && (
                        <div style={{
                          display: 'flex',
                          gap: '8px',
                          marginBottom: '12px',
                          flexWrap: 'wrap'
                        }}>
                          {msg.files.map((f, i) => (
                            <div key={i} style={{
                              padding: '8px 12px',
                              backgroundColor: activeTheme.surface,
                              border: `1px solid ${activeTheme.border}`,
                              borderRadius: '8px',
                              fontSize: '13px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px'
                            }}>
                              <Paperclip size={14} color={activeTheme.secondary} />
                              {f.filename || f.name}
                            </div>
                          ))}
                        </div>
                      )}

                      <div style={{
                        fontSize: '15px',
                        lineHeight: '1.7',
                        color: activeTheme.text,
                        whiteSpace: 'pre-wrap'
                      }}>
                        <MarkdownRenderer text={msg.txt} theme={activeTheme} />
                      </div>

                      {msg.streaming && (
                        <span style={{
                          display: 'inline-block',
                          width: '8px',
                          height: '16px',
                          marginLeft: '4px',
                          backgroundColor: activeTheme.accent,
                          animation: 'blink 1s infinite',
                          borderRadius: '2px'
                        }} />
                      )}

                      {!isUser && !msg.streaming && (
                        <div style={{
                          marginTop: '12px',
                          display: 'flex',
                          gap: '6px',
                          opacity: 0,
                          transition: 'opacity 0.2s'
                        }}
                        className="action-buttons"
                        onMouseEnter={(e) => e.currentTarget.style.opacity = 1}
                        onMouseLeave={(e) => e.currentTarget.style.opacity = 0}
                        >
                          <button
                            onClick={() => copyToClipboard(msg.txt)}
                            style={{
                              padding: '6px 10px',
                              backgroundColor: activeTheme.surface,
                              border: `1px solid ${activeTheme.border}`,
                              borderRadius: '6px',
                              color: activeTheme.textMuted,
                              cursor: 'pointer',
                              fontSize: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.borderColor = activeTheme.accent;
                              e.target.style.color = activeTheme.accent;
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.borderColor = activeTheme.border;
                              e.target.style.color = activeTheme.textMuted;
                            }}
                          >
                            <Copy size={12} />
                            Copy
                          </button>
                          <button
                            onClick={() => regenerate(msg.id)}
                            style={{
                              padding: '6px 10px',
                              backgroundColor: activeTheme.surface,
                              border: `1px solid ${activeTheme.border}`,
                              borderRadius: '6px',
                              color: activeTheme.textMuted,
                              cursor: 'pointer',
                              fontSize: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.borderColor = activeTheme.accent;
                              e.target.style.color = activeTheme.accent;
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.borderColor = activeTheme.border;
                              e.target.style.color = activeTheme.textMuted;
                            }}
                          >
                            <RefreshCw size={12} />
                            Retry
                          </button>
                          <button
                            onClick={() => forkChat(msg.id)}
                            style={{
                              padding: '6px 10px',
                              backgroundColor: activeTheme.surface,
                              border: `1px solid ${activeTheme.border}`,
                              borderRadius: '6px',
                              color: activeTheme.textMuted,
                              cursor: 'pointer',
                              fontSize: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.borderColor = activeTheme.accent;
                              e.target.style.color = activeTheme.accent;
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.borderColor = activeTheme.border;
                              e.target.style.color = activeTheme.textMuted;
                            }}
                          >
                            <GitBranch size={12} />
                            Fork
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {thinking && !streamingMessage && (
                <div style={{
                  display: 'flex',
                  gap: '16px',
                  alignItems: 'center',
                  marginTop: '20px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    background: `linear-gradient(135deg, ${activeTheme.secondary}, ${activeTheme.accent})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    animation: 'pulse 2s ease-in-out infinite'
                  }}>
                    <Loader size={20} color="white" style={{ animation: 'spin 1s linear infinite' }} />
                  </div>
                  <div style={{ fontSize: '14px', color: activeTheme.textMuted }}>
                    Thinking...
                  </div>
                </div>
              )}

              <div ref={bottom} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div style={{
          padding: '20px 32px 28px',
          backgroundColor: activeTheme.surface,
          borderTop: `1px solid ${activeTheme.border}`
        }}>
          <div style={{ maxWidth: '900px', margin: '0 auto' }}>
            
            {attachments.length > 0 && (
              <div style={{
                marginBottom: '12px',
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap'
              }}>
                {attachments.map((file, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: activeTheme.bg,
                      border: `1px dashed ${activeTheme.accent}`,
                      borderRadius: '10px',
                      fontSize: '13px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      animation: 'bounceIn 0.3s ease-out'
                    }}
                  >
                    <FileText size={14} color={activeTheme.accent} />
                    <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {file.name}
                    </span>
                    <button
                      onClick={() => dropFile(i)}
                      style={{
                        padding: '2px',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: activeTheme.textMuted,
                        cursor: 'pointer'
                      }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div style={{
              display: 'flex',
              gap: '12px',
              backgroundColor: activeTheme.bg,
              padding: '6px',
              borderRadius: '16px',
              border: `2px solid ${activeTheme.border}`,
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.currentTarget.style.borderColor = activeTheme.accent}
            onBlur={(e) => e.currentTarget.style.borderColor = activeTheme.border}
            >
              <input
                type="file"
                ref={fileBtn}
                style={{ display: 'none' }}
                multiple
                onChange={grabFiles}
              />

              <button
                onClick={() => fileBtn.current.click()}
                style={{
                  padding: '12px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: activeTheme.textMuted,
                  cursor: 'pointer',
                  borderRadius: '10px',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = activeTheme.surfaceHover;
                  e.target.style.color = activeTheme.accent;
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'transparent';
                  e.target.style.color = activeTheme.textMuted;
                }}
              >
                <Upload size={20} />
              </button>

              <textarea
                ref={inputBox}
                value={chatInput}
                onChange={(e) => {
                  setChatInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    blast();
                  }
                }}
                placeholder="Type something clever..."
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: activeTheme.text,
                  fontSize: '15px',
                  resize: 'none',
                  outline: 'none',
                  fontFamily: 'inherit',
                  lineHeight: '1.5',
                  maxHeight: '150px'
                }}
                rows={1}
              />

              {chatInput.trim() || attachments.length > 0 ? (
                <button
                  onClick={blast}
                  disabled={thinking || status !== 'connected'}
                  style={{
                    padding: '12px 20px',
                    background: (thinking || status !== 'connected')
                      ? activeTheme.surfaceHover 
                      : `linear-gradient(135deg, ${activeTheme.accent}, ${activeTheme.secondary})`,
                    border: 'none',
                    borderRadius: '10px',
                    color: 'white',
                    cursor: (thinking || status !== 'connected') ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'all 0.2s',
                    boxShadow: (thinking || status !== 'connected') ? 'none' : `0 4px 12px ${activeTheme.accent}40`
                  }}
                  onMouseEnter={(e) => {
                    if (!thinking && status === 'connected') e.target.style.transform = 'scale(1.05)';
                  }}
                  onMouseLeave={(e) => {
                    if (!thinking && status === 'connected') e.target.style.transform = 'scale(1)';
                  }}
                >
                  {thinking ? <Loader size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={18} />}
                  {thinking ? 'Wait...' : 'Send'}
                </button>
              ) : (
                <button
                  onClick={toggleVoice}
                  style={{
                    padding: '12px',
                    backgroundColor: isRecording ? activeTheme.accent : 'transparent',
                    border: 'none',
                    borderRadius: '10px',
                    color: isRecording ? 'white' : activeTheme.textMuted,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (!isRecording) {
                      e.target.style.backgroundColor = activeTheme.surfaceHover;
                      e.target.style.color = activeTheme.accent;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isRecording) {
                      e.target.style.backgroundColor = 'transparent';
                      e.target.style.color = activeTheme.textMuted;
                    }
                  }}
                >
                  {isRecording ? <StopCircle size={20} /> : <Mic size={20} />}
                </button>
              )}
            </div>

            <div style={{
              marginTop: '12px',
              fontSize: '11px',
              color: activeTheme.textMuted,
              textAlign: 'center',
              fontStyle: 'italic',
              opacity: 0.6
            }}>
              Powered by council reasoning • May hallucinate occasionally • Always verify important info
            </div>
          </div>
        </div>
      </div>
      
      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
        config={config} 
        onSave={(newConfig) => {
          setConfig(newConfig);
          setShowSettings(false);
        }}
        onClearHistory={clearHistory}
        activeTheme={activeTheme}
      />

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes bounceIn {
          0% {
            opacity: 0;
            transform: scale(0.3);
          }
          50% {
            transform: scale(1.05);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }

        .action-buttons:hover {
          opacity: 1 !important;
        }

        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: ${activeTheme.bg};
        }

        ::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, ${activeTheme.accent}, ${activeTheme.secondary});
          border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, ${activeTheme.accentDark}, ${activeTheme.secondary});
        }

        ::selection {
          background: ${activeTheme.accent}40;
          color: ${activeTheme.text};
        }

        button {
          user-select: none;
          -webkit-user-select: none;
        }

        textarea:focus {
          outline: none;
        }

        * {
          scroll-behavior: smooth;
        }
      `}</style>
    </div>
  );
};

export default NexusAI;


