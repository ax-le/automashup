"""
Pitch utilities for audio processing.

This module provides functions for key detection and pitch shifting.

## TODO
- Adapt the pitch according to the whole kye, not just the root note
"""

import numpy as np
import pyrubberband as pyrb
from automashup.src.key_finder import KeyFinder

def estimate_key(waveform, sr):
    key_finder = KeyFinder(waveform=waveform, sr=sr)
    return key_finder.key_primary

def estimate_key_from_path(path):
    key_info = KeyFinder(filepath=path)
    return key_info.key_primary

def repitch_audio(audio: np.ndarray, sr: int, semitone_shift: float) -> np.ndarray:
    """
    Repitch audio by a given number of semitones.
    
    Args:
        audio: Audio array to repitch.
        sr: Sample rate of the audio.
        semitone_shift: Number of semitones to shift (positive = higher pitch).
        
    Returns:
        The repitched audio array.
    """
    return pyrb.pitch_shift(y=audio, sr=sr, n_steps=semitone_shift)


def repitch_audio_to_target(audio: np.ndarray, sr: int, source_key: str, target_key: str) -> np.ndarray:
    """
    Repitch audio from a source key to a target key.
    
    Args:
        audio: Audio array to repitch.
        sr: Sample rate of the audio.
        source_key: The current key of the audio (e.g., "C major").
        target_key: The desired key for the audio (e.g., "G major").
        
    Returns:
        The repitched audio array.
    """
    ## Still not satisfactory actually, because we want the difference bewteen keys, not the absolute pitch
    semitone_shift = semitones_between_keys(source_key, target_key)
    return repitch_audio(audio, sr, semitone_shift)

# Semitone offsets from C (C = 0)
SEMITONE_OFFSETS = {
    'C': 0, 'C#': 1, 'Db': 1, 
    'D': 2, 'D#': 3, 'Eb': 3, 
    'E': 4, 'Fb': 4, 'E#': 5,
    'F': 5, 'F#': 6, 'Gb': 6, 
    'G': 7, 'G#': 8, 'Ab': 8, 
    'A': 9, 'A#': 10, 'Bb': 10, 
    'B': 11, 'Cb': 11, 'B#': 0
}

def semitones_between_keys(source_key: str, target_key: str) -> int:
    """
    Compute the number of semitones between two keys, accounting for major/minor modes.
    
    Uses the circle of fifths relationship: relative major/minor keys (e.g., C major 
    and A minor) are harmonically equivalent and require 0 semitones shift.
    
    Args:
        source_key: The source key (e.g., "C major", "G minor").
        target_key: The target key (e.g., "G major", "A minor").
        
    Returns:
        Number of semitones to shift from source to target (positive = up, negative = down).
        The shift is always the shortest path (max 6 semitones in either direction).
    """
    # Parse note and mode from key (e.g., "C major" -> ("C", "major"))
    source_parts = source_key.split(' ', 1)
    target_parts = target_key.split(' ', 1)
    
    source_note = source_parts[0]
    target_note = target_parts[0]
    source_mode = source_parts[1].lower() if len(source_parts) > 1 else 'major'
    target_mode = target_parts[1].lower() if len(target_parts) > 1 else 'major'
    
    source_semitone = SEMITONE_OFFSETS[source_note]
    target_semitone = SEMITONE_OFFSETS[target_note]
    
    # Normalize to equivalent major key using circle of fifths
    # The relative major of a minor key is 3 semitones above
    if source_mode == 'minor':
        source_semitone = (source_semitone + 3) % 12
    if target_mode == 'minor':
        target_semitone = (target_semitone + 3) % 12
    
    # Calculate semitone difference
    diff = target_semitone - source_semitone
    
    # Normalize to shortest path (-6 to +6 semitones)
    if diff > 6:
        diff -= 12
    elif diff < -6:
        diff += 12
    
    return diff