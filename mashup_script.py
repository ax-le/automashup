import os
from IPython.display import Audio, display

import automashup.src.preprocessing as preprocessing
import automashup.src.postprocessing as postprocessing
import automashup.src.mixing as mixing
import automashup.src.utils as utils
from automashup.src.track import Track
import automashup.src.mashup as mashupper
from automashup.src import tempo_utils

from copy import deepcopy

default_data_path = "/Brain/private/a23marmo/projects/automashup/data/my_samples"
default_music_path = f"{default_data_path}/audio"
default_stored_data_path = f"{default_data_path}/intermediate_data"
default_save_mashup_path = f"{default_data_path}/mashups_created"

def mashup_script(song_path_1, song_path_2, stored_data_folder = default_stored_data_path, mashup_save_folder = default_save_mashup_path, verbose = True):

    # Create the stored data folder if it doesn't exist
    os.makedirs(stored_data_folder, exist_ok=True)

    if verbose:
        print("Processing the first song...")
        print("Estimating key, structure, and everything else.")
    song_name_1 = utils.extract_filename_from_path(song_path_1)
    # Estimate key, structure, and everything else
    metadata_1 = preprocessing.song_info_estimation(song_path_1, default_stored_data_path)

    if verbose:
        print("Source separation.")
    # Do 2 stems music source separation - vocals/instrumental
    # vocals_1, instru_1 = preprocessing.load_or_compute_source_separated_songs(song_path_1, default_stored_data_path, two_stems=True)
    # Do 4 stems music source separation - vocals/bass/drums/other. I would prefer 2 stems, but 4 stems is already done by Allin1
    vocals_4stems_1, bass_4stems_1, drums_4stems_1, other_4stems_1 = preprocessing.load_or_compute_source_separated_songs(song_path_1, default_stored_data_path, two_stems = False, model = 'htdemucs', verbose = True)

    if verbose:
        print("Initializing the Track object.")
    mashup_vocals = Track(song_name_1, 'vocals', vocals_4stems_1[0], vocals_4stems_1[1], metadata_1['bpm'], metadata_1['beats'], metadata_1['downbeats'], metadata_1['key'], metadata_1['segments'], metadata_1['path'], metadata_1['beat_positions'])

    if verbose:
        print("Estimating key, structure, and everything else.")
    song_name_2 = utils.extract_filename_from_path(song_path_2)
    # Estimate key, structure, and everything else
    metadata_2 = preprocessing.song_info_estimation(song_path_2, default_stored_data_path)

    if verbose:
        print("Source separation.")
    # Do 2 stems music source separation - vocals/instrumental
    # vocals_2, instru_2 = preprocessing.load_or_compute_source_separated_songs(song_path_2, default_stored_data_path, two_stems=True)
    # Do 4 stems music source separation - vocals/bass/drums/other. I would prefer 2 stems, but 4 stems is already done by Allin1
    vocals_4stems_2, bass_4stems_2, drums_4stems_2, other_4stems_2 = preprocessing.load_or_compute_source_separated_songs(song_path_2, default_stored_data_path, two_stems = False, model = 'htdemucs', verbose = True)

    if verbose:
        print("Initializing the Track object.")
    mashup_bass = Track(song_name_2, 'bass', bass_4stems_2[0], bass_4stems_2[1], metadata_2['bpm'], metadata_2['beats'], metadata_2['downbeats'], metadata_2['key'], metadata_2['segments'], metadata_2['path'], metadata_2['beat_positions'])
    mashup_drums = Track(song_name_2, 'drums', drums_4stems_2[0], drums_4stems_2[1], metadata_2['bpm'], metadata_2['beats'], metadata_2['downbeats'], metadata_2['key'], metadata_2['segments'], metadata_2['path'], metadata_2['beat_positions'])
    mashup_other = Track(song_name_2, 'other', other_4stems_2[0], other_4stems_2[1], metadata_2['bpm'], metadata_2['beats'], metadata_2['downbeats'], metadata_2['key'], metadata_2['segments'], metadata_2['path'], metadata_2['beat_positions'])

    if verbose:
        print("Vocals attributes:")
        print(f"  BPM: {mashup_vocals.bpm}")
        print(f"  Key: {mashup_vocals.key}")
        print(f"  Beat frames: {mashup_vocals.beats}")
        print(f"  Audio shape: {mashup_vocals.audio.shape}")
        print(f"  Sampling Frequency: {mashup_vocals.sr}")
        print()
        print("Bass attributes:")
        print(f"  BPM: {mashup_bass.bpm}")
        print(f"  Key: {mashup_bass.key}")
        print(f"  Beat frames: {mashup_bass.beats}")
        print(f"  Audio shape: {mashup_bass.audio.shape}")
        print(f"  Sampling Frequency: {mashup_bass.sr}")

    if verbose:
        print("Creating mashups with different techniques...")
        print("Starting with mashup without pitch shifting nor structure alignment.")
    mashup_result_vanilla = mashupper.mashup_technic(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], save_folder_path = default_save_mashup_path)

    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_vanilla.audio, rate=mashup_result_vanilla.sr))

    if verbose:
        print("Mashup with repitching the vocal to the instrumental key, but no structure alignment.")
    mashup_result_repitch_vocals_to_instrumental = mashupper.mashup_technic(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], save_folder_path = default_save_mashup_path, repitch='vocals_to_instrumental')

    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_repitch_vocals_to_instrumental.audio, rate=mashup_result_repitch_vocals_to_instrumental.sr))
    
    if verbose:
        print("Mashup with repitching the instrumental to the vocal key, but no structure alignment.")
    mashup_result_repitch_instrumental_to_vocals = mashupper.mashup_technic(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], save_folder_path = default_save_mashup_path, repitch='instrumental_to_vocals')
    
    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_repitch_instrumental_to_vocals.audio, rate=mashup_result_repitch_instrumental_to_vocals.sr))

    if verbose:
        print("Mashup with structure alignment.")
        print("First, aligning the instrumental to the vocal structure, each section being set to the bpm of the vocal song.")
        print("Mashup without repitching.")
    mashup_result_structure_bpm = mashupper.mashup_by_section(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], time_adapt_method='bpm', save_folder_path = default_save_mashup_path)

    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_structure_bpm.audio, rate=mashup_result_structure_bpm.sr))

    if verbose:
        print("Mashup with repitching the instrumental to the vocal key.")            
    mashup_result_structure_bpm_repitch = mashupper.mashup_by_section(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], time_adapt_method='bpm', repitch = "instrumental_to_vocals", save_folder_path = default_save_mashup_path)

    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_structure_bpm_repitch.audio, rate=mashup_result_structure_bpm_repitch.sr))

    if verbose:
        print("Secondly, aligning the instrumental to the vocal structure, each bar of the instrumental being adapted to the size of each bar in the vocal part.")
        print("Mashup without repitching.")
    mashup_result_structure_db = mashupper.mashup_by_section(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], time_adapt_method='downbeats', save_folder_path = default_save_mashup_path)

    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_structure_db.audio, rate=mashup_result_structure_db.sr))

    if verbose:
        print("Mashup with repitching the instrumental to the vocal key.")
    mashup_result_structure_db_repitch = mashupper.mashup_by_section(vocal_track=deepcopy(mashup_vocals), instrumental_tracks=[deepcopy(mashup_bass), deepcopy(mashup_drums), deepcopy(mashup_other)], time_adapt_method='downbeats', repitch = "instrumental_to_vocals", save_folder_path = default_save_mashup_path)

    # if verbose:
    #     print("Playing the mashup.")
    # display(Audio(mashup_result_structure_db_repitch.audio, rate=mashup_result_structure_db_repitch.sr))


if __name__ == "__main__":
    
    default_song_name_1 = 'rickroll.mp3'
    default_song_name_2 = 'doomscroll.mp3'

    song_path_1 = f"{default_music_path}/{default_song_name_1}"
    song_path_2 = f"{default_music_path}/{default_song_name_2}"

    mashup_script(song_path_1, song_path_2)