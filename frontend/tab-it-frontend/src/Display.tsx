import React, { useState } from 'react';
import type { ChangeEvent } from 'react';


// 1. UPDATE INTERFACE
interface NoteObj {
  string: number;
  fret: number;
  stacking: boolean;
}

interface TabJson {
  notes: NoteObj[];
}

export default function TabDisplay() {
  const [jsonInput, setJsonInput] = useState<string>('');
  const [tabOutput, setTabOutput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // --- HANDLE FILE UPLOAD (Same as before) ---
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

  // --- NEW LOGIC: HANDLING STACKING ---
  const generateTab = (data?: TabJson) => {
    setError(null);
    try {
      let parsed: TabJson;
      if (data) parsed = data;
      else parsed = JSON.parse(jsonInput);

      if (!parsed.notes || !Array.isArray(parsed.notes)) {
        throw new Error("JSON must contain a 'notes' array.");
      }

      // --- STEP 1: GROUP NOTES INTO COLUMNS ---
      // We assume the first note always starts a new column.
      // Subsequent notes with stacking=true go into the SAME column.
      
      // A "Column" is a map of String -> Fret (e.g., { 6: "0", 5: "2" })
      let columns: Array<{ [stringNum: number]: string }> = [];
      let currentColumn: { [stringNum: number]: string } | null = null;

      parsed.notes.forEach((note, index) => {
        // Validate
        if (note.string < 1 || note.string > 6) return;

        // LOGIC: If it's the first note OR stacking is false, create NEW column
        if (index === 0 || note.stacking === false) {
          // Push previous column if exists
          if (currentColumn) columns.push(currentColumn);
          
          // Start new column
          currentColumn = {};
        }

        // Add note to current column (whether new or existing)
        if (currentColumn) {
           currentColumn[note.string] = note.fret.toString();
        }
      });
      
      // Push the final column
      if (currentColumn) columns.push(currentColumn);

      // --- STEP 2: RENDER STRINGS ---
      // Initialize lines
      let lines: { [key: number]: string } = {
        1: "e|", 2: "B|", 3: "G|", 4: "D|", 5: "A|", 6: "E|"
      };

      columns.forEach(col => {
        // Find max width in this column (e.g. "12" is width 2, "5" is width 1)
        // We need this so "5" gets padded to match "12" in a chord
        let maxWidth = 0;
        Object.values(col).forEach(fretStr => {
          if (fretStr.length > maxWidth) maxWidth = fretStr.length;
        });
        
        // If column is empty (rest), default width is 1
        if (maxWidth === 0) maxWidth = 1;

        // Append to all 6 strings
        for (let i = 1; i <= 6; i++) {
          const fret = col[i]; // Value at this string (or undefined)
          
          if (fret !== undefined) {
            // Note exists: Pad it to match max width
            // e.g. "5" becomes "5 " if max is 2
            const padding = "-".repeat(maxWidth - fret.length);
            lines[i] += `-${fret}${padding}-`;
          } else {
            // No note: Add full dashes
            lines[i] += `-${'-'.repeat(maxWidth)}-`;
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
      
      {/* UPLOAD */}
      <div style={{ border: "2px dashed #ccc", padding: "20px", borderRadius: "8px", textAlign: "center" }}>
        <h3>Step 1: Upload Audio</h3>
        <input type="file" accept="audio/*" onChange={handleFileUpload} disabled={loading} />
        {loading && <p>Processing...</p>}
      </div>

      {/* MANUAL EDIT */}
      <div style={{ marginTop: "20px" }}>
        <h3>Step 2: JSON Data</h3>
        <textarea
          value={jsonInput}
          onChange={(e) => setJsonInput(e.target.value)}
          placeholder='{"notes": [{"string":6, "fret":0, "stacking":false}, ...]}'
          rows={10}
          style={{ width: "100%", fontFamily: "monospace", padding: "10px" }}
        />
        <br />
        <button onClick={() => generateTab()} style={{ marginTop: "10px", padding: "8px 16px" }}>
          Regenerate Tab
        </button>
      </div>

      {/* OUTPUT */}
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