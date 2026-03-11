// src/components/Message.js
import React from 'react';
import { Brain, CheckCircle, AlertCircle } from 'lucide-react';

const BRAINS = {
  EDUCATIONAL: "educational",
  ADMIN: "admin",
  DOCUMENT: "document"
};

const getBrainInfo = (brain) => {
  const info = {
    [BRAINS.EDUCATIONAL]: { color: "🔵", label: "Professional Brain" },
    [BRAINS.ADMIN]: { color: "🟢", label: "Admin Brain" },
    [BRAINS.DOCUMENT]: { color: "🟣", label: "Document Brain" },
    system: { color: "⚙️", label: "System Message" },
    error: { color: "⚠️", label: "Error" }
  };
  return info[brain] || { color: "⚪", label: "Unknown" };
};

const Message = ({ msg }) => {
  const isUser = msg.role === "user";
  const metadata = msg.metadata || {};
  const brainInfo = getBrainInfo(metadata.brain);

  return (
    <div className={`message ${isUser ? "user-msg" : "ai-msg"}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="avatar-user">👤</div>
        ) : (
          <div className="avatar-ai">
            {metadata.brain === "error" ? <AlertCircle size={24} /> : <Brain size={24} />}
          </div>
        )}
      </div>
      
      <div className="message-content">
        <p className="message-text">{msg.content}</p>
        
        {!isUser && metadata.brain && metadata.brain !== "system" && (
          <div className="message-metadata">
            <span className="brain-badge">{brainInfo.color} {brainInfo.label}</span>
            
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

export default Message;
