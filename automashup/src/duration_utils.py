import numpy as np


# %% Signal manipulation stuff
def adapt_all_stems_durations(vocal_track, instrumental_tracks, padding_type='constant', target_length=None):
    if target_length is None:
        target_length = get_target_length(vocal_track, instrumental_tracks, length_type='max')
    vocal_track_adapted = adapt_audio_duration(vocal_track, target_length, padding_type=padding_type)
    instr_tracks_adapted = [adapt_audio_duration(stem, target_length, padding_type=padding_type) for stem in instrumental_tracks]
    return vocal_track_adapted, instr_tracks_adapted

def get_target_length(vocal_track, instrumental_tracks, length_type='max'): #May be adapted for otehr types of length computation (median, or bar splitting)
    match length_type:
        case 'max':
            return max(len(vocal_track), max([len(track) for track in instrumental_tracks]))
        case _:
            raise ValueError(f"Invalid length type: {length_type}")

def adapt_audio_duration(audio, target_length, padding_type='constant'):
    if len(audio) == target_length:
        return audio
    elif len(audio) < target_length:
        return pad_audio(audio, target_length, padding_type)
    else:
        return crop_audio(audio, target_length)

def pad_audio(audio, target_length, padding_type='constant'):
    assert len(audio) <= target_length, "Audio is longer than target length, cannot pad"
    match padding_type:
        case 'constant':
            padded_audio = np.pad(audio, (0, target_length - len(audio)), mode='constant', constant_values=0)
        case 'reflect':
            padded_audio = np.pad(audio, (0, target_length - len(audio)), mode='reflect')
        case 'repeat':
            padded_audio = np.pad(audio, (0, target_length - len(audio)), mode='wrap')
        case _:
            raise ValueError(f"Invalid padding type: {padding_type}")
    assert len(padded_audio) == target_length, "Audio is not of the target length after padding, this is a bug."
    return padded_audio

def crop_audio(audio, target_length):
    assert len(audio) >= target_length, "Audio is shorter than target length, cannot crop"
    return audio[0:target_length]

def adapt_start_audio(audio, start_time, sr):
    return audio[int(start_time * sr):]

def extract_section_audio(audio, sr, start_time, end_time):
    """
    Extract audio samples between start and end times.
    
    Args:
        audio: Audio data as numpy array
        sr: Sample rate
        start_time: Start time in seconds
        end_time: End time in seconds
    
    Returns:
        np.ndarray: Extracted audio segment
    """
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    return audio[start_sample:end_sample]

def prepad_to_length(audio, target_length):
    """Prepad audio with zeros to reach target_length."""
    pad_needed = target_length - len(audio)
    if pad_needed > 0:
        return np.concatenate([np.zeros(pad_needed), audio])
    return audio