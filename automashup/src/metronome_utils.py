"""
Metronome utilities for audio processing.

This module provides functions to add metronome sounds to audio tracks.
"""

import librosa
import numpy as np

import automashup.src.duration_utils as duration_utils

def add_metronome(audio: np.ndarray, sr: int, beats: list, metronome_sound_path: str = "/data/audio/metronome-sounds") -> np.ndarray:
    """
    Add metronome click sounds to an audio array at beat positions.
    
    Args:
        audio: Audio array to add metronome to.
        sr: Sample rate of the audio.
        beats: List of beat times in seconds.
        metronome_sound_path: Path to the directory containing metronome sounds.
        
    Returns:
        Audio array with metronome sounds added.
    """
    # Load metronome sounds
    downbeat_sound_audio, _ = librosa.load(f"{metronome_sound_path}/block.mp3")
    otherbeat_sound_audio, _ = librosa.load(f"{metronome_sound_path}/drumstick.mp3")

    # Make a copy to avoid modifying the original
    result = audio.copy()

    # Add sound for each beat
    for i, beat_frame in enumerate(beats):
        # If it's a downbeat, use the according sound
        clic_sound = downbeat_sound_audio if i % 4 == 0 else otherbeat_sound_audio
        clic = duration_utils.adapt_audio_duration(clic_sound, len(result[round(sr * beat_frame):]), padding_type='constant')
        # Check that we do not get out of the track's bounds
        if len(result[round(sr * beat_frame):]) >= len(clic):
            result[round(sr * beat_frame):] += clic

    return result
