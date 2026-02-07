"""
Unit Tests for Vehicle Type System

Tests follow the AAA pattern (Arrange, Act, Assert) and cover:
- Vehicle type specifications
- Vehicle factory creation
- Vehicle generator with typed vehicles
- Vehicle behavior differences
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the dearpygui module before importing anything from trafficSimulator
sys.modules['dearpygui'] = type(sys)('dearpygui')
sys.modules['dearpygui.dearpygui'] = type(sys)('dearpygui.dearpygui')

from trafficSimulator.core.vehicle_types import (
    VehicleType,
    VehicleTypeRegistry,
    CarSpecification,
    TruckSpecification,
    BusSpecification,
    MotorcycleSpecification
)
from trafficSimulator.core.vehicle_factory import VehicleFactory
from trafficSimulator.core.vehicle import Vehicle
from trafficSimulator.core.vehicle_generator import VehicleGenerator


class TestVehicleTypeSpecifications:
    """Tests for vehicle type specification classes."""

    def test_car_specification_properties(self):
        # Arrange
        spec = CarSpecification()

        # Act & Assert
        assert spec.vehicle_type == VehicleType.CAR
        assert spec.length == 4.5
        assert spec.width == 1.8
        assert spec.max_speed == 16.6
        assert spec.max_acceleration == 2.0
        assert spec.max_deceleration == 4.5
        assert spec.color == (0, 100, 255)

    def test_truck_specification_properties(self):
        # Arrange
        spec = TruckSpecification()

        # Act & Assert
        assert spec.vehicle_type == VehicleType.TRUCK
        assert spec.length == 12.0
        assert spec.width == 2.5
        assert spec.max_speed == 13.9
        assert spec.max_acceleration == 0.8
        assert spec.color == (139, 69, 19)

    def test_bus_specification_properties(self):
        # Arrange
        spec = BusSpecification()

        # Act & Assert
        assert spec.vehicle_type == VehicleType.BUS
        assert spec.length == 10.0
        assert spec.width == 2.5
        assert spec.max_speed == 14.0
        assert spec.color == (0, 180, 0)

    def test_motorcycle_specification_properties(self):
        # Arrange
        spec = MotorcycleSpecification()

        # Act & Assert
        assert spec.vehicle_type == VehicleType.MOTORCYCLE
        assert spec.length == 2.2
        assert spec.width == 0.8
        assert spec.max_speed == 19.4
        assert spec.max_acceleration == 3.5
        assert spec.color == (255, 50, 50)

    def test_specification_to_config(self):
        # Arrange
        spec = CarSpecification()

        # Act
        config = spec.to_config()

        # Assert
        assert config['l'] == spec.length
        assert config['w'] == spec.width
        assert config['v_max'] == spec.max_speed
        assert config['a_max'] == spec.max_acceleration
        assert config['b_max'] == spec.max_deceleration
        assert config['color'] == spec.color


class TestVehicleTypeRegistry:
    """Tests for the vehicle type registry."""

    def test_registry_contains_all_default_types(self):
        # Arrange & Act
        all_specs = VehicleTypeRegistry.get_all()

        # Assert
        assert VehicleType.CAR in all_specs
        assert VehicleType.TRUCK in all_specs
        assert VehicleType.BUS in all_specs
        assert VehicleType.MOTORCYCLE in all_specs

    def test_registry_get_returns_correct_specification(self):
        # Arrange & Act
        car_spec = VehicleTypeRegistry.get(VehicleType.CAR)
        truck_spec = VehicleTypeRegistry.get(VehicleType.TRUCK)

        # Assert
        assert isinstance(car_spec, CarSpecification)
        assert isinstance(truck_spec, TruckSpecification)

    def test_registry_raises_for_unknown_type(self):
        # Arrange
        class FakeType:
            pass

        # Act & Assert
        with pytest.raises(ValueError):
            VehicleTypeRegistry.get(FakeType())


class TestVehicleFactory:
    """Tests for the vehicle factory."""

    def test_factory_creates_car(self):
        # Arrange & Act
        vehicle = VehicleFactory.create_car()

        # Assert
        assert vehicle.vehicle_type == VehicleType.CAR
        assert vehicle.l == 4.5
        assert vehicle.w == 1.8
        assert vehicle.color == (0, 100, 255)

    def test_factory_creates_truck(self):
        # Arrange & Act
        vehicle = VehicleFactory.create_truck()

        # Assert
        assert vehicle.vehicle_type == VehicleType.TRUCK
        assert vehicle.l == 12.0
        assert vehicle.w == 2.5
        assert vehicle.color == (139, 69, 19)

    def test_factory_creates_bus(self):
        # Arrange & Act
        vehicle = VehicleFactory.create_bus()

        # Assert
        assert vehicle.vehicle_type == VehicleType.BUS
        assert vehicle.l == 10.0
        assert vehicle.color == (0, 180, 0)

    def test_factory_creates_motorcycle(self):
        # Arrange & Act
        vehicle = VehicleFactory.create_motorcycle()

        # Assert
        assert vehicle.vehicle_type == VehicleType.MOTORCYCLE
        assert vehicle.l == 2.2
        assert vehicle.w == 0.8
        assert vehicle.color == (255, 50, 50)

    def test_factory_applies_config_overrides(self):
        # Arrange
        custom_path = [0, 1, 2]
        custom_velocity = 10.0

        # Act
        vehicle = VehicleFactory.create_car({'path': custom_path, 'v': custom_velocity})

        # Assert
        assert vehicle.path == custom_path
        assert vehicle.v == custom_velocity
        assert vehicle.vehicle_type == VehicleType.CAR  # Type still set

    def test_factory_create_with_vehicle_type_enum(self):
        # Arrange & Act
        vehicle = VehicleFactory.create(VehicleType.TRUCK)

        # Assert
        assert vehicle.vehicle_type == VehicleType.TRUCK
        assert vehicle.l == 12.0


class TestVehicle:
    """Tests for vehicle behavior with different types."""

    def test_vehicle_default_configuration(self):
        # Arrange & Act
        vehicle = Vehicle()

        # Assert
        assert vehicle.l == 4.5
        assert vehicle.w == 1.8
        assert vehicle.v_max == 16.6
        assert vehicle.color == (0, 0, 255)

    def test_vehicle_accepts_custom_config(self):
        # Arrange
        config = {'l': 10.0, 'color': (255, 0, 0)}

        # Act
        vehicle = Vehicle(config)

        # Assert
        assert vehicle.l == 10.0
        assert vehicle.color == (255, 0, 0)

    def test_vehicle_update_without_lead(self):
        # Arrange
        vehicle = VehicleFactory.create_car({'v': 10.0})
        dt = 0.1

        # Act
        vehicle.update(None, dt)

        # Assert
        assert vehicle.x > 0  # Vehicle moved forward
        assert vehicle.a > 0  # Accelerating toward max speed

    def test_vehicle_update_with_lead_vehicle(self):
        # Arrange
        lead = VehicleFactory.create_car({'x': 20.0, 'v': 10.0})
        follower = VehicleFactory.create_car({'x': 0.0, 'v': 15.0})  # Faster
        dt = 0.1

        # Act
        follower.update(lead, dt)

        # Assert
        # Follower should decelerate when approaching slower lead
        assert follower.a < follower.a_max

    def test_truck_slower_acceleration_than_car(self):
        # Arrange
        car = VehicleFactory.create_car({'v': 5.0})
        truck = VehicleFactory.create_truck({'v': 5.0})

        # Act & Assert
        assert truck.a_max < car.a_max

    def test_motorcycle_faster_than_car(self):
        # Arrange
        car = VehicleFactory.create_car()
        motorcycle = VehicleFactory.create_motorcycle()

        # Act & Assert
        assert motorcycle.v_max > car.v_max
        assert motorcycle.a_max > car.a_max


class TestVehicleGenerator:
    """Tests for vehicle generator with typed vehicles."""

    def test_generator_creates_typed_vehicles(self):
        # Arrange
        config = {
            'vehicle_rate': 60,
            'vehicles': [
                (1, {'vehicle_type': VehicleType.CAR, 'path': [0]}),
            ]
        }
        generator = VehicleGenerator(config)

        # Act
        vehicle = generator.generate_vehicle()

        # Assert
        assert vehicle.vehicle_type == VehicleType.CAR
        assert vehicle.path == [0]

    def test_generator_creates_typed_vehicles_from_string(self):
        # Arrange
        config = {
            'vehicle_rate': 60,
            'vehicles': [
                (1, {'vehicle_type': 'truck', 'path': [0]}),
            ]
        }
        generator = VehicleGenerator(config)

        # Act
        vehicle = generator.generate_vehicle()

        # Assert
        assert vehicle.vehicle_type == VehicleType.TRUCK

    def test_generator_backward_compatible_with_legacy_config(self):
        # Arrange
        config = {
            'vehicle_rate': 60,
            'vehicles': [
                (1, {'path': [0], 'l': 5.0}),  # No vehicle_type
            ]
        }
        generator = VehicleGenerator(config)

        # Act
        vehicle = generator.generate_vehicle()

        # Assert
        assert vehicle.vehicle_type is None  # Legacy vehicle
        assert vehicle.l == 5.0


class TestVehicleBehaviorDifferences:
    """Integration tests verifying behavioral differences between vehicle types."""

    def test_acceleration_comparison_over_time(self):
        # Arrange
        car = VehicleFactory.create_car({'v': 0})
        truck = VehicleFactory.create_truck({'v': 0})
        motorcycle = VehicleFactory.create_motorcycle({'v': 0})
        dt = 0.1

        # Act - Simulate 2 seconds
        for _ in range(20):
            car.update(None, dt)
            truck.update(None, dt)
            motorcycle.update(None, dt)

        # Assert - Motorcycle should be fastest, truck slowest
        assert motorcycle.v > car.v > truck.v

    def test_following_distance_varies_by_type(self):
        # Arrange
        car = VehicleFactory.create_car()
        truck = VehicleFactory.create_truck()

        # Act & Assert
        assert truck.s0 > car.s0  # Trucks maintain larger safe distance

    def test_braking_capability_varies_by_type(self):
        # Arrange
        car = VehicleFactory.create_car()
        truck = VehicleFactory.create_truck()
        motorcycle = VehicleFactory.create_motorcycle()

        # Act & Assert
        assert motorcycle.b_max > car.b_max > truck.b_max


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
