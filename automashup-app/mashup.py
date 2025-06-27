from utils import increase_array_size
import librosa
import numpy as np
import pyrubberband as pyrb
import pyloudnorm as pyln

# Mashup Technics
# In this file, you may add mashup technics
# the input of such a method is a list of up to 4 objects of type Track. 
# You can modify them without making any copy, it's already done before.
# You may find useful methods in the track.py file
# Be sure to return a Track object

def mashup_technic(tracks, phase_fit=False, target_loudness=-14.0):
    # Mashup technic with first beat alignment and bpm sync
    sr = tracks[0].sr # The first track is used to determine the target bpm
    tempo = tracks[0].bpm
    main_track_length = len(tracks[0].audio)
    beginning_instant = tracks[0].beats[0] # beats metadata
    beginning = beginning_instant * sr
    mashup = np.zeros(0)
    mashup_name = ""

    # we add each track to the mashup
    for track in tracks:
        mashup_name += track.name + " " # name
        track_tempo = track.bpm
        if track == tracks[0]:
            track_beginning_temporal = track.beats[0]
        else:
            track_beginning_temporal = track.downbeats[0]
        track_sr = track.sr
        track_beginning = track_beginning_temporal * track_sr
        track_audio = track.audio

        # reset first beat position
        track_audio_no_offset = np.array(track_audio)[round(track_beginning):] 

        # Change the bpm if there is no phase fit
        if not phase_fit:
            track_audio_accelerated = pyrb.time_stretch(track_audio_no_offset, track_sr, rate = tempo / track_tempo)
        else:
            #bpm is handled in segment.py
            track_audio_accelerated = track_audio_no_offset

        # add the right number of zeros to align with the main track
        final_track_audio = np.concatenate((np.zeros(round(beginning)), track_audio_accelerated)) 

        size = max(len(mashup), len(final_track_audio))
        mashup = np.array(mashup)
        mashup = (increase_array_size(final_track_audio, size) + increase_array_size(mashup, size))

    # Adjust mashup length to be the same as the main track's audio length
    if len(mashup) > main_track_length:
        mashup = mashup[:main_track_length]
    else:
        mashup = increase_array_size(mashup, main_track_length)

    # Apply LUFS normalization to the mashup
    meter = pyln.Meter(sr)  # Create a BS.1770 loudness meter
    mashup_loudness = meter.integrated_loudness(mashup)  # Measure the loudness
    print(f"Mashup loudness (before normalization): {mashup_loudness} LUFS")

    # Normalize the mashup to the target loudness (-14 LUFS by deafult)
    mashup_normalized = pyln.normalize.loudness(mashup, mashup_loudness, target_loudness)
    print(f"Mashup normalized to {target_loudness} LUFS")

    # we return a modified version of the first track
    # doing so, we keep its metadata
    tracks[0].audio = mashup

    return tracks[0]


def mashup_technic_repitch(tracks):
    # Mashup technique to change the key by repitch
    key = tracks[0].get_key() # target key
    for i in range(len(tracks)-1):
        tracks[i+1].pitch_track(key) # repitch

    return mashup_technic(tracks)


def mashup_technic_fit_phase(tracks):
    # Mashup technique with phase alignment (i.e., chorus with chorus, verse with verse...)
    # Each track's structure is aligned with the first one
    for i in range(len(tracks) - 1):
        tracks[i + 1].fit_phase(tracks[0])

    # Standard mashup method
    return mashup_technic(tracks, phase_fit=True)

def mashup_technic_fit_phase_repitch(tracks):
    # Mashup technique with phase alignment and repitch
    # Repitch has to be the last method for it to be effective
    key = tracks[0].get_key() # target key
    for i in range(len(tracks)-1):
        tracks[i + 1].fit_phase(tracks[0]) # phase fit
        tracks[i+1].pitch_track(key) # repitch
    # Phase fit mashup
    return mashup_technic(tracks, phase_fit=True)