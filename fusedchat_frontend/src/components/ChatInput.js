// src/components/ChatInput.js
import React from 'react';
import { Send } from 'lucide-react';

const BRAINS = {
  EDUCATIONAL: "educational",
  ADMIN: "admin",
  DOCUMENT: "document"
};

const ChatInput = ({ input, setInput, handleSend, isLoading, activeBrain }) => {
  
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getPlaceholder = () => {
    const placeholders = {
      [BRAINS.EDUCATIONAL]: "Ask about concepts, courses, or topics...",
      [BRAINS.ADMIN]: "Ask about fees, faculty, buses, placements...",
      [BRAINS.DOCUMENT]: "Ask a question about the document..."
    };
    return placeholders[activeBrain];
  };

  return (
    <footer className="chat-footer">
      <div className="input-wrapper">
        <input
          type="text"
          className="chat-input"
          placeholder={getPlaceholder()}
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
  );
};

export default ChatInput;
