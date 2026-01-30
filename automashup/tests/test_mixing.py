import unittest
import numpy as np

from automashup.src.mixing import (
    additive_mix,
    additive_mix_instrumentals
)


class TestAdditiveMixInstrumentals(unittest.TestCase):
    """Tests for the additive_mix_instrumentals function."""

    def test_mix_two_equal_tracks(self):
        """Test mixing two tracks of equal length."""
        track1 = np.array([1, 2, 3, 4, 5])
        track2 = np.array([5, 4, 3, 2, 1])
        
        result = additive_mix_instrumentals([track1, track2])
        expected = np.array([6, 6, 6, 6, 6])
        np.testing.assert_array_equal(result, expected)

    def test_mix_three_equal_tracks(self):
        """Test mixing three tracks of equal length."""
        track1 = np.array([1, 1, 1])
        track2 = np.array([2, 2, 2])
        track3 = np.array([3, 3, 3])
        
        result = additive_mix_instrumentals([track1, track2, track3])
        expected = np.array([6, 6, 6])
        np.testing.assert_array_equal(result, expected)

    def test_mix_single_track(self):
        """Test mixing a single track returns the same track."""
        track = np.array([1, 2, 3, 4, 5])
        result = additive_mix_instrumentals([track])
        np.testing.assert_array_equal(result, track)

    def test_mix_unequal_lengths_raises_assertion(self):
        """Test that mixing tracks of unequal length raises AssertionError."""
        track1 = np.array([1, 2, 3])
        track2 = np.array([1, 2, 3, 4, 5])
        
        with self.assertRaises(AssertionError):
            additive_mix_instrumentals([track1, track2])

    def test_mix_with_floats(self):
        """Test mixing with floating point values."""
        track1 = np.array([0.5, 0.25, 0.1])
        track2 = np.array([0.5, 0.75, 0.9])
        
        result = additive_mix_instrumentals([track1, track2])
        expected = np.array([1.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_mix_with_negative_values(self):
        """Test mixing with negative values (audio can be negative)."""
        track1 = np.array([1, -1, 1, -1])
        track2 = np.array([-1, 1, -1, 1])
        
        result = additive_mix_instrumentals([track1, track2])
        expected = np.array([0, 0, 0, 0])
        np.testing.assert_array_equal(result, expected)


class TestAdditiveMix(unittest.TestCase):
    """Tests for the additive_mix function."""

    def test_basic_mix(self):
        """Test basic mixing of vocal and instrumentals."""
        vocal = np.array([1, 1, 1, 1])
        instrumentals = [np.array([2, 2, 2, 2]), np.array([3, 3, 3, 3])]
        
        result = additive_mix(vocal, instrumentals, padding_type='constant')
        expected = np.array([6, 6, 6, 6])  # 1 + 2 + 3 = 6
        np.testing.assert_array_equal(result, expected)

    def test_mix_with_different_lengths_vocal_shorter(self):
        """Test mixing when vocal is shorter than instrumentals."""
        vocal = np.array([1, 1])
        instrumentals = [np.array([2, 2, 2, 2])]
        
        result = additive_mix(vocal, instrumentals, padding_type='constant')
        # Vocal should be padded: [1, 1, 0, 0]
        expected = np.array([3, 3, 2, 2])
        np.testing.assert_array_equal(result, expected)

    def test_mix_with_different_lengths_instrumental_shorter(self):
        """Test mixing when instrumental is shorter than vocal."""
        vocal = np.array([1, 1, 1, 1])
        instrumentals = [np.array([2, 2])]
        
        result = additive_mix(vocal, instrumentals, padding_type='constant')
        # Instrumental should be padded: [2, 2, 0, 0]
        expected = np.array([3, 3, 1, 1])
        np.testing.assert_array_equal(result, expected)

    def test_mix_with_repeat_padding(self):
        """Test mixing with repeat padding type."""
        vocal = np.array([1, 2, 3])
        instrumentals = [np.array([10, 20, 30, 40, 50])]
        
        result = additive_mix(vocal, instrumentals, padding_type='repeat')
        # Vocal padded with repeat: [1, 2, 3, 1, 2]
        expected = np.array([11, 22, 33, 41, 52])
        np.testing.assert_array_equal(result, expected)

    def test_mix_with_single_instrumental(self):
        """Test mixing with a single instrumental track."""
        vocal = np.array([1, 1, 1])
        instrumentals = [np.array([2, 2, 2])]
        
        result = additive_mix(vocal, instrumentals, padding_type='constant')
        expected = np.array([3, 3, 3])
        np.testing.assert_array_equal(result, expected)

    def test_mix_with_multiple_instrumentals(self):
        """Test mixing with multiple instrumental tracks."""
        vocal = np.array([1, 1])
        instrumentals = [
            np.array([1, 1]),
            np.array([1, 1]),
            np.array([1, 1])
        ]
        
        result = additive_mix(vocal, instrumentals, padding_type='constant')
        expected = np.array([4, 4])  # 1 + 1 + 1 + 1 = 4
        np.testing.assert_array_equal(result, expected)


if __name__ == '__main__':
    unittest.main()
