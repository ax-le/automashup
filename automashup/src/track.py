"""
Track module for representing musical tracks.

This module provides the Track class for handling audio data with metadata,
delegating specific functionality to utility modules.
"""

import json
import librosa

from automashup.src.segment import Segment
from automashup.src.pitch_utils import repitch_audio_to_target
from automashup.src.metronome_utils import add_metronome
import automashup.src.utils as utils

class Track:
    """
    Represents a musical track with audio data, metadata, and segments.
    
    The Track class keeps together the audio itself, the sampling frequency,
    and the metadata coming from allin1 analysis.
    """
    
    transition_time = 1  # transition time in seconds

    def __init__(self, track_name, instrument, audio, sr, bpm, beats, downbeats, key, segments, path, beat_positions):
        """
        Initialize a Track instance.
        
        Args:
            track_name: Name of the track.
            audio: Audio data as numpy array.
            metadata: Dictionary containing track metadata.
            sr: Sample rate of the audio.
        """
        self.name = track_name
        self.instrument = instrument
        self.audio = audio
        self.sr = sr
        self.segments = []
        self.bpm = bpm
        self.beats = beats
        self.downbeats = downbeats
        self.path = path
        self.beat_positions = beat_positions # Probably useless, but hey
        self.key = key

        if isinstance(segments[0], Segment): # To avoid an error in fuse_consecutive_sections, we convert the segments to dicts
            segments = utils.segments_as_dict(segments)

        segments = self.fuse_consecutive_sections(segments)

        # Load segments
        for seg_data in segments:
            segment = seg_data if isinstance(seg_data, Segment) else Segment(seg_data)
            segment.associate_track_info(self)
            self.segments.append(segment)

    # def repitch_track(self, target_key): # Should not be in the object I think
    #     """
    #     Repitch the track to a target key.
        
    #     Args:
    #         target_key: The desired key for the track.
    #     """
    #     self.audio = pitch_audio_to_target(
    #         self.audio, 
    #         self.sr, 
    #         self.key, 
    #         target_key
    #     )
    #     self.key = target_key

    def add_metronome(self, stored_data_path="."):
        """
        Add metronome sounds on the beats.
        
        Args:
            stored_data_path: Path to the directory containing metronome sounds.
        """
        self.audio = add_metronome(
            self.audio, 
            self.sr, 
            self.beats, 
            stored_data_path
        )

    def fuse_consecutive_sections(self, segments, start_after_first_downbeat=True):
        """
        Fuse consecutive segments that have the same label.
        
        Args:
            segments: List of segment objects with start, end, label attributes
        
        Returns:
            List of fused segment dicts with start, end, label
        """
        if not segments:
            raise ValueError("Empty list of segments provided")
        
        fused = []
        idx_first_seg_to_fuse = 0
        if start_after_first_downbeat:
            # Sometimes, some intro happens and is not fixed to the bar grid (ex: Never Gonna Give You Up, or My Own Summer - both start with a drum break).
            # We skip all segments that end before the first downbeat (generally one, but easy to extend to multiple if ever needed), and add them to the fused list.
            # If not handled, the first segment could consist of a fusing between an intro of less than a bar, and the first bar of the first section,
            # hence leading to a weird not bar-aligned first segment.
            while idx_first_seg_to_fuse < len(segments) and segments[idx_first_seg_to_fuse]['end'] <= self.downbeats[0]:
                fused.append(segments[idx_first_seg_to_fuse]) # We add the intro to the fused list, and continue with the next segment
                idx_first_seg_to_fuse += 1
        current = {'start': segments[idx_first_seg_to_fuse]['start'], 'end': segments[idx_first_seg_to_fuse]['end'], 'label': segments[idx_first_seg_to_fuse]['label']}
        
        for i in range(idx_first_seg_to_fuse + 1, len(segments)):
            seg = segments[i]
            if seg['label'] == current['label']:
                # Extend current segment
                current['end'] = seg['end']
            else:
                fused.append(current)
                current = {'start': seg['start'], 'end': seg['end'], 'label': seg['label']}
        
        # Append the last segment
        fused.append(current)
        return fused

    def get_segments_as_dict(self):
        return utils.segments_as_dict(self.segments)

    # def fit_phase(self, target_track):
    #     """
    #     Align track phases to a target track's structure.
        
    #     Args:
    #         target_track: Target Track object to align phases to.
    #     """
    #     print(f" ********************** Adjusting the song {self.name}  **********************")
    #     self.audio, self.beats, self.downbeats = fit_phase(
    #         self.segments, 
    #         self.sr, 
    #         target_track
    #     )

    # @staticmethod
    # def get_segments(track_name, stored_data_path="."):
    #     """
    #     Get a list of segment labels for a given song.
        
    #     Args:
    #         track_name: Name of the track.
    #         stored_data_path: Path to stored data directory.
            
    #     Returns:
    #         List of segment labels.
    #     """
    #     track = Track.track_from_song(track_name, 'entire', stored_data_path=stored_data_path)
    #     return [segment.label for segment in track.segments]

    # @staticmethod
    # def get_segments_full(track_name, stored_data_path="."):
    #     """
    #     Get full segment information for a given song.
        
    #     Args:
    #         track_name: Name of the track.
    #         stored_data_path: Path to stored data directory.
            
    #     Returns:
    #         List of dicts with start, end, and label for each segment.
    #     """
    #     track = Track.track_from_song(track_name, 'entire', stored_data_path=stored_data_path)
    #     return [{'start': segment.start, 'end': segment.end, 'label': segment.label} 
    #             for segment in track.segments]