import unittest
import numpy as np
from unittest.mock import MagicMock, patch

from automashup.src.structure_utils import (
    find_matching_section,
    adapt_this_instrumental_section,
    extract_intro_audio,
    pad_and_align_intro_audios
)


class TestFindMatchingSection(unittest.TestCase):
    """Tests for the find_matching_section function."""

    def setUp(self):
        """Create mock segments for testing."""
        self.mock_segments = []
        for label in ['intro', 'verse', 'chorus', 'verse', 'chorus', 'outro']:
            seg = MagicMock()
            seg.label = label
            self.mock_segments.append(seg)

    def test_exact_label_match_first_occurrence(self):
        """Test finding the first occurrence of an exact label match."""
        result, new_index = find_matching_section('verse', self.mock_segments, current_index=0)
        self.assertEqual(result.label, 'verse')
        self.assertEqual(new_index, 1)

    def test_exact_label_match_second_occurrence(self):
        """Test finding the second occurrence with current_index."""
        result, new_index = find_matching_section('verse', self.mock_segments, current_index=1)
        self.assertEqual(result.label, 'verse')
        self.assertEqual(new_index, 2)

    def test_exact_label_match_index_clamped(self):
        """Test that current_index is clamped to available matches."""
        # There are only 2 verses, so index 5 should clamp to the last one
        result, new_index = find_matching_section('verse', self.mock_segments, current_index=5)
        self.assertEqual(result.label, 'verse')
        self.assertEqual(new_index, 6)

    def test_closest_label_match(self):
        """Test matching with label prefix (e.g., 'chorus' matches 'chorus A')."""
        segments = []
        for label in ['intro', 'verse A', 'chorus 1', 'verse B']:
            seg = MagicMock()
            seg.label = label
            segments.append(seg)

        result, new_index = find_matching_section('chorus', segments, current_index=0)
        self.assertEqual(result.label, 'chorus 1')
        self.assertEqual(new_index, 1)

    def test_fallback_to_verse(self):
        """Test fallback to first verse when no match found."""
        segments = []
        for label in ['intro', 'verse', 'bridge', 'outro']:
            seg = MagicMock()
            seg.label = label
            segments.append(seg)

        result, new_index = find_matching_section('solo', segments, current_index=0)
        self.assertEqual(result.label, 'verse')
        # Index should not increment on fallback
        self.assertEqual(new_index, 0)

    def test_fallback_to_first_segment(self):
        """Test fallback to first segment when no verse or match found."""
        segments = []
        for label in ['intro', 'bridge', 'outro']:
            seg = MagicMock()
            seg.label = label
            segments.append(seg)

        result, new_index = find_matching_section('chorus', segments, current_index=0)
        self.assertEqual(result.label, 'intro')
        # Index should not increment on fallback
        self.assertEqual(new_index, 0)

    def test_empty_segments_raises_error(self):
        """Test that empty segment list raises ValueError."""
        with self.assertRaises(ValueError):
            find_matching_section('verse', [], current_index=0)

    def test_case_insensitive_closest_match(self):
        """Test that closest match is case-insensitive."""
        segments = []
        for label in ['INTRO', 'VERSE', 'CHORUS']:
            seg = MagicMock()
            seg.label = label
            segments.append(seg)

        result, new_index = find_matching_section('verse', segments, current_index=0)
        self.assertEqual(result.label, 'VERSE')


class TestExtractIntroAudio(unittest.TestCase):
    """Tests for the extract_intro_audio function."""

    def test_extract_intro_with_audio(self):
        """Test extracting intro audio before first downbeat."""
        track = MagicMock()
        track.sr = 44100
        track.bpm = 120.0
        track.downbeats = [1.0, 2.0, 3.0]  # First downbeat at 1 second
        track.audio = np.arange(44100 * 3)  # 3 seconds of audio

        with patch('automashup.src.structure_utils.tempo_utils.accelerate_audio') as mock_accel:
            mock_accel.return_value = np.arange(44100)
            result = extract_intro_audio(track, target_bpm=100.0)
            
            # Should call accelerate_audio with the intro portion
            mock_accel.assert_called_once()
            call_args = mock_accel.call_args[0]
            self.assertEqual(len(call_args[0]), 44100)  # 1 second of intro
            self.assertEqual(call_args[1], 44100)  # sr
            self.assertEqual(call_args[2], 120.0)  # orig_tempo
            self.assertEqual(call_args[3], 100.0)  # ref_tempo

    def test_extract_intro_empty_when_downbeat_at_zero(self):
        """Test that empty array is returned when first downbeat is at 0."""
        track = MagicMock()
        track.sr = 44100
        track.bpm = 120.0
        track.downbeats = [0.0, 1.0, 2.0]
        track.audio = np.arange(44100 * 3)

        result = extract_intro_audio(track, target_bpm=100.0)
        self.assertEqual(len(result), 0)


class TestPadAndAlignIntroAudios(unittest.TestCase):
    """Tests for the pad_and_align_intro_audios function."""

    def test_align_multiple_intros(self):
        """Test aligning multiple intros of different lengths."""
        intro1 = np.array([1, 2, 3])
        intro2 = np.array([4, 5, 6, 7, 8])
        intro3 = np.array([9])

        result = pad_and_align_intro_audios([intro1, intro2, intro3])

        self.assertEqual(len(result), 3)
        self.assertTrue(all(len(intro) == 5 for intro in result))
        # Check that intro2 (the longest) is unchanged
        np.testing.assert_array_equal(result[1], intro2)
        # Check that others are pre-padded with zeros
        np.testing.assert_array_equal(result[0], np.array([0, 0, 1, 2, 3]))
        np.testing.assert_array_equal(result[2], np.array([0, 0, 0, 0, 9]))

    def test_align_single_intro(self):
        """Test with a single intro."""
        intro = np.array([1, 2, 3])
        result = pad_and_align_intro_audios([intro])
        
        self.assertEqual(len(result), 1)
        np.testing.assert_array_equal(result[0], intro)

    def test_align_empty_list(self):
        """Test with empty list returns empty list."""
        result = pad_and_align_intro_audios([])
        self.assertEqual(result, [])

    def test_align_equal_length_intros(self):
        """Test with intros of equal length."""
        intro1 = np.array([1, 2, 3])
        intro2 = np.array([4, 5, 6])

        result = pad_and_align_intro_audios([intro1, intro2])

        np.testing.assert_array_equal(result[0], intro1)
        np.testing.assert_array_equal(result[1], intro2)


class TestAdaptThisInstrumentalSection(unittest.TestCase):
    """Tests for the adapt_this_instrumental_section function."""

    def setUp(self):
        """Create mock objects for testing."""
        self.vocal_segment = MagicMock()
        self.vocal_segment.label = 'verse'
        self.vocal_segment.duration_samples = 44100
        self.vocal_segment.bpm = 120.0
        self.vocal_segment.downbeats_samples = np.array([0, 22050, 44100])
        
        self.instrumental_segment = MagicMock()
        self.instrumental_segment.label = 'verse'
        self.instrumental_segment.original_audio = np.random.randn(44100)
        self.instrumental_segment.sr = 44100
        self.instrumental_segment.bpm = 100.0
        
        self.instrumental_track = MagicMock()
        self.instrumental_track.segments = [self.instrumental_segment]

    def test_adapt_with_bpm_method(self):
        """Test adaptation using bpm method."""
        with patch('automashup.src.structure_utils.tempo_utils.accelerate_audio') as mock_accel, \
             patch('automashup.src.structure_utils.duration_utils.adapt_audio_duration') as mock_adapt:
            mock_accel.return_value = np.random.randn(44100)
            mock_adapt.return_value = np.random.randn(44100)
            
            result, new_index = adapt_this_instrumental_section(
                self.vocal_segment,
                self.instrumental_track,
                current_index=0,
                time_adapt_method='bpm'
            )
            
            mock_accel.assert_called_once()
            mock_adapt.assert_called_once()
            self.assertEqual(len(result), 44100)
            self.assertEqual(new_index, 1)

    def test_adapt_with_downbeats_method(self):
        """Test adaptation using downbeats method."""
        self.instrumental_segment.get_audio_barwise = MagicMock(
            return_value=np.array([[1, 2, 3], [4, 5, 6]])
        )
        
        with patch('automashup.src.structure_utils.tempo_utils.accelerate_to_match_downbeats') as mock_accel, \
             patch('automashup.src.structure_utils.duration_utils.adapt_audio_duration') as mock_adapt:
            mock_accel.return_value = np.random.randn(44100)
            mock_adapt.return_value = np.random.randn(44100)
            
            result, new_index = adapt_this_instrumental_section(
                self.vocal_segment,
                self.instrumental_track,
                current_index=0,
                time_adapt_method='downbeats'
            )
            
            mock_accel.assert_called_once()
            self.assertEqual(new_index, 1)

    def test_adapt_with_unknown_method_raises_error(self):
        """Test that unknown method raises ValueError."""
        with self.assertRaises(ValueError):
            adapt_this_instrumental_section(
                self.vocal_segment,
                self.instrumental_track,
                current_index=0,
                time_adapt_method='unknown'
            )


if __name__ == '__main__':
    unittest.main()
