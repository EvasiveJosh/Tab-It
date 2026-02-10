import os
import json
import shutil
import uuid
import traceback
import threading
import queue
import torch
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from audio_separator.separator import Separator

# Initialize App
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './output_stems'
DOWNLOAD_FOLDER = './downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def sse_event(data):
    """Format a dict as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


@app.route('/separate', methods=['POST'])
def separate_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['audio_file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    def generate():
        try:
            print(f"🎸 Received '{filename}' for separation...")
            yield sse_event({
                "message": "Checking dependencies...",
                "progress": 5
            })

            if not shutil.which("ffmpeg"):
                yield sse_event({"error": "FFmpeg is not installed or not in PATH."})
                return

            print("FFmpeg found! Starting separation...")
            yield sse_event({
                "message": "Configuring audio separator...",
                "progress": 10
            })

            separator = Separator(
                output_dir=OUTPUT_FOLDER,
                output_single_stem="guitar"
            )

            yield sse_event({
                "message": "Loading ML model (htdemucs_6s)...",
                "progress": 20
            })
            print("Loading model 'htdemucs_6s' (this may take a moment)...")
            separator.load_model(model_filename="htdemucs_6s.yaml")

            yield sse_event({
                "message": "Separating guitar audio (this may take a few minutes)...",
                "progress": 40
            })
            print(f"Separating '{input_path}'...")

            # Run separation in a thread so we can send keepalive events
            result_queue: queue.Queue = queue.Queue()

            def _run_separation():
                try:
                    files = separator.separate(input_path)
                    result_queue.put(("ok", files))
                except Exception as exc:
                    result_queue.put(("error", exc))

            sep_thread = threading.Thread(target=_run_separation, daemon=True)
            sep_thread.start()

            # Send a keepalive heartbeat every 15 s while separation runs
            tick = 0
            while True:
                try:
                    status, payload = result_queue.get(timeout=15)
                    if status == "error":
                        raise payload          # re-raise in generator
                    output_files = payload
                    break
                except queue.Empty:
                    tick += 1
                    yield sse_event({
                        "message": f"Separating guitar audio... ({tick * 15}s elapsed)",
                        "progress": min(40 + tick, 90)
                    })

            print(f"Success! Created {len(output_files)} stems:")
            for f in output_files:
                print(f" - {f}")

            if not output_files:
                yield sse_event({"error": "Separation produced no output"})
                return

            output_path = os.path.join(OUTPUT_FOLDER, output_files[0])

            # Move the result to the downloads folder with a unique ID
            file_id = str(uuid.uuid4())
            download_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.wav")
            shutil.move(output_path, download_path)

            # Clean up input file
            if os.path.exists(input_path):
                os.remove(input_path)

            yield sse_event({
                "message": "Separation complete!",
                "progress": 100,
                "file_id": file_id
            })
            print(f"✅ Separation complete! file_id={file_id}")

        except Exception as e:
            print(f"❌ ERROR during separation: {type(e).__name__}: {e}")
            traceback.print_exc()
            if os.path.exists(input_path):
                os.remove(input_path)
            yield sse_event({"error": str(e)})

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
    })


@app.route('/download/<file_id>', methods=['GET'])
def download_result(file_id):
    """Download a separated audio file by its unique ID, then clean up."""
    # Sanitize the file_id to prevent path traversal
    safe_id = secure_filename(file_id)
    download_path = os.path.join(DOWNLOAD_FOLDER, f"{safe_id}.wav")

    if not os.path.exists(download_path):
        return jsonify({"error": "File not found"}), 404

    response = send_file(
        download_path,
        mimetype='audio/wav',
        as_attachment=True,
        download_name=f"{safe_id}.wav"
    )

    @response.call_on_close
    def cleanup():
        if os.path.exists(download_path):
            os.remove(download_path)

    return response


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
