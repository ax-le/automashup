import unittest
import numpy as np
from automashup.src.duration_utils import (
    adapt_all_stems_durations,
    get_target_length,
    adapt_audio_duration,
    pad_audio,
    crop_audio,
    adapt_start_audio,
    extract_section_audio,
    prepad_to_length
)

class TestCropAudio(unittest.TestCase):
    """Tests for the crop_audio function."""

    def test_crop_audio_basic(self):
        """Test basic cropping of audio to a shorter length."""
        audio = np.array([1, 2, 3, 4, 5])
        result = crop_audio(audio, 3)
        expected = np.array([1, 2, 3])
        np.testing.assert_array_equal(result, expected)

    def test_crop_audio_same_length(self):
        """Test cropping when audio length equals target length."""
        audio = np.array([1, 2, 3])
        result = crop_audio(audio, 3)
        np.testing.assert_array_equal(result, audio)

    def test_crop_audio_to_one(self):
        """Test cropping audio to a single sample."""
        audio = np.array([1, 2, 3, 4, 5])
        result = crop_audio(audio, 1)
        expected = np.array([1])
        np.testing.assert_array_equal(result, expected)

    def test_crop_audio_assertion_error(self):
        """Test that cropping fails when audio is shorter than target."""
        audio = np.array([1, 2, 3])
        with self.assertRaises(AssertionError):
            crop_audio(audio, 5)


class TestPadAudio(unittest.TestCase):
    """Tests for the pad_audio function."""

    def test_pad_audio_constant(self):
        """Test padding with constant (zero) values."""
        audio = np.array([1, 2, 3])
        result = pad_audio(audio, 5, padding_type='constant')
        expected = np.array([1, 2, 3, 0, 0])
        np.testing.assert_array_equal(result, expected)

    def test_pad_audio_reflect(self):
        """Test padding with reflect mode."""
        audio = np.array([1, 2, 3])
        result = pad_audio(audio, 5, padding_type='reflect')
        # Reflect mode reflects at the edge: [1, 2, 3] -> [1, 2, 3, 2, 1]
        expected = np.array([1, 2, 3, 2, 1])
        np.testing.assert_array_equal(result, expected)

    def test_pad_audio_repeat(self):
        """Test padding with repeat (wrap) mode."""
        audio = np.array([1, 2, 3])
        result = pad_audio(audio, 5, padding_type='repeat')
        # Wrap mode repeats the array: [1, 2, 3] -> [1, 2, 3, 1, 2]
        expected = np.array([1, 2, 3, 1, 2])
        np.testing.assert_array_equal(result, expected)

    def test_pad_audio_repeat_several_times(self):
        """Test padding with repeat (wrap) mode."""
        audio = np.array([1, 2, 3])
        result = pad_audio(audio, 10, padding_type='repeat')
        # Wrap mode repeats the array: [1, 2, 3] -> [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
        expected = np.array([1, 2, 3, 1, 2, 3, 1, 2, 3, 1])
        np.testing.assert_array_equal(result, expected)

    def test_pad_audio_same_length(self):
        """Test padding when audio length equals target length."""
        audio = np.array([1, 2, 3])
        result = pad_audio(audio, 3, padding_type='constant')
        np.testing.assert_array_equal(result, audio)

    def test_pad_audio_invalid_type(self):
        """Test that padding fails with an invalid padding type."""
        audio = np.array([1, 2, 3])
        with self.assertRaises(ValueError):
            pad_audio(audio, 5, padding_type='invalid_type')

    def test_pad_audio_assertion_error(self):
        """Test that padding fails when audio is longer than target."""
        audio = np.array([1, 2, 3, 4, 5])
        with self.assertRaises(AssertionError):
            pad_audio(audio, 3)


class TestAdaptAudio(unittest.TestCase):
    """Tests for the adapt_audio_duration function."""

    def test_adapt_audio_duration_same_length(self):
        """Test when audio length equals target length (no change)."""
        audio = np.array([1, 2, 3])
        result = adapt_audio_duration(audio, 3)
        np.testing.assert_array_equal(result, audio)

    def test_adapt_audio_duration_needs_padding(self):
        """Test when audio needs padding."""
        audio = np.array([1, 2, 3])
        result = adapt_audio_duration(audio, 5, padding_type='constant')
        expected = np.array([1, 2, 3, 0, 0])
        np.testing.assert_array_equal(result, expected)

    def test_adapt_audio_duration_needs_cropping(self):
        """Test when audio needs cropping."""
        audio = np.array([1, 2, 3, 4, 5])
        result = adapt_audio_duration(audio, 3)
        expected = np.array([1, 2, 3])
        np.testing.assert_array_equal(result, expected)

    def test_adapt_audio_duration_with_reflect_padding(self):
        """Test padding with reflect mode through adapt_audio_duration."""
        audio = np.array([1, 2, 3])
        result = adapt_audio_duration(audio, 5, padding_type='reflect')
        expected = np.array([1, 2, 3, 2, 1])
        np.testing.assert_array_equal(result, expected)

    def test_adapt_audio_duration_with_repeat_padding(self):
        """Test padding with repeat mode through adapt_audio_duration."""
        audio = np.array([1, 2, 3])
        result = adapt_audio_duration(audio, 5, padding_type='repeat')
        expected = np.array([1, 2, 3, 1, 2])
        np.testing.assert_array_equal(result, expected)

    def test_adapt_audio_duration_with_repeat_padding_several_times(self):
        """Test padding with repeat mode through adapt_audio_duration."""
        audio = np.array([1, 2, 3])
        result = adapt_audio_duration(audio, 10, padding_type='repeat')
        expected = np.array([1, 2, 3, 1, 2, 3, 1, 2, 3, 1])
        np.testing.assert_array_equal(result, expected)


class TestGetTargetLength(unittest.TestCase):
    """Tests for the get_target_length function."""

    def test_get_target_length_vocal_longest(self):
        """Test when vocal track is the longest."""
        vocal = np.array([1, 2, 3, 4, 5])
        instrumentals = [np.array([1, 2]), np.array([1, 2, 3])]
        result = get_target_length(vocal, instrumentals, length_type='max')
        self.assertEqual(result, 5)

    def test_get_target_length_instrumental_longest(self):
        """Test when an instrumental track is the longest."""
        vocal = np.array([1, 2])
        instrumentals = [np.array([1, 2, 3, 4, 5]), np.array([1, 2, 3])]
        result = get_target_length(vocal, instrumentals, length_type='max')
        self.assertEqual(result, 5)

    def test_get_target_length_all_equal(self):
        """Test when all tracks have the same length."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([1, 2, 3]), np.array([1, 2, 3])]
        result = get_target_length(vocal, instrumentals, length_type='max')
        self.assertEqual(result, 3)

    def test_get_target_length_single_instrumental(self):
        """Test with a single instrumental track."""
        vocal = np.array([1, 2])
        instrumentals = [np.array([1, 2, 3, 4])]
        result = get_target_length(vocal, instrumentals, length_type='max')
        self.assertEqual(result, 4)

    def test_get_target_length_invalid_type(self):
        """Test that an invalid length_type raises ValueError."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([1, 2])]
        with self.assertRaises(ValueError):
            get_target_length(vocal, instrumentals, length_type='invalid')


class TestAdaptAllStems(unittest.TestCase):
    """Tests for the adapt_all_stems_durations function."""

    def test_adapt_all_stems_durations_vocal_shortest(self):
        """Test when vocal track is shorter than instrumentals."""
        vocal = np.array([1, 2])
        instrumentals = [np.array([1, 2, 3, 4]), np.array([1, 2, 3])]
        
        adapted_vocal, adapted_instrumentals = adapt_all_stems_durations(vocal, instrumentals, padding_type='constant')
        
        # All outputs should have length 4 (the max)
        self.assertEqual(len(adapted_vocal), 4)
        self.assertTrue(all(len(track) == 4 for track in adapted_instrumentals))
        
        # Check vocal is padded correctly
        expected_vocal = np.array([1, 2, 0, 0])
        np.testing.assert_array_equal(adapted_vocal, expected_vocal)

    def test_adapt_all_stems_durations_vocal_longest(self):
        """Test when vocal track is the longest."""
        vocal = np.array([1, 2, 3, 4, 5])
        instrumentals = [np.array([1, 2]), np.array([1, 2, 3])]
        
        adapted_vocal, adapted_instrumentals = adapt_all_stems_durations(vocal, instrumentals, padding_type='constant')
        
        # All outputs should have length 5 (the max)
        self.assertEqual(len(adapted_vocal), 5)
        self.assertTrue(all(len(track) == 5 for track in adapted_instrumentals))
        
        # Vocal should remain unchanged
        np.testing.assert_array_equal(adapted_vocal, vocal)

    def test_adapt_all_stems_durations_all_equal_length(self):
        """Test when all tracks have the same length."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([4, 5, 6]), np.array([7, 8, 9])]
        
        adapted_vocal, adapted_instrumentals = adapt_all_stems_durations(vocal, instrumentals, padding_type='constant')
        
        # All should remain unchanged
        np.testing.assert_array_equal(adapted_vocal, vocal)
        np.testing.assert_array_equal(adapted_instrumentals[0], instrumentals[0])
        np.testing.assert_array_equal(adapted_instrumentals[1], instrumentals[1])

    def test_adapt_all_stems_durations_with_reflect_padding(self):
        """Test with reflect padding type."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([1, 2, 3, 4])]
        
        adapted_vocal, adapted_instrumentals = adapt_all_stems_durations(
            vocal, instrumentals, padding_type='reflect'
        )
        
        # Vocal should be padded with reflect: [1, 2, 3] -> [1, 2, 3, 2]
        expected_vocal = np.array([1, 2, 3, 2])
        np.testing.assert_array_equal(adapted_vocal, expected_vocal)

    def test_adapt_all_stems_durations_single_instrumental(self):
        """Test with a single instrumental track."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([1, 2, 3, 4, 5])]
        
        adapted_vocal, adapted_instrumentals = adapt_all_stems_durations(vocal, instrumentals, padding_type='constant')
        
        self.assertEqual(len(adapted_vocal), 5)
        self.assertEqual(len(adapted_instrumentals), 1)
        self.assertEqual(len(adapted_instrumentals[0]), 5)

    def test_adapt_all_stems_durations_returns_correct_types(self):
        """Test that the function returns numpy arrays."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([1, 2, 3, 4])]
        
        adapted_vocal, adapted_instrumentals = adapt_all_stems_durations(vocal, instrumentals, padding_type='constant')
        
        self.assertIsInstance(adapted_vocal, np.ndarray)
        self.assertTrue(all(isinstance(track, np.ndarray) for track in adapted_instrumentals))


class TestAdaptStartAudio(unittest.TestCase):
    """Tests for the adapt_start_audio function."""

    def test_adapt_start_audio_basic(self):
        """Test extracting audio from a start time."""
        audio = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        sr = 10  # 10 samples per second
        
        result = adapt_start_audio(audio, start_time=0.5, sr=sr)
        # Start at 0.5 seconds = sample 5
        expected = np.array([5, 6, 7, 8, 9])
        np.testing.assert_array_equal(result, expected)

    def test_adapt_start_audio_from_beginning(self):
        """Test with start_time = 0."""
        audio = np.array([1, 2, 3, 4, 5])
        result = adapt_start_audio(audio, start_time=0, sr=10)
        np.testing.assert_array_equal(result, audio)

    def test_adapt_start_audio_near_end(self):
        """Test with start_time near the end of audio."""
        audio = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        sr = 10
        result = adapt_start_audio(audio, start_time=0.9, sr=sr)
        expected = np.array([10])
        np.testing.assert_array_equal(result, expected)


class TestExtractSectionAudio(unittest.TestCase):
    """Tests for the extract_section_audio function."""

    def test_extract_section_basic(self):
        """Test extracting audio between start and end times."""
        audio = np.arange(100)
        sr = 10
        
        result = extract_section_audio(audio, sr, start_time=2.0, end_time=5.0)
        # Samples 20 to 50
        expected = np.arange(20, 50)
        np.testing.assert_array_equal(result, expected)

    def test_extract_section_from_beginning(self):
        """Test extracting from the beginning."""
        audio = np.arange(50)
        sr = 10
        
        result = extract_section_audio(audio, sr, start_time=0.0, end_time=2.0)
        expected = np.arange(0, 20)
        np.testing.assert_array_equal(result, expected)

    def test_extract_section_to_end(self):
        """Test extracting to near the end."""
        audio = np.arange(50)
        sr = 10
        
        result = extract_section_audio(audio, sr, start_time=3.0, end_time=5.0)
        expected = np.arange(30, 50)
        np.testing.assert_array_equal(result, expected)

    def test_extract_section_single_sample(self):
        """Test extracting a very short section."""
        audio = np.arange(100)
        sr = 100  # 100 samples per second
        
        result = extract_section_audio(audio, sr, start_time=0.5, end_time=0.51)
        expected = np.arange(50, 51)
        np.testing.assert_array_equal(result, expected)


class TestPrepadToLength(unittest.TestCase):
    """Tests for the prepad_to_length function."""

    def test_prepad_basic(self):
        """Test pre-padding audio with zeros."""
        audio = np.array([1, 2, 3])
        result = prepad_to_length(audio, 5)
        expected = np.array([0, 0, 1, 2, 3])
        np.testing.assert_array_equal(result, expected)

    def test_prepad_same_length(self):
        """Test that same length audio is unchanged."""
        audio = np.array([1, 2, 3, 4, 5])
        result = prepad_to_length(audio, 5)
        np.testing.assert_array_equal(result, audio)

    def test_prepad_longer_audio(self):
        """Test that longer audio is unchanged."""
        audio = np.array([1, 2, 3, 4, 5, 6, 7])
        result = prepad_to_length(audio, 5)
        # Should return unchanged when audio is longer
        np.testing.assert_array_equal(result, audio)

    def test_prepad_to_double_length(self):
        """Test pre-padding to double length."""
        audio = np.array([1, 2, 3])
        result = prepad_to_length(audio, 6)
        expected = np.array([0, 0, 0, 1, 2, 3])
        np.testing.assert_array_equal(result, expected)

    def test_prepad_single_element(self):
        """Test pre-padding a single element."""
        audio = np.array([5])
        result = prepad_to_length(audio, 4)
        expected = np.array([0, 0, 0, 5])
        np.testing.assert_array_equal(result, expected)


if __name__ == '__main__':
    unittest.main()
