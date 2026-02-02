"""
Track module for representing musical tracks.

This module provides the Track class for handling audio data with metadata,
delegating specific functionality to utility modules.
"""

import json
import librosa

from automashup.src.segment import Segment
import automashup.src.utils as utils
import automashup.src.pitch_utils as pitch_utils
import automashup.src.tempo_utils as tempo_utils
import automashup.src.metronome_utils as metronome_utils

class Track:
    """
    Represents a musical track with audio data and metadata.
    
    The Track class keeps together the audio itself, the sampling rate,
    and metadata about the track (bpm, key, segments, etc.).
    """
    
    # Song contructor and info
    def __repr__(self):
        return f"Track(name={self.name}, instrument={self.instrument}, sr={self.sr}, bpm={self.bpm}, key={self.key})"

    def __init__(self, track_name, instrument, audio, sr, bpm, beats, downbeats, key, segments, path):
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
        self._audio = audio
        self._sr = sr
        self._segments = []
        self._bpm = bpm
        self._beats = beats
        self._downbeats = downbeats
        self.path = path
        self._key = key

        if isinstance(segments[0], Segment): # To avoid an error in fuse_consecutive_sections, we convert the segments to dicts
            segments = utils.segments_as_dict(segments)

        segments = self.fuse_consecutive_sections(segments)

        # Load segments
        for seg_data in segments:
            segment = seg_data if isinstance(seg_data, Segment) else Segment(seg_data)
            segment.associate_track_info(self)
            self._segments.append(segment)

    # Getters and setters
    @property
    def audio(self):
        """Get the audio data."""
        return self._audio
    
    @audio.setter
    def audio(self, value):
        """Set the audio data."""
        self._audio = value

    @property
    def sr(self):
        """Get the sample rate."""
        return self._sr        

    @property
    def bpm(self):
        """Get the beats per minute."""
        return self._bpm

    @property
    def beats(self):
        """Get the beat timestamps."""
        return self._beats

    @property
    def downbeats(self):
        """Get the downbeat timestamps."""
        return self._downbeats

    @property
    def key(self):
        """Get the musical key."""
        return self._key

    @property
    def segments(self):
        """Get the segments."""
        return self._segments

    @segments.setter
    def segments(self, value):
        """Set the segments."""
        self._segments = value

    def get_segments_as_dict(self):
        """
        Return the segments as a list of dictionaries.
        
        Returns:
            List of segment dictionaries with start, end, label attributes
        """
        return utils.segments_as_dict(self.segments)

    # Track manipulation methods
    def repitch(self, new_key):
        """
        Repitch the track to a target key.
        
        Args:
            target_key: The desired key for the track.
        """
        self.audio = pitch_utils.repitch_audio_to_target(self.audio, self.sr, self.key, new_key)
        self._key = new_key

    def resample(self, new_sr):
        """
        Resample the track to a target sample rate.
        
        Args:
            new_sr: The desired sample rate for the track.
        """
        self.audio = librosa.resample(self.audio, orig_sr=self.sr, target_sr=new_sr)
        self._sr = new_sr

    def change_tempo(self, new_tempo):
        """
        Change the tempo of the track.
        
        Args:
            new_tempo: The desired tempo for the track.
        """
        self.audio = tempo_utils.time_stretch_audio(self.audio, self.sr, self.bpm, new_tempo)
        self._bpm = new_tempo

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

    def add_metronome(self, metronome_sound_path="/data/audio/metronome-sounds"):
        """
        Add metronome sounds on the beats.
        
        Args:
            metronome_sound_path: Path to the directory containing metronome sounds.
        """
        self.audio = metronome_utils.add_metronome(
            self.audio, 
            self.sr, 
            self.beats, 
            metronome_sound_path
        )