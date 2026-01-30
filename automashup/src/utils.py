import os
import shutil

# %% File manipulation stuff
def extract_filename_from_path(file_path):
    # Extract filename from a given path
    filename = os.path.basename(file_path)
    return get_song_name_without_extension(filename)

def get_song_name_without_extension(song_name):
    return os.path.splitext(song_name)[0]

def remove_track(track_name, stored_data_path="."):
    # function to remove a track and all the files that concern it.
    struct_path = f"{stored_data_path}/struct/{track_name}.json"
    folder_path = f"{stored_data_path}/separated/htdemucs/{track_name}/"
    os.remove(struct_path)
    shutil.rmtree(folder_path)

def closest_index(value, value_list):
    # get the index of the closest value of a specific target in a list
    closest_index = min(range(len(value_list)), key=lambda i: abs(value_list[i] - value))
    return closest_index

def segments_as_dict(segments):
    assert not isinstance(segments[0], dict), "Segments are already in dict format."
    to_return = []
    for seg in segments:
        new_seg = {
            'start': seg.start,
            'end': seg.end,
            'label': seg.label
        }
        to_return.append(new_seg)
    return to_return