import json

def map_to_fretboard(notes, tuning=None, max_frets=21):
    """
    Input: List of dicts with 'offset', 'duration', 'midi_pitches', 'note_names'
    Output: Dict with key "notes", which is a list of notes according to the spe
    """
    if tuning is None:
        tuning = [64, 59, 55, 50, 45, 40]
    
    avg_hand_pos = 2.0   
    # avg for rolling/sliding avg
    smoothing = 0.8  
    low_fret_bias = 0.5  
    
    final_tab = []

    for event in notes:
        offset = event['offset']
        duration = event['duration']
        pitches = event['midi_pitches']
        
        assigned_notes = []
        used_strings = set()

        # high notes first for high frets
        for pitch in sorted(pitches, reverse=avg_hand_pos > 12): 

            # all locations we can place this on fretboard
            options = []
            for s_idx, open_pitch in enumerate(tuning):
                fret = int(pitch - open_pitch)
                string_num = s_idx + 1 # 1-6
                
                if 0 <= fret <= max_frets and string_num not in used_strings:
                    options.append({"string": string_num, "fret": fret})

            if not options:
                # print("WARNING: No options found for note", pitch)
                continue

            # cost = distance tp hand + (fret * bias) - (open strings reward)
            best_pos = min(
                options,
                key=lambda n: (
                    abs(n['fret'] - avg_hand_pos) + 
                    (n['fret'] * low_fret_bias) + 
                    (-2 if n['fret'] == 0 else 0)
                )
            )

            assigned_notes.append({
                "string": best_pos['string'],
                "fret": best_pos['fret'],
                "midi": int(pitch)
            })
            used_strings.add(best_pos['string'])

            # update rolling average if the note wasn't an open string
            if best_pos['fret'] > 0:
                avg_hand_pos = (avg_hand_pos * smoothing) + (best_pos['fret'] * (1 - smoothing))

        final_tab.append({
            "time": offset,
            "duration": duration,
            "string": [n["string"] for n in assigned_notes],
            "fret": [f["fret"] for f in assigned_notes],
        })

    return {"notes": final_tab}