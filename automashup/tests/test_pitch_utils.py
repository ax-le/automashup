import unittest
from automashup.src.pitch_utils import (
    semitones_between_keys,
    SEMITONE_OFFSETS
)


class TestSemitonesBetweenKeys(unittest.TestCase):
    """Tests for the semitones_between_keys function."""

    # === Same mode tests (major to major) ===
    
    def test_same_key_major(self):
        """Test that same key returns 0 semitones."""
        self.assertEqual(semitones_between_keys("C major", "C major"), 0)
        self.assertEqual(semitones_between_keys("G major", "G major"), 0)
    
    def test_same_key_minor(self):
        """Test that same minor key returns 0 semitones."""
        self.assertEqual(semitones_between_keys("A minor", "A minor"), 0)
        self.assertEqual(semitones_between_keys("E minor", "E minor"), 0)

    def test_major_to_major_ascending(self):
        """Test ascending semitone shifts between major keys."""
        # C to D = 2 semitones up
        self.assertEqual(semitones_between_keys("C major", "D major"), 2)
        # C to E = 4 semitones up
        self.assertEqual(semitones_between_keys("C major", "E major"), 4)
        # C to F = 5 semitones up
        self.assertEqual(semitones_between_keys("C major", "F major"), 5)

    def test_major_to_major_descending(self):
        """Test descending semitone shifts between major keys."""
        # G to C = -7 semitones, but shortest path is +5
        self.assertEqual(semitones_between_keys("G major", "C major"), 5)
        # D to C = -2 semitones
        self.assertEqual(semitones_between_keys("D major", "C major"), -2)

    def test_major_to_major_shortest_path(self):
        """Test that the shortest path is always chosen (max 6 semitones)."""
        # C to G = 7 semitones up, but shortest is 5 down
        self.assertEqual(semitones_between_keys("C major", "G major"), -5)
        # C to F# = 6 semitones (exactly half, could be either direction)
        result = semitones_between_keys("C major", "F# major")
        self.assertIn(result, [6, -6])

    # === Same mode tests (minor to minor) ===
    
    def test_minor_to_minor(self):
        """Test semitone shifts between minor keys."""
        # A minor to E minor: A=9+3=0, E=4+3=7, diff=7 -> -5
        self.assertEqual(semitones_between_keys("A minor", "E minor"), -5)
        # A minor to D minor: A=9+3=0, D=2+3=5, diff=5
        self.assertEqual(semitones_between_keys("A minor", "D minor"), 5)

    # === Circle of fifths: relative major/minor ===
    
    def test_relative_major_minor_zero_shift(self):
        """Test that relative major/minor keys require 0 semitones shift.
        
        Circle of fifths: C major and A minor are relative keys (same key signature).
        """
        # C major <-> A minor (relative keys)
        self.assertEqual(semitones_between_keys("C major", "A minor"), 0)
        self.assertEqual(semitones_between_keys("A minor", "C major"), 0)

    def test_relative_keys_g_major_e_minor(self):
        """Test G major <-> E minor relative keys."""
        self.assertEqual(semitones_between_keys("G major", "E minor"), 0)
        self.assertEqual(semitones_between_keys("E minor", "G major"), 0)

    def test_relative_keys_d_major_b_minor(self):
        """Test D major <-> B minor relative keys."""
        self.assertEqual(semitones_between_keys("D major", "B minor"), 0)
        self.assertEqual(semitones_between_keys("B minor", "D major"), 0)

    def test_relative_keys_f_major_d_minor(self):
        """Test F major <-> D minor relative keys."""
        self.assertEqual(semitones_between_keys("F major", "D minor"), 0)
        self.assertEqual(semitones_between_keys("D minor", "F major"), 0)

    # === Cross-mode tests (major to non-relative minor) ===
    
    def test_major_to_non_relative_minor(self):
        """Test shifts between non-relative major and minor keys."""
        # C major to E minor: C=0, E minor=4+3=7, diff=7 -> -5
        self.assertEqual(semitones_between_keys("C major", "E minor"), -5)
        # C major to D minor: C=0, D minor=2+3=5, diff=5
        self.assertEqual(semitones_between_keys("C major", "D minor"), 5)

    def test_minor_to_non_relative_major(self):
        """Test shifts between non-relative minor and major keys."""
        # A minor to G major: A=9+3=0, G=7, diff=7 -> -5
        self.assertEqual(semitones_between_keys("A minor", "G major"), -5)

    # === Edge cases with enharmonic equivalents ===
    
    def test_enharmonic_equivalents(self):
        """Test keys with enharmonic note names (C# = Db, etc.)."""
        # C# major and Db major should give same result
        result_sharp = semitones_between_keys("C major", "C# major")
        result_flat = semitones_between_keys("C major", "Db major")
        self.assertEqual(result_sharp, result_flat)

    def test_default_mode_is_major(self):
        """Test that keys without mode default to major."""
        # "C" should be treated as "C major"
        self.assertEqual(semitones_between_keys("C", "G"), -5)
        self.assertEqual(semitones_between_keys("C", "C major"), 0)

class TestSemitoneOffsets(unittest.TestCase):
    """Tests for the SEMITONE_OFFSETS constant."""

    def test_all_notes_present(self):
        """Test that all standard notes are in the offset dictionary."""
        expected_notes = ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 
                          'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']
        for note in expected_notes:
            self.assertIn(note, SEMITONE_OFFSETS)

    def test_enharmonic_equivalents_same_offset(self):
        """Test that enharmonic equivalents have the same offset."""
        self.assertEqual(SEMITONE_OFFSETS['C#'], SEMITONE_OFFSETS['Db'])
        self.assertEqual(SEMITONE_OFFSETS['D#'], SEMITONE_OFFSETS['Eb'])
        self.assertEqual(SEMITONE_OFFSETS['F#'], SEMITONE_OFFSETS['Gb'])
        self.assertEqual(SEMITONE_OFFSETS['G#'], SEMITONE_OFFSETS['Ab'])
        self.assertEqual(SEMITONE_OFFSETS['A#'], SEMITONE_OFFSETS['Bb'])

    def test_octave_range(self):
        """Test that all offsets are within 0-11 range."""
        for note, offset in SEMITONE_OFFSETS.items():
            self.assertGreaterEqual(offset, 0, f"{note} offset should be >= 0")
            self.assertLessEqual(offset, 11, f"{note} offset should be <= 11")


if __name__ == '__main__':
    unittest.main()
