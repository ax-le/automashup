import json
import librosa
import numpy as np
import pyrubberband as pyrb

from utils import note_to_frequency, calculate_pitch_shift, get_path,\
      increase_array_size
from segment import *


# Define a Track class to represent a musical track
# This class uses objects of type Segment
# The aim of this kind of object is to keep together the audio itself,
# the sampling frequency and the metadata coming from allin1 analysis

class Track:
    transition_time = 1 # transition time in seconds

    # Standard constructor
    def __init__(self, track_name, audio, metadata, sr):

        # Initialize track properties
        self.name = track_name
        self.audio = audio
        self.sr = sr
        self.segments = []

        # Load track metadatas
        for key in metadata.keys():
            if key!="segments":
                setattr(self, key, metadata[key])
            else:
                for segment in metadata["segments"]:
                    # Create segment objects
                    if isinstance(segment, Segment):
                        segment_ = segment
                    else:
                        # we handle the segments as stored in the struct files
                        segment_ = Segment(segment)
                    segment_.link_track(self)
                    self.segments.append(segment_)


    def track_from_song(track_name, type):
        # Function to create a track from a preprocessed song
        # type should be one of the following : 
        # 'entire', 'bass', 'drums', 'vocals', 'other'       
        name = track_name + ' - ' + type
        audio, sr = librosa.load(get_path(track_name, type), sr=None)
        struct_path = f"./struct/{track_name}.json"
        with open(struct_path, 'r') as file:
            metadata = json.load(file)
        return Track(name, audio, metadata, sr)

        
    def get_key(self):
        # Function to retrieve the key of a track
        # we use the "key" metadata which is a list of correlation
        # with each key. We look for the max correlation to get the 
        # right key
        best_key, best_score = "", ""
        for key, score in self.key.items():
            if best_score=="" or best_score<score:
                best_key, best_score = key, score
        return best_key


    def __repitch(self, semitone_shift):
        # Function to repitch a track using a semitone shift
        # https://www.youtube.com/watch?v=Y2lUmwB7lzI
        shifted_audio = pyrb.pitch_shift(y=self.audio, sr=self.sr, n_steps=semitone_shift)
        self.audio = shifted_audio


    def pitch_track(self, target_key):
        # Function to repitch a track to a target key
        target_frequency = note_to_frequency(target_key)
        track_frequency = note_to_frequency(self.get_key())
        self.__repitch(calculate_pitch_shift(track_frequency, target_frequency))


    def add_metronome(self):
        # Function to add metronome sounds on the beats according
        # to the metadata of the track
        # sounds
        downbeat_sound_audio, _ = librosa.load("../metronome-sounds/block.mp3")
        otherbeat_sound_audio, _ = librosa.load("../metronome-sounds/drumstick.mp3")

        # add sound for each beat
        for i, beat_frame in enumerate(self.beats):
            # if it's a downbeat, use the according sound
            clic_sound = downbeat_sound_audio if i % 4 == 0 else otherbeat_sound_audio
            clic = increase_array_size(clic_sound, len(self.audio[round(self.sr*beat_frame):]))
            # check that we do not get out of the track's bounds
            if len(self.audio[round(self.sr*beat_frame):])>=len(clic):
                self.audio[round(self.sr*beat_frame):] += clic


    def fit_phase(self, target_track):
        # Function to align track phases (verse, chorus, bridge, ...)
        # to a target track.
        # we'll do loops on the track to reach the number of beats targetted
        # for each phase
        # The challenge for this function is to keep the beats metadata
        # updated
        audio = np.array([])

        # lists of the return track beats and downbeats
        # we put 0 for convenience (see beats[-1] after)
        beats = [0]
        downbeats = [0]


        print(f" ********************** Adjusting the song {self.name}  **********************")

        # List of already found segments
        found_segments = {}

        # loop over each phase to reproduce
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

            # loop over each segment to find occurrences
            while i < len(self.segments):
                segment = self.segments[i]
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
                segment = self.segments[last_found_index]
                tempo = round(len(segment.beats) / segment.duration)
                found_segment = True

            # if we do not find it, we add zeros with the right length
            if (not found_segment):
                tempo = round(len(target_segment.beats)/target_segment.duration)
                try:
                    if tempo == 0:
                        segment_length = 0
                    else:
                        segment_length = int((len(target_segment.beats) / (tempo / 60) * self.sr))
                    audio = np.concatenate([audio, np.zeros(segment_length)])
                    beats += [beats[-1] + (i + 1) / (tempo / 60) for i in range(len(target_segment.beats))]
                    downbeats += [downbeats[-1] + (4 * i + 1) / (tempo / 60) for i in range(len(target_segment.beats) // 4)]
                except Exception as e:
                    print(f"Error fitting silence. Error: {e}")
            else:
                try:
                    # if we find it, we make it fit to the desired beat number
                    if len(target_segment.beats) > 0:
                        target_bpm = len(target_segment.beats)/target_segment.duration

                        segment_fitted = segment.get_audio_beat_fitted(len(target_segment.beats), target_bpm, len(target_segment.audio), self.sr)
                        audio = np.concatenate([audio, segment_fitted.audio])

                        # reset first beat position per segment
                        track_sr = target_track.sr
                        track_beginning_temporal = target_segment.beats[0]
                        track_beginning = track_beginning_temporal * track_sr
                        # reset first beat position
                        audio = np.array(audio)[round(track_beginning):] 

                        # we add the new beats to be able to sync after
                        beats += [beats[-1] + phase_beat for phase_beat in segment_fitted.beats]
                        downbeats += [downbeats[-1] + phase_downbeat for phase_downbeat in segment_fitted.downbeats]
                    # If its empty we ignore it
                    else: pass

                except Exception as e:
                    print(f"Error fitting segment: {segment.label} at {segment.start}, Error: {e}")
                    continue

        # we get rid of the first beats added for convenience
        beats = beats[1:]
        downbeats = downbeats[1:]

        self.audio = audio
        self.beats = beats
        self.downbeats = downbeats

    def get_segments(track_name):
        # This method should return a list of segments for the given song
        track = Track.track_from_song(track_name, 'entire')
        return [segment.label for segment in track.segments]
    
    def get_segments_full(track_name):
        # This method should return a list of the structure of segments for the given song
        track = Track.track_from_song(track_name, 'entire')
        return [{'start': segment.start, 'end': segment.end, 'label': segment.label} for segment in track.segments]