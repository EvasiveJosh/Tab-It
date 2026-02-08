import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from file_conversion import wav_to_midi
from extraction import quantize_and_extract_notes
from placement import map_to_fretboard
from dotenv import load_dotenv


# Initialize App
app = Flask(__name__)
CORS(app)

load_dotenv() 

# Configuration
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# URL of the audio separator service running on the cluster
SEPARATOR_URL = os.environ.get('SEPARATOR_URL', 'http://localhost:5001')

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

        # Step 1: Send to separator service to isolate guitar audio
        print(f"🎸 Sending to separator service...")
        wav_path = None
        try:
            with open(filepath, 'rb') as audio:
                resp = requests.post(
                    f"{SEPARATOR_URL}/separate",
                    files={'audio_file': (filename, audio, 'audio/mpeg')}
                )

            if resp.status_code != 200:
                error_msg = resp.json().get('error', 'Separation failed')
                return jsonify({"error": error_msg}), 500

            # Save the returned .wav file
            wav_filename = filename.rsplit('.', 1)[0] + '_guitar.wav'
            wav_path = os.path.join(UPLOAD_FOLDER, wav_filename)
            with open(wav_path, 'wb') as f:
                f.write(resp.content)

            print(f"🎸 Guitar audio received: {wav_filename}")

        except requests.ConnectionError:
            os.remove(filepath)
            return jsonify({"error": "Separator service is unavailable"}), 503

        # Step 2: Convert WAV to MIDI
        print(f"🎵 Converting to MIDI...")
        midi = wav_to_midi(wav_path)

        # Step 3: Extract notes
        print(f"🎵 Extracting notes...")
        notes = quantize_and_extract_notes(midi)

        # Step 4: Map to fretboard
        print(f"🎵 Mapping to fretboard...")
        frettings = map_to_fretboard(notes, max_frets=15)
        
        # Cleanup
        print(f"🎵 Removing temporary files...")
        os.remove(filepath)
        os.remove(wav_path)
        os.remove(midi)
        return jsonify(frettings)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
