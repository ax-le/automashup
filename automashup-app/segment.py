import numpy as np
import copy
import pyrubberband as pyrb
from utils import closest_index

# Define a Track class to represent a part of a track
# The aim of this kind of object is to keep together the audio itself,
# and the beats

class Segment:

    transition_time = 0.5 # transition time in seconds

    def __init__(self, segment_dict):
        # We create a segment from a dict coming from metadata.
        # They look like this : 
        # {
        #   "start": 0.4,
        #   "end": 22.82,
        #   "label": "verse"
        # }
        

        for key in segment_dict.keys():
            setattr(self, key, segment_dict[key])

        # We calculate the time in minutes for each segment
        self.duration = (self.end - self.start)/60



    def link_track(self, track):
        # Function to link a segment to a track, must be set whenever
        # we create a segment
        # it loads all the pieces of information useful for a segment
        self.sr = track.sr
        beats = track.beats
        downbeats = track.downbeats
        
        
        start_beat = closest_index(self.start, beats)
        end_beat = closest_index(self.end, beats)

        self.beats = beats[start_beat:end_beat]

        if self.beats == []:
            self.downbeats = []
            self.audio = np.array([])
            self.left_transition = np.array([])
            self.right_transition = np.array([])

        else:
            # Make sure the first beat and downbeat starts on zero 
            self.beats = self.beats - np.repeat(self.beats[0], len(self.beats))

            self.downbeats = downbeats - np.repeat(downbeats[0], len(downbeats))
            self.downbeats = [downbeat for downbeat in self.downbeats if downbeat in self.beats]
            if self.downbeats != []:
                self.downbeats = self.downbeats - np.repeat(self.downbeats[0], len(self.downbeats))

            self.audio = track.audio[round(self.start*self.sr):round(self.end*self.sr)]

            if self.start - self.transition_time > 0 :
                self.left_transition = track.audio[round((self.start-self.transition_time)*self.sr):round(self.start*self.sr)]
            else :
                self.left_transition = track.audio[:round(self.start*self.sr)]
            if self.end + self.transition_time < len(track.audio) * self.sr:
                self.right_transition = track.audio[round(self.end*self.sr):round((self.end+self.transition_time)*self.sr)]
            else : 
                self.right_transition = track.audio[round(self.end*self.sr):]

    def concatenate(self):
        # Calculate the seconds to shift the incoming beats to start where the current segment's audio ends.
        offset = len(self.audio) / self.sr

        # Concatenate the beats array of the current segment
        new_beats = self.beats + offset
        self.beats = np.concatenate([self.beats, new_beats])

        # Concatenate the downbeats array
        new_downbeats = self.downbeats + offset
        self.downbeats = np.concatenate([self.downbeats, new_downbeats])

        # Concatenate the audio data of the two segments
        self.audio = np.concatenate((self.audio, self.audio))


    def get_audio_beat_fitted(self, beat_number, tempo, duration, sr):
        """
        Adjusts the audio segment to fit a specified number of beats at a given tempo.

        Parameters:
        - beat_number: The target number of beats for the segment.
        - tempo: The target tempo (BPM) for the segment.
        - duration: The target segment duration 

        Returns:
        - A new audio segment adjusted to the specified number of beats and tempo.
        """
        try:
            # Make a deep copy of the segment to avoid modifying the original
            result = copy.deepcopy(self)

            if beat_number == 0:
                # If beat_number is 0, return an empty segment
                result.audio = np.array([])
                result.beats = []
                result.downbeats = []
            else:
                # We compare the bpm of the target segment and the current segment. 
                # If the difference is too big, half or double it
                segment_bpm =(len(result.beats)/result.duration)
                if tempo / segment_bpm > 1.5:
                    tempo /= 2
                    beat_number //= 2
                    # If we reduce the bpm to half, then the amount of beats as well so the duration stays the same
                elif tempo / segment_bpm < 0.75:
                    tempo *= 2
                    beat_number //= 2
                else:
                    pass

                # We calculate the rate of stretch for the segment.
                stretch_rate = tempo / segment_bpm
                result.audio = pyrb.time_stretch(result.audio, sr, rate=stretch_rate)

                # We concatenate the segment to itself if it's shorter than the target
                while len(result.beats) < beat_number:
                    print(f"Concatenating for segment '{result.label}'")
                    result.concatenate()

                # Then we cut the amount of beats and downbeats so they end at the same time
                result.beats = result.beats[:beat_number]
                result.downbeats = [downbeat for downbeat in result.downbeats if downbeat <= result.beats[-1]]

                # Then we cut the audio for the same length as the objetive
                result.audio = result.audio[:duration]

            return result

        except Exception as e:
            # Handle any exceptions gracefully and print detailed error message
            print(f"Error fitting segment '{self.label}' to {beat_number} beats: {e}")
            raise e  # or return None or handle the error appropriately