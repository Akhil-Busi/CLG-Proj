// src/components/ChatWindow.js
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Sparkles, FileSearch, HelpCircle, Code, Zap, Brain } from 'lucide-react';

const ChatWindow = ({ messages, input, setInput, handleSend, hasDocument, isLoading, profMode, setProfMode }) => {
  return (
    <main className="main-content">
      <div className="messages-container">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role === 'user' ? 'user-msg' : 'ai-msg'}`}>
            {msg.role === 'assistant' && (
              <div className="ai-icon">
                <Sparkles size={20} color="#10a37f" />
              </div>
            )}
            <div className={msg.role === 'assistant' ? 'ai-bubble' : 'message-text'}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>

      {hasDocument && (
        <div className="quick-tasks">
          <button className="task-btn" onClick={() => setInput("Summarize this document")}> 
            <FileSearch size={14} /> Summarize
          </button>
          <button className="task-btn" onClick={() => setInput("Create a quiz from this file")}>
            <HelpCircle size={14} /> Generate Quiz
          </button>
          <button className="task-btn" onClick={() => setInput("Explain the core logic in this doc")}>
            <Code size={14} /> Explain Logic
          </button>
        </div>
      )}

      <div className="mode-toggle-container">
        <button 
          className={`mode-toggle ${profMode === 'fast' ? 'active' : ''}`}
          onClick={() => setProfMode('fast')}
        >
          <Zap size={14} /> Fast
        </button>
        <button 
          className={`mode-toggle ${profMode === 'deep' ? 'active' : ''}`}
          onClick={() => setProfMode('deep')}
        >
          <Brain size={14} /> Deep Research
        </button>
      </div>

      <div className="input-area">
        <div className="input-pill">
          <input
            placeholder="Ask anything about the syllabus or your documents..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
          />
          <button className="send-btn" onClick={handleSend} disabled={isLoading || !input.trim()}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </main>
  );
};

export default ChatWindow;
