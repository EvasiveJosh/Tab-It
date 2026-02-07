import os
import numpy as np
from music21 import converter, instrument, tempo, chord, note, stream

def quantize_and_extract_notes(midi_file_path, quarter_length_divisor=4):
    
    s = converter.parse(midi_file_path)
    
    quantized_s = s.quantize((quarter_length_divisor,), processOffsets=True, processDurations=True)
    
    extracted_notes = []
    
    for element in quantized_s.flatten().notes:
        offset = element.offset # 1/4 notes
        duration = element.duration.quarterLength
        
        if isinstance(element, chord.Chord):
            pitches = [p.ps for p in element.pitches]
            names = [p.nameWithOctave for p in element.pitches]
        else:
            pitches = [element.pitch.ps]
            names = [element.pitch.nameWithOctave]
             
        extracted_notes.append({
            "offset": float(offset),
            "duration": float(duration),
            "midi_pitches": pitches,
            "note_names": names
        })
        
    return extracted_notes