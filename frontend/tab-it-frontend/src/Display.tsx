import React, { useState } from 'react';
import type { ChangeEvent } from 'react';

// 1. NEW INTERFACE: Matches your specific { string: [], fret: [] } structure
interface NoteGroup {
  string: number[]; // e.g. [6, 5, 4]
  fret: number[];   // e.g. [0, 2, 2]
}

interface TabJson {
  notes: NoteGroup[];
}

export default function TabDisplay() {
  const [jsonInput, setJsonInput] = useState<string>('');
  const [tabOutput, setTabOutput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // --- HANDLE FILE UPLOAD (No changes here) ---
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
      generateTab(data);
    } catch (err) {
      setError("Error processing file.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // --- NEW GENERATION LOGIC ---
  const generateTab = (data?: TabJson) => {
    setError(null);
    try {
      let parsed: TabJson;
      if (data) parsed = data;
      else parsed = JSON.parse(jsonInput);

      if (!parsed.notes || !Array.isArray(parsed.notes)) {
        throw new Error("JSON must contain a 'notes' array.");
      }

      // Initialize the 6 strings lines
      let lines: { [key: number]: string } = {
        1: "e|", 2: "B|", 3: "G|", 4: "D|", 5: "A|", 6: "E|"
      };

      // Iterate through each "Time Column" (NoteGroup)
      parsed.notes.forEach((group) => {
        // 1. Create a quick lookup map for this specific beat
        // key = string number, value = fret string
        let currentBeat: { [key: number]: string } = {};
        
        // Loop through the arrays in the group
        group.string.forEach((stringNum, idx) => {
          const fretNum = group.fret[idx];
          currentBeat[stringNum] = fretNum.toString();
        });

        // 2. Calculate Alignment Width
        // Find the longest fret number in this chord (e.g. "12" is width 2)
        let maxWidth = 0;
        Object.values(currentBeat).forEach(f => {
          if (f.length > maxWidth) maxWidth = f.length;
        });
        if (maxWidth === 0) maxWidth = 1; // Minimum width for empty beats

        // 3. Append to all 6 lines
        for (let string = 1; string <= 6; string++) {
          const fret = currentBeat[string];

          if (fret !== undefined) {
            // If note exists, pad it to match maxWidth
            // e.g. "5" becomes "5-" if max is 2
            const padding = "-".repeat(maxWidth - fret.length);
            lines[string] += `-${fret}${padding}-`;
          } else {
            // If silent, add full dashes
            lines[string] += `-${'-'.repeat(maxWidth)}-`;
          }
        }
      });

      // Join lines (High E on top)
      const finalString = [
        lines[1], lines[2], lines[3], lines[4], lines[5], lines[6]
      ].join("\n");

      setTabOutput(finalString);

    } catch (err) {
      setError("Invalid JSON format or array length mismatch.");
      console.error(err);
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "2rem auto", padding: "1rem" }}>
      <h1>Tab-It: Audio to Tab Converter</h1>
      
      {/* Upload Section */}
      <div style={{ border: "2px dashed #ccc", padding: "20px", borderRadius: "8px", textAlign: "center" }}>
        <h3>Step 1: Upload Audio</h3>
        <input type="file" accept="audio/*" onChange={handleFileUpload} disabled={loading} />
        {loading && <p>Processing...</p>}
      </div>

      {/* Manual JSON Edit */}
      <div style={{ marginTop: "20px" }}>
        <h3>Step 2: JSON Data</h3>
        <textarea
          value={jsonInput}
          onChange={(e) => setJsonInput(e.target.value)}
          placeholder='{"notes": [{"string": [6,5], "fret": [0,2]}]}'
          rows={10}
          style={{ width: "100%", fontFamily: "monospace", padding: "10px" }}
        />
        <br />
        <button onClick={() => generateTab()} style={{ marginTop: "10px", padding: "8px 16px" }}>
          Regenerate Tab
        </button>
      </div>

      {/* Error Output */}
      {error && <p style={{color: 'red'}}>{error}</p>}

      {/* Tab Output */}
      {tabOutput && (
        <div style={{ marginTop: "20px" }}>
          <h3>Step 3: Guitar Tab</h3>
          

[Image of simple guitar chord chart]

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