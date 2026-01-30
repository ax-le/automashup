import unittest



import numpy as np



from unittest.mock import MagicMock




from automashup.src.segment import Segment





class TestSegmentInit(unittest.TestCase):



    """Tests for Segment initialization."""




    def test_basic_initialization(self):



        """Test basic segment creation from dict."""



        segment_dict = {



            "start": 0.5,



            "end": 10.5,



            "label": "verse"



        }



        segment = Segment(segment_dict)




        self.assertEqual(segment.start, 0.5)



        self.assertEqual(segment.end, 10.5)



        self.assertEqual(segment.label, "verse")



        self.assertEqual(segment.duration, 10.0)




    def test_initialization_attributes_none(self):



        """Test that track-related attributes are None before association."""



        segment_dict = {"start": 0.0, "end": 5.0, "label": "intro"}



        segment = Segment(segment_dict)




        self.assertIsNone(segment.sr)



        self.assertIsNone(segment.start_samples)



        self.assertIsNone(segment.end_samples)



        self.assertIsNone(segment.duration_samples)



        self.assertIsNone(segment.audio)





class TestSegmentSetStart(unittest.TestCase):



    """Tests for the set_start method."""




    def setUp(self):



        """Create a segment with sample rate set."""



        self.segment = Segment({"start": 1.0, "end": 5.0, "label": "verse"})



        self.segment.sr = 44100



        self.segment._start_samples = int(1.0 * 44100)



        self.segment._end_samples = int(5.0 * 44100)



        self.segment._duration_samples = int(4.0 * 44100)




    def test_set_start_valid(self):



        """Test setting a valid start time."""



        self.segment.set_start(2.0)
        



        self.assertEqual(self.segment.start, 2.0)



        self.assertEqual(self.segment.duration, 3.0)  # 5.0 - 2.0




    def test_set_start_sample_conversion(self):



        """Test that setting start correctly updates sample values."""



        self.segment.set_start(2.0)
        



        expected_start_samples = int(2.0 * 44100)



        expected_duration_samples = int(3.0 * 44100)
        



        self.assertEqual(self.segment.start_samples, expected_start_samples)



        self.assertEqual(self.segment.duration_samples, expected_duration_samples)




    def test_set_start_negative_raises_error(self):



        """Test that negative start time raises AssertionError."""



        with self.assertRaises(AssertionError):



            self.segment.set_start(-1.0)




    def test_set_start_greater_than_end_raises_error(self):



        """Test that start >= end raises AssertionError."""



        with self.assertRaises(AssertionError):



            self.segment.set_start(6.0)




    def test_set_start_without_sr_raises_error(self):



        """Test that setting start without sample rate raises ValueError."""



        segment = Segment({"start": 1.0, "end": 5.0, "label": "verse"})



        with self.assertRaises(ValueError):



            segment.set_start(2.0)





class TestSegmentSetEnd(unittest.TestCase):



    """Tests for the set_end method."""




    def setUp(self):



        """Create a segment with sample rate set."""



        self.segment = Segment({"start": 1.0, "end": 5.0, "label": "verse"})



        self.segment.sr = 44100



        self.segment._start_samples = int(1.0 * 44100)



        self.segment._end_samples = int(5.0 * 44100)



        self.segment._duration_samples = int(4.0 * 44100)




    def test_set_end_valid(self):



        """Test setting a valid end time."""



        self.segment.set_end(10.0)
        



        self.assertEqual(self.segment.end, 10.0)



        self.assertEqual(self.segment.duration, 9.0)  # 10.0 - 1.0




    def test_set_end_sample_conversion(self):



        """Test that setting end correctly updates sample values."""



        self.segment.set_end(10.0)
        



        expected_end_samples = int(10.0 * 44100)



        expected_duration_samples = int(9.0 * 44100)
        



        self.assertEqual(self.segment.end_samples, expected_end_samples)



        self.assertEqual(self.segment.duration_samples, expected_duration_samples)




    def test_set_end_without_sr_raises_error(self):



        """Test that setting end without sample rate raises ValueError."""



        segment = Segment({"start": 1.0, "end": 5.0, "label": "verse"})



        with self.assertRaises(ValueError):



            segment.set_end(10.0)





class TestSegmentSetKey(unittest.TestCase):



    """Tests for the set_key method."""




    def test_set_key_without_audio(self):



        """Test setting key without providing new audio."""



        segment = Segment({"start": 0.0, "end": 5.0, "label": "verse"})



        segment.set_key("A minor")
        



        self.assertEqual(segment.key, "A minor")



        self.assertTrue(segment.audio_was_modified)



        self.assertIsNone(segment.audio)




    def test_set_key_with_audio(self):



        """Test setting key with new audio."""



        segment = Segment({"start": 0.0, "end": 5.0, "label": "verse"})



        new_audio = np.array([1, 2, 3, 4, 5])



        segment.set_key("G major", new_audio=new_audio)
        



        self.assertEqual(segment.key, "G major")



        np.testing.assert_array_equal(segment.audio, new_audio)





class TestSegmentSetDownbeats(unittest.TestCase):



    """Tests for the set_downbeats method."""




    def setUp(self):



        """Create a segment with sample rate set."""



        self.segment = Segment({"start": 0.0, "end": 10.0, "label": "verse"})



        self.segment.sr = 44100




    def test_set_downbeats_from_list(self):



        """Test setting downbeats from a list."""



        downbeats = [0.5, 1.0, 1.5, 2.0]


        self.segment.set_downbeats(downbeats)
        



        np.testing.assert_array_equal(self.segment.downbeats, np.array(downbeats))




    def test_set_downbeats_sample_conversion(self):



        """Test that downbeats are correctly converted to samples."""



        downbeats = [0.0, 1.0, 2.0]


        self.segment.set_downbeats(downbeats)
        



        expected_samples = np.array([0, 44100, 88200])



        np.testing.assert_array_equal(self.segment.downbeats_samples, expected_samples)




    def test_set_downbeats_from_array(self):



        """Test setting downbeats from a numpy array."""



        downbeats = np.array([0.25, 0.5, 0.75])


        self.segment.set_downbeats(downbeats)
        



        np.testing.assert_array_equal(self.segment.downbeats, downbeats)




    def test_set_downbeats_without_sr_raises_error(self):



        """Test that setting downbeats without sample rate raises ValueError."""



        segment = Segment({"start": 0.0, "end": 5.0, "label": "verse"})



        with self.assertRaises(ValueError):


            segment.set_downbeats([0.5, 1.0])





class TestSegmentAssociateTrackInfo(unittest.TestCase):



    """Tests for the associate_track_info method."""




    def test_associate_track_info_basic(self):



        """Test basic track association."""



        segment = Segment({"start": 1.0, "end": 3.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 44100



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(44100 * 5)  # 5 seconds of audio



        track.downbeats = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        



        segment.associate_track_info(track)
        



        self.assertEqual(segment.sr, 44100)



        self.assertEqual(segment.key, "C major")



        self.assertEqual(segment.bpm, 120.0)




    def test_associate_track_info_sample_calculation(self):



        """Test that sample positions are calculated correctly."""



        segment = Segment({"start": 1.0, "end": 3.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 44100



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(44100 * 5)



        track.downbeats = np.array([0.5, 1.5, 2.5, 3.5])
        



        segment.associate_track_info(track)
        



        self.assertEqual(segment.start_samples, 44100)



        self.assertEqual(segment.end_samples, 44100 * 3)



        self.assertEqual(segment.duration_samples, 44100 * 2)




    def test_associate_track_info_downbeat_extraction(self):



        """Test that downbeats within segment are extracted correctly."""



        segment = Segment({"start": 1.0, "end": 3.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 44100



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(44100 * 5)



        track.downbeats = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
        



        segment.associate_track_info(track)
        



        # Downbeats within [1.0, 3.0] should be [1.0, 1.5, 2.0, 2.5, 3.0]



        expected_downbeats = np.array([1.0, 1.5, 2.0, 2.5, 3.0])



        np.testing.assert_array_equal(segment.downbeats, expected_downbeats)




    def test_associate_track_info_audio_extraction(self):



        """Test that audio segment is extracted correctly."""



        segment = Segment({"start": 1.0, "end": 2.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 100  # Simple sample rate for easy calculation



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(500)  # 5 seconds



        track.downbeats = np.array([0.5, 1.5])
        



        segment.associate_track_info(track)
        



        # Audio from sample 100 to 200



        expected_audio = np.arange(100, 200)



        np.testing.assert_array_equal(segment.original_audio, expected_audio)



        np.testing.assert_array_equal(segment.audio, expected_audio)





class TestSegmentGetAudioBarwise(unittest.TestCase):



    """Tests for the get_audio_barwise method - central function."""




    def test_get_audio_barwise_basic(self):



        """Test basic barwise audio extraction with fake audio."""



        segment = Segment({"start": 0.0, "end": 4.0, "label": "verse"})
        



        # Create fake track with known audio pattern



        track = MagicMock()



        track.sr = 10  # 10 samples per second for easy calculation



        track.key = "C major"



        track.bpm = 120.0



        # Audio: [0, 1, 2, ..., 39] for 4 seconds at 10 samples/sec



        track.audio = np.arange(40)



        # Downbeats at 0, 1, 2, 3, 4 seconds



        track.downbeats = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        



        segment.associate_track_info(track)
        



        result = segment.get_audio_barwise()
        



        # Should have 4 bars (downbeats 0-1, 1-2, 2-3, 3-4)



        self.assertEqual(len(result), 4)



        # Bar 0: samples 0-9



        np.testing.assert_array_equal(result[0], np.arange(0, 10))



        # Bar 1: samples 10-19



        np.testing.assert_array_equal(result[1], np.arange(10, 20))



        # Bar 2: samples 20-29



        np.testing.assert_array_equal(result[2], np.arange(20, 30))



        # Bar 3: samples 30-39



        np.testing.assert_array_equal(result[3], np.arange(30, 40))




    def test_get_audio_barwise_with_offset(self):



        """Test barwise extraction when segment doesn't start at 0."""



        segment = Segment({"start": 2.0, "end": 4.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 10



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(50)  # 5 seconds



        # Downbeats at 0, 1, 2, 3, 4 seconds



        track.downbeats = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        



        segment.associate_track_info(track)
        



        result = segment.get_audio_barwise()
        



        # Should have 2 bars (downbeats 2-3, 3-4 within segment)



        self.assertEqual(len(result), 2)



        # Bar 0: samples 20-29 in track, but 0-9 in segment audio



        np.testing.assert_array_equal(result[0], np.arange(20, 30))



        # Bar 1: samples 30-39 in track, but 10-19 in segment audio



        np.testing.assert_array_equal(result[1], np.arange(30, 40))




    def test_get_audio_barwise_uneven_bars(self):



        """Test barwise extraction with bars of different lengths."""



        segment = Segment({"start": 0.0, "end": 3.5, "label": "verse"})
        



        track = MagicMock()



        track.sr = 10



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(35)



        # Downbeats at irregular intervals



        track.downbeats = np.array([0.0, 0.5, 1.5, 3.5])
        



        segment.associate_track_info(track)
        



        result = segment.get_audio_barwise()
        



        # Should have 3 bars



        self.assertEqual(len(result), 3)



        # Bar 0: 0.0 to 0.5 seconds = 5 samples



        self.assertEqual(len(result[0]), 5)



        # Bar 1: 0.5 to 1.5 seconds = 10 samples



        self.assertEqual(len(result[1]), 10)



        # Bar 2: 1.5 to 3.5 seconds = 20 samples



        self.assertEqual(len(result[2]), 20)




    def test_get_audio_barwise_single_bar(self):



        """Test barwise extraction with only one bar."""



        segment = Segment({"start": 0.0, "end": 2.0, "label": "intro"})
        



        track = MagicMock()



        track.sr = 10



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(20)



        # Only one bar from 0 to 2



        track.downbeats = np.array([0.0, 2.0])
        



        segment.associate_track_info(track)
        



        result = segment.get_audio_barwise()
        



        self.assertEqual(len(result), 1)



        np.testing.assert_array_equal(result[0], np.arange(20))





class TestSegmentGetAudioSegment(unittest.TestCase):



    """Tests for the get_audio_segment method."""




    def test_get_audio_segment_not_modified(self):



        """Test getting audio when it wasn't modified."""



        segment = Segment({"start": 0.0, "end": 1.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 10



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(20)



        track.downbeats = np.array([0.0, 1.0])
        



        segment.associate_track_info(track)
        



        result = segment.get_audio_segment()



        np.testing.assert_array_equal(result, np.arange(10))




    def test_get_audio_segment_raises_without_association(self):



        """Test that getting audio raises error without track association."""



        segment = Segment({"start": 0.0, "end": 1.0, "label": "verse"})
        



        with self.assertRaises(ValueError):
            segment.get_audio_segment()





class TestSegmentOffsetSegment(unittest.TestCase):



    """Tests for the offset_segment method."""




    def setUp(self):



        """Create a segment with track association."""



        self.segment = Segment({"start": 1.0, "end": 3.0, "label": "verse"})
        



        track = MagicMock()



        track.sr = 100



        track.key = "C major"



        track.bpm = 120.0



        track.audio = np.arange(500)



        track.downbeats = np.array([0.5, 1.5, 2.5, 3.5])
        



        self.segment.associate_track_info(track)




    def test_offset_by_time(self):



        """Test offsetting segment by time."""



        self.segment.offset_segment(offset_time=1.0)
        



        self.assertEqual(self.segment.start, 2.0)



        self.assertEqual(self.segment.end, 4.0)



        self.assertEqual(self.segment.duration, 2.0)  # Duration should stay same




    def test_offset_by_samples(self):



        """Test offsetting segment by samples."""



        self.segment.offset_segment(offset_samples=100)  # 1 second at sr=100
        



        self.assertEqual(self.segment.start, 2.0)



        self.assertEqual(self.segment.end, 4.0)




    def test_offset_requires_time_or_samples(self):



        """Test that offset requires either time or samples."""



        with self.assertRaises(AssertionError):
            self.segment.offset_segment()





if __name__ == '__main__':
    unittest.main()



