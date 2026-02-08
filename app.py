import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

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

        # --- YOUR AI LOGIC WOULD GO HERE ---
        # data = my_ai_function(filepath)

        # --- UPDATED DUMMY DATA ---
        # This matches your new { string: [], fret: [] } structure
        dummy_response = {
            "notes": [
                {
                "string": [
                    6,
                    5,
                    4
                ],
                "fret": [
                    0,
                    2,
                    2
                ]
                },
                {
                "string": [
                    1
                ],
                "fret": [
                    0
                ]
                }
            ]
        }
        
        return jsonify(dummy_response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)