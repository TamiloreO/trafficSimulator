import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trafficSimulator import (
    Vehicle, Car, Truck, Bus, Motorcycle,
    VehicleType, VEHICLE_SPECS, VEHICLE_COLORS
)


class TestVehicleTypes:
    """Tests for the vehicle type system."""

    def test_car_default_properties(self):
        """Test that Car has correct default properties."""
        car = Car({})
        assert car.vehicle_type == VehicleType.CAR
        assert car.l == VEHICLE_SPECS[VehicleType.CAR]['l']
        assert car.w == VEHICLE_SPECS[VehicleType.CAR]['w']
        assert car.v_max == VEHICLE_SPECS[VehicleType.CAR]['v_max']
        assert car.a_max == VEHICLE_SPECS[VehicleType.CAR]['a_max']
        assert car.color == VEHICLE_COLORS[VehicleType.CAR]

    def test_truck_default_properties(self):
        """Test that Truck has correct default properties."""
        truck = Truck({})
        assert truck.vehicle_type == VehicleType.TRUCK
        assert truck.l == VEHICLE_SPECS[VehicleType.TRUCK]['l']
        assert truck.w == VEHICLE_SPECS[VehicleType.TRUCK]['w']
        assert truck.v_max == VEHICLE_SPECS[VehicleType.TRUCK]['v_max']
        assert truck.a_max == VEHICLE_SPECS[VehicleType.TRUCK]['a_max']
        assert truck.color == VEHICLE_COLORS[VehicleType.TRUCK]

    def test_bus_default_properties(self):
        """Test that Bus has correct default properties."""
        bus = Bus({})
        assert bus.vehicle_type == VehicleType.BUS
        assert bus.l == VEHICLE_SPECS[VehicleType.BUS]['l']
        assert bus.w == VEHICLE_SPECS[VehicleType.BUS]['w']
        assert bus.v_max == VEHICLE_SPECS[VehicleType.BUS]['v_max']
        assert bus.a_max == VEHICLE_SPECS[VehicleType.BUS]['a_max']
        assert bus.color == VEHICLE_COLORS[VehicleType.BUS]

    def test_motorcycle_default_properties(self):
        """Test that Motorcycle has correct default properties."""
        motorcycle = Motorcycle({})
        assert motorcycle.vehicle_type == VehicleType.MOTORCYCLE
        assert motorcycle.l == VEHICLE_SPECS[VehicleType.MOTORCYCLE]['l']
        assert motorcycle.w == VEHICLE_SPECS[VehicleType.MOTORCYCLE]['w']
        assert motorcycle.v_max == VEHICLE_SPECS[VehicleType.MOTORCYCLE]['v_max']
        assert motorcycle.a_max == VEHICLE_SPECS[VehicleType.MOTORCYCLE]['a_max']
        assert motorcycle.color == VEHICLE_COLORS[VehicleType.MOTORCYCLE]

    def test_vehicle_with_type_config(self):
        """Test creating Vehicle with vehicle_type in config."""
        vehicle = Vehicle({'vehicle_type': VehicleType.TRUCK})
        assert vehicle.vehicle_type == VehicleType.TRUCK
        assert vehicle.l == VEHICLE_SPECS[VehicleType.TRUCK]['l']

    def test_vehicle_with_string_type(self):
        """Test creating Vehicle with string vehicle_type."""
        vehicle = Vehicle({'vehicle_type': 'bus'})
        assert vehicle.vehicle_type == VehicleType.BUS
        assert vehicle.l == VEHICLE_SPECS[VehicleType.BUS]['l']

    def test_vehicle_lengths_are_different(self):
        """Test that different vehicle types have different lengths."""
        car = Car({})
        truck = Truck({})
        bus = Bus({})
        motorcycle = Motorcycle({})
        
        lengths = [car.l, truck.l, bus.l, motorcycle.l]
        assert len(set(lengths)) == 4  # All different

    def test_vehicle_max_speeds_order(self):
        """Test that motorcycle is fastest and bus is slowest."""
        car = Car({})
        truck = Truck({})
        bus = Bus({})
        motorcycle = Motorcycle({})
        
        assert motorcycle.v_max > car.v_max
        assert car.v_max > truck.v_max
        assert truck.v_max > bus.v_max

    def test_vehicle_colors_are_different(self):
        """Test that all vehicle types have unique colors."""
        car = Car({})
        truck = Truck({})
        bus = Bus({})
        motorcycle = Motorcycle({})
        
        colors = [car.color, truck.color, bus.color, motorcycle.color]
        assert len(set(colors)) == 4  # All different

    def test_vehicle_update_with_lead(self):
        """Test that vehicle update works with a leading vehicle."""
        car1 = Car({'x': 10, 'v': 10})
        car2 = Car({'x': 0, 'v': 15})
        
        car2.update(car1, 0.1)
        
        assert car2.x > 0  # Should have moved forward
        assert car2.a < car2.a_max  # Should be decelerating due to lead

    def test_vehicle_update_without_lead(self):
        """Test that vehicle moves when no lead vehicle."""
        car = Car({'x': 0, 'v': 5})
        
        car.update(None, 0.1)
        
        assert car.x > 0  # Should have moved forward


class TestVehicleSpecs:
    """Tests for vehicle specifications."""

    def test_all_vehicle_types_have_specs(self):
        """Test that all vehicle types have specifications."""
        for vtype in VehicleType:
            assert vtype in VEHICLE_SPECS
            specs = VEHICLE_SPECS[vtype]
            assert 'l' in specs
            assert 'w' in specs
            assert 'v_max' in specs
            assert 'a_max' in specs
            assert 'b_max' in specs

    def test_all_vehicle_types_have_colors(self):
        """Test that all vehicle types have colors."""
        for vtype in VehicleType:
            assert vtype in VEHICLE_COLORS
            color = VEHICLE_COLORS[vtype]
            assert len(color) == 4  # RGBA


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
