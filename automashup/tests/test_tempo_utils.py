import unittest
import numpy as np
from unittest.mock import patch, MagicMock

from automashup.src.tempo_utils import (
    accelerate_audio,
    accelerate_to_match_timesteps,
    accelerate_to_match_downbeats
)


class TestAccelerateAudio(unittest.TestCase):
    """Tests for the accelerate_audio function."""

    def test_accelerate_audio_speed_up(self):
        """Test speeding up audio (higher target tempo)."""
        # Create a simple test audio
        sr = 44100
        duration = 1.0  # 1 second
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
        
        result = accelerate_audio(audio, sr, orig_tempo=100, ref_tempo=200)
        
        # When doubling tempo, audio should be roughly half length
        # pyrubberband may not be exact, so we use a tolerance
        expected_length = len(audio) // 2
        self.assertAlmostEqual(len(result), expected_length, delta=100)

    def test_accelerate_audio_slow_down(self):
        """Test slowing down audio (lower target tempo)."""
        sr = 44100
        duration = 1.0
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
        
        result = accelerate_audio(audio, sr, orig_tempo=200, ref_tempo=100)
        
        # When halving tempo, audio should be roughly double length
        expected_length = len(audio) * 2
        self.assertAlmostEqual(len(result), expected_length, delta=200)

    def test_accelerate_audio_same_tempo(self):
        """Test that same tempo returns similar length audio."""
        sr = 44100
        duration = 0.5
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration)))
        
        result = accelerate_audio(audio, sr, orig_tempo=120, ref_tempo=120)
        
        # Same tempo should give same length
        self.assertAlmostEqual(len(result), len(audio), delta=10)


class TestAccelerateToMatchTimesteps(unittest.TestCase):
    """Tests for the accelerate_to_match_timesteps function."""

    def test_match_timesteps_basic(self):
        """Test matching audio to timesteps."""
        # This function relies on accelerate_to_match_length which has a bug
        # (uses audio.sr which doesn't exist for numpy arrays)
        # We'll test via mocking
        with patch('automashup.src.tempo_utils.accelerate_to_match_length') as mock_match:
            mock_match.return_value = np.zeros(100)
            
            audio = np.zeros(150)
            sr = 1
            result = accelerate_to_match_timesteps(audio, sr, ref_start=0, ref_end=100)
            
            # Should call accelerate_to_match_length with duration = 100 - 0 = 100
            mock_match.assert_called_once_with(audio, sr, 100)

    def test_match_timesteps_with_offset(self):
        """Test matching with non-zero start."""
        with patch('automashup.src.tempo_utils.accelerate_to_match_length') as mock_match:
            mock_match.return_value = np.zeros(50)
            
            audio = np.zeros(100)
            sr = 1
            result = accelerate_to_match_timesteps(audio, sr,ref_start=50, ref_end=100)
            
            # Duration should be 100 - 50 = 50
            mock_match.assert_called_once_with(audio, sr, 50)


class TestAccelerateToMatchDownbeats(unittest.TestCase):
    """Tests for the accelerate_to_match_downbeats function."""

    def test_match_downbeats_equal_bars(self):
        """Test with equal number of bars in source and reference."""
        with patch('automashup.src.tempo_utils.accelerate_to_match_timesteps') as mock_accel, \
             patch('automashup.src.tempo_utils.concatenate.concatenate_sections') as mock_concat:
            
            # 2 bars of audio, each 10 samples
            barwise_audio = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                       [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]])
            # Reference downbeats for 2 bars
            ref_downbeats = np.array([0, 15, 30])
            
            mock_accel.return_value = np.zeros(15)
            mock_concat.return_value = np.zeros(30)

            sr=1
            
            result = accelerate_to_match_downbeats(barwise_audio, sr, ref_downbeats)
            
            # Should call accelerate_to_match_timesteps twice
            self.assertEqual(mock_accel.call_count, 2)

    def test_match_downbeats_looping(self):
        """Test that bars loop when source has fewer bars than reference."""
        with patch('automashup.src.tempo_utils.accelerate_to_match_timesteps') as mock_accel, \
             patch('automashup.src.tempo_utils.concatenate.concatenate_sections') as mock_concat:
            
            # Only 1 bar of source audio
            barwise_audio = np.array([[1, 2, 3, 4, 5]])
            # Reference has 3 bars
            ref_downbeats = np.array([0, 10, 20, 30])
            
            mock_accel.return_value = np.zeros(10)
            mock_concat.return_value = np.zeros(30)

            sr=1
            result = accelerate_to_match_downbeats(barwise_audio, sr, ref_downbeats)
            
            # Should loop through the single bar 3 times
            self.assertEqual(mock_accel.call_count, 3)

    def test_match_downbeats_truncation(self):
        """Test that source bars are truncated when more than reference."""
        with patch('automashup.src.tempo_utils.accelerate_to_match_timesteps') as mock_accel, \
             patch('automashup.src.tempo_utils.concatenate.concatenate_sections') as mock_concat:
            
            # 5 bars of source audio
            barwise_audio = np.array([[1], [2], [3], [4], [5]])
            # Reference has only 2 bars
            ref_downbeats = np.array([0, 10, 20])
            
            mock_accel.return_value = np.zeros(10)
            mock_concat.return_value = np.zeros(20)

            sr=1
            result = accelerate_to_match_downbeats(barwise_audio, sr, ref_downbeats)
            
            # Should only use first 2 bars (nb_bars_ref = 2)
            self.assertEqual(mock_accel.call_count, 2)

    def test_match_downbeats_empty_bar_raises_error(self):
        """Test that empty bar raises ValueError."""
        barwise_audio = np.array([[]])  # Empty bar
        ref_downbeats = np.array([0, 10])
        sr=1
        
        with self.assertRaises(ValueError) as context:
            accelerate_to_match_downbeats(barwise_audio, sr, ref_downbeats)
        
        self.assertIn("Empty barwise segment audio", str(context.exception))

    def test_match_downbeats_no_bars_raises_error(self):
        """Test that no available bars raises ValueError."""
        barwise_audio = np.array([[1, 2, 3]])
        ref_downbeats = np.array([0])  # Only 1 downbeat = 0 bars
        sr=1
        
        with patch('automashup.src.tempo_utils.concatenate.concatenate_sections'):
            with self.assertRaises(ValueError) as context:
                accelerate_to_match_downbeats(barwise_audio, sr, ref_downbeats)
            
            self.assertIn("No adaptation", str(context.exception))


if __name__ == '__main__':
    unittest.main()
