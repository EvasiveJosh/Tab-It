from extraction import quantize_and_extract_notes
from placement import map_to_fretboard
import json

# example usage
notes = quantize_and_extract_notes("test.mid")
print(notes)

test_input = [
    {
        "offset": 0.0,
        "duration": 1.0,
        "midi_pitches": [40, 47, 52], # E Major
        "note_names": ["E2", "B2", "E3"]
    },
    {
        "offset": 1.0,
        "duration": 0.5,
        "midi_pitches": [64], # High E
        "note_names": ["E4"]
    }
]

result = map_to_fretboard(test_input)
print(json.dumps(result, indent=2))