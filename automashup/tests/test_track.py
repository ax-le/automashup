import unittest
import sys
sys.path.insert(0, '..')

from automashup.src.track import Track


class TestFuseConsecutiveSections(unittest.TestCase):
    """Tests for the Track.fuse_consecutive_sections method."""
    
    def setUp(self):
        """Set up a mock Track instance for testing."""
        # Create a minimal Track instance (we only need the method, not full initialization)
        # We'll call the method directly with test data
        self.track = None  # We'll use Track.fuse_consecutive_sections as a static-like method
    
    def test_basic_fusion_same_labels(self):
        """Test fusing consecutive segments with the same label."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
            {'start': 20.0, 'end': 30.0, 'label': 'chorus'},
        ]
        
        # Create a dummy track just to call the method
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {'start': 0.0, 'end': 20.0, 'label': 'verse'})
        self.assertEqual(result[1], {'start': 20.0, 'end': 30.0, 'label': 'chorus'})
    
    def test_no_fusion_different_labels(self):
        """Test when no segments have consecutive same labels."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'intro'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
            {'start': 20.0, 'end': 30.0, 'label': 'chorus'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result, segments)
    
    def test_multiple_fusions(self):
        """Test multiple groups of consecutive same-label segments."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
            {'start': 20.0, 'end': 30.0, 'label': 'chorus'},
            {'start': 30.0, 'end': 40.0, 'label': 'chorus'},
            {'start': 40.0, 'end': 50.0, 'label': 'verse'},
            {'start': 50.0, 'end': 60.0, 'label': 'verse'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], {'start': 0.0, 'end': 20.0, 'label': 'verse'})
        self.assertEqual(result[1], {'start': 20.0, 'end': 40.0, 'label': 'chorus'})
        self.assertEqual(result[2], {'start': 40.0, 'end': 60.0, 'label': 'verse'})
    
    def test_single_segment(self):
        """Test with a single segment (no fusion possible)."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'intro'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], segments[0])
    
    def test_all_same_label(self):
        """Test when all segments have the same label."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
            {'start': 20.0, 'end': 30.0, 'label': 'verse'},
            {'start': 30.0, 'end': 40.0, 'label': 'verse'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {'start': 0.0, 'end': 40.0, 'label': 'verse'})
    
    def test_empty_segments_raises_error(self):
        """Test that empty segment list raises ValueError."""
        segments = []
        
        track = self._create_dummy_track()
        with self.assertRaises(ValueError) as context:
            track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertIn("Empty list of segments", str(context.exception))
    
    def test_skip_intro_before_first_downbeat(self):
        """Test skipping intro segments that end before the first downbeat."""
        segments = [
            {'start': 0.0, 'end': 0.5, 'label': 'intro'},  # Ends before first downbeat
            {'start': 0.5, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
            {'start': 20.0, 'end': 30.0, 'label': 'chorus'},
        ]
        
        track = self._create_dummy_track(first_downbeat=1.0)
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=True)
        
        # Intro should be kept separate, verses should be fused
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], {'start': 0.0, 'end': 0.5, 'label': 'intro'})
        self.assertEqual(result[1], {'start': 0.5, 'end': 20.0, 'label': 'verse'})
        self.assertEqual(result[2], {'start': 20.0, 'end': 30.0, 'label': 'chorus'})
    
    def test_multiple_intros_before_first_downbeat_no_fuse(self):
        """Test skipping multiple intro segments before first downbeat."""
        segments = [
            {'start': 0.0, 'end': 0.3, 'label': 'intro'},
            {'start': 0.3, 'end': 0.8, 'label': 'intro'},
            {'start': 0.8, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
        ]
        
        track = self._create_dummy_track(first_downbeat=1.0)
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=True)
        
        # Both intro segments should be kept, verses fused
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], {'start': 0.0, 'end': 0.3, 'label': 'intro'})
        self.assertEqual(result[1], {'start': 0.3, 'end': 0.8, 'label': 'intro'})
        self.assertEqual(result[2], {'start': 0.8, 'end': 20.0, 'label': 'verse'})

    def test_multiple_intros_before_first_downbeat_fuse(self):
        """Test fusing multiple intro segments after first downbeat."""
        segments = [
            {'start': 0.0, 'end': 0.3, 'label': 'intro'},
            {'start': 0.3, 'end': 0.8, 'label': 'intro'},
            {'start': 0.8, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
        ]
        
        track = self._create_dummy_track(first_downbeat=0.2)
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=True)

        # Both intro segments should be kept, verses fused
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {'start': 0.0, 'end': 0.8, 'label': 'intro'})
        self.assertEqual(result[1], {'start': 0.8, 'end': 20.0, 'label': 'verse'})
    
    def test_no_intro_all_after_first_downbeat(self):
        """Test when all segments start after the first downbeat."""
        segments = [
            {'start': 2.0, 'end': 10.0, 'label': 'verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},
            {'start': 20.0, 'end': 30.0, 'label': 'chorus'},
        ]
        
        track = self._create_dummy_track(first_downbeat=1.0)
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=True)
        
        # All verses should be fused
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {'start': 2.0, 'end': 20.0, 'label': 'verse'})
        self.assertEqual(result[1], {'start': 20.0, 'end': 30.0, 'label': 'chorus'})
    
    def test_preserves_segment_boundaries(self):
        """Test that start/end times are preserved correctly during fusion."""
        segments = [
            {'start': 1.5, 'end': 8.3, 'label': 'verse'},
            {'start': 8.3, 'end': 15.7, 'label': 'verse'},
            {'start': 15.7, 'end': 22.1, 'label': 'chorus'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 2)
        # Should preserve first start and last end of fused segments
        self.assertEqual(result[0]['start'], 1.5)
        self.assertEqual(result[0]['end'], 15.7)
        self.assertEqual(result[1]['start'], 15.7)
        self.assertEqual(result[1]['end'], 22.1)
    
    def test_case_sensitive_labels(self):
        """Test that label matching is case-sensitive."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'Verse'},
            {'start': 10.0, 'end': 20.0, 'label': 'verse'},  # Different case
            {'start': 20.0, 'end': 30.0, 'label': 'verse'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        # 'Verse' and 'verse' should not be fused
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {'start': 0.0, 'end': 10.0, 'label': 'Verse'})
        self.assertEqual(result[1], {'start': 10.0, 'end': 30.0, 'label': 'verse'})
    
    def test_alternating_labels(self):
        """Test with alternating labels (no fusion should occur)."""
        segments = [
            {'start': 0.0, 'end': 10.0, 'label': 'A'},
            {'start': 10.0, 'end': 20.0, 'label': 'B'},
            {'start': 20.0, 'end': 30.0, 'label': 'A'},
            {'start': 30.0, 'end': 40.0, 'label': 'B'},
        ]
        
        track = self._create_dummy_track()
        result = track.fuse_consecutive_sections(segments, start_after_first_downbeat=False)
        
        self.assertEqual(len(result), 4)
        self.assertEqual(result, segments)
    
    # Helper method to create a minimal Track instance
    def _create_dummy_track(self, first_downbeat=None):
        """Create a minimal Track instance for testing."""
        import numpy as np

        class DummyTrack(Track):
            def __init__(self, downbeats):
                self._downbeats = downbeats
        
        # Create minimal required arguments
        downbeats = [first_downbeat] if first_downbeat is not None else [0.0]

        return DummyTrack(downbeats=downbeats)


class TestTrackInitialization(unittest.TestCase):
    """Tests for Track initialization."""
    
    def test_track_basic_properties(self):
        """Test that Track stores basic properties correctly."""
        import numpy as np
        from unittest.mock import patch, MagicMock
        
        audio = np.arange(10000)
        sr = 44100
        bpm = 120.0
        beats = np.array([0.5, 1.0, 1.5, 2.0])
        downbeats = np.array([0.5, 2.5])
        key = "C major"
        segments = [{'start': 0.0, 'end': 2.0, 'label': 'verse'}]
        
        track = Track(
            track_name="test_track",
            instrument="vocals",
            audio=audio,
            sr=sr,
            bpm=bpm,
            beats=beats,
            downbeats=downbeats,
            key=key,
            segments=segments,
            path="/test/path"
        )
        
        self.assertEqual(track.name, "test_track")
        self.assertEqual(track.instrument, "vocals")
        self.assertEqual(track.sr, sr)
        self.assertEqual(track.bpm, bpm)
        self.assertEqual(track.key, key)
        self.assertEqual(track.path, "/test/path")
        np.testing.assert_array_equal(track.beats, beats)
        np.testing.assert_array_equal(track.downbeats, downbeats)
    
    def test_track_repr(self):
        """Test the Track __repr__ method."""
        import numpy as np
        
        audio = np.arange(10000)
        segments = [{'start': 0.0, 'end': 2.0, 'label': 'verse'}]
        
        track = Track(
            track_name="my_song",
            instrument="guitar",
            audio=audio,
            sr=22050,
            bpm=100.0,
            beats=np.array([0.5, 1.0]),
            downbeats=np.array([0.5, 1.5]),
            key="G major",
            segments=segments,
            path="/test"
        )
        
        repr_str = repr(track)
        self.assertIn("my_song", repr_str)
        self.assertIn("guitar", repr_str)
        self.assertIn("22050", repr_str)
        self.assertIn("100.0", repr_str)
        self.assertIn("G major", repr_str)


class TestTrackRepitch(unittest.TestCase):
    """Tests for the Track.repitch method."""
    
    def setUp(self):
        """Create a Track instance for testing."""
        import numpy as np
        
        self.audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        self.sr = 44100
        self.segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
        
    def test_repitch_updates_key(self):
        """Test that repitch updates the track key."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        # Mock the pitch utility function
        with patch('automashup.src.pitch_utils.repitch_audio_to_target') as mock_repitch:
            mock_repitch.return_value = self.audio.copy()
            
            track.repitch("G major")
            
            self.assertEqual(track.key, "G major")
            mock_repitch.assert_called_once()
            # Verify the call arguments
            args = mock_repitch.call_args[0]
            self.assertEqual(args[1], self.sr)  # sr
            self.assertEqual(args[2], "C major")  # original key
            self.assertEqual(args[3], "G major")  # new key
    
    def test_repitch_updates_audio(self):
        """Test that repitch updates the audio data."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        new_audio = np.zeros(len(self.audio))
        
        with patch('automashup.src.pitch_utils.repitch_audio_to_target') as mock_repitch:
            mock_repitch.return_value = new_audio
            
            track.repitch("A minor")
            
            np.testing.assert_array_equal(track.audio, new_audio)


class TestTrackResample(unittest.TestCase):
    """Tests for the Track.resample method."""
    
    def setUp(self):
        """Create a Track instance for testing."""
        import numpy as np
        
        self.audio = np.arange(44100)  # 1 second at 44100 Hz
        self.sr = 44100
        self.segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
    
    def test_resample_updates_sr(self):
        """Test that resample updates the sample rate."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        # Mock librosa.resample
        resampled_audio = np.arange(22050)  # Half the samples
        with patch('librosa.resample') as mock_resample:
            mock_resample.return_value = resampled_audio
            
            track.resample(22050)
            
            self.assertEqual(track.sr, 22050)
            mock_resample.assert_called_once()
    
    def test_resample_updates_audio(self):
        """Test that resample updates the audio data."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        resampled_audio = np.arange(22050)
        with patch('librosa.resample') as mock_resample:
            mock_resample.return_value = resampled_audio
            
            track.resample(22050)
            
            np.testing.assert_array_equal(track.audio, resampled_audio)


class TestTrackChangeTempo(unittest.TestCase):
    """Tests for the Track.change_tempo method."""
    
    def setUp(self):
        """Create a Track instance for testing."""
        import numpy as np
        
        self.audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        self.sr = 44100
        self.segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
    
    def test_change_tempo_updates_bpm(self):
        """Test that change_tempo updates the BPM."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        with patch('automashup.src.tempo_utils.time_stretch_audio') as mock_stretch:
            mock_stretch.return_value = self.audio.copy()
            
            track.change_tempo(140.0)
            
            self.assertEqual(track.bpm, 140.0)
            mock_stretch.assert_called_once()
            # Verify call arguments
            args = mock_stretch.call_args[0]
            self.assertEqual(args[1], self.sr)  # sr
            self.assertEqual(args[2], 120.0)    # original bpm
            self.assertEqual(args[3], 140.0)    # new bpm
    
    def test_change_tempo_updates_audio(self):
        """Test that change_tempo updates the audio data."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        # Stretching to faster tempo should result in shorter audio
        stretched_audio = np.zeros(22050)  # Half length for double tempo
        
        with patch('automashup.src.tempo_utils.time_stretch_audio') as mock_stretch:
            mock_stretch.return_value = stretched_audio
            
            track.change_tempo(240.0)
            
            np.testing.assert_array_equal(track.audio, stretched_audio)
    
    def test_change_tempo_slow_down(self):
        """Test changing tempo to a slower value."""
        import numpy as np
        from unittest.mock import patch
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=self.audio.copy(),
            sr=self.sr,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=self.segments,
            path="/test"
        )
        
        # Stretching to slower tempo
        stretched_audio = np.zeros(88200)  # Double length for half tempo
        
        with patch('automashup.src.tempo_utils.time_stretch_audio') as mock_stretch:
            mock_stretch.return_value = stretched_audio
            
            track.change_tempo(60.0)
            
            self.assertEqual(track.bpm, 60.0)
            self.assertEqual(len(track.audio), 88200)


class TestTrackGetSegmentsAsDict(unittest.TestCase):
    """Tests for the Track.get_segments_as_dict method."""
    
    def test_get_segments_as_dict_basic(self):
        """Test getting segments as dictionaries."""
        import numpy as np
        
        audio = np.arange(10000)
        segments = [
            {'start': 0.0, 'end': 1.0, 'label': 'intro'},
            {'start': 1.0, 'end': 3.0, 'label': 'verse'}
        ]
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=audio,
            sr=100,
            bpm=120.0,
            beats=np.array([0.0, 0.5, 1.0]),
            downbeats=np.array([0.0, 1.0, 2.0, 3.0]),
            key="C major",
            segments=segments,
            path="/test"
        )
        
        result = track.get_segments_as_dict()
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        # Each result should have start, end, label keys
        for seg in result:
            self.assertIn('start', seg)
            self.assertIn('end', seg)
            self.assertIn('label', seg)


class TestTrackAudioProperty(unittest.TestCase):
    """Tests for the Track audio property getter/setter."""
    
    def test_audio_getter(self):
        """Test getting audio data."""
        import numpy as np
        
        audio = np.arange(1000)
        segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=audio,
            sr=100,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=segments,
            path="/test"
        )
        
        np.testing.assert_array_equal(track.audio, audio)
    
    def test_audio_setter(self):
        """Test setting audio data."""
        import numpy as np
        
        audio = np.arange(1000)
        new_audio = np.zeros(500)
        segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=audio,
            sr=100,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=segments,
            path="/test"
        )
        
        track.audio = new_audio
        np.testing.assert_array_equal(track.audio, new_audio)


class TestTrackSegmentsProperty(unittest.TestCase):
    """Tests for the Track segments property getter/setter."""
    
    def test_segments_getter(self):
        """Test getting segments."""
        import numpy as np
        from automashup.src.segment import Segment
        
        audio = np.arange(1000)
        segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=audio,
            sr=100,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=segments,
            path="/test"
        )
        
        result = track.segments
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Segment)
    
    def test_segments_setter(self):
        """Test setting segments."""
        import numpy as np
        from automashup.src.segment import Segment
        
        audio = np.arange(1000)
        segments = [{'start': 0.0, 'end': 1.0, 'label': 'verse'}]
        
        track = Track(
            track_name="test",
            instrument="vocals",
            audio=audio,
            sr=100,
            bpm=120.0,
            beats=np.array([0.0, 0.5]),
            downbeats=np.array([0.0, 1.0]),
            key="C major",
            segments=segments,
            path="/test"
        )
        
        new_segments = [Segment({'start': 0.0, 'end': 0.5, 'label': 'new'})]
        track.segments = new_segments
        
        self.assertEqual(len(track.segments), 1)
        self.assertEqual(track.segments[0].label, 'new')


if __name__ == '__main__':
    unittest.main()
