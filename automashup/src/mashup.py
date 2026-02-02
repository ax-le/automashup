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
def mashup_adjust_songscale(vocal_track_in, instrumental_tracks_in, target_loudness=-14.0, save_folder_path=None, repitch = None):
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
    
    add_to_save_name = ""

    # Repitching
    match repitch:
        case None: # No repitching
            mashup_key = None
            add_to_save_name += "_no_repitch"
        case 'vocals_to_instrumental': # Repitch the vocal track to match the instrumental track's key
            mashup_key = instrumental_tracks[0].key
            if mashup_key != vocal_track.key: # We save computation time if the key is already the same.
                vocal_track.repitch(mashup_key)
            add_to_save_name += "_repitch_vocals_to_instrumental"
        case 'instrumental_to_vocals': # Repitch the instrumental tracks to match the vocal track's key
            mashup_key = vocal_track.key
            for track in instrumental_tracks:
                if track.key != mashup_key: # We save computation time if the key is already the same.
                    # if track.instrument != 'drums': # Don't repitch drums?
                    track.audio = pitch_utils.repitch_audio_to_target(track.audio, track.sr, track.key, mashup_key)
                    track.key = mashup_key
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
    audio_vocal_cropped = vocal_track.audio[:int(vocal_track.downbeats[0] * vocal_track.sr)]

    # Adjusting the instrumental tracks to match the vocal track
    inst_tracks_audio = []
    for track in instrumental_tracks:
        # Starting the song on the first downbeat
        track.audio = track.audio[:int(track.downbeats[0] * track.sr)] # inplace modification because the following functions are inplace

        # Resample if needed
        if track.sr != mashup.sr:
            track.resample(mashup.sr)
        
        # Change the bpm
        track.change_tempo(new_tempo=mashup.bpm)
        inst_tracks_audio.append(track.audio)

    mashup.audio = mixing.additive_mix(audio_vocal_cropped, inst_tracks_audio)

    # Normalize the mashup to the target loudness (-14 LUFS by deafult)
    mashup.audio = postprocessing.normalize_lufs(mashup.audio, mashup_sr, target_lufs=target_loudness)

    if save_folder_path:
        # Save audio
        mashup.path = postprocessing.save_song(mashup.audio, mashup.sr, save_folder_path, mashup.name, add_name=add_to_save_name)

    return mashup

# ============================================================================
# Section-Based Mashup Functions
# ============================================================================

def mashup_by_section(vocal_track_in, instrumental_tracks_in, target_loudness=-14.0, time_adapt_method='bpm', adding_intros=True, save_folder_path=None, repitch = None):
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
    add_to_save_name = ""

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
    set_of_segments = [[] for _ in instrumental_tracks]
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
    crop_vocal = vocal_track.audio[int(start_song):]

    for vocal_section in vocal_segments_after_first_downbeat:
        for i, inst_track in enumerate(instrumental_tracks):
            # Get the number of times this label has appeared in the instrumental track so far
            current_index_before_increment = label_counts[i].get(vocal_section.label, 0)

            # Find the matching section in the instrumental track
            inst_section, current_index_after_increment = structure_utils.find_matching_section(vocal_section.label, inst_track.segments, current_index_before_increment)
            inst_section.time_stretch_this_section(ref_section=vocal_section, time_adapt_method=time_adapt_method)

            if inst_section.audio is None: # Should not happen
                raise ValueError(f"Instrumental section audio is empty for section {vocal_section.label} for instrumental track {inst_track.name}")
            
            # Repitch the instrumental section to the vocal section
            if repitch == 'instrumental_to_vocals' and inst_track.key != vocal_section.key: 
                # if inst_track.instrument != 'drums': # Don't repitch drums?
                inst_section.repitch(vocal_section.key)

            # Append the adapted instrumental section to the list of instrumental sections
            instrumental_audio_sections[i].append(inst_section.audio)
            # Update the number of times this label has appeared in the instrumental track. May have not changed if the label was not found
            label_counts[i][vocal_section.label] = current_index_after_increment

    # Concatenate main sections
    main_sections_instrumental = [concatenate.concatenate_sections(s) for s in instrumental_audio_sections]

    # Mix main sections
    if len(crop_vocal) != len(main_sections_instrumental[0]):
        warnings.warn(f"Length mismatch between vocal final main section ({len(crop_vocal)}) and instrumental final main sections ({len(main_sections_instrumental[0])}). Not a problem if both lengths are close, may be if they are too different (gap: {abs(len(crop_vocal) - len(main_sections_instrumental[0]))} samples, i.e. {abs(len(crop_vocal) - len(main_sections_instrumental[0])) / mashup_sr} seconds).")
    mixed_main_sections = mixing.additive_mix(crop_vocal, main_sections_instrumental)
    
    # We may want to add the original instrumental intro of the song
    if adding_intros:
        # Extract intros
        intro_audios = [structure_utils.extract_intro_audio(t, mashup_bpm) for t in instrumental_tracks]
        # Pad and align the instrumental intros together
        padded_intro_audios = structure_utils.pad_and_align_intro_audios(intro_audios)
        # Mix intros together
        mixed_intros = mixing.additive_mix_instrumentals(padded_intro_audios)
    
        # Concatenate the instrumental intro and the main sections
        final_song = np.concatenate([mixed_intros, mixed_main_sections])

    else: # We start on the first downbeat of the song, and disregard potential intro
        final_song = mixed_main_sections

    # Normalize the mashup to the target loudness
    final_song = postprocessing.normalize_lufs(final_song, mashup_sr, target_loudness)

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