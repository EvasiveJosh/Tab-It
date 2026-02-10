import os
import json
import requests
from flask import Flask, request, jsonify, Response
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


def sse_event(data):
    """Format a dict as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['audio_file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not file:
        return jsonify({"error": "No file provided"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    def generate():
        wav_path = None
        midi_path = None

        try:
            # ── Step 1: File received ──────────────────────────────
            print(f"🎵 Processing: {filename}")
            yield sse_event({
                "step": 1, "totalSteps": 6,
                "message": f"File received: {filename}",
                "progress": 5
            })

            # ── Step 2: Send to separator service ──────────────────
            print(f"🎸 Sending to separator service...")
            yield sse_event({
                "step": 2, "totalSteps": 6,
                "message": "Sending audio to separator service...",
                "progress": 8
            })

            with open(filepath, 'rb') as audio:
                resp = requests.post(
                    f"{SEPARATOR_URL}/separate",
                    files={'audio_file': (filename, audio, 'audio/mpeg')},
                    stream=True
                )

            # Read SSE events from the separator and forward progress
            file_id = None
            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode('utf-8')
                if not decoded.startswith('data: '):
                    continue

                sep_data = json.loads(decoded[6:])

                if 'error' in sep_data:
                    yield sse_event({"error": sep_data['error']})
                    return

                if 'file_id' in sep_data:
                    file_id = sep_data['file_id']

                # Map separator progress (0-100) → overall progress (8-45)
                sep_progress = sep_data.get('progress', 0)
                overall_progress = 8 + int(sep_progress * 0.37)

                yield sse_event({
                    "step": 2, "totalSteps": 6,
                    "message": f"Separator: {sep_data.get('message', 'Processing...')}",
                    "progress": min(overall_progress, 45)
                })

            if file_id is None:
                yield sse_event({"error": "Separation failed — no output file received"})
                return

            # ── Step 3: Download separated guitar audio ────────────
            yield sse_event({
                "step": 3, "totalSteps": 6,
                "message": "Downloading separated guitar audio...",
                "progress": 48
            })

            dl_resp = requests.get(f"{SEPARATOR_URL}/download/{file_id}")
            if dl_resp.status_code != 200:
                yield sse_event({"error": "Failed to download separated audio from separator"})
                return

            wav_filename = filename.rsplit('.', 1)[0] + '_guitar.wav'
            wav_path = os.path.join(UPLOAD_FOLDER, wav_filename)
            with open(wav_path, 'wb') as f:
                f.write(dl_resp.content)

            print(f"🎸 Guitar audio received: {wav_filename}")

            # ── Step 4: Convert WAV to MIDI ────────────────────────
            yield sse_event({
                "step": 4, "totalSteps": 6,
                "message": "Converting audio to MIDI...",
                "progress": 55
            })
            print(f"🎵 Converting to MIDI...")
            midi_path = wav_to_midi(wav_path)

            # ── Step 5: Extract notes ──────────────────────────────
            yield sse_event({
                "step": 5, "totalSteps": 6,
                "message": "Extracting notes from MIDI...",
                "progress": 75
            })
            print(f"🎵 Extracting notes...")
            notes = quantize_and_extract_notes(midi_path)

            # ── Step 6: Map to fretboard ───────────────────────────
            yield sse_event({
                "step": 6, "totalSteps": 6,
                "message": "Mapping notes to fretboard...",
                "progress": 90
            })
            print(f"🎵 Mapping to fretboard...")
            frettings = map_to_fretboard(notes, max_frets=15)

            # ── Complete! ──────────────────────────────────────────
            yield sse_event({
                "step": 6, "totalSteps": 6,
                "message": "Complete!",
                "progress": 100,
                "result": frettings
            })
            print(f"✅ Processing complete!")

            # Cleanup
            print(f"🎵 Removing temporary files...")
            for p in [filepath, wav_path, midi_path]:
                if p and os.path.exists(p):
                    os.remove(p)

        except requests.ConnectionError:
            if os.path.exists(filepath):
                os.remove(filepath)
            yield sse_event({"error": "Separator service is unavailable"})

        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            for p in [filepath, wav_path, midi_path]:
                if p and os.path.exists(p):
                    os.remove(p)
            yield sse_event({"error": str(e)})

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
