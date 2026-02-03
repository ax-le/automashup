import librosa
import numpy as np
import warnings
import copy

from automashup.src.track import Track
import automashup.src.tempo_utils as tempo_utils
import automashup.src.duration_utils as duration_utils
import automashup.src.pitch_utils as pitch_utils
import automashup.src.structure_utils as structure_utils
import automashup.src.mixing as mixing
import automashup.src.postprocessing as postprocessing
import automashup.src.concatenate as concatenate

# %% Vanilla mashup (just bpm adjustment)
def mashup_adjust_songscale(vocal_track_in, instrumental_tracks_in, target_loudness=-14.0, save_folder_path=None, repitch = None, add_to_save_name = ""):
    """
    Vanilla mashup with first downbeat alignment and bpm sync.

    The tracks are aligned on their first downbeat and the bpm is adjusted to match the vocal track.
    The instrumental tracks are resampled to match the vocal track's sampling rate.
    Tracks can be repitched to match the instrumental or vocal track's key, depending on the repitch arg.

    Args:
        vocal_track_in: Vocal track object
        instrumental_tracks_in: List of instrumental track objects
        target_loudness: Target loudness in LUFS
        save_folder_path: Path to save the mashup
        repitch: 'vocals_to_instrumental' or 'instrumental_to_vocals' to repitch the instrumental tracks to match the vocal track's key
    
    Returns:
        mashup: Track object
    """
    # Make a copy of the tracks
    vocal_track = copy.deepcopy(vocal_track_in)
    instrumental_tracks = [copy.deepcopy(track) for track in instrumental_tracks_in]

    mashup_name = f"{vocal_track.name} - {instrumental_tracks[0].name}_adjust_songscale"

    # Init initial audio variables
    vocal_track_audio = vocal_track.audio 
    instrumental_tracks_audio = [track.audio for track in instrumental_tracks]
    
    # Repitching
    match repitch:
        case None: # No repitching
            mashup_key = None
            add_to_save_name += "_no_repitch"
        
        case 'vocals_to_instrumental': # Repitch the vocal track to match the instrumental track's key
            mashup_key = instrumental_tracks[0].key

            # Repitch the vocal track to match the instrumental track's key
            if mashup_key != vocal_track.key: # We save computation time if the key is already the same.
                vocal_track_audio = vocal_track.repitch(mashup_key)
            add_to_save_name += "_repitch_vocals_to_instrumental"
        
        case 'instrumental_to_vocals': # Repitch the instrumental tracks to match the vocal track's key
            mashup_key = vocal_track.key
            for i in range(len(instrumental_tracks)):
                if instrumental_tracks[i].key != mashup_key: # We save computation time if the key is already the same.
                    # if track.instrument != 'drums': # Don't repitch drums?
                    instrumental_tracks_audio[i] = instrumental_tracks[i].repitch(mashup_key)
            add_to_save_name += "_repitch_instrumental_to_vocals"
        case _:
            raise ValueError(f"Invalid repitch value: {repitch}")

    # Create a dummy track to store the mashup
    mashup = Track(
        track_name=mashup_name, 
        instrument='mashup', 
        audio=np.zeros(1), # Init with dummy audio
        sr=vocal_track.sr,
        bpm=vocal_track.bpm, # Align with the vocal track
        beats=vocal_track.beats, # Align with the vocal track
        downbeats=vocal_track.downbeats, # Align with the vocal track
        key=mashup_key, # Align with the one chosen above with repitch arg
        segments=vocal_track.get_segments_as_dict(), # Align with the vocal track
        path=None, 
    )

    # Starting the song on the first downbeat
    audio_vocal_cropped = vocal_track_audio[int(vocal_track.downbeats[0] * vocal_track.sr):]

    # Adjusting the instrumental tracks to match the vocal track
    for idx_track, track in enumerate(instrumental_tracks):
        # Starting the song on the first downbeat
        instr_audio = instrumental_tracks_audio[idx_track][int(track.downbeats[0] * track.sr):]

        # Change the bpm
        instrumental_tracks_audio[idx_track] = track.change_tempo(new_tempo=mashup.bpm, overwrite_audio=instr_audio)

    mashup.audio = mixing.additive_mix(audio_vocal_cropped, instrumental_tracks_audio)

    # Normalize the mashup to the target loudness (-14 LUFS by deafult)
    mashup.audio = postprocessing.normalize_lufs(mashup.audio, mashup.sr, target_lufs=target_loudness)

    if save_folder_path:
        # Save audio
        mashup.path = postprocessing.save_song(mashup.audio, mashup.sr, save_folder_path, mashup.name, add_name=add_to_save_name)

    return mashup

# ============================================================================
# Section-Based Mashup Functions
# ============================================================================

def mashup_adjust_by_section(vocal_track_in, instrumental_tracks_in, target_loudness=-14.0, time_adapt_method='bpm', adding_intros=True, save_folder_path=None, repitch = None, add_to_save_name = ""):
    """
    Create a mashup by aligning sections of instrumental tracks to the vocal structure.
    
    Aligns vocal and instrumental tracks on their respective first downbeats.
    Extracts instrumental intros (before first downbeat) and prepends them to the mix.
    """
    # Mashup technic with first downbeat alignment and bpm sync
    # Make a copy of the tracks
    vocal_track = copy.deepcopy(vocal_track_in)
    instrumental_tracks = [copy.deepcopy(track) for track in instrumental_tracks_in]

    mashup_name = f"{vocal_track.name} - {instrumental_tracks[0].name}_section_alignment"

    # Create a dummy track to store the mashup
    mashup = Track(
        track_name=mashup_name, 
        instrument='mashup_by_section', 
        audio=np.zeros(1), # Init with dummy audio
        sr=vocal_track.sr,
        bpm=vocal_track.bpm, # Align with the vocal track
        beats=vocal_track.beats, # Align with the vocal track
        downbeats=vocal_track.downbeats, # Align with the vocal track
        key=vocal_track.key, # Align with the cvocal_track. Actually, does not matter since we repitch to the section key. Maybe the key attribute should be set section-wise?
        segments=vocal_track.get_segments_as_dict(), # Align with the vocal track
        path=None, 
    )

    # Collect adapted instrumental sections for each vocal segment
    instrumental_audio_sections = [[] for _ in instrumental_tracks]
    label_counts = [{} for _ in instrumental_tracks]
    
    # Filter vocal segments to only those ending after the first downbeat
    # This seems important because introduction are sometimes not aligned with bar segmentation of the song,
    # and we want to avoid weird alignments.
    vocal_first_downbeat = vocal_track.downbeats[0]
    vocal_segments_after_first_downbeat = [
        seg for seg in vocal_track.segments if seg.end >= vocal_first_downbeat
    ]

    # Crop vocal to the start of the song
    if time_adapt_method == 'bpm':
        # In the bpm condition, sections are aligned on their estimated start and end, and not on the downbeats!
        start_song = vocal_segments_after_first_downbeat[0].start_samples
    elif time_adapt_method == 'downbeats':
        start_song = vocal_segments_after_first_downbeat[0].downbeats_samples[0]
    # Crop vocal to the start of the song
    vocal_audio = vocal_track.audio[int(start_song):]

    for vocal_section in vocal_segments_after_first_downbeat:
        # In downbeat alignment, ensure that the reference segment has at least 2 downbeats (i.e., at least 1 bar).
        if time_adapt_method == 'downbeats' and (vocal_section.downbeats_samples is None or len(vocal_section.downbeats_samples) < 2):
            continue
        for i, inst_track in enumerate(instrumental_tracks):
            # Get the number of times this label has appeared in the instrumental track so far
            current_index_before_increment = label_counts[i].get(vocal_section.label, 0)

            # Find the matching section in the instrumental track
            inst_section, current_index_after_increment = structure_utils.find_matching_section(vocal_section.label, inst_track.segments, current_index_before_increment)

            # Repitch the instrumental section to the vocal section
            if repitch == 'instrumental_to_vocals' and inst_section.key != vocal_section.key: 
                # if inst_track.instrument != 'drums': # Don't repitch drums?
                inst_section_audio = inst_section.repitch(vocal_section.key)
            else:
                inst_section_audio = inst_section.audio

            this_sec_audio_adapted = inst_section.time_stretch_this_section(ref_section=vocal_section, time_adapt_method=time_adapt_method, overwrite_audio = inst_section_audio)

            if this_sec_audio_adapted is None: # Should not happen
                raise ValueError(f"Instrumental section audio is empty for section {vocal_section.label} for instrumental track {inst_track.name}")
            
            # Append the adapted instrumental section to the list of instrumental sections
            instrumental_audio_sections[i].append(this_sec_audio_adapted)
            # Update the number of times this label has appeared in the instrumental track. May have not changed if the label was not found
            label_counts[i][vocal_section.label] = current_index_after_increment

    # Concatenate main sections
    main_sections_instrumental = [concatenate.concatenate_sections(s) for s in instrumental_audio_sections]

    # Mix main sections
    if len(vocal_audio) != len(main_sections_instrumental[0]):
        length_mismatch_seconds = abs(len(vocal_audio) - len(main_sections_instrumental[0])) / mashup.sr
        if length_mismatch_seconds > 1:
            warnings.warn(f"Length mismatch between vocal final main section ({len(vocal_audio)}) and instrumental final main sections ({len(main_sections_instrumental[0])}). Not a problem if both lengths are close, may be if they are too different (gap: {abs(len(vocal_audio) - len(main_sections_instrumental[0]))} samples, i.e. {length_mismatch_seconds} seconds).")
    mixed_main_sections = mixing.additive_mix(vocal_audio, main_sections_instrumental)
    
    # We may want to add the original instrumental intro of the song
    if adding_intros:
        # Extract intros
        intro_audios = [structure_utils.extract_intro_audio(t, mashup.bpm) for t in instrumental_tracks]

        # Repitch the instrumental section to the vocal section
        if repitch == 'instrumental_to_vocals':
            for i in range(len(intro_audios)):
                vocal_first_key = vocal_segments_after_first_downbeat[0].key
                intro_key = instrumental_tracks[i].key # Assume the key of the entire song.
                intro_sr = instrumental_tracks[i].sr
                if intro_key != vocal_first_key: 
                    # if inst_track.instrument != 'drums': # Don't repitch drums?
                    intro_audios[i] = pitch_utils.repitch_audio_to_target(intro_audios[i], intro_sr, intro_key, vocal_first_key)

        # Pad and align the instrumental intros together
        padded_intro_audios = structure_utils.pad_and_align_intro_audios(intro_audios)
        # Mix intros together
        mixed_intros = mixing.additive_mix_instrumentals(padded_intro_audios)
    
        # Concatenate the instrumental intro and the main sections
        final_song = np.concatenate([mixed_intros, mixed_main_sections])

    else: # We start on the first downbeat of the song, and disregard potential intro
        final_song = mixed_main_sections

    # Normalize the mashup to the target loudness
    final_song = postprocessing.normalize_lufs(final_song, mashup.sr, target_loudness)

    mashup.audio = final_song

    # Repitching naming
    match repitch:
        case None:
            add_to_save_name += "_no_repitch"
        case 'vocals_to_instrumental':
            raise NotImplementedError("Only instrumental to vocals repitching is implemented yet, because the section adaptation is only implemented for instrumental tracks.")
        case 'instrumental_to_vocals':
            add_to_save_name += "_repitch_instrumental_to_vocals"
        case _:
            raise ValueError(f"Invalid repitch value: {repitch}")

    # Time adaptation naming
    match time_adapt_method:
        case 'bpm':
            add_to_save_name += "_bpm"
        case 'downbeats':
            add_to_save_name += "_downbeats"
        case _:
            raise ValueError(f"Invalid time adaptation method: {time_adapt_method}")

    if save_folder_path:
        # Save audio
        mashup.path = postprocessing.save_song(mashup.audio, mashup.sr, save_folder_path, mashup.name, add_name=add_to_save_name)

    return mashup