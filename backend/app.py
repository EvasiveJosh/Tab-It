import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from file_conversion import wav_to_midi 
from extraction import quantize_and_extract_notes
from placement import map_to_fretboard

# Initialize App
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['audio_file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        print(f"🎵 Processing: {filename}")

        print(f"🎵 Converting to MIDI...")
        midi = wav_to_midi(filepath)

        print(f"🎵 Extracting notes...")
        notes = quantize_and_extract_notes(midi)

        print(f"🎵 Mapping to fretboard...")
        frettings = map_to_fretboard(notes, max_frets=15)
        
        print(f"🎵 Removing files...")
        os.remove(filepath)
        os.remove(midi)
        return jsonify(frettings)

if __name__ == '__main__':
    app.run(debug=True, port=5000)