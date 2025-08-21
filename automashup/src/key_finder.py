'''
Raw file extracted from https://pypi.org/project/pymusickit.

The original code is from 'https://github.com/jackmcarthur/musical-key-finder'
modified by: 'bin2ai' to be used as an installable package with pip

Imported by ax-le as a raw file because the original pip repo fixes an old version of librosa
and does not work with the 0.10 version of librosa, which is required by cocola.
'''

import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display

# class that uses the librosa library to analyze the key that an mp3 is in
# arguments:
#     waveform: an mp3 file loaded by librosa, ideally separated out from any percussive sources
#     sr: sampling rate of the mp3, which can be obtained when the file is read with librosa
#     tstart and tend: the range in seconds of the file to be analyzed; default to the beginning and end of file if not specified


class KeyFinder(object):

    filename: str = None  # path to mp3 file
    title: str = None  # title of song (defaults to filename if None)
    waveform: np.ndarray = None  # waveform of song
    duration: float = None  # song duration in seconds
    sr: int = None  # sampling rate
    t_start: int = None  # time in seconds
    t_end: int = None  # time in seconds
    s_start: int = None  # sample number
    s_end: int = None  # sample number
    y_segment: np.ndarray = None  # waveform of song segment
    chromograph: np.ndarray = None  # chroma graph of song segment
    chroma_vals: list = None  # amount of each pitch class present in this time interval
    keyfreqs: dict = None  # pitch names to the associated intensity in the song
    min_key_corrs: list = None  # correlations between pitch class vs minor keys
    maj_key_corrs: list = None  # correlations between pitch class vs major keys
    key_dict: dict = None    # dictionary of the musical keys (major/minor)
    key_primary: str = None  # key determined by the algorithm
    # strength of correlation for the key determined by the algorithm
    best_corr_primary: float = None
    key_alt: str = None  # alternative key determined by the algorithm
    best_corr_alt: float = None  # strength of correlation for the alternative key
    chroma_max: float = None  # maximum value of the chroma graph
    pitch_max: str = None  # pitch class with the highest intensity in the song segment
    pitch_max_corr: float = None  # strength of pitch class with the highest intensity
    pitches: list = None  # list of pitch classes
    # major key profile from Krumhansl-Schmuckler algorithm
    major_profile_ks: list = None
    # minor key profile from Krumhansl-Schmuckler algorithm
    minor_profile_ks: list = None

    def __init__(self,
                 file: str,  # path to mp3 file
                 title: str = None,  # title of song, if None, defaults to filename from path
                 t_start: int = None,  # time in seconds, if None, defaults to beginning of file
                 t_end: int = None  # time in seconds, if None, defaults to end of file
                 ) -> None:

        self.filename = file

        if title is None:
            self.title = file
        else:
            self.title = title

        self.waveform, self.sr = librosa.load(path=file, sr=None)
        self.duration = librosa.get_duration(y=self.waveform, sr=self.sr)

        self.waveform
        self.sr = self.sr

        self.t_start = t_start
        self.t_end = t_end

        if self.t_start is not None:
            self.s_start = librosa.time_to_samples(self.t_start, sr=self.sr)
        if self.t_end is not None:
            self.s_end = librosa.time_to_samples(self.t_end, sr=self.sr)
        self.y_segment = self.waveform[self.s_start:self.s_end]
        self.chromograph = librosa.feature.chroma_cqt(
            y=self.y_segment, sr=self.sr, bins_per_octave=24)

        # chroma_vals is the amount of each pitch class present in this time interval
        self.chroma_vals = []
        for i in range(12):
            self.chroma_vals.append(np.sum(self.chromograph[i]))
        self.pitches = ['C', 'C#', 'D', 'D#', 'E',
                        'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        # dictionary relating pitch names to the associated intensity in the song
        self.keyfreqs = {self.pitches[i]
            : self.chroma_vals[i] for i in range(12)}

        # list of musical keys (major/minor)
        keys = [
            self.pitches[i] + ' major' for i in range(12)] + [self.pitches[i] + ' minor' for i in range(12)]

        # use of the Krumhansl-Schmuckler key-finding algorithm, which compares the chroma
        # data above to typical profiles of major and minor keys:
        self.major_profile_ks = [6.35, 2.23, 3.48, 2.33, 4.38,
                                 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        self.minor_profile_ks = [6.33, 2.68, 3.52, 5.38, 2.60,
                                 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

        # finds correlations between the amount of each pitch class in the time interval and the above profiles,
        # starting on each of the 12 pitches. then creates dict of the musical keys (major/minor) to the correlation
        self.min_key_corrs = []
        self.maj_key_corrs = []
        for i in range(12):
            key_test = [self.keyfreqs.get(self.pitches[(i + m) % 12])
                        for m in range(12)]
            # correlation coefficients (strengths of correlation for each key)
            self.maj_key_corrs.append(
                round(np.corrcoef(self.major_profile_ks, key_test)[1, 0], 3))
            self.min_key_corrs.append(
                round(np.corrcoef(self.minor_profile_ks, key_test)[1, 0], 3))

        # names of all major and minor keys
        self.key_dict = {**{keys[i]: self.maj_key_corrs[i] for i in range(12)},
                         **{keys[i+12]: self.min_key_corrs[i] for i in range(12)}}

        # this attribute represents the key determined by the algorithm
        self.key_primary = max(self.key_dict, key=self.key_dict.get)
        self.best_corr_primary = max(self.key_dict.values())

        # this attribute represents the second-best key determined by the algorithm,
        # if the correlation is close to that of the actual key determined
        self.key_alt = None
        self.best_corr_alt = None

        best_corr_alt = 0
        for key, corr in self.key_dict.items():
            # if the correlation is close to the best correlation, but not the same,
            # if corr > self.best_corr_primary*0.9 and corr != self.best_corr_primary:
            #     self.key_alt = key
            #     self.best_corr_alt = corr
            # get the second best key
            if corr < self.best_corr_primary and corr >= best_corr_alt:
                self.key_alt = key
                best_corr_alt = corr
                self.best_corr_alt = best_corr_alt

        # done initializing

    # get primary key and correlation
    def get_primary_key_corr(self) -> tuple:
        return self.key_primary, self.best_corr_primary

    # get secondary key and correlation
    def get_secondary_key_corr(self) -> tuple:
        return self.key_alt, self.best_corr_alt

    # prints the relative prominence of each pitch class
    def print_chroma(self) -> None:
        self.chroma_max = max(self.chroma_vals)
        for key, chrom in self.keyfreqs.items():
            print(key, '\t', f'{chrom/self.chroma_max:5.3f}')

    # prints the correlation coefficients associated with each major/minor key
    def print_corr_table(self) -> None:
        for key, corr in self.key_dict.items():
            print(key, '\t', f'{corr:6.3f}')

    # printout of the key determined by the algorithm; if another key is close, that key is mentioned
    def print_key(self) -> None:
        print("likely key: ", max(self.key_dict, key=self.key_dict.get),
              ", correlation: ", self.best_corr_primary, sep='')
        if self.key_alt is not None:
            print("also possible: ", self.key_alt,
                  ", correlation: ", self.best_corr_alt, sep='')

    # prints a chromagram of the file, showing the intensity of each pitch class over time
    def show_chromagram(self, title: str = 'Chromagram') -> None:
        C = librosa.feature.chroma_cqt(
            y=self.waveform, sr=self.sr, bins_per_octave=24)
        plt.figure(figsize=(12, 4))
        librosa.display.specshow(
            C, sr=self.sr, x_axis='time', y_axis='chroma', vmin=0, vmax=1)
        if title is None:
            plt.title('Chromagram')
        else:
            plt.title(title)
        plt.colorbar()
        plt.tight_layout()
        plt.show()


# example usage:
if __name__ == '__main__':

    file = 'angry-birds-theme-song.mp3'
    song = KeyFinder(file)
    song.print_chroma()
    song.print_corr_table()
    song.print_key()
    song.show_chromagram()

    # print primary key and correlation
    print(song.get_primary_key_corr())
    # print secondary key and correlation
    print(song.get_secondary_key_corr())

    # for attr in dir(song):
    #     if not attr.startswith('_'):
    #         # if not an ndarray, or a list
    #         if not isinstance(getattr(song, attr), np.ndarray):
    #             print(attr, ':', getattr(song, attr))
