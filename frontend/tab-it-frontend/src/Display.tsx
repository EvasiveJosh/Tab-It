import { useState, useEffect, useCallback } from 'react';
import type { ChangeEvent } from 'react';
import './TabDisplay.css';

// --- INTERFACES ---
interface NoteGroup {
  string: number[];
  fret: number[];
}

interface TabJson {
  notes: NoteGroup[];
}

// --- ICONS ---
const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
);

const CodeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
);

const CloseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
);

export default function TabDisplay() {
  const [jsonInput, setJsonInput] = useState<string>('');
  
  const [rawLines, setRawLines] = useState<{ [key: number]: string } | null>(null);
  const [tabOutput, setTabOutput] = useState<string>('');
  
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // --- 1. PROCESS JSON TO RAW LINES ---
  // This function only builds the "infinite" strings, it does NOT format them for the screen yet.
  const processJsonToLines = (data?: TabJson) => {
    setError(null);
    try {
      let parsed: TabJson;
      if (data) parsed = data;
      else parsed = JSON.parse(jsonInput);

      if (!parsed.notes || !Array.isArray(parsed.notes)) {
        throw new Error("JSON must contain a 'notes' array.");
      }

      let lines: { [key: number]: string } = {
        1: "e|", 2: "B|", 3: "G|", 4: "D|", 5: "A|", 6: "E|"
      };

      parsed.notes.forEach((group) => {
        let currentBeat: { [key: number]: string } = {};
        group.string.forEach((stringNum, idx) => {
          const fretNum = group.fret[idx];
          currentBeat[stringNum] = fretNum.toString();
        });

        let maxWidth = 1; 
        Object.values(currentBeat).forEach(f => {
          if (f.length > maxWidth) maxWidth = f.length;
        });

        for (let string = 1; string <= 6; string++) {
          const fret = currentBeat[string];
          if (fret !== undefined) {
            const padding = "-".repeat(maxWidth - fret.length);
            lines[string] += `-${fret}${padding}-`;
          } else {
            lines[string] += `-${"-".repeat(maxWidth)}-`;
          }
        }
      });

      // Save the raw infinite lines to state
      setRawLines(lines);
      setIsModalOpen(false);

    } catch (err) {
      setError("Invalid JSON format.");
    }
  };

  // --- 2. DYNAMIC FORMATTER ---
  const formatLinesToScreen = useCallback(() => {
    if (!rawLines) return;

    const PADDING_PX = 100; 
    
    const CHAR_WIDTH_PX = 9.8; 
    
    const availableWidth = window.innerWidth - PADDING_PX; 
    
    // Calculate how many chars fit (min 40 to avoid breaking on tiny screens)
    const dynamicLimit = Math.max(40, Math.floor(availableWidth / CHAR_WIDTH_PX));

    const CHARS_PER_LINE = dynamicLimit;
    
    let formattedOutput = "";
    const totalLength = rawLines[1].length;

    for (let i = 0; i < totalLength; i += CHARS_PER_LINE) {
      const sliceEnd = i + CHARS_PER_LINE;
      for (let string = 1; string <= 6; string++) {
        const prefix = i === 0 ? "" : rawLines[string].substring(0, 2); 
        let slice = rawLines[string].slice(i === 0 ? 0 : i + 2, sliceEnd);
        formattedOutput += prefix + slice + "\n";
      }
      formattedOutput += "\n";
    }

    setTabOutput(formattedOutput);
  }, [rawLines]);

  // --- 3. RESIZE LISTENER ---
  // Window Resize check for re-formatting
  useEffect(() => {
    formatLinesToScreen();

    const handleResize = () => formatLinesToScreen();
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);
  }, [formatLinesToScreen]);


  // --- HANDLERS ---
  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('audio_file', file);

    try {
      const response = await fetch('http://localhost:5000/process-audio', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error("Upload failed");
      const data: TabJson = await response.json();
      
      setJsonInput(JSON.stringify(data, null, 2));
      processJsonToLines(data);
    } catch (err) {
      setError("Error processing file.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleManualRegenerate = () => {
    processJsonToLines();
  };

  return (
    <div className="app-container">
      
      {/* --- HOT BAR --- */}
      <header className="hot-bar">
        <div className="hot-bar-left">
          <h1 className="brand-title">TAB-IT</h1>
          <label className="upload-btn">
            <UploadIcon />
            <span>{loading ? "Processing..." : "Upload File"}</span>
            <input type="file" className="hidden-input" accept="audio/*" onChange={handleFileUpload} disabled={loading} />
          </label>
        </div>

        <button onClick={() => setIsModalOpen(true)} className="icon-btn">
          <CodeIcon />
          <span>Edit JSON</span>
        </button>
      </header>

      {/* --- MAIN CONTENT --- */}
      <main className="main-content">
        
        {error && <div className="error-msg">{error}</div>}

        {tabOutput ? (
          <div className="tab-container">
            <div className="tab-header">Generated Tab</div>
            {/* Note: We added whitespace-pre-wrap just in case, but our JS handles the breaks */}
            <pre className="tab-pre">
              {tabOutput}
            </pre>
          </div>
        ) : (
          <div className="empty-state">
            <p>Upload an audio file to generate your guitar tab.</p>
          </div>
        )}
      </main>

      {/* --- MODAL --- */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Edit JSON Data</h3>
              <button onClick={() => setIsModalOpen(false)} className="icon-btn" style={{color: '#6b7280'}}>
                <CloseIcon />
              </button>
            </div>
            <div className="modal-body">
              <textarea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                className="json-textarea"
                placeholder='{"notes": []}'
              />
            </div>
            <div className="modal-footer">
              <button onClick={() => setIsModalOpen(false)} className="btn-cancel">Cancel</button>
              <button onClick={handleManualRegenerate} className="btn-confirm">Regenerate Tab</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}