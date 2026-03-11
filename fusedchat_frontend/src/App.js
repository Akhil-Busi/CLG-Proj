// src/App.js
import { useState, useRef } from "react";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const BRAINS = {
  PROFESSIONAL: "educational",
  ADMIN: "admin",
  DOCUMENT: "document"
};

const PROF_MODES = {
  FAST: "fast",
  DEEP: "deep"
};

function App() {
  // State remains here as the single source of truth
  const [messages, setMessages] = useState([
    { role: "assistant", content: "👋 Welcome to FusedChat! Select a brain to get started.", metadata: { brain: "system", timestamp: new Date() } }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeBrain] = useState(BRAINS.PROFESSIONAL);
  const [profMode, setProfMode] = useState(PROF_MODES.FAST);
  const [uploadedDocument, setUploadedDocument] = useState(null);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [regulation, setRegulation] = useState("SITE 21");  // New regulation state
  const sessionId = useRef(uuidv4());

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input, metadata: { brain: "studio", timestamp: new Date() }};
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      // ALWAYS send the mode (fast/deep), regulation, and document_id if available
      const payload = { 
        session_id: sessionId.current, 
        query: input,
        mode: profMode, // This ensures "Deep Mode" works
        regulation: regulation,  // Include the selected regulation
        document_id: uploadedDocument?.document_id || null 
      };

      // Use the main /chat endpoint for everything in Studio
      const response = await axios.post(`${API_URL}/chat`, payload);

      const aiMsg = {
        role: "assistant", 
        content: response.data.response,
        metadata: {
          brain: response.data.brain, 
          sources: response.data.sources_used || [],
          timestamp: new Date()
        }
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMsg = {
        role: "assistant", content: `❌ Error: ${error.response?.data?.detail || error.message}`,
        metadata: { brain: "error", timestamp: new Date() }
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId.current);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData);
      setUploadedDocument({ document_id: response.data.document_id, filename: response.data.filename, chunks: response.data.chunks_created });
      setFile(null);

      setMessages((prev) => [...prev, {
        role: "assistant", content: `✅ Document "${response.data.filename}" loaded! You can now ask questions about it.`,
        metadata: { brain: "system", timestamp: new Date() }
      }]);
    } catch (error) {
      console.error("Upload error:", error);
    } finally {
      setIsUploading(false);
    }
  };


  return (
    <div className="app-container">
      <div className="bg-orb orb-1"></div>
      <div className="bg-orb orb-2"></div>
      <Sidebar
        activeBrain={activeBrain}
        uploadedDocument={uploadedDocument}
        file={file}
        setFile={setFile}
        handleUpload={handleUpload}
        isUploading={isUploading}
        regulation={regulation}
        setRegulation={setRegulation}
      />
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        handleSend={handleSend}
        input={input}
        setInput={setInput}
        activeBrain={activeBrain}
        profMode={profMode}
        setProfMode={setProfMode}
        hasDocument={!!uploadedDocument}
      />
    </div>
  );
}

export default App;
