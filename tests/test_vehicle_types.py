"""
Tests for the vehicle type system.

These tests verify:
- Vehicle creation with different types
- Proper error handling for invalid types
- Registry validation
- Vehicle specifications and colors
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trafficSimulator import (
    Vehicle,
    create_vehicle,
    VEHICLE_SPECS,
    VEHICLE_COLORS,
    get_vehicle_specs,
    get_vehicle_color,
    get_available_vehicle_types,
    is_valid_vehicle_type,
    validate_registry_integrity,
    VehicleTypeError,
    UnknownVehicleTypeError,
    InvalidVehicleSpecError,
    MissingVehicleColorError,
)


class TestVehicleCreation:
    """Tests for vehicle creation."""

    def test_create_car(self):
        """Test creating a car with factory function."""
        car = create_vehicle('car', path=[0])
        assert car.vehicle_type == 'car'
        assert car.l == VEHICLE_SPECS['car']['l']
        assert car.w == VEHICLE_SPECS['car']['w']
        assert car.v_max == VEHICLE_SPECS['car']['v_max']
        assert car.color == VEHICLE_COLORS['car']

    def test_create_truck(self):
        """Test creating a truck with factory function."""
        truck = create_vehicle('truck', path=[0])
        assert truck.vehicle_type == 'truck'
        assert truck.l == VEHICLE_SPECS['truck']['l']
        assert truck.w == VEHICLE_SPECS['truck']['w']
        assert truck.v_max == VEHICLE_SPECS['truck']['v_max']
        assert truck.color == VEHICLE_COLORS['truck']

    def test_create_bus(self):
        """Test creating a bus with factory function."""
        bus = create_vehicle('bus', path=[0])
        assert bus.vehicle_type == 'bus'
        assert bus.l == VEHICLE_SPECS['bus']['l']
        assert bus.v_max == VEHICLE_SPECS['bus']['v_max']
        assert bus.color == VEHICLE_COLORS['bus']

    def test_create_motorcycle(self):
        """Test creating a motorcycle with factory function."""
        motorcycle = create_vehicle('motorcycle', path=[0])
        assert motorcycle.vehicle_type == 'motorcycle'
        assert motorcycle.l == VEHICLE_SPECS['motorcycle']['l']
        assert motorcycle.v_max == VEHICLE_SPECS['motorcycle']['v_max']
        assert motorcycle.color == VEHICLE_COLORS['motorcycle']

    def test_create_vehicle_with_config(self):
        """Test creating vehicle with Vehicle class and config dict."""
        vehicle = Vehicle({'vehicle_type': 'truck', 'path': [0], 'v': 10})
        assert vehicle.vehicle_type == 'truck'
        assert vehicle.v == 10
        assert vehicle.l == VEHICLE_SPECS['truck']['l']

    def test_create_vehicle_default_type(self):
        """Test that default vehicle type is car."""
        vehicle = Vehicle({'path': [0]})
        assert vehicle.vehicle_type == 'car'
        assert vehicle.l == VEHICLE_SPECS['car']['l']

    def test_vehicle_with_custom_overrides(self):
        """Test that config can override type defaults."""
        vehicle = create_vehicle('car', path=[0], v=15, x=100)
        assert vehicle.v == 15
        assert vehicle.x == 100
        assert vehicle.l == VEHICLE_SPECS['car']['l']  # Not overridden


class TestErrorHandling:
    """Tests for error handling."""

    def test_unknown_vehicle_type_raises_error(self):
        """Test that unknown vehicle type raises UnknownVehicleTypeError."""
        with pytest.raises(UnknownVehicleTypeError) as excinfo:
            create_vehicle('spaceship', path=[0])
        
        assert 'spaceship' in str(excinfo.value)
        assert 'Unknown vehicle type' in str(excinfo.value)

    def test_unknown_type_error_includes_available_types(self):
        """Test that error message includes available types."""
        with pytest.raises(UnknownVehicleTypeError) as excinfo:
            create_vehicle('invalid_type', path=[0])
        
        error = excinfo.value
        assert error.vehicle_type == 'invalid_type'
        assert 'car' in error.available_types
        assert 'truck' in error.available_types

    def test_get_vehicle_specs_unknown_type(self):
        """Test that get_vehicle_specs raises for unknown type."""
        with pytest.raises(UnknownVehicleTypeError):
            get_vehicle_specs('unknown')

    def test_get_vehicle_color_unknown_type(self):
        """Test that get_vehicle_color raises for unknown type."""
        with pytest.raises(UnknownVehicleTypeError):
            get_vehicle_color('unknown')


class TestVehicleSpecs:
    """Tests for vehicle specifications."""

    def test_all_types_have_required_specs(self):
        """Test that all vehicle types have all required specifications."""
        required_keys = {'l', 'w', 's0', 'T', 'v_max', 'a_max', 'b_max'}
        
        for vehicle_type in get_available_vehicle_types():
            specs = get_vehicle_specs(vehicle_type)
            assert required_keys.issubset(set(specs.keys())), \
                f"Vehicle type '{vehicle_type}' missing required specs"

    def test_all_types_have_colors(self):
        """Test that all vehicle types have colors defined."""
        for vehicle_type in get_available_vehicle_types():
            color = get_vehicle_color(vehicle_type)
            assert len(color) == 4, f"Color for '{vehicle_type}' should be RGBA"
            assert all(0 <= c <= 255 for c in color), \
                f"Color values for '{vehicle_type}' should be 0-255"

    def test_vehicle_lengths_are_realistic(self):
        """Test that vehicle lengths are in realistic ranges."""
        for vehicle_type in get_available_vehicle_types():
            specs = get_vehicle_specs(vehicle_type)
            assert 1 < specs['l'] < 20, \
                f"Length for '{vehicle_type}' should be realistic"

    def test_vehicle_speeds_are_positive(self):
        """Test that all vehicle max speeds are positive."""
        for vehicle_type in get_available_vehicle_types():
            specs = get_vehicle_specs(vehicle_type)
            assert specs['v_max'] > 0, \
                f"Max speed for '{vehicle_type}' should be positive"

    def test_get_specs_returns_copy(self):
        """Test that get_vehicle_specs returns a copy, not original."""
        specs1 = get_vehicle_specs('car')
        specs1['l'] = 999
        specs2 = get_vehicle_specs('car')
        assert specs2['l'] != 999


class TestVehicleTypeComparisons:
    """Tests comparing different vehicle types."""

    def test_vehicle_lengths_differ(self):
        """Test that different vehicle types have different lengths."""
        car = create_vehicle('car')
        truck = create_vehicle('truck')
        motorcycle = create_vehicle('motorcycle')
        
        assert car.l != truck.l
        assert car.l != motorcycle.l
        assert truck.l != motorcycle.l

    def test_motorcycle_is_fastest(self):
        """Test that motorcycle has highest max speed."""
        types = get_available_vehicle_types()
        speeds = {t: get_vehicle_specs(t)['v_max'] for t in types}
        
        assert speeds['motorcycle'] == max(speeds.values())

    def test_truck_is_longest(self):
        """Test that truck is the longest vehicle."""
        types = get_available_vehicle_types()
        lengths = {t: get_vehicle_specs(t)['l'] for t in types}
        
        assert lengths['truck'] == max(lengths.values())

    def test_motorcycle_is_shortest(self):
        """Test that motorcycle is the shortest vehicle."""
        types = get_available_vehicle_types()
        lengths = {t: get_vehicle_specs(t)['l'] for t in types}
        
        assert lengths['motorcycle'] == min(lengths.values())

    def test_all_colors_unique(self):
        """Test that all vehicle types have unique colors."""
        colors = [get_vehicle_color(t) for t in get_available_vehicle_types()]
        assert len(colors) == len(set(colors))


class TestRegistryValidation:
    """Tests for registry validation functions."""

    def test_is_valid_vehicle_type(self):
        """Test is_valid_vehicle_type function."""
        assert is_valid_vehicle_type('car') is True
        assert is_valid_vehicle_type('truck') is True
        assert is_valid_vehicle_type('invalid') is False
        assert is_valid_vehicle_type('') is False

    def test_get_available_types(self):
        """Test get_available_vehicle_types returns all types."""
        types = get_available_vehicle_types()
        assert 'car' in types
        assert 'truck' in types
        assert 'bus' in types
        assert 'motorcycle' in types
        assert len(types) >= 4

    def test_validate_registry_integrity(self):
        """Test that registry validation passes for valid registry."""
        validate_registry_integrity()  # Should not raise


class TestVehicleUpdate:
    """Tests for vehicle update behavior."""

    def test_vehicle_moves_forward(self):
        """Test that vehicle moves forward when updated."""
        car = create_vehicle('car', path=[0], v=10)
        initial_x = car.x
        
        car.update(None, 0.1)
        
        assert car.x > initial_x

    def test_vehicle_follows_leader(self):
        """Test that vehicle adjusts when following a leader."""
        leader = create_vehicle('car', x=20, v=10)
        follower = create_vehicle('car', x=0, v=15)
        
        follower.update(leader, 0.1)
        
        # Follower should decelerate when faster than leader
        assert follower.a < follower.a_max

    def test_stopped_vehicle_decelerates(self):
        """Test that stopped vehicle decelerates."""
        car = create_vehicle('car', v=10)
        car.stopped = True
        
        car.update(None, 0.1)
        
        assert car.a < 0


class TestVehicleGeneratorIntegration:
    """Integration tests with VehicleGenerator."""

    def test_generator_creates_typed_vehicles(self):
        """Test that generator creates vehicles with correct types."""
        from trafficSimulator import VehicleGenerator
        
        gen = VehicleGenerator({
            'vehicle_rate': 60,
            'vehicles': [
                (1, {'path': [0], 'vehicle_type': 'truck'}),
            ]
        })
        
        vehicle = gen.generate_vehicle()
        assert vehicle.vehicle_type == 'truck'
        assert vehicle.l == VEHICLE_SPECS['truck']['l']

    def test_generator_rejects_invalid_type(self):
        """Test that generator raises error for invalid vehicle type."""
        from trafficSimulator import VehicleGenerator
        
        with pytest.raises(UnknownVehicleTypeError):
            VehicleGenerator({
                'vehicles': [
                    (1, {'path': [0], 'vehicle_type': 'invalid_type'}),
                ]
            })


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
