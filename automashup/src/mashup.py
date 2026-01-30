from automashup.src.track import Track
import automashup.src.tempo_utils as tempo_utils
import automashup.src.duration_utils as duration_utils
import automashup.src.pitch_utils as pitch_utils
import automashup.src.structure_utils as structure_utils
import automashup.src.mixing as mixing
import automashup.src.postprocessing as postprocessing
import automashup.src.concatenate as concatenate
import librosa
import numpy as np
import warnings

# Mashup Technics
# In this file, you may add mashup technics
# the input of such a method is a list of up to 4 objects of type Track. 
# You can modify them without making any copy, it's already done before.
# You may find useful methods in the track.py file
# Be sure to return a Track object

# %% Vanilla mashup (just bpm adjustment)
def mashup_technic(vocal_track, instrumental_tracks, target_loudness=-14.0, save_folder_path=None, repitch = None):
    """
    Vanilla mashup technic with first downbeat alignment and bpm sync
    
    Args:
        vocal_track: Vocal track object
        instrumental_tracks: List of instrumental track objects
        target_loudness: Target loudness in LUFS
        save_folder_path: Path to save the mashup
        repitch: track on which to repitch the instrumental tracks
    
    Returns:
        Track object
    """
    # Mashup technic with first downbeat alignment and bpm sync
    mashup_sr = vocal_track.sr
    mashup_bpm = vocal_track.bpm # The vocal track is used to determine the target bpm
    mashup_beats = vocal_track.beats # The vocal track is used to determine the target beats
    mashup_downbeats = vocal_track.downbeats # The vocal track is used to determine the target downbeats
    match repitch:
        case None:
            mashup_key = None
            add_to_save_name = "no_repitch"
        case 'vocals_to_instrumental':
            mashup_key = instrumental_tracks[0].key
            if mashup_key != vocal_track.key: # We save computation time if the key is already the same.
                vocal_track.audio = pitch_utils.repitch_audio_to_target(vocal_track.audio, vocal_track.sr, vocal_track.key, mashup_key)
                vocal_track.key = mashup_key
            add_to_save_name = "repitch_vocals_to_instrumental"
        case 'instrumental_to_vocals':
            mashup_key = vocal_track.key
            for track in instrumental_tracks:
                if track.instrument != 'drums': # Don't repitch drums
                    if track.key != mashup_key: # We save computation time if the key is already the same.
                        track.audio = pitch_utils.repitch_audio_to_target(track.audio, track.sr, track.key, mashup_key)
                        track.key = mashup_key
            add_to_save_name = "repitch_instrumental_to_vocals"
        case _:
            raise ValueError(f"Invalid repitch value: {repitch}")

    mashup_name = f"{vocal_track.name} - {instrumental_tracks[0].name}"

    # Create a dummy track to store the mashup
    mashup = Track(mashup_name, 'mashup', np.zeros(1), mashup_sr, mashup_bpm, mashup_beats, mashup_downbeats, mashup_key, vocal_track.get_segments_as_dict(), path=None, beat_positions=vocal_track.beat_positions)

    # Starting the song on the first downbeat
    beginning_instant = vocal_track.downbeats[0]
    beginning_frame = beginning_instant * mashup_sr
    crop_vocal = vocal_track.audio[int(beginning_frame):]

    # Adding each track to the mashup
    inst_tracks_audio = []
    for track in instrumental_tracks:
        track_tempo = track.bpm
        track_sr = track.sr
        track_beginning = track.downbeats[0] * track_sr
        track_audio = track.audio[int(track_beginning):]
        if track_sr != mashup_sr:
            track_audio = librosa.resample(track_audio, orig_sr=track_sr, target_sr=mashup_sr)
            track_sr = mashup_sr

        # Change the bpm
        track_audio_accelerated =  tempo_utils.accelerate_audio(track_audio, track_sr, track_tempo, mashup_bpm)
        inst_tracks_audio.append(track_audio_accelerated)

    mashup.audio = mixing.additive_mix(crop_vocal, inst_tracks_audio)

    # Normalize the mashup to the target loudness (-14 LUFS by deafult)
    mashup.audio = postprocessing.normalize_lufs(mashup.audio, mashup_sr, target_lufs=target_loudness)

    if save_folder_path:
        # Save audio
        mashup.path = postprocessing.save_song(mashup.audio, mashup.sr, save_folder_path, mashup.name, add_name=add_to_save_name)

    return mashup

# ============================================================================
# Section-Based Mashup Functions
# ============================================================================

def mashup_by_section(vocal_track, instrumental_tracks, target_loudness=-14.0, time_adapt_method='bpm', adding_intros=True, save_folder_path=None, repitch = None):
    """
    Create a mashup by aligning sections of instrumental tracks to the vocal structure.
    
    Aligns vocal and instrumental tracks on their respective first downbeats.
    Extracts instrumental intros (before first downbeat) and prepends them to the mix.
    """
    # Mashup technic with first downbeat alignment and bpm sync
    mashup_sr = vocal_track.sr
    mashup_bpm = vocal_track.bpm # The vocal track is used to determine the target bpm
    mashup_beats = vocal_track.beats # The vocal track is used to determine the target beats
    mashup_downbeats = vocal_track.downbeats # The vocal track is used to determine the target downbeats

    mashup_name = f"{vocal_track.name} - {instrumental_tracks[0].name}"

    match repitch:
        case None:
            mashup_key = None
            add_to_save_name = "no_repitch"
        case 'vocals_to_instrumental':
            raise NotImplementedError("Only instrumental to vocals repitching is implemented yet, because the section adaptation is only implemented for instrumental tracks.")
        case 'instrumental_to_vocals':
            mashup_key = vocal_track.key # Actually, does not matter since we repitch to the section key. Maybe the key attribute should be set section-wise?
            add_to_save_name = "repitch_instrumental_to_vocals"
        case _:
            raise ValueError(f"Invalid repitch value: {repitch}")

    # Create a dummy track to store the mashup
    mashup = Track(mashup_name, 'mashup_by_section', np.zeros(1), mashup_sr, mashup_bpm, mashup_beats, mashup_downbeats, mashup_key, vocal_track.get_segments_as_dict(), path=None, beat_positions=vocal_track.beat_positions)

    # Collect adapted instrumental sections for each vocal segment
    instrumental_audio_sections = [[] for _ in instrumental_tracks]
    label_counts = [{} for _ in instrumental_tracks]

    vocal_first_downbeat = vocal_track.downbeats[0]
    
    # Filter vocal segments to only those starting at or after the first downbeat
    vocal_segments_after_downbeat = [
        seg for seg in vocal_track.segments if seg.end >= vocal_first_downbeat
    ]

    if time_adapt_method == 'bpm':
        start_song = vocal_segments_after_downbeat[0].start_samples # Should it be on the first downbeat?
    elif time_adapt_method == 'downbeats':
        start_song = vocal_segments_after_downbeat[0].downbeats_samples[0]
    # Crop vocal to the start of the song
    crop_vocal = vocal_track.audio[int(start_song):]

    for section in vocal_segments_after_downbeat:
        for i, inst_track in enumerate(instrumental_tracks):
            # Get the number of times this label has appeared in the instrumental track so far
            current_index_before_increment = label_counts[i].get(section.label, 0)
            # Adapt the instrumental section to the vocal section
            inst_audio_aligned, current_index_after_increment = structure_utils.adapt_this_instrumental_section(
                section, inst_track, current_index_before_increment, time_adapt_method=time_adapt_method
            )
            if inst_audio_aligned is None:
                warnings.warn(f"Skipping an entire empty section: {section.label} for instrumental track {inst_track.name}")
                continue
            # Repitch the instrumental section to the vocal section
            if repitch == 'instrumental_to_vocals' and inst_track.key != section.key and inst_track.instrument != 'drums':
                inst_audio_aligned = pitch_utils.repitch_audio_to_target(inst_audio_aligned, inst_track.sr, inst_track.key, section.key) # Repitching to the section. As of now, it is only the same as the vocal track key, but could be adapted in the future.
            # Append the adapted instrumental section to the list of instrumental sections
            instrumental_audio_sections[i].append(inst_audio_aligned)
            # Update the number of times this label has appeared in the instrumental track. May have not changed if the label was not found
            label_counts[i][section.label] = current_index_after_increment

    # Concatenate main sections
    main_sections_instrumental = [concatenate.concatenate_sections(s) for s in instrumental_audio_sections]

    # Mix main sections
    if len(crop_vocal) != len(main_sections_instrumental[0]):
        warnings.warn(f"Length mismatch between vocal final main section ({len(crop_vocal)}) and instrumental final main sections ({len(main_sections_instrumental[0])}). Not a problem if both lengths are close, may be if they are too different (gap: {abs(len(crop_vocal) - len(main_sections_instrumental[0]))} samples, i.e. {abs(len(crop_vocal) - len(main_sections_instrumental[0])) / mashup_sr} seconds).")
    mixed_main_sections = mixing.additive_mix(crop_vocal, main_sections_instrumental)
    
    if adding_intros: # We want to add the instrumental intro of the song
        # Extract intros and concatenate main sections
        intro_audios = [structure_utils.extract_intro_audio(t, mashup_bpm) for t in instrumental_tracks]
        padded_intro_audios = structure_utils.pad_and_align_intro_audios(intro_audios)
        mixed_intros = mixing.additive_mix_instrumentals(padded_intro_audios)
    
        # Concatenate intros and main sections
        final_song = np.concatenate([mixed_intros, mixed_main_sections])

    else: # We start on the first downbeat of the song, and disregard potential intro
        final_song = mixed_main_sections

    # Normalize the mashup to the target loudness
    final_song = postprocessing.normalize_lufs(final_song, mashup_sr, target_loudness)

    mashup.audio = final_song

    if save_folder_path:
        # Save audio
        mashup.path = postprocessing.save_song(mashup.audio, mashup.sr, save_folder_path, mashup.name, add_name=add_to_save_name)

    return mashup