import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trafficSimulator import RoadNetwork, Segment, QuadraticCurve, CubicCurve


class TestRoadNetworkCreation(unittest.TestCase):
    """Tests for RoadNetwork initialization and basic properties."""

    def test_init_creates_empty_network(self):
        network = RoadNetwork()
        self.assertEqual(len(network), 0)
        self.assertEqual(network.get_segment_count(), 0)

    def test_segments_property_returns_list(self):
        network = RoadNetwork()
        self.assertIsInstance(network.segments, list)


class TestRoadNetworkSegmentOperations(unittest.TestCase):
    """Tests for adding and retrieving segments."""

    def setUp(self):
        self.network = RoadNetwork()

    def test_create_segment_returns_index(self):
        idx = self.network.create_segment((0, 0), (100, 0))
        self.assertEqual(idx, 0)

    def test_create_segment_increments_count(self):
        self.network.create_segment((0, 0), (100, 0))
        self.assertEqual(self.network.get_segment_count(), 1)

    def test_create_multiple_segments_returns_sequential_indices(self):
        idx0 = self.network.create_segment((0, 0), (100, 0))
        idx1 = self.network.create_segment((100, 0), (200, 0))
        idx2 = self.network.create_segment((200, 0), (300, 0))
        
        self.assertEqual(idx0, 0)
        self.assertEqual(idx1, 1)
        self.assertEqual(idx2, 2)
        self.assertEqual(len(self.network), 3)

    def test_get_segment_returns_correct_segment(self):
        self.network.create_segment((0, 0), (100, 0))
        self.network.create_segment((100, 0), (200, 0))
        
        segment = self.network.get_segment(1)
        self.assertIsNotNone(segment)
        self.assertEqual(segment.points[0], (100, 0))
        self.assertEqual(segment.points[1], (200, 0))

    def test_get_segment_returns_none_for_invalid_index(self):
        self.network.create_segment((0, 0), (100, 0))
        
        self.assertIsNone(self.network.get_segment(-1))
        self.assertIsNone(self.network.get_segment(1))
        self.assertIsNone(self.network.get_segment(100))

    def test_add_segment_accepts_segment_object(self):
        segment = Segment(((0, 0), (50, 50), (100, 0)))
        idx = self.network.add_segment(segment)
        
        self.assertEqual(idx, 0)
        self.assertIs(self.network.get_segment(0), segment)


class TestRoadNetworkCurves(unittest.TestCase):
    """Tests for creating curved segments."""

    def setUp(self):
        self.network = RoadNetwork()

    def test_create_quadratic_bezier_curve(self):
        idx = self.network.create_quadratic_bezier_curve(
            start=(0, 0),
            control=(50, 50),
            end=(100, 0)
        )
        
        self.assertEqual(idx, 0)
        segment = self.network.get_segment(0)
        self.assertIsInstance(segment, QuadraticCurve)

    def test_create_cubic_bezier_curve(self):
        idx = self.network.create_cubic_bezier_curve(
            start=(0, 0),
            control_1=(25, 50),
            control_2=(75, 50),
            end=(100, 0)
        )
        
        self.assertEqual(idx, 0)
        segment = self.network.get_segment(0)
        self.assertIsInstance(segment, CubicCurve)

    def test_mixed_segment_types(self):
        self.network.create_segment((0, 0), (100, 0))
        self.network.create_quadratic_bezier_curve((100, 0), (150, 50), (200, 0))
        self.network.create_cubic_bezier_curve((200, 0), (225, 25), (275, 25), (300, 0))
        
        self.assertEqual(len(self.network), 3)
        self.assertIsInstance(self.network.get_segment(0), Segment)
        self.assertIsInstance(self.network.get_segment(1), QuadraticCurve)
        self.assertIsInstance(self.network.get_segment(2), CubicCurve)


class TestRoadNetworkIteration(unittest.TestCase):
    """Tests for iterating and indexing the network."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (100, 0))
        self.network.create_segment((100, 0), (200, 0))
        self.network.create_segment((200, 0), (300, 0))

    def test_iteration(self):
        segments = list(self.network)
        self.assertEqual(len(segments), 3)

    def test_indexing(self):
        segment = self.network[1]
        self.assertEqual(segment.points[0], (100, 0))

    def test_len(self):
        self.assertEqual(len(self.network), 3)

    def test_enumerate_segments(self):
        indices = []
        for idx, segment in enumerate(self.network):
            indices.append(idx)
        self.assertEqual(indices, [0, 1, 2])


class TestRoadNetworkVehicleTransfer(unittest.TestCase):
    """Tests for vehicle transfer between segments."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (100, 0))
        self.network.create_segment((100, 0), (200, 0))

    def test_transfer_vehicle_success(self):
        vehicle_id = "test-vehicle-1"
        self.network.get_segment(0).vehicles.append(vehicle_id)
        
        result = self.network.transfer_vehicle(vehicle_id, 0, 1)
        
        self.assertTrue(result)
        self.assertNotIn(vehicle_id, self.network.get_segment(0).vehicles)
        self.assertIn(vehicle_id, self.network.get_segment(1).vehicles)

    def test_transfer_vehicle_invalid_from_segment(self):
        result = self.network.transfer_vehicle("vehicle", 99, 0)
        self.assertFalse(result)

    def test_transfer_vehicle_invalid_to_segment(self):
        result = self.network.transfer_vehicle("vehicle", 0, 99)
        self.assertFalse(result)

    def test_transfer_vehicle_not_in_source(self):
        # Should still add to destination even if not in source
        result = self.network.transfer_vehicle("new-vehicle", 0, 1)
        
        self.assertTrue(result)
        self.assertIn("new-vehicle", self.network.get_segment(1).vehicles)


class TestRoadNetworkSegmentProperties(unittest.TestCase):
    """Tests verifying segment properties are accessible."""

    def setUp(self):
        self.network = RoadNetwork()

    def test_segment_has_length(self):
        self.network.create_segment((0, 0), (100, 0))
        segment = self.network.get_segment(0)
        
        self.assertAlmostEqual(segment.get_length(), 100.0, places=5)

    def test_segment_has_vehicles_deque(self):
        self.network.create_segment((0, 0), (100, 0))
        segment = self.network.get_segment(0)
        
        self.assertEqual(len(segment.vehicles), 0)
        segment.vehicles.append("test")
        self.assertEqual(len(segment.vehicles), 1)

    def test_curve_has_length(self):
        self.network.create_quadratic_bezier_curve((0, 0), (50, 50), (100, 0))
        segment = self.network.get_segment(0)
        
        # Curve length should be greater than straight line distance
        self.assertGreater(segment.get_length(), 100.0)


if __name__ == '__main__':
    unittest.main()
