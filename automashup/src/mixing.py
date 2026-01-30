import automashup.src.duration_utils as duration_utils
import numpy as np

def additive_mix(vocal_audio, instrumental_tracks_audios, padding_type='constant'):
    padded_vocal, padded_instr_tracks = duration_utils.adapt_all_stems_durations(vocal_audio, instrumental_tracks_audios, padding_type=padding_type)
    mixed_audio = padded_vocal + additive_mix_instrumentals(padded_instr_tracks)
    return mixed_audio

def additive_mix_instrumentals(instrumental_tracks_audios):
    assert np.all([len(audio) == len(instrumental_tracks_audios[0]) for audio in instrumental_tracks_audios])
    mixed_audio = np.sum(instrumental_tracks_audios, axis=0)
    return mixed_audio