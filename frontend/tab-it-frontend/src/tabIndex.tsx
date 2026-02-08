import React, { useState } from 'react';
import type { ChangeEvent } from 'react';

// 1. Define the Shape of our Data
interface TabJson {
  notes: [number, number][]; // Array of [string, fret] tuples
}

// Map string numbers (1-6) to their names
const STRING_NAMES: { [key: number]: string } = {
  1: "e", 2: "B", 3: "G", 4: "D", 5: "A", 6: "E"
};

export default function TabDisplay() {
  const [jsonInput, setJsonInput] = useState<string>('');
  const [tabOutput, setTabOutput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // --- A. HANDLE FILE UPLOAD ---
  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    // 1. Create FormData to send the file
    const formData = new FormData();
    formData.append('audio_file', file); // 'audio_file' must match backend key

    try {
      // 2. Send to Backend (Replace with your actual URL)
      const response = await fetch('http://localhost:5000/process-audio', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      // 3. Receive JSON from Backend
      const data: TabJson = await response.json();
      
      // 4. Auto-generate the tab from the response
      setJsonInput(JSON.stringify(data, null, 2)); // Show raw JSON in text box
      generateTab(data); // Generate visual tab

    } catch (err) {
      setError("Error processing file. Is the backend running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // --- B. GENERATE ASCII TAB ---
  // Accepts data object directly, OR uses the text box state if null
  const generateTab = (data?: TabJson) => {
    setError(null);
    try {
      let parsed: TabJson;

      // If data is passed (from upload), use it. Otherwise parse text box.
      if (data) {
        parsed = data;
      } else {
        parsed = JSON.parse(jsonInput);
      }

      if (!parsed.notes || !Array.isArray(parsed.notes)) {
        throw new Error("JSON must contain a 'notes' array of [string, fret].");
      }

      // Initialize the 6 strings
      // We use a Map or Object to hold the lines
      let lines: { [key: number]: string } = {
        1: "e|", 2: "B|", 3: "G|", 4: "D|", 5: "A|", 6: "E|"
      };

      parsed.notes.forEach(([stringNum, fret]) => {
        // Validate
        if (stringNum < 1 || stringNum > 6) return;

        const fretStr = fret.toString();
        const width = fretStr.length; // 1 or 2 chars usually

        // Update all 6 strings for this time slice
        for (let i = 1; i <= 6; i++) {
          if (i === stringNum) {
            lines[i] += `-${fretStr}-`;
          } else {
            // Add dashes of equal width to keep alignment
            lines[i] += `-${'-'.repeat(width)}-`;
          }
        }
      });

      // Join lines (High E on top)
      const finalString = [
        lines[1], lines[2], lines[3], lines[4], lines[5], lines[6]
      ].join("\n");

      setTabOutput(finalString);

    } catch (err) {
      setError("Invalid JSON format.");
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "2rem auto", padding: "1rem" }}>
      <h1>Tab-It: Audio to Tab Converter</h1>
      
      {/* 1. FILE UPLOAD SECTION */}
      <div style={{ 
        border: "2px dashed #ccc", 
        padding: "20px", 
        marginBottom: "20px", 
        borderRadius: "8px",
        textAlign: "center"
      }}>
        <h3>Step 1: Upload Audio</h3>
        <input 
          type="file" 
          accept="audio/*" // Only allow audio files
          onChange={handleFileUpload} 
          disabled={loading}
        />
        {loading && <p>Processing... (This uses AI, please wait)</p>}
      </div>

      {/* 2. MANUAL EDIT SECTION */}
      <div style={{ marginBottom: "20px" }}>
        <h3>Step 2: Review JSON Data</h3>
        <textarea
          value={jsonInput}
          onChange={(e) => setJsonInput(e.target.value)}
          placeholder='{"notes": [[6,0], [6,3], [6,5]]}'
          rows={6}
          style={{ width: "100%", fontFamily: "monospace", padding: "10px" }}
        />
        <br />
        <button 
          onClick={() => generateTab()}
          style={{ marginTop: "10px", padding: "8px 16px", cursor: "pointer" }}
        >
          Regenerate Tab
        </button>
      </div>

      {/* 3. ERROR DISPLAY */}
      {error && (
        <div style={{ color: "red", backgroundColor: "#ffe6e6", padding: "10px", borderRadius: "4px" }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* 4. TAB OUTPUT */}
      {tabOutput && (
        <div style={{ marginTop: "20px" }}>
          <h3>Step 3: Guitar Tab</h3>
          
          <pre style={{ 
            backgroundColor: "#222", 
            color: "#4CAF50", 
            padding: "20px", 
            borderRadius: "8px", 
            overflowX: "auto",
            fontFamily: "Courier New, monospace",
            fontWeight: "bold",
            fontSize: "14px"
          }}>
            {tabOutput}
          </pre>
        </div>
      )}
    </div>
  );
}