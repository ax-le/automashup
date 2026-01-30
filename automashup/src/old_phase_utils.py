"""
Phase fitting utilities for audio processing.

This module provides functions for aligning track phases (verse, chorus, bridge, etc.)
"""

import numpy as np


def fit_phase(source_segments, source_sr, target_track):
    """
    Align source track phases to a target track's structure.
    
    This function loops and stretches segments to match the target track's
    phase structure, keeping beats and downbeats updated.
    
    Args:
        source_segments: List of Segment objects from the source track.
        source_sr: Sample rate of the source track.
        target_track: Target Track object to align phases to.
        
    Returns:
        Tuple of (audio, beats, downbeats) for the fitted track.
    """
    audio = np.array([])
    
    # Lists for return track beats and downbeats
    # We put 0 for convenience (see beats[-1] after)
    beats = [0]
    downbeats = [0]

    # List of already found segments
    found_segments = {}

    # Loop over each phase to reproduce
    for target_segment in target_track.segments:
        i = 0
        found_segment = False
        current_label = target_segment.label

        # Check if we have already found this label before
        if current_label in found_segments:
            start_index = found_segments[current_label] + 1
        else:
            start_index = 0

        i = start_index

        # Loop over each segment to find occurrences
        while i < len(source_segments):
            segment = source_segments[i]
            if segment.label == current_label:
                # If this is the first time we find the label or we have moved past the previous index
                if not found_segment or i > found_segments[current_label]:
                    found_segment = True
                    tempo = round(len(segment.beats) / segment.duration)
                    found_segments[current_label] = i
                    break
            i += 1

        # If no segment was found, reuse the last found segment
        if not found_segment and current_label in found_segments:
            last_found_index = found_segments[current_label]
            segment = source_segments[last_found_index]
            tempo = round(len(segment.beats) / segment.duration)
            found_segment = True

        # If we do not find it, we add zeros with the right length
        if not found_segment:
            tempo = round(len(target_segment.beats) / target_segment.duration)
            try:
                if tempo == 0:
                    segment_length = 0
                else:
                    segment_length = int((len(target_segment.beats) / (tempo / 60) * source_sr))
                audio = np.concatenate([audio, np.zeros(segment_length)])
                beats += [beats[-1] + (i + 1) / (tempo / 60) for i in range(len(target_segment.beats))]
                downbeats += [downbeats[-1] + (4 * i + 1) / (tempo / 60) for i in range(len(target_segment.beats) // 4)]
            except Exception as e:
                print(f"Error fitting silence. Error: {e}")
        else:
            try:
                # If we find it, we make it fit to the desired beat number
                if len(target_segment.beats) > 0:
                    target_bpm = len(target_segment.beats) / target_segment.duration

                    segment_fitted = segment.get_audio_beat_fitted(
                        len(target_segment.beats), 
                        target_bpm, 
                        len(target_segment.audio), 
                        source_sr
                    )
                    audio = np.concatenate([audio, segment_fitted.audio])

                    # Reset first beat position per segment
                    track_sr = target_track.sr
                    track_beginning_temporal = target_segment.beats[0]
                    track_beginning = track_beginning_temporal * track_sr
                    # Reset first beat position
                    audio = np.array(audio)[round(track_beginning):]

                    # We add the new beats to be able to sync after
                    beats += [beats[-1] + phase_beat for phase_beat in segment_fitted.beats]
                    downbeats += [downbeats[-1] + phase_downbeat for phase_downbeat in segment_fitted.downbeats]
                # If it's empty we ignore it
                else:
                    pass

            except Exception as e:
                print(f"Error fitting segment: {segment.label} at {segment.start}, Error: {e}")
                continue

    # We get rid of the first beats added for convenience
    beats = beats[1:]
    downbeats = downbeats[1:]

    return audio, beats, downbeats
