import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trafficSimulator import RoadNetwork, Segment, QuadraticCurve, CubicCurve


class TestRoadNetworkInitialization:
    def test_empty_network_on_creation(self):
        network = RoadNetwork()
        assert len(network) == 0
        assert network.get_segment_count() == 0

    def test_segments_property_returns_list(self):
        network = RoadNetwork()
        assert isinstance(network.segments, list)
        assert len(network.segments) == 0


class TestRoadNetworkSegmentCreation:
    def test_create_segment_returns_index(self):
        network = RoadNetwork()
        idx = network.create_segment((0, 0), (100, 0))
        assert idx == 0

    def test_create_multiple_segments_returns_sequential_indices(self):
        network = RoadNetwork()
        idx0 = network.create_segment((0, 0), (100, 0))
        idx1 = network.create_segment((100, 0), (200, 0))
        idx2 = network.create_segment((200, 0), (300, 0))
        assert idx0 == 0
        assert idx1 == 1
        assert idx2 == 2
        assert len(network) == 3

    def test_create_segment_with_multiple_points(self):
        network = RoadNetwork()
        idx = network.create_segment((0, 0), (50, 10), (100, 0))
        assert idx == 0
        segment = network.get_segment(0)
        assert len(segment.points) == 3

    def test_create_quadratic_bezier_curve(self):
        network = RoadNetwork()
        idx = network.create_quadratic_bezier_curve(
            start=(0, 0),
            control=(50, 50),
            end=(100, 0)
        )
        assert idx == 0
        assert len(network) == 1
        segment = network.get_segment(0)
        assert isinstance(segment, QuadraticCurve)

    def test_create_cubic_bezier_curve(self):
        network = RoadNetwork()
        idx = network.create_cubic_bezier_curve(
            start=(0, 0),
            control_1=(25, 50),
            control_2=(75, 50),
            end=(100, 0)
        )
        assert idx == 0
        assert len(network) == 1
        segment = network.get_segment(0)
        assert isinstance(segment, CubicCurve)

    def test_add_segment_directly(self):
        network = RoadNetwork()
        segment = Segment(((0, 0), (100, 0)))
        idx = network.add_segment(segment)
        assert idx == 0
        assert network.get_segment(0) is segment


class TestRoadNetworkSegmentAccess:
    def test_get_segment_valid_index(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        segment = network.get_segment(0)
        assert segment is not None

    def test_get_segment_invalid_index_returns_none(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        assert network.get_segment(1) is None
        assert network.get_segment(-1) is None
        assert network.get_segment(100) is None

    def test_get_segment_empty_network_returns_none(self):
        network = RoadNetwork()
        assert network.get_segment(0) is None

    def test_indexing_operator(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        assert network[0] is network.get_segment(0)
        assert network[1] is network.get_segment(1)

    def test_indexing_out_of_bounds_raises_error(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        with pytest.raises(IndexError):
            _ = network[5]


class TestRoadNetworkIteration:
    def test_iteration_over_segments(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        network.create_segment((200, 0), (300, 0))
        
        segments = list(network)
        assert len(segments) == 3
        for i, segment in enumerate(segments):
            assert segment is network.get_segment(i)

    def test_iteration_empty_network(self):
        network = RoadNetwork()
        segments = list(network)
        assert segments == []

    def test_enumerate_segments(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        
        for idx, segment in enumerate(network):
            assert segment is network[idx]


class TestRoadNetworkVehicleTransfer:
    def test_transfer_vehicle_between_segments(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        
        # Simulate a vehicle ID
        vehicle_id = "test-vehicle-123"
        network[0].vehicles.append(vehicle_id)
        
        assert vehicle_id in network[0].vehicles
        assert vehicle_id not in network[1].vehicles
        
        result = network.transfer_vehicle(vehicle_id, 0, 1)
        
        assert result is True
        assert vehicle_id not in network[0].vehicles
        assert vehicle_id in network[1].vehicles

    def test_transfer_vehicle_invalid_from_segment(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        
        result = network.transfer_vehicle("vehicle", 99, 0)
        assert result is False

    def test_transfer_vehicle_invalid_to_segment(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        
        result = network.transfer_vehicle("vehicle", 0, 99)
        assert result is False

    def test_transfer_vehicle_not_in_source_segment(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        
        # Transfer vehicle that doesn't exist in source - should still add to destination
        result = network.transfer_vehicle("nonexistent", 0, 1)
        assert result is True
        assert "nonexistent" in network[1].vehicles


class TestRoadNetworkSegmentProperties:
    def test_segment_has_length(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        segment = network.get_segment(0)
        assert segment.get_length() == pytest.approx(100.0, rel=0.01)

    def test_segment_has_vehicles_deque(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        segment = network.get_segment(0)
        assert hasattr(segment, 'vehicles')
        assert len(segment.vehicles) == 0

    def test_curve_segment_has_length(self):
        network = RoadNetwork()
        network.create_quadratic_bezier_curve((0, 0), (50, 50), (100, 0))
        segment = network.get_segment(0)
        # Curve length should be greater than straight line distance
        assert segment.get_length() > 100.0


class TestRoadNetworkMixedSegments:
    def test_mixed_segment_types(self):
        network = RoadNetwork()
        
        # Straight segment
        idx0 = network.create_segment((0, 0), (100, 0))
        # Quadratic curve
        idx1 = network.create_quadratic_bezier_curve((100, 0), (150, 50), (200, 0))
        # Cubic curve
        idx2 = network.create_cubic_bezier_curve((200, 0), (225, 25), (275, 25), (300, 0))
        # Another straight segment
        idx3 = network.create_segment((300, 0), (400, 0))
        
        assert len(network) == 4
        assert idx0 == 0
        assert idx1 == 1
        assert idx2 == 2
        assert idx3 == 3
        
        # Verify types
        assert isinstance(network[1], QuadraticCurve)
        assert isinstance(network[2], CubicCurve)
