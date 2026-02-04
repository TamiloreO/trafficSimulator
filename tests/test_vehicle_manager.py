import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trafficSimulator import RoadNetwork, VehicleManager, Vehicle, VehicleGenerator


class TestVehicleManagerInitialization:
    def test_empty_manager_on_creation(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        assert manager.get_vehicle_count() == 0
        assert len(manager.vehicles) == 0
        assert len(manager.generators) == 0

    def test_manager_holds_reference_to_network(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        # Manager should work with the provided network
        network.create_segment((0, 0), (100, 0))
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        # Vehicle should be on segment 0
        assert vehicle.id in network[0].vehicles


class TestVehicleManagerAddVehicle:
    def test_add_vehicle_increments_count(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        
        assert manager.get_vehicle_count() == 1

    def test_add_vehicle_stores_in_vehicles_dict(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        
        assert vehicle.id in manager.vehicles
        assert manager.vehicles[vehicle.id] is vehicle

    def test_add_vehicle_places_on_starting_segment(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [1, 0]})  # Starts on segment 1
        manager.add_vehicle(vehicle)
        
        assert vehicle.id in network[1].vehicles
        assert vehicle.id not in network[0].vehicles

    def test_add_vehicle_with_empty_path(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': []})
        manager.add_vehicle(vehicle)
        
        # Should still be added to manager, just not placed on any segment
        assert manager.get_vehicle_count() == 1
        assert len(network[0].vehicles) == 0

    def test_add_multiple_vehicles(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        v1 = Vehicle({'path': [0], 'x': 0})
        v2 = Vehicle({'path': [0], 'x': 20})
        v3 = Vehicle({'path': [0], 'x': 40})
        
        manager.add_vehicle(v1)
        manager.add_vehicle(v2)
        manager.add_vehicle(v3)
        
        assert manager.get_vehicle_count() == 3
        assert len(network[0].vehicles) == 3


class TestVehicleManagerGetVehicle:
    def test_get_vehicle_by_id(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        
        retrieved = manager.get_vehicle(vehicle.id)
        assert retrieved is vehicle

    def test_get_vehicle_nonexistent_returns_none(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        assert manager.get_vehicle("nonexistent-id") is None

    def test_get_vehicle_after_multiple_adds(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicles = [Vehicle({'path': [0]}) for _ in range(5)]
        for v in vehicles:
            manager.add_vehicle(v)
        
        # Should be able to retrieve any vehicle
        for v in vehicles:
            assert manager.get_vehicle(v.id) is v


class TestVehicleManagerRemoveVehicle:
    def test_remove_vehicle_decrements_count(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        assert manager.get_vehicle_count() == 1
        
        removed = manager.remove_vehicle(vehicle.id)
        assert manager.get_vehicle_count() == 0
        assert removed is vehicle

    def test_remove_vehicle_returns_vehicle(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        
        removed = manager.remove_vehicle(vehicle.id)
        assert removed is vehicle

    def test_remove_nonexistent_vehicle_returns_none(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        removed = manager.remove_vehicle("nonexistent")
        assert removed is None

    def test_remove_vehicle_removes_from_dict(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        manager.remove_vehicle(vehicle.id)
        
        assert vehicle.id not in manager.vehicles
        assert manager.get_vehicle(vehicle.id) is None


class TestVehicleManagerCreateVehicle:
    def test_create_vehicle_returns_vehicle(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = manager.create_vehicle(path=[0], v=10.0)
        
        assert isinstance(vehicle, Vehicle)
        assert vehicle.path == [0]
        assert vehicle.v == 10.0

    def test_create_vehicle_adds_to_manager(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = manager.create_vehicle(path=[0])
        
        assert manager.get_vehicle_count() == 1
        assert manager.get_vehicle(vehicle.id) is vehicle

    def test_create_vehicle_places_on_segment(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = manager.create_vehicle(path=[0])
        
        assert vehicle.id in network[0].vehicles


class TestVehicleManagerGenerators:
    def test_add_generator(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        generator = VehicleGenerator({'vehicle_rate': 10})
        manager.add_generator(generator)
        
        assert len(manager.generators) == 1
        assert manager.generators[0] is generator

    def test_add_multiple_generators(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        gen1 = VehicleGenerator({'vehicle_rate': 10})
        gen2 = VehicleGenerator({'vehicle_rate': 20})
        
        manager.add_generator(gen1)
        manager.add_generator(gen2)
        
        assert len(manager.generators) == 2

    def test_create_generator_returns_generator(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        generator = manager.create_generator(vehicle_rate=15)
        
        assert isinstance(generator, VehicleGenerator)
        assert generator.vehicle_rate == 15

    def test_create_generator_adds_to_list(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        generator = manager.create_generator(vehicle_rate=15)
        
        assert len(manager.generators) == 1
        assert manager.generators[0] is generator


class TestVehicleManagerGeneratorUpdate:
    def test_update_generators_spawns_vehicle_when_time_elapsed(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        # Rate of 60 = 1 vehicle per second
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        manager.add_generator(generator)
        
        assert manager.get_vehicle_count() == 0
        
        # Update at t=1.0 (1 second elapsed)
        manager.update_generators(1.0)
        
        assert manager.get_vehicle_count() == 1

    def test_update_generators_respects_vehicle_rate(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        # Rate of 60 = 1 vehicle per second
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        manager.add_generator(generator)
        
        # Update at t=0.5 (not enough time)
        manager.update_generators(0.5)
        assert manager.get_vehicle_count() == 0
        
        # Update at t=1.0 (enough time)
        manager.update_generators(1.0)
        assert manager.get_vehicle_count() == 1

    def test_update_generators_no_spawn_when_no_space(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        # Add a vehicle at x=0 (blocking the spawn point)
        blocking_vehicle = Vehicle({'path': [0], 'x': 0, 'v': 0})
        manager.add_vehicle(blocking_vehicle)
        
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        manager.add_generator(generator)
        
        # Try to spawn at t=1.0
        manager.update_generators(1.0)
        
        # Should still be only 1 vehicle (the blocking one)
        assert manager.get_vehicle_count() == 1

    def test_update_generators_spawns_when_space_available(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        # Add a vehicle far enough ahead
        existing_vehicle = Vehicle({'path': [0], 'x': 20, 'v': 10})
        manager.add_vehicle(existing_vehicle)
        
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        manager.add_generator(generator)
        
        manager.update_generators(1.0)
        
        # Should have 2 vehicles now
        assert manager.get_vehicle_count() == 2

    def test_update_generators_updates_last_added_time(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        manager.add_generator(generator)
        
        assert generator.last_added_time == 0
        
        manager.update_generators(1.0)
        
        assert generator.last_added_time == 1.0

    def test_update_generators_with_invalid_segment(self):
        network = RoadNetwork()
        # No segments created
        manager = VehicleManager(network)
        
        generator = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [99], 'v': 10})]  # Invalid segment
        })
        manager.add_generator(generator)
        
        # Should not raise, just not spawn
        manager.update_generators(1.0)
        assert manager.get_vehicle_count() == 0

    def test_update_multiple_generators(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        manager = VehicleManager(network)
        
        gen1 = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [0], 'v': 10})]
        })
        gen2 = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [(1, {'path': [1], 'v': 10})]
        })
        
        manager.add_generator(gen1)
        manager.add_generator(gen2)
        
        manager.update_generators(1.0)
        
        # Both generators should have spawned
        assert manager.get_vehicle_count() == 2
        assert len(network[0].vehicles) == 1
        assert len(network[1].vehicles) == 1


class TestVehicleManagerVehiclesProperty:
    def test_vehicles_property_returns_dict(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        assert isinstance(manager.vehicles, dict)

    def test_vehicles_property_is_same_reference(self):
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        manager = VehicleManager(network)
        
        vehicle = Vehicle({'path': [0]})
        manager.add_vehicle(vehicle)
        
        # Should be the actual internal dict, not a copy
        vehicles_ref1 = manager.vehicles
        vehicles_ref2 = manager.vehicles
        assert vehicles_ref1 is vehicles_ref2


class TestVehicleManagerGeneratorsProperty:
    def test_generators_property_returns_list(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        assert isinstance(manager.generators, list)

    def test_generators_property_is_same_reference(self):
        network = RoadNetwork()
        manager = VehicleManager(network)
        
        gen = VehicleGenerator({})
        manager.add_generator(gen)
        
        gens_ref1 = manager.generators
        gens_ref2 = manager.generators
        assert gens_ref1 is gens_ref2


class TestVehicleManagerIntegration:
    def test_full_workflow(self):
        """Test a complete workflow of vehicle management."""
        network = RoadNetwork()
        network.create_segment((0, 0), (100, 0))
        network.create_segment((100, 0), (200, 0))
        
        manager = VehicleManager(network)
        
        # Create some vehicles directly
        v1 = manager.create_vehicle(path=[0, 1], x=50, v=10)
        v2 = manager.create_vehicle(path=[0, 1], x=20, v=10)
        
        assert manager.get_vehicle_count() == 2
        
        # Add a generator
        manager.create_generator(
            vehicle_rate=60,
            vehicles=[(1, {'path': [1], 'v': 15})]
        )
        
        # Simulate time passing
        manager.update_generators(1.0)
        
        assert manager.get_vehicle_count() == 3
        
        # Remove a vehicle
        manager.remove_vehicle(v1.id)
        
        assert manager.get_vehicle_count() == 2
        assert manager.get_vehicle(v1.id) is None
        assert manager.get_vehicle(v2.id) is v2
