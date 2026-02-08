from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
import os

def wav_to_midi(guitar_track):
    output_directory = "./midi_output"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    predict_and_save(
        [guitar_track],
        output_directory,
        save_midi=True,
        save_model_outputs=False,
        save_notes=False,
        sonify_midi= False,
        model_or_model_path=ICASSP_2022_MODEL_PATH,
        onset_threshold=0.6, 
        frame_threshold=0.4  
    )

    base_name = os.path.splitext(os.path.basename(guitar_track))[0]
    
    # Example: "./midi_output/guitared_basic_pitch.mid"
    output_path = os.path.join(output_directory, f"{base_name}_basic_pitch.mid")
    
    return output_path



