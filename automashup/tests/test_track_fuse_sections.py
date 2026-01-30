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
                self.downbeats = downbeats
        
        # Create minimal required arguments
        downbeats = [first_downbeat] if first_downbeat is not None else [0.0]

        return DummyTrack(downbeats=downbeats)


if __name__ == '__main__':
    unittest.main()
