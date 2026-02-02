import pyrubberband as pyrb
import numpy as np
import automashup.src.duration_utils as duration_utils
import automashup.src.concatenate as concatenate

def time_stretch_audio(audio, sr, orig_tempo, ref_tempo):
    """
    Time stretch (accelerate or decelerate) this audio to fit into timesteps.
    Actually adapted for downbeat-scale alignment.

    Returns:
        time-stretched audio array
    """
    return pyrb.time_stretch(audio, sr, rate = ref_tempo / orig_tempo)

def time_stretch_to_match_timesteps(audio, sr, ref_start, ref_end):
    """
    Time stretch (accelerate or decelerate) this audio to fit into timesteps.
    Actually adapted for downbeat-scale alignment.

    Returns:
        time-stretched audio array
    """
    ref_duration = ref_end - ref_start
    return time_stretch_to_match_length(audio, sr, ref_duration)

def time_stretch_to_match_length(audio, sr, ref_length):
    """
    Time stretch this audio to fit into timesteps.
    Actually adapted for downbeat-scale alignment.

    Returns:
        Time-stretched audio array
    """
    orig_length = len(audio)
    length_ratio = orig_length / ref_length
    stretched = time_stretch_audio(
        audio, sr, 1.0, length_ratio    
    )
    assert len(stretched) == ref_length, f"Expected length {ref_length}, got {len(stretched)}"
    return stretched

def time_stretch_to_match_downbeats(barwise_audio, sr, ref_downbeats_in_samples):
    """
    Time stretch audio by adapting each downbeat segment individually.
    
    Args:
        barwise_audio: List of audio arrays, each corresponding to a bar
        ref_downbeats_in_samples: List of reference downbeat times in samples
    
    Returns:
        np.ndarray: Concatenated audio with each downbeat segment adapted
    """
    
    adapted_bars = []

    nb_bars = len(barwise_audio) # To check
    if nb_bars == 0:
        raise ValueError("Empty barwise audio. Should be catched earlier.")
        
    nb_bars_ref = len(ref_downbeats_in_samples) - 1

    if nb_bars_ref == 0:
        raise ValueError("Empty or length < 2 reference downbeats. Should be catched earlier.")

    for i in range(nb_bars_ref):
        # So, according to the length differences, we need to handle 3 cases:
        # 1. exactly the same number of bars in both tracks 
        #   -> nb_bars == nb_bars_ref: i % nb_bars == i
        # 2. more bars in the instrumental track
        #   -> nb_bars < nb_bars_ref: i % nb_bars repeats the bars (looping)
        # 3. less bars in the instrumental track
        #   -> nb_bars > nb_bars_ref: i % nb_bars == i, and loop stops at nb_bars_ref (truncation)
        a_bar = barwise_audio[i % nb_bars]
        
        if len(a_bar) == 0:
            raise ValueError("Empty barwise segment audio") 
        
        # Adapt this segment to match reference downbeat timing
        adapted = time_stretch_to_match_timesteps(
            a_bar, sr, ref_downbeats_in_samples[i], ref_downbeats_in_samples[i+1]
        )
        adapted_bars.append(adapted)
    
    if not adapted_bars:
        return None
    
    return concatenate.concatenate_sections(adapted_bars)
    