// src/components/Sidebar.js
import React from 'react';
import { Book, Database, FileText, Upload } from 'lucide-react';

const Sidebar = ({ activeBrain, uploadedDocument, file, setFile, handleUpload, isUploading, regulation, setRegulation }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header" style={{ marginBottom: '40px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600' }}>FusedChat Studio</h2>
      </div>

      <div className="section">
        <h3>🎓 Academic Context</h3>
        <select 
          className="glass-dropdown"
          value={regulation}
          onChange={(e) => setRegulation(e.target.value)}
        >
          <option value="SITE 23">SITE 23</option>
          <option value="SITE 21">SITE 21</option>
          <option value="SITE 18">SITE 18</option>
        </select>
      </div>

      <div className="section">
        <h3>Active Sources</h3>
        <div className="source-card active">
          <Book size={18} color="#10a37f" />
          <div>
            <h4>Course Syllabus</h4>
            <p>✅ Standard context loaded</p>
          </div>
        </div>

        <div className="source-card active">
          <Database size={18} color="#10a37f" />
          <div>
            <h4>SASI Database</h4>
            <p>✅ JSON records ready</p>
          </div>
        </div>

        <div className={`source-card ${uploadedDocument ? 'active' : ''}`}>
          <FileText size={18} color={uploadedDocument ? "#10a37f" : "#555"} />
          <div>
            <h4>Your Document</h4>
            <p>{uploadedDocument ? '✅ Indexed' : 'Not Uploaded'}</p>
          </div>
        </div>
      </div>

      <div className="section" style={{ marginTop: 'auto' }}>
        <input type="file" id="file-up" accept=".pdf" hidden onChange={(e) => setFile(e.target.files[0])} />
        <label
          htmlFor="file-up"
          className="upload-pdf-btn"
        >
          <Upload size={16} />
          <span>{file ? `Selected: ${file.name.slice(0, 22)}...` : 'Upload PDF'}</span>
        </label>
        <button className="upload-btn" onClick={handleUpload} disabled={!file || isUploading}>
          {isUploading ? "Processing..." : "Upload & Index"}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
