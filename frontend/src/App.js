import React, { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHUNK_SIZE = 1024 * 1024; // 1MB

function prettyBytes(bytes) {
  const sizes = ['B','KB','MB','GB'];
  if (bytes === 0) return '0 B';
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

function App() {
  const [isDragOver, setIsDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState("Idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const inputRef = useRef();

  useEffect(() => {
    // warm up API
    axios.get(`${API}/`).catch(() => {});
  }, []);

  const onFiles = useCallback((files) => {
    const f = files[0];
    if (!f) return;
    const ext = f.name.toLowerCase();
    const allowed = ext.endsWith(".pdf") || ext.endsWith(".docx");
    if (!allowed) {
      setError("Please upload a PDF or DOCX file");
      return;
    }
    setError(null);
    setResult(null);
    setFile(f);
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    onFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setStatus("Initializing upload...");
      setUploadProgress(0);

      const initRes = await axios.post(`${API}/upload/init`, {
        filename: file.name,
        size: file.size,
        mimeType: file.type || (file.name.toLowerCase().endsWith('.pdf') ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
      });
      const uploadId = initRes.data.uploadId;

      setStatus("Uploading chunks...");
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

      for (let index = 0; index < totalChunks; index++) {
        const start = index * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const blob = file.slice(start, end);
        await axios.post(`${API}/upload/chunk`, blob, {
          headers: { 'Content-Type': 'application/octet-stream' },
          params: { uploadId, index }
        });
        setUploadProgress(Math.round(((index + 1) / totalChunks) * 100));
      }

      setStatus("Analyzing resume...");
      const completeRes = await axios.post(`${API}/upload/complete`, { uploadId });
      setResult(completeRes.data);
      setStatus("Done");
    } catch (e) {
      console.error(e);
      setError(e?.response?.data?.detail || e.message || "Upload failed");
      setStatus("Error");
    }
  };

  return (
    <div className="App">
      <div className="container">
        <div className="card" style={{ padding: "2rem" }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>Resume → Job Matches</h1>
          <p className="subtitle" style={{ marginBottom: 24 }}>Upload your resume (PDF or DOCX). We extract skills and show top matching jobs.</p>

          <div
            className={`dropzone ${isDragOver ? "dragover" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input ref={inputRef} type="file" style={{ display: 'none' }} accept=".pdf,.docx" onChange={(e) => onFiles(e.target.files)} />
            {!file ? (
              <>
                <div style={{ fontSize: 18, opacity: 0.9 }}>Drag & drop your resume here, or click to browse</div>
                <div className="subtitle" style={{ marginTop: 8 }}>Accepted: PDF, DOCX • Max ~25MB</div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 18 }}><strong>{file.name}</strong> <span className="subtitle">({prettyBytes(file.size)})</span></div>
                <div style={{ marginTop: 16 }}>
                  <button className="btn" onClick={handleUpload} disabled={status === 'Analyzing resume...' || status === 'Uploading chunks...'}>
                    {status.startsWith('Initializing') || status.startsWith('Uploading') || status.startsWith('Analyzing') ? 'Working...' : 'Upload & Analyze'}
                  </button>
                </div>
              </>
            )}
          </div>

          {(status !== 'Idle') && (
            <div style={{ marginTop: 16 }}>
              <div className="subtitle" style={{ marginBottom: 8 }}>{status}</div>
              <div className="progress">
                <div className="progressbar" style={{ width: `${uploadProgress}%` }}></div>
              </div>
            </div>
          )}

          {error && (
            <div style={{ marginTop: 16, color: '#fca5a5' }}>{error}</div>
          )}
        </div>

        {result && (
          <div className="card" style={{ marginTop: 24, padding: 20 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>Top Matches</h2>
            <div className="subtitle" style={{ marginBottom: 16 }}>Extracted {result?.analysis?.extracted_skills?.length || 0} skills • Text size {result?.analysis?.text_chars} chars</div>

            <div style={{ marginBottom: 10 }}>
              {(result?.analysis?.extracted_skills || []).map((s) => (
                <span key={s} className="badge">{s}</span>
              ))}
            </div>

            <div className="jobs-grid">
              {(result?.matches || []).map((m) => (
                <div className="job-card" key={m.job_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <div>
                      <div style={{ fontWeight: 700 }}>{m.job_title}</div>
                      <div className="subtitle">{m.company}{m.location ? ` • ${m.location}` : ''}</div>
                    </div>
                    <div className="badge" style={{ fontWeight: 800 }}>{m.match_percent}%</div>
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <div className="subtitle" style={{ marginBottom: 6 }}>Matched</div>
                    {(m.matched_skills || []).map(s => <span key={s} className="badge">{s}</span>)}
                  </div>
                  {m.missing_skills?.length > 0 && (
                    <div style={{ marginTop: 10 }}>
                      <div className="subtitle" style={{ marginBottom: 6 }}>Missing</div>
                      {(m.missing_skills || []).map(s => <span key={s} className="badge" style={{ opacity: 0.7 }}>{s}</span>)}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={{ marginTop: 20 }}>
              <button className="btn" onClick={() => { setFile(null); setResult(null); setStatus('Idle'); setUploadProgress(0); }}>Try another resume</button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;