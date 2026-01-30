import os
import warnings
from IPython.display import Audio # For Notebooks

import automashup.src.preprocessing as preprocessing
import automashup.src.postprocessing as postprocessing
import automashup.src.utils as utils
from automashup.src.track import Track
import automashup.src.mashup as mashupper

default_data_path = "/Brain/private/a23marmo/projects/automashup/git_folder/automashup/data"
default_music_path = f"{default_data_path}/audio"
default_stored_data_path = f"{default_data_path}/intermediate_data"
default_save_mashup_path = f"{default_data_path}/mashups_created"

def mashup_script(song_path_1, song_path_2, stored_data_folder = default_stored_data_path, mashup_save_folder = default_save_mashup_path, verbose = True):

    # Create the stored data folder if it doesn't exist
    os.makedirs(stored_data_folder, exist_ok=True)

    if verbose:
        print("Starting the mashup script.")

        print("Processing the first song.")
        print("Separating vocals from the instrumental.")
    
    # Do music source separation - vocals/instrumental
    vocals, instru = preprocessing.load_or_compute_source_separated_paths(song_path_1, stored_data_folder, two_stems = True)

    if verbose:
        print("Estimating key, structure, and everything else.")
    # Estimate key, structure, and everything else
    metadata_1 = preprocessing.song_info_estimation(song_path_1, stored_data_folder)

    if verbose:
        print("Processing the second song.")
        print("Separating vocals from the instrumental.")
    # Do music source separation - vocals/instrumental
    vocals, instru = preprocessing.load_or_compute_source_separated_paths(song_path_2, stored_data_folder, two_stems = True)

    if verbose:
        print("Estimating key, structure, and everything else.")
    # Estimate key, structure, and everything else
    metadata_2 = preprocessing.song_info_estimation(song_path_2, stored_data_folder)

    if verbose:
        print("Let's create some Track objects with our preprocessed songs")

    tracks =  [] # input of the mashup methods

    # type attribute enables to choose a separated part of a song (from demucs source separation)
    # it can be 'vocals', 'bass', 'drums' or 'other'

    song_name_1 = utils.extract_filename(song_path_1)
    song_name_2 = utils.extract_filename(song_path_2)
    
    track_1 = Track.track_from_song(song_name_1, type='vocals', stored_data_path=stored_data_folder)
    track_2 = Track.track_from_song(song_name_2, type='bass', stored_data_path=stored_data_folder)
    track_3 = Track.track_from_song(song_name_2, type='drums', stored_data_path=stored_data_folder)
    track_4 = Track.track_from_song(song_name_2, type='other', stored_data_path=stored_data_folder)

    tracks = [track_1, track_2, track_3, track_4]

    if verbose:
        print("We can have access to some attributes :")
        print(f"BPM 1 : {track_1.bpm}")
        print(f"Key correlation 1 : {track_1.key}")
        print(f"Beat frames 1 : {track_1.beats}")
        print(f"Track audio 1 : {track_1.audio}")
        print(f"Track Sampling Frequency 1 {track_1.sr}")

        print(f"BPM 2 : {track_2.bpm}")
        print(f"Key correlation 2 : {track_2.key}")
        print(f"Beat frames 2 : {track_2.beats}")
        print(f"Track audio 2 : {track_2.audio}")
        print(f"Track Sampling Frequency 2 {track_2.sr}")

    if verbose:
        print("Standard method, nothing done")
    ## Standard method, nothing done
    mashup_result_vanilla = mashupper.mashup_technic(tracks) # Apply the mashup_technic function to the 'tracks' list.

    if verbose:
        print("Save the file")
    # Save the file :
    postprocessing.save_song(mashup_result_vanilla, mashup_save_folder, song_name_1, song_name_2, "vanilla")

    if verbose:
        print("Apply the method here")
    ### Apply the method here
    mashup_result = mashupper.mashup_technic_fit_phase_repitch(tracks, save_path=default_stored_data_path) # Apply the mashup_technic function to the 'tracks' list.

    if verbose:
        print("Save the file")
    # Save the file :
    postprocessing.save_song(mashup_result, mashup_save_folder, song_name_1, song_name_2, "fit_phase_repitch")

if __name__ == "__main__":

    default_song_name_1 = 'fma_Shearer_Itch.mp3'
    default_song_name_2 = 'rickroll.mp3'

    song_path_1 = f"{default_music_path}/{default_song_name_1}"
    song_path_2 = f"{default_music_path}/{default_song_name_2}"

    mashup_script(song_path_1, song_path_2)