import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";
import { 
  Send, BookOpen, FileText, Cpu, Settings, ChevronDown, 
  Upload, AlertCircle, CheckCircle, Brain, Zap
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

// Brain Types
const BRAINS = {
  PROFESSIONAL: "professional",
  ADMIN: "administrator",
  DOCUMENT: "document"
};

// Professional Brain Modes
const PROF_MODES = {
  FAST: "fast",
  DEEP: "deep"
};

function App() {
  // ========== STATE MANAGEMENT ==========
  
  // Core chat state
  const [messages, setMessages] = useState([
    { 
      role: "assistant", 
      content: "👋 Welcome to FusedChat! I'm a three-brain AI assistant for SASI Institute of Technology & Engineering.",
      metadata: {
        brain: "system",
        timestamp: new Date()
      }
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // Brain selection
  const [activeBrain, setActiveBrain] = useState(BRAINS.PROFESSIONAL);
  const [profMode, setProfMode] = useState(PROF_MODES.FAST); // Fast or Deep
  
  // Document mode
  const [uploadedDocument, setUploadedDocument] = useState(null);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  
  // UI state
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Session management
  const sessionId = useRef(uuidv4());
  
  // Auto-scroll
  const messagesEndRef = useRef(null);

  
  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ========== HANDLERS ==========

  const handleSend = async () => {
    if (!input.trim()) return;
    if (activeBrain === BRAINS.DOCUMENT && !uploadedDocument) {
      alert("⚠️ Please upload a document first!");
      return;
    }

    const userMsg = {
      role: "user",
      content: input,
      metadata: {
        brain: activeBrain,
        timestamp: new Date()
      }
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      let response;
      const payload = {
        session_id: sessionId.current,
        query: input
      };

      // Route based on active brain
      if (activeBrain === BRAINS.PROFESSIONAL) {
        payload.mode = profMode; // Add fast/deep mode
        response = await axios.post(`${API_URL}/chat`, payload);
      } 
      else if (activeBrain === BRAINS.ADMIN) {
        response = await axios.post(`${API_URL}/chat`, payload);
      } 
      else if (activeBrain === BRAINS.DOCUMENT) {
        payload.document_id = uploadedDocument.document_id;
        response = await axios.post(`${API_URL}/chat/document`, payload);
      }

      // Add AI response with metadata
      const aiMsg = {
        role: "assistant",
        content: response.data.response,
        metadata: {
          brain: response.data.brain,
          confidence: response.data.confidence,
          sources: response.data.sources || [],
          citations: response.data.citations || [],
          timestamp: new Date()
        }
      };
      
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMsg = {
        role: "assistant",
        content: `❌ Error: ${error.response?.data?.detail || error.message}`,
        metadata: {
          brain: "error",
          timestamp: new Date()
        }
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadStatus({ type: "uploading", message: "📤 Uploading document..." });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId.current);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData);
      
      setUploadedDocument({
        document_id: response.data.document_id,
        filename: response.data.filename,
        chunks: response.data.chunks_created
      });
      
      setFile(null);
      setUploadStatus({
        type: "success",
        message: `✅ Document loaded! (${response.data.chunks_created} chunks)`
      });

      // Add system message
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: `✅ Document "${response.data.filename}" loaded successfully! I've indexed ${response.data.chunks_created} chunks. You can now ask questions about this document.`,
        metadata: {
          brain: "system",
          timestamp: new Date()
        }
      }]);

      setTimeout(() => setUploadStatus(null), 3000);
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus({
        type: "error",
        message: `❌ Upload failed: ${error.response?.data?.detail || error.message}`
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const switchBrain = (brainType) => {
    setActiveBrain(brainType);
    setShowModeSelector(false);
    
    // Add system message
    setMessages((prev) => [...prev, {
      role: "assistant",
      content: getBrainSwitchMessage(brainType),
      metadata: {
        brain: "system",
        timestamp: new Date()
      }
    }]);
  };

  const getBrainSwitchMessage = (brain) => {
    const messages = {
      [BRAINS.PROFESSIONAL]: "🧠 Professional Brain activated! Ask me about courses, concepts, and academic topics. Use Fast mode for quick answers or Deep mode for comprehensive research.",
      [BRAINS.ADMIN]: "🤖 Administrator Brain activated! I can help with faculty info, fees, bus routes, placements, and other campus information.",
      [BRAINS.DOCUMENT]: "📄 Document Brain activated! Upload a PDF and I'll analyze it for you. Ask any questions about the document content."
    };
    return messages[brain] || "Brain switched!";
  };

  // ========== RENDERING HELPERS ==========

  const getBrainColor = (brain) => {
    const colors = {
      [BRAINS.PROFESSIONAL]: "🔵",
      [BRAINS.ADMIN]: "🟢",
      [BRAINS.DOCUMENT]: "🟣"
    };
    return colors[brain] || "⚪";
  };

  const getBrainLabel = (brain) => {
    const labels = {
      [BRAINS.PROFESSIONAL]: "Professional Brain",
      [BRAINS.ADMIN]: "Admin Brain",
      [BRAINS.DOCUMENT]: "Document Brain"
    };
    return labels[brain] || "Unknown";
  };

  const renderMessage = (msg, index) => {
    const isUser = msg.role === "user";
    const metadata = msg.metadata || {};

    return (
      <div key={index} className={`message ${isUser ? "user-msg" : "ai-msg"}`}>
        <div className="message-avatar">
          {isUser ? (
            <div className="avatar-user">👤</div>
          ) : (
            <div className="avatar-ai">
              {metadata.brain === "error" ? "⚠️" : "🤖"}
            </div>
          )}
        </div>
        
        <div className="message-content">
          <p className="message-text">{msg.content}</p>
          
          {/* Metadata - Show for AI messages */}
          {!isUser && metadata.brain && metadata.brain !== "system" && (
            <div className="message-metadata">
              <span className="brain-badge">{getBrainColor(metadata.brain)} {getBrainLabel(metadata.brain)}</span>
              
              {metadata.confidence && (
                <span className="confidence-badge">
                  ⭐ {(metadata.confidence * 100).toFixed(0)}% confidence
                </span>
              )}
              
              {metadata.sources && metadata.sources.length > 0 && (
                <span className="sources-badge">
                  📚 {metadata.sources.length} sources
                </span>
              )}
              
              {metadata.citations && metadata.citations.length > 0 && (
                <div className="citations-list">
                  {metadata.citations.map((cite, i) => (
                    <span key={i} className="citation-item">
                      📄 Page {cite.page}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  
  // ========== MAIN RENDER ==========

  return (
    <div className="app-layout">
      {/* ===== SIDEBAR ===== */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "collapsed"}`}>
        <div className="sidebar-header">
          <div className="logo">
            <Brain size={28} />
            <h1>FusedChat</h1>
          </div>
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <ChevronDown size={20} />
          </button>
        </div>

        {sidebarOpen && (
          <>
            {/* Brain Selection */}
            <div className="section">
              <h3>🧠 Select Brain</h3>
              
              <button
                className={`brain-btn ${activeBrain === BRAINS.PROFESSIONAL ? "active" : ""}`}
                onClick={() => switchBrain(BRAINS.PROFESSIONAL)}
              >
                <BookOpen size={18} />
                <span>Professional Brain</span>
                <span className="brain-desc">Education</span>
              </button>

              <button
                className={`brain-btn ${activeBrain === BRAINS.ADMIN ? "active" : ""}`}
                onClick={() => switchBrain(BRAINS.ADMIN)}
              >
                <Settings size={18} />
                <span>Admin Brain</span>
                <span className="brain-desc">Institute Info</span>
              </button>

              <button
                className={`brain-btn ${activeBrain === BRAINS.DOCUMENT ? "active" : ""}`}
                onClick={() => switchBrain(BRAINS.DOCUMENT)}
              >
                <FileText size={18} />
                <span>Document Brain</span>
                <span className="brain-desc">PDF Analysis</span>
              </button>
            </div>

            {/* Professional Brain Settings */}
            {activeBrain === BRAINS.PROFESSIONAL && (
              <div className="section">
                <h3>⚡ Mode Selection</h3>
                
                <button
                  className={`mode-btn ${profMode === PROF_MODES.FAST ? "active" : ""}`}
                  onClick={() => setProfMode(PROF_MODES.FAST)}
                >
                  <Zap size={16} />
                  <span>Fast Mode</span>
                  <span className="mode-desc">Quick answers</span>
                </button>

                <button
                  className={`mode-btn ${profMode === PROF_MODES.DEEP ? "active" : ""}`}
                  onClick={() => setProfMode(PROF_MODES.DEEP)}
                >
                  <Brain size={16} />
                  <span>Deep Mode</span>
                  <span className="mode-desc">Comprehensive</span>
                </button>
              </div>
            )}

            {/* Document Upload */}
            {activeBrain === BRAINS.DOCUMENT && (
              <div className="section upload-section">
                <h3>📤 Upload Document</h3>
                
                {uploadedDocument ? (
                  <div className="document-loaded">
                    <CheckCircle size={20} color="#10a37f" />
                    <div>
                      <p className="doc-name">{uploadedDocument.filename}</p>
                      <p className="doc-info">{uploadedDocument.chunks} chunks indexed</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setFile(e.target.files[0])}
                      className="file-input"
                      id="pdf-input"
                    />
                    <label htmlFor="pdf-input" className="file-label">
                      <Upload size={18} />
                      Choose PDF
                    </label>

                    <button
                      className="upload-btn"
                      onClick={handleUpload}
                      disabled={!file || isUploading}
                    >
                      {isUploading ? "Indexing..." : "Upload & Index"}
                    </button>
                  </>
                )}

                {uploadStatus && (
                  <div className={`upload-status ${uploadStatus.type}`}>
                    {uploadStatus.type === "success" && <CheckCircle size={16} />}
                    {uploadStatus.type === "error" && <AlertCircle size={16} />}
                    {uploadStatus.message}
                  </div>
                )}
              </div>
            )}

            {/* Session Info */}
            <div className="section session-info">
              <p className="session-label">Session ID</p>
              <code className="session-id">{sessionId.current.slice(0, 8)}...</code>
            </div>
          </>
        )}
      </aside>

      {/* ===== MAIN CHAT AREA ===== */}
      <main className="main-content">
        {/* Header */}
        <header className="chat-header">
          <h2>
            {getBrainColor(activeBrain)} {getBrainLabel(activeBrain)}
          </h2>
          {activeBrain === BRAINS.PROFESSIONAL && (
            <span className="mode-indicator">
              {profMode === PROF_MODES.FAST ? "⚡ Fast Mode" : "🔬 Deep Mode"}
            </span>
          )}
        </header>

        {/* Messages */}
        <div className="messages-container">
          <div className="messages-list">
            {messages.map((msg, idx) => renderMessage(msg, idx))}
            {isLoading && (
              <div className="message ai-msg loading-msg">
                <div className="loader">
                  <div className="dot"></div>
                  <div className="dot"></div>
                  <div className="dot"></div>
                </div>
                <span>Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <footer className="chat-footer">
          <div className="input-wrapper">
            <input
              type="text"
              className="chat-input"
              placeholder={
                activeBrain === BRAINS.PROFESSIONAL
                  ? "Ask about concepts, courses, or topics..."
                  : activeBrain === BRAINS.ADMIN
                  ? "Ask about fees, faculty, buses, placements..."
                  : "Ask a question about the document..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              title="Send message (Enter)"
            >
              <Send size={20} />
            </button>
          </div>
          <p className="input-hint">Press Enter to send • Shift+Enter for new line</p>
        </footer>
      </main>
    </div>
  );
}

export default App;
