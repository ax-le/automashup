import numpy as np
import os
import shutil
import math
import json
from pymusickit.key_finder import KeyFinder
from collections import OrderedDict
from pydub import AudioSegment
from pydub.playback import play

### Here are some useful functions used in other parts of the project


def increase_array_size(arr, new_size):
    if len(arr) < new_size:
        # Create a new array with the new size
        increased_arr = np.zeros(new_size)
        # Copy elements from the original array to the new array
        increased_arr[:len(arr)] = arr
        return increased_arr
    else:
        return arr


def get_path(track_name, type):
    # returns the path of a song
    # It can return the whole track or just a separated part of it,
    # depending on the type, which should be one of the following : 
    # 'entire', 'bass', 'drums', 'vocals', 'other'   
    if type == 'entire':
        if os.path.exists('./input/' + track_name + '.wav'):
            path = './input/' + track_name + '.wav'
        else :
            path = './input/' + track_name + '.mp3'
    else : 
        path = './separated/htdemucs/' + track_name + '/' + type + '.wav'
        if not os.path.exists(path):
            path = './separated/htdemucs/' + track_name + type + '.mp3'
    assert(os.path.exists(path))
    return path


def remove_track(track_name):
    # function to remove a track and all the files that concern it.
    struct_path = "./struct/" + track_name + ".json"
    folder_path = "./separated/htdemucs/" + track_name + "/"
    os.remove(struct_path)
    shutil.rmtree(folder_path)


def extract_filename(file_path):
    # Extract filename from a given path
    filename = os.path.basename(file_path)
    filename_without_extension, _ = os.path.splitext(filename)
    return filename_without_extension


def note_to_frequency(key):
    # turn a note with a mode to a frequency
    note, mode = key.split(' ', 1)
    reference_frequency=440.0
    semitone_offsets = {'C': -9, 'C#': -8, 'Db': -8, 'D': -7, 'D#': -6, 'Eb': -6, 'E': -5, 'Fb': -5, 'E#': -4,
                        'F': -4, 'F#': -3, 'Gb': -3, 'G': -2, 'G#': -1, 'Ab': -1, 'A': 0, 'A#': 1, 'Bb': 1, 'B': 2, 'Cb': 2, 'B#': 3}
    semitone_offset = semitone_offsets[note]
    if mode == 'minor':
        semitone_offset -= 3 
    frequency = reference_frequency * 2 ** (semitone_offset / 12)
    return frequency


def key_finder(path): 
    filename = extract_filename(path)
    struct_path = f"./struct/{filename}.json"
    with open(struct_path, 'r') as file:
        data = json.load(file)
        data['key'] = KeyFinder(path).key_dict
    with open(struct_path, 'w') as file:
        json.dump(data, file, indent=2)


def calculate_pitch_shift(source_freq, target_freq):
    pitch_shift = 12 * math.log2(target_freq / source_freq)
    return pitch_shift


def key_from_dict(dict):
    # get key from the metadata correlation list
    best_key, best_score = "", ""
    for key, score in dict.items():
        if best_score=="" or best_score<score:
            best_key, best_score = key, score
    return best_key


def closest_index(value, value_list):
    # get the index of the closest value of a specific target in a list
    closest_index = min(range(len(value_list)), key=lambda i: abs(value_list[i] - value))
    return closest_index

def get_unique_ordered_list(input_list):
    # Use OrderedDict to preserve order while removing duplicates
    return list(OrderedDict.fromkeys(input_list))

# extracts the start and end times for the selected segment
def get_segment_times(segments, selected_label):
    for segment in segments:
        if segment['label'] == selected_label:
            return segment['start'], segment['end']
    return 0, 2  # Default to first 2 seconds if segment not found

def extract_audio_segment(file_path, start_time, end_time, output_path):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(file_path)
        # Extract the segment
        segment = audio[start_time * 1000:end_time * 1000]  # pydub works in milliseconds
        # Export the segment to a temporary file
        segment.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        print(f"Error extracting audio segment: {e}")
        return None
    
# Function to merge the segments that have the same label and are next to each other
def merge_segments(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    merged_segments = []
    previous_segment = None

    for segment in data.get('segments', []):
        if previous_segment and previous_segment['label'] == segment['label']:
            # Merge with the previous segment
            previous_segment['end'] = segment['end']
        else:
            # Add the previous segment to the list if it exists
            if previous_segment:
                merged_segments.append(previous_segment)
            # Update the previous segment
            previous_segment = segment
    
    # Add the last segment
    if previous_segment:
        merged_segments.append(previous_segment)
    
    # Update the segments in the data
    data['segments'] = merged_segments
    
    # Save the modified data back to the JSON file
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)