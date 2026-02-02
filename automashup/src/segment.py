import numpy as np
import copy
import pyrubberband as pyrb
import warnings

import automashup.src.tempo_utils as tempo_utils
import automashup.src.duration_utils as duration_utils
import automashup.src.pitch_utils as pitch_utils

class Segment:

    def __repr__(self):
        return f"Segment(start={self._start}, end={self._end}, label={self.label})"

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

    @property
    def end(self):
        """End time of the segment in seconds."""
        return self._end

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
        self._key = track.key
        self._original_key = track.key # Store original key for reference
        self._bpm = track.bpm

        self._start_samples = int(self._start * self.sr)
        self._end_samples = int(self._end * self.sr)
        self._duration_samples = int(self._duration * self.sr)

        self.original_audio = track.audio[self._start_samples:self._end_samples]
        self.audio = self.original_audio.copy()

        # Store downbeats that fall within this segment (absolute times)
        db_to_add = self.get_downbeats_in_segment(track.downbeats)
        
        # If less than 2 downbeats found, we cannot make a bar. Hence, consider this section invalid.
        if db_to_add == [] or len(db_to_add) == 1:
            warnings.warn(f"Less than 2 downbeats found in segment {self} for track {track.name}, cannot make a bar. Setting downbeats to None.")
            self._downbeats = None
            self._downbeats_samples = None
        else: # If there are at least 2 downbeats, we can make a bar. Then, it's ok.
            self.set_downbeats(db_to_add)

    def time_stretch_this_section(self, ref_section, time_adapt_method='bpm'):
        """
        Time stretch the segment to match the tempo and duration of the reference section.
        No inplace modification of the segment, because a same segment can be used in multiple parts of the mashup,
        and each part can have a different tempo and duration. Hence, it may degenerates in cascade of errors.

        Args:
            ref_section: The reference section to match the tempo and duration of.
            time_adapt_method: The method to use for time stretching.
        """
        match time_adapt_method:
            case 'bpm':
                stretched_original_section_audio = tempo_utils.time_stretch_audio(
                    self.audio, # Use the current audio, because repitching concerns audio only.
                    self.sr, 
                    self.bpm,
                    ref_section.bpm
                )

                # Time stretch to match duration
                target_length_samples = ref_section.duration_samples
                return duration_utils.adapt_audio_duration(stretched_original_section_audio, target_length_samples, padding_type='repeat')
                
            case 'downbeats': # May sometimes be a problem if the downbeats that needs to be added slow or accelerate too much, but it's better than nothing
                audio_barwise = self.get_audio_barwise()
                if len(audio_barwise) == 0:
                    raise ValueError("Empty barwise audio. Should be catched earlier.")
                for a_bar in audio_barwise:
                    if len(a_bar) == 0:
                        raise ValueError("Empty barwise audio. Should be catched earlier.")
                return tempo_utils.time_stretch_to_match_downbeats(
                    audio_barwise, self.sr, ref_section.downbeats_samples
                )

            case _:
                raise ValueError(f"Unknown time adapt method: {time_adapt_method}")

    def repitch(self, new_key):
        """
        Repitch the track to a target key.
        
        Args:
            target_key: The desired key for the track.
        """
        # We repitch the original audio, not the current audio, because the current audio may have been repitched already.
        # This is important because the segment can be used multiple times in the mashup, and hence repitched multiple times.
        # Because repithcing alters the audio, we want to start from the original audio each time, instead of accumulating repitchings.
        self.audio = pitch_utils.repitch_audio_to_target(self.original_audio, self.sr, self._original_key, new_key)
        self._key = new_key

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

    def get_audio_barwise(self):
        """
        Get the audio segments from the track, barwise (i.e. partioning the signal for each bar).

        Args:
            track: The track to get the audio segment from.
        """
        audio_segments = []
        offset_samples = self._start_samples
        for i in range(len(self._downbeats_samples)-1):
            db_start_samples = self._downbeats_samples[i] # Starting the bar on a downbeat
            db_end_samples = self._downbeats_samples[i+1] # Ending the bar on the next downbeat

            # Add the audio, to account for repitching (which is inplace)
            # Don't store the results, because the segment can be used multiple times in the mashup.
            audio_to_add = self.audio[db_start_samples-offset_samples:db_end_samples-offset_samples]
            if audio_to_add.shape[0] != 0: # Do not add empty bars, if any
                audio_segments.append(audio_to_add)
        return audio_segments

    def get_downbeats_in_segment(self, downbeats):
        """
        Get the downbeats that fall within this segment.

        Args:
            downbeats: The downbeats to get the downbeats from.
        """
        # Used for downbeat-based tempo alignment in mashup_by_section
        last_i = 0 # local variable to also get the next downbeat, the first outside of this segment. (It ends the bar.)
        db_to_add = [] # list of downbeats to add
        for i in range(len(downbeats)): # parsing the downbeats
            if self._start <= downbeats[i] < self._end: # if the downbeat is within the segment
                db_to_add.append(downbeats[i])
                last_i = i
        try: # We add the first downbeat outside of the box, corresponding to the first beat of the next segment.
            db_to_add.append(downbeats[last_i+1])
        except IndexError: # Failed because it was (probably) the last segment, but try to catch it if it was not.
            if last_i+1 != len(downbeats): # If it was not the last segment, raise an error.
                raise ValueError(f"DEBUG: Index {last_i+1} out of bounds in downbeats {downbeats} of size {len(downbeats)}")
            if downbeats[-1] not in db_to_add: # If it was the last segment, add the last downbeat.
                db_to_add.append(downbeats[-1])
        return db_to_add