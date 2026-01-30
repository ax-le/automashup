import numpy as np
import copy
import pyrubberband as pyrb
import warnings

class Segment:

    transition_time = 0.5 # transition time in seconds

    def __init__(self, segment_dict):
        # We create a segment from a dict coming from metadata.
        # They look like this :
        # {
        #   "start": 0.4,
        #   "end": 22.82,
        #   "label": "verse"
        # }

        self._start = segment_dict["start"]
        self._end = segment_dict["end"]
        self.label = segment_dict["label"] # Doesn't need to be a property
        self._start_samples = None
        self._end_samples = None

        # We calculate the time in seconds for each segment
        self._duration = self._end - self._start
        self._duration_samples = None

        # Initialize track-associated attributes to None
        self.sr = None # Doesn't need to be a property
        self._key = None
        self._bpm = None
        self._downbeats = None
        self._downbeats_samples = None
        self.original_audio = None
        self.audio = None
        self.audio_was_modified = False # To use when modifications took place, notably bpm/key wise.

    # ==================== Properties ====================

    @property
    def start(self):
        """Start time of the segment in seconds."""
        return self._start

    @property
    def end(self):
        """End time of the segment in seconds."""
        return self._end

    @property
    def duration(self):
        """Duration of the segment in seconds."""
        return self._duration

    @property
    def start_samples(self):
        """Start position in samples (set via associate_track_info)."""
        return self._start_samples

    @property
    def end_samples(self):
        """End position in samples (set via associate_track_info)."""
        return self._end_samples

    @property
    def duration_samples(self):
        """Duration of the segment in samples (set via associate_track_info)."""
        return self._duration_samples

    @property
    def key(self):
        """Musical key of the segment (modifiable via set_key)."""
        return self._key

    @property
    def bpm(self):
        """BPM/tempo of the segment (modifiable via set_bpm)."""
        return self._bpm

    @property
    def downbeats(self):
        """Downbeats within this segment (set via associate_track_info)."""
        return self._downbeats

    @property
    def downbeats_samples(self):
        """Downbeats within this segment (set via associate_track_info)."""
        return self._downbeats_samples

    # ==================== Setter Methods ====================

    def set_start(self, new_start):
        """
        Set the start time for this segment.

        Args:
            new_start: The new start time in seconds.
        """
        assert new_start >= 0, "Start time must be non-negative."
        assert new_start < self._end, "Start time must be less than end time. Set end before if you need to."
        
        self._start = new_start
        self._duration = self._end - self._start

        # Update sample-based values only if sr is available
        if self.sr is not None:
            self._start_samples = int(self._start * self.sr)
            self._duration_samples = int(self._duration * self.sr)
        else:
            raise ValueError("Sample rate not set in segment object.")

    def set_end(self, new_end):
        """
        Set the end time for this segment.

        Args:
            new_end: The new end time in seconds.
        """
        self._end = new_end
        self._duration = self._end - self._start

        # Update sample-based values only if sr is available
        if self.sr is not None:
            self._end_samples = int(self._end * self.sr)
            self._duration_samples = int(self._duration * self.sr)
        else:
            raise ValueError("Sample rate not set in segment object.")

    def set_key(self, new_key, new_audio=None): # To be modified with the song.
        """
        Set the musical key for this segment.

        Args:
            new_key: The new musical key value.
        """
        self._key = new_key
        if new_audio is not None:
            self.audio = new_audio
        else:
            self.audio_was_modified = True
            self.audio = None

    def set_bpm(self, new_bpm, new_audio=None): #, recalculate_downbeats=False):
        """
        Set the BPM/tempo for this segment.

        Args:
            new_bpm: The new BPM value.
            recalculate_downbeats: If True, invalidate downbeats (they need recalculation).
        """
        raise NotImplementedError("Set BPM not implemented yet, as the modification of downbeats is not implemented yet.")
        self._bpm = new_bpm
        if new_audio is not None:
            self.audio = new_audio
        else:
            self.audio_was_modified = True
            self.audio = None

        # # When BPM changes, downbeats may no longer be valid
        # if recalculate_downbeats:
        #     self._downbeats = None  # Mark as invalid - requires recalculation
        # else:
        #     raise NotImplementedError("Recalculate downbeats not set. This is TODO.")

    def set_downbeats(self, new_downbeats):
        """
        Set the downbeats for this segment.

        Args:
            new_downbeats: The new downbeats for this segment.
        """
        if self.sr is None:
            raise ValueError("Sample rate not set. Call associate_track_info() first.")
        
        self._downbeats = np.array(new_downbeats) if type(new_downbeats) is list else new_downbeats
        self._downbeats_samples = np.array([
            int(db * self.sr) for db in self._downbeats
        ])

    # ==================== Methods ====================

    def associate_track_info(self, track):
        """
        Associate segment to a track, extracting audio and timing information.

        Core purpose:
        - Store sample rate for audio operations
        - Extract audio slice for this segment
        - Store downbeats within segment range (for tempo alignment)
        """
        self.sr = track.sr
        self._key = track.key  # Can be modified later via set_key()
        self._bpm = track.bpm  # Can be modified later via set_bpm()

        self._start_samples = int(self._start * self.sr)
        self._end_samples = int(self._end * self.sr)
        self._duration_samples = int(self._duration * self.sr)

        self.original_audio = track.audio[self._start_samples:self._end_samples]
        self.audio = self.original_audio.copy()

        # Store downbeats that fall within this segment (absolute times)
        # Used for downbeat-based tempo alignment in mashup_by_section
        last_i = 0
        db_to_add = []
        for i in range(len(track.downbeats)):
            if self._start <= track.downbeats[i] < self._end:
                db_to_add.append(track.downbeats[i])
                last_i = i
        try:
            db_to_add.append(track.downbeats[last_i+1]) # We add the first downbeat outside of the box, corresponding to the first beat of the next segment.
        except IndexError: # Probably the last one
            if last_i+1 != len(track.downbeats):
                raise ValueError(f"DEBUG: Last index {last_i+1} out of bounds for track {track.name} in downbeats {track.downbeats} of size {len(track.downbeats)}")
            if track.downbeats[-1] not in db_to_add:
                db_to_add.append(track.downbeats[-1])
        
        if db_to_add == [] or len(db_to_add) == 1:
            warnings.warn(f"Less than 2 downbeats found in segment {self} for track {track.name}, cannot make a bar.")
            self._downbeats = None
            self._downbeats_samples = None
        else:
            self._downbeats = np.array(db_to_add)
            self._downbeats_samples = np.array([
                int(db * self.sr) for db in self._downbeats
            ])

    def get_audio_segment(self, track=None):
        """
        Get the audio segment from the track.

        Args:
            track: The track to get the audio segment from.
        """
        if self.audio_was_modified:
            if track is None:
                raise ValueError("The audio was modified (bpm or key change), so you must provide the newly modified track.")
            return track.audio[self._start_samples:self._end_samples]
        else:
            if self.audio is None:
                raise ValueError("Audio not found. Call associate_track_info() first.")
            return self.audio

    def offset_segment(self, offset_time = None, offset_samples = None):
        """
        Offset the segment by a given number of samples.

        Args:
            offset_time: The number of seconds to offset the segment by.
            offset_samples: The number of samples to offset the segment by.
        """
        assert offset_time is not None or offset_samples is not None, "Offset time or samples must be provided."
        if offset_time is not None:
            offset_samples = int(offset_time * self.sr)
        else:
            offset_time = offset_samples / self.sr

        self.set_end(self._end + offset_time)
        self.set_start(self._start + offset_time)
        self.set_downbeats(np.array([db + offset_time for db in self._downbeats]))

    def get_audio_barwise(self, track=None):
        """
        Get the audio segments from the track, barwise (i.e. partioning the signal for each bar).

        Args:
            track: The track to get the audio segment from.
        """
        audio_segments = []
        offset_samples = self._start_samples
        audio = self.get_audio_segment(track)
        for i in range(len(self._downbeats_samples)-1):
            db_start_samples = self._downbeats_samples[i] # Starting the bar on a downbeat
            db_end_samples = self._downbeats_samples[i+1] # Ending the bar on the next downbeat
            audio_segments.append(audio[db_start_samples-offset_samples:db_end_samples-offset_samples]) # This is because the downbeats are absolute times, but the original audio is a slice of the track.
            # if self.audio_was_modified:
            #     if track is None:
            #         raise ValueError("The audio was modified (bpm or key change), so you must provide the newly modified track.")
            #     audio_segments.append(track.audio[db_start_samples:db_end_samples])
            # else:
            #     assert self.audio is not None, "Audio not found in segment object.."
            #     audio_segments.append(self.audio[db_start_samples-offset_samples:db_end_samples-offset_samples]) # This is because the downbeats are absolute times, but the original audio is a slice of the track.
        return audio_segments