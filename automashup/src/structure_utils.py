from automashup.src.segment import Segment
import automashup.src.tempo_utils as tempo_utils
import automashup.src.duration_utils as duration_utils
import numpy as np

def adapt_this_instrumental_section(vocal_segment_of_interest, instrumental_track, current_index, time_adapt_method='bpm'):
    """
    Process a single section:
        1) find a matching section in the other track
        2) adapt the tempo of the original track to the tempo of the matching section
        3) adapt the length of the re-bpm'd track to the length of the matching section
    
    Returns:
        Tuple of (processed audio array, updated current_index)
    """
    instrumental_track_segments = instrumental_track.segments
    instrumental_matching_section, current_index = find_matching_section(vocal_segment_of_interest.label, instrumental_track_segments, current_index)
    
    if instrumental_matching_section is None: # Has to be handled in find_matching_section, is not for now. TODO.
        print(f"No matching section for '{vocal_segment_of_interest.label}'. Using zeros (TODO: inpainting).")
        # Return zeros with correct sample count
        return np.zeros(int(vocal_segment_of_interest.duration_samples)), current_index
    
    # Extract the segment audio from the original track
    instrumental_matching_section_audio = instrumental_matching_section.original_audio # instrumental_matching_section.get_audio_segment(instrumental_track)
    
    # Accelerate to match tempo
    match time_adapt_method:
        case 'bpm':
            accelerated_instrumental_matching_section_audio = tempo_utils.accelerate_audio(
                instrumental_matching_section_audio, 
                instrumental_matching_section.sr, 
                instrumental_matching_section.bpm,  # Use section BPM, not track BPM
                vocal_segment_of_interest.bpm
            )
            target_length_samples = vocal_segment_of_interest.duration_samples
            adapted = duration_utils.adapt_audio_duration(accelerated_instrumental_matching_section_audio, target_length_samples, padding_type='repeat')
            return adapted, current_index
            
        case 'downbeats': # May sometimes be a problem if the downbeats that needs to be added slow or accelerate too much, but it's better than nothing
            audio_barwise = instrumental_matching_section.get_audio_barwise(track=instrumental_track)
            if len(audio_barwise) == 0:
                raise ValueError("Empty barwise audio. Should be catched earlier.")
            accelerated_instrumental_matching_section_audio = tempo_utils.accelerate_to_match_downbeats(
                audio_barwise, instrumental_matching_section.sr, vocal_segment_of_interest.downbeats_samples  # Property, not method - no ()
            )
            
            # # Fix assertion to compare lengths, and add safety padding
            # target_length_samples = vocal_segment_of_interest.duration_samples
            # if len(accelerated_instrumental_matching_section_audio) != target_length_samples: # Actually, differences can happen at the barscale, but may cancel at the songscale
            #     print(f"DEBUG: Length mismatch: {len(accelerated_instrumental_matching_section_audio)} != {target_length_samples}")
            #     # Adapt to exact length if rounding caused mismatch
            #     accelerated_instrumental_matching_section_audio = duration_utils.adapt_audio_duration(
            #         accelerated_instrumental_matching_section_audio, target_length_samples, padding_type='repeat'
            #     )
            
            return accelerated_instrumental_matching_section_audio, current_index
            
        case _:
            raise ValueError(f"Unknown time adaptation method: {time_adapt_method}")

def find_matching_section(target_label, segments, current_index=0):
    """
    Find a segment with matching label from the list of segments.
    
    Priority:
        1. Exact label match (starting from current_index to handle multiple same-label sections)
        2. Closest label match (e.g., 'verse' matches 'verse A')
        3. Fallback to first 'verse' section
        4. Fallback to first segment
    
    Args:
        target_label: The label to match (e.g., 'chorus', 'verse')
        segments: List of segment objects or dicts with 'label' attribute/key
        current_index: Index to help match corresponding sections when multiple exist
    
    Returns:
        The matching segment object/dict, or None if empty list
    """
    if not segments:
        raise ValueError("Empty list of segments provided")
    
    def _is_section_empty(section):
        return section.downbeats_samples is None  

    # Count segments with matching labels to handle multiple same-label sections
    exact_matches = [seg for seg in segments if seg.label == target_label]
    if exact_matches: # We found sections with the same label. Yay!
        # Use current_index to pick corresponding section when multiple exist
        idx = min(current_index, len(exact_matches) - 1)
        if not _is_section_empty(exact_matches[idx]):
            return exact_matches[idx], current_index + 1
    
    # Else, try closest label match (e.g., 'chorus' matches 'chorus A', 'chorus 1', etc.)
    target_base = target_label.split()[0].lower() if target_label else ''
    close_matches = [seg for seg in segments if seg.label.lower().startswith(target_base)]
    if close_matches: # Ok, we found sections with the same label base. Yay!
        # Use current_index to pick corresponding section when multiple exist
        idx = min(current_index, len(close_matches) - 1)
        if not _is_section_empty(close_matches[idx]):
            return close_matches[idx], current_index + 1
    
    # Fallback to first verse, by default. We don't increment current_index because we haven't found a match.
    verse_matches = [seg for seg in segments if 'verse' in seg.label.lower()]
    if verse_matches:
        if not _is_section_empty(verse_matches[0]):
            return verse_matches[0], current_index
    
    # Ultimate fallback: first non-empty segment, by default. We don't increment current_index because we haven't found a match.
    i = 0
    while _is_section_empty(segments[i]):
        i += 1
        if i >= len(segments):
            raise ValueError("No non-empty segment found in list of segments")
    return segments[i], current_index
    # return None # Could also be None, notably to know where to inpaint. Can be handled from here actually.

def extract_intro_audio(track, target_bpm):
    """Extract and tempo-adjust the intro (audio before first downbeat) from a track."""
    first_downbeat = track.downbeats[0]
    intro_frame = int(first_downbeat * track.sr)
    intro_audio = track.audio[:intro_frame]
    
    if len(intro_audio) > 0:
        return tempo_utils.accelerate_audio(intro_audio, track.sr, track.bpm, target_bpm)
    return np.array([])

def pad_and_align_intro_audios(intro_audios):
    """Align intros to end at the same time."""
    max_intro_length = max((len(intro_audio) for intro_audio in intro_audios), default=0)
    return [duration_utils.prepad_to_length(intro_audio, max_intro_length) for intro_audio in intro_audios] 