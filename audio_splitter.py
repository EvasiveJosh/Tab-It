import torch
import shutil
import sys
from audio_separator.separator import Separator

def get_guitar_audio(input_file):
    if not shutil.which("ffmpeg"):
        print("ERROR: FFmpeg is not installed or not in your PATH.")
        print("Please install it from https://ffmpeg.org/download.html")
        print("or run: 'winget install Gyan.FFmpeg' in a generic terminal.")
        sys.exit(1)

    print("FFmpeg found! Starting separation...")

    # 2. Configure the separator
    # We use 'htdemucs_6s' because it is the specific model that splits Guitar.
    separator = Separator(
        output_dir="output_stems",
        output_single_stem="guitar"  # <--- THIS IS THE KEY CHANGE
    )

    # 3. Load the model
    print("Loading model 'htdemucs_6s' (this may take a moment)...")
    separator.load_model(model_filename="htdemucs_6s.yaml")

    print(f"Separating '{input_file}'...")
    output_files = separator.separate(input_file)

    print(f"Success! Created {len(output_files)} stems:")
    for file in output_files:
        print(f" - {file}")
    
    # Return the output file path
    return output_files[0] if output_files else None
