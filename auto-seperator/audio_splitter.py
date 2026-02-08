import os
import shutil
import sys
import torch
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from audio_separator.separator import Separator

# Initialize App
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './output_stems'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_guitar_audio(input_file):
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "FFmpeg is not installed or not in your PATH. "
            "Please install it from https://ffmpeg.org/download.html "
            "or run: 'winget install Gyan.FFmpeg' in a generic terminal."
        )

    print("FFmpeg found! Starting separation...")

    # Configure the separator
    # We use 'htdemucs_6s' because it is the specific model that splits Guitar.
    separator = Separator(
        output_dir=OUTPUT_FOLDER,
        output_single_stem="guitar"
    )

    # Load the model
    print("Loading model 'htdemucs_6s' (this may take a moment)...")
    separator.load_model(model_filename="htdemucs_6s.yaml")

    print(f"Separating '{input_file}'...")
    output_files = separator.separate(input_file)

    print(f"Success! Created {len(output_files)} stems:")
    for file in output_files:
        print(f" - {file}")

    # Return the output file path
    return output_files[0] if output_files else None


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

    try:
        print(f"🎸 Received '{filename}' for separation...")
        output_file = get_guitar_audio(input_path)

        if output_file is None:
            return jsonify({"error": "Separation produced no output"}), 500

        output_path = os.path.join(OUTPUT_FOLDER, output_file)

        # Send the .wav file back to the caller, then clean up
        response = send_file(
            output_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=os.path.basename(output_file)
        )

        @response.call_on_close
        def cleanup():
            """Remove temporary files after the response is sent."""
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

        return response

    except Exception as e:
        # Clean up input file on error
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
