import allin1
import json
import demucs.separate
import numpy as np
import os
import librosa

import automashup.src.utils as utils
import automashup.src.pitch_utils as pitch_utils

# %% Key, structure, and tempo estimation
def song_info_estimation(song_path, stored_data_folder):

    # Get the track name from the path
    track_name = utils.extract_filename_from_path(song_path)

    # Check if the track has already been processed
    struct_path = f"{stored_data_folder}/struct/{track_name}.json"
    if not os.path.exists(struct_path):
        allin1.analyze(song_path, out_dir=f'{stored_data_folder}/struct', demix_dir=f'{stored_data_folder}/separated/four_stems', keep_byproducts=True, overwrite=False)

    # Load the metadata
    with open(struct_path, 'r') as file:
        metadata = json.load(file)

    if 'key' not in metadata:
        key = pitch_utils.estimate_key_from_path(song_path)
        metadata['key'] = key
        with open(struct_path, 'w') as file: # update the stored metadata with the key
            json.dump(metadata, file, indent=2)

    return metadata


# %% source separation
def load_or_compute_source_separated_songs(song_path, stored_data_folder, two_stems = True, model = 'htdemucs_ft', verbose = True):
    if verbose:
        print("Loading or computing source separated songs.")

    source_separated_paths = load_or_compute_source_separated_paths(song_path, stored_data_folder, two_stems=two_stems, model=model, verbose=verbose)

    source_separated_songs = [(librosa.load(path)[0], librosa.load(path)[1]) for path in source_separated_paths]

    return source_separated_songs

def load_or_compute_source_separated_paths(song_path, stored_data_folder, two_stems = True, model = 'htdemucs_ft', verbose = True):
    if verbose:
        print("Loading or computing source separated paths.")

    # Get the track name from the path
    track_name = utils.extract_filename_from_path(song_path)

    source_separated_paths = get_source_separated_paths(song_path, stored_data_folder, two_stems=two_stems, model=model)

    # Source separation already done, and stored in the stored_data_folder
    all_paths_exist = np.all([os.path.exists(path) for path in source_separated_paths])
    if all_paths_exist:
        if verbose:
            print(f"Source separation already done, and stored in {stored_data_folder}.")
        return source_separated_paths
    
    if verbose:
        print("Source separation not done, running source separation.")
    run_source_separation(song_path, stored_data_folder, two_stems=two_stems, verbose=verbose)

    return source_separated_paths    

def run_source_separation(song_path, stored_data_folder, two_stems = True, model = 'htdemucs_ft', verbose = True):
    if two_stems:
        demucs.separate.main(["--two-stems", 'vocals', "--name", model, "-o", f"{stored_data_folder}/separated/two_stems", song_path])

    else:
        demucs.separate.main(["--name", model, "-o", f"{stored_data_folder}/separated/four_stems", song_path])

    if verbose:
        print("Source separation done.")
 
def get_source_separated_paths(song_path, stored_data_folder, two_stems = True, model = 'htdemucs_ft'):
    track_name = utils.extract_filename_from_path(song_path)
    if two_stems:
        return f"{stored_data_folder}/separated/two_stems/{model}/{track_name}/vocals.wav", f"{stored_data_folder}/separated/two_stems/{model}/{track_name}/no_vocals.wav"
    else:
        return f"{stored_data_folder}/separated/four_stems/{model}/{track_name}/vocals.wav", f"{stored_data_folder}/separated/four_stems/{model}/{track_name}/bass.wav", f"{stored_data_folder}/separated/four_stems/{model}/{track_name}/drums.wav", f"{stored_data_folder}/separated/four_stems/{model}/{track_name}/other.wav"
