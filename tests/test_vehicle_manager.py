import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trafficSimulator import RoadNetwork, VehicleManager, Vehicle, VehicleGenerator


class TestVehicleManagerCreation(unittest.TestCase):
    """Tests for VehicleManager initialization."""

    def test_init_with_road_network(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        self.assertEqual(manager.get_vehicle_count(), 0)
        self.assertEqual(len(manager.generators), 0)

    def test_vehicles_property_returns_dict(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        self.assertIsInstance(manager.vehicles, dict)

    def test_generators_property_returns_list(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        self.assertIsInstance(manager.generators, list)


class TestVehicleManagerVehicleOperations(unittest.TestCase):
    """Tests for adding and managing vehicles."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (100, 0))
        self.network.create_segment((100, 0), (200, 0))
        self.manager = VehicleManager(self.network)

    def test_add_vehicle(self):
        vehicle = Vehicle({'path': [0], 'x': 0, 'v': 10})
        self.manager.add_vehicle(vehicle)
        
        self.assertEqual(self.manager.get_vehicle_count(), 1)
        self.assertIn(vehicle.id, self.manager.vehicles)

    def test_add_vehicle_places_on_segment(self):
        vehicle = Vehicle({'path': [0], 'x': 0, 'v': 10})
        self.manager.add_vehicle(vehicle)
        
        segment = self.network.get_segment(0)
        self.assertIn(vehicle.id, segment.vehicles)

    def test_add_vehicle_with_different_starting_segment(self):
        vehicle = Vehicle({'path': [1], 'x': 0, 'v': 10})
        self.manager.add_vehicle(vehicle)
        
        self.assertNotIn(vehicle.id, self.network.get_segment(0).vehicles)
        self.assertIn(vehicle.id, self.network.get_segment(1).vehicles)

    def test_add_vehicle_with_empty_path(self):
        vehicle = Vehicle({'path': [], 'x': 0, 'v': 10})
        self.manager.add_vehicle(vehicle)
        
        # Should still be added to manager, just not placed on segment
        self.assertEqual(self.manager.get_vehicle_count(), 1)

    def test_get_vehicle_returns_correct_vehicle(self):
        vehicle = Vehicle({'path': [0], 'x': 5, 'v': 15})
        self.manager.add_vehicle(vehicle)
        
        retrieved = self.manager.get_vehicle(vehicle.id)
        self.assertIs(retrieved, vehicle)
        self.assertEqual(retrieved.x, 5)
        self.assertEqual(retrieved.v, 15)

    def test_get_vehicle_returns_none_for_unknown_id(self):
        result = self.manager.get_vehicle("nonexistent-id")
        self.assertIsNone(result)

    def test_remove_vehicle(self):
        vehicle = Vehicle({'path': [0], 'x': 0, 'v': 10})
        self.manager.add_vehicle(vehicle)
        
        removed = self.manager.remove_vehicle(vehicle.id)
        
        self.assertIs(removed, vehicle)
        self.assertEqual(self.manager.get_vehicle_count(), 0)
        self.assertIsNone(self.manager.get_vehicle(vehicle.id))

    def test_remove_vehicle_returns_none_for_unknown_id(self):
        result = self.manager.remove_vehicle("nonexistent-id")
        self.assertIsNone(result)

    def test_create_vehicle(self):
        vehicle = self.manager.create_vehicle(path=[0], x=10, v=20)
        
        self.assertEqual(self.manager.get_vehicle_count(), 1)
        self.assertEqual(vehicle.x, 10)
        self.assertEqual(vehicle.v, 20)
        self.assertIn(vehicle.id, self.manager.vehicles)


class TestVehicleManagerMultipleVehicles(unittest.TestCase):
    """Tests for managing multiple vehicles."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (200, 0))
        self.manager = VehicleManager(self.network)

    def test_add_multiple_vehicles(self):
        v1 = Vehicle({'path': [0], 'x': 0, 'v': 10})
        v2 = Vehicle({'path': [0], 'x': 20, 'v': 10})
        v3 = Vehicle({'path': [0], 'x': 40, 'v': 10})
        
        self.manager.add_vehicle(v1)
        self.manager.add_vehicle(v2)
        self.manager.add_vehicle(v3)
        
        self.assertEqual(self.manager.get_vehicle_count(), 3)

    def test_multiple_vehicles_on_same_segment(self):
        v1 = Vehicle({'path': [0], 'x': 0, 'v': 10})
        v2 = Vehicle({'path': [0], 'x': 20, 'v': 10})
        
        self.manager.add_vehicle(v1)
        self.manager.add_vehicle(v2)
        
        segment = self.network.get_segment(0)
        self.assertEqual(len(segment.vehicles), 2)
        self.assertIn(v1.id, segment.vehicles)
        self.assertIn(v2.id, segment.vehicles)

    def test_vehicles_have_unique_ids(self):
        v1 = self.manager.create_vehicle(path=[0], x=0, v=10)
        v2 = self.manager.create_vehicle(path=[0], x=20, v=10)
        v3 = self.manager.create_vehicle(path=[0], x=40, v=10)
        
        ids = {v1.id, v2.id, v3.id}
        self.assertEqual(len(ids), 3)


class TestVehicleManagerGenerators(unittest.TestCase):
    """Tests for vehicle generator management."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (200, 0))
        self.manager = VehicleManager(self.network)

    def test_add_generator(self):
        generator = VehicleGenerator({
            'vehicle_rate': 10,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        self.manager.add_generator(generator)
        
        self.assertEqual(len(self.manager.generators), 1)

    def test_add_multiple_generators(self):
        gen1 = VehicleGenerator({'vehicles': [(1, {'path': [0], 'v': 10})]})
        gen2 = VehicleGenerator({'vehicles': [(1, {'path': [0], 'v': 15})]})
        
        self.manager.add_generator(gen1)
        self.manager.add_generator(gen2)
        
        self.assertEqual(len(self.manager.generators), 2)

    def test_create_generator(self):
        generator = self.manager.create_generator(
            vehicle_rate=20,
            vehicles=[(1, {'path': [0], 'v': 10})]
        )
        
        self.assertEqual(len(self.manager.generators), 1)
        self.assertEqual(generator.vehicle_rate, 20)


class TestVehicleManagerGeneratorUpdates(unittest.TestCase):
    """Tests for generator update logic."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (200, 0))
        self.manager = VehicleManager(self.network)

    def test_update_generators_spawns_vehicle_when_time_elapsed(self):
        generator = VehicleGenerator({
            'vehicle_rate': 60,  # 1 vehicle per second
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        self.manager.add_generator(generator)
        
        # Simulate 1 second elapsed
        self.manager.update_generators(t=1.0)
        
        self.assertEqual(self.manager.get_vehicle_count(), 1)

    def test_update_generators_no_spawn_before_interval(self):
        generator = VehicleGenerator({
            'vehicle_rate': 60,  # 1 vehicle per second
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        self.manager.add_generator(generator)
        
        # Simulate 0.5 seconds elapsed (not enough time)
        self.manager.update_generators(t=0.5)
        
        self.assertEqual(self.manager.get_vehicle_count(), 0)

    def test_update_generators_multiple_spawns_over_time(self):
        generator = VehicleGenerator({
            'vehicle_rate': 60,  # 1 vehicle per second
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        self.manager.add_generator(generator)
        
        # Spawn first vehicle at t=1
        self.manager.update_generators(t=1.0)
        self.assertEqual(self.manager.get_vehicle_count(), 1)
        
        # Move existing vehicle forward to make room
        for vid in self.manager.vehicles:
            self.manager.vehicles[vid].x = 50
        
        # Spawn second vehicle at t=2
        self.manager.update_generators(t=2.0)
        self.assertEqual(self.manager.get_vehicle_count(), 2)

    def test_update_generators_no_spawn_when_no_space(self):
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        self.manager.add_generator(generator)
        
        # Spawn first vehicle
        self.manager.update_generators(t=1.0)
        # Don't move the vehicle, so there's no space
        
        # Try to spawn second vehicle
        self.manager.update_generators(t=2.0)
        
        # Should still be only 1 vehicle (no space for second)
        self.assertEqual(self.manager.get_vehicle_count(), 1)

    def test_update_generators_spawns_when_space_available(self):
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        self.manager.add_generator(generator)
        
        # Spawn first vehicle
        self.manager.update_generators(t=1.0)
        
        # Move existing vehicle forward (beyond s0 + l)
        for vid in self.manager.vehicles:
            v = self.manager.vehicles[vid]
            v.x = v.s0 + v.l + 10  # Move past minimum gap
        
        # Now there should be space
        self.manager.update_generators(t=2.0)
        self.assertEqual(self.manager.get_vehicle_count(), 2)

    def test_update_generators_with_no_generators(self):
        # Should not raise any errors
        self.manager.update_generators(t=1.0)
        self.assertEqual(self.manager.get_vehicle_count(), 0)

    def test_update_generators_with_invalid_segment(self):
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [99], 'v': 10})]  # Invalid segment
        })
        self.manager.add_generator(generator)
        
        # Should not raise, just not spawn
        self.manager.update_generators(t=1.0)
        self.assertEqual(self.manager.get_vehicle_count(), 0)


class TestVehicleManagerIsolation(unittest.TestCase):
    """Tests verifying VehicleManager works independently."""

    def test_manager_does_not_modify_network_structure(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        initial_count = network.get_segment_count()
        
        manager = VehicleManager(network)
        manager.create_vehicle(path=[0], x=0, v=10)
        manager.create_generator(vehicles=[(1, {'path': [0], 'v': 10})])
        
        self.assertEqual(network.get_segment_count(), initial_count)

    def test_multiple_managers_same_network(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        
        manager1 = VehicleManager(network)
        manager2 = VehicleManager(network)
        
        v1 = manager1.create_vehicle(path=[0], x=0, v=10)
        v2 = manager2.create_vehicle(path=[0], x=50, v=10)
        
        # Each manager tracks its own vehicles
        self.assertEqual(manager1.get_vehicle_count(), 1)
        self.assertEqual(manager2.get_vehicle_count(), 1)
        
        # But both vehicles are on the same segment
        segment = network.get_segment(0)
        self.assertEqual(len(segment.vehicles), 2)


class TestVehicleProperties(unittest.TestCase):
    """Tests verifying vehicle properties are correctly set."""

    def setUp(self):
        self.network = RoadNetwork()
        self.network.create_segment((0, 0), (100, 0))
        self.manager = VehicleManager(self.network)

    def test_vehicle_default_properties(self):
        vehicle = self.manager.create_vehicle(path=[0])
        
        self.assertEqual(vehicle.x, 0)
        self.assertEqual(vehicle.v, 0)
        self.assertEqual(vehicle.path, [0])
        self.assertEqual(vehicle.current_road_index, 0)

    def test_vehicle_custom_properties(self):
        vehicle = self.manager.create_vehicle(
            path=[0, 1],
            x=25,
            v=15,
            v_max=20
        )
        
        self.assertEqual(vehicle.x, 25)
        self.assertEqual(vehicle.v, 15)
        self.assertEqual(vehicle.v_max, 20)
        self.assertEqual(vehicle.path, [0, 1])

    def test_vehicle_has_required_attributes(self):
        vehicle = self.manager.create_vehicle(path=[0])
        
        # These attributes are needed for simulation
        self.assertTrue(hasattr(vehicle, 'id'))
        self.assertTrue(hasattr(vehicle, 'x'))
        self.assertTrue(hasattr(vehicle, 'v'))
        self.assertTrue(hasattr(vehicle, 'l'))
        self.assertTrue(hasattr(vehicle, 's0'))
        self.assertTrue(hasattr(vehicle, 'path'))
        self.assertTrue(hasattr(vehicle, 'current_road_index'))


if __name__ == '__main__':
    unittest.main()
