"""
Vehicle Module
==============

This module provides the Vehicle class and factory function for creating vehicles
in the traffic simulation.

The vehicle system uses a registry-based approach where vehicle types are defined
in vehicle_types.py. To add new vehicle types, you only need to update the
VEHICLE_SPECS and VEHICLE_COLORS dictionaries in that module.

Usage
-----
Creating vehicles:

    # Using the factory function (recommended)
    car = create_vehicle('car', path=[0], v=10)
    truck = create_vehicle('truck', path=[1])
    
    # Using Vehicle class directly with config
    vehicle = Vehicle({'vehicle_type': 'bus', 'path': [0]})
    
    # Using Vehicle class with default type (car)
    vehicle = Vehicle({'path': [0]})
"""

import uuid
import numpy as np

from .vehicle_types import (
    get_vehicle_specs,
    get_vehicle_color,
    get_available_vehicle_types,
    is_valid_vehicle_type,
    UnknownVehicleTypeError,
    InvalidVehicleSpecError,
    VehicleTypeError,
)


# Default vehicle type used when none is specified
DEFAULT_VEHICLE_TYPE = "car"


class VehicleConfigError(Exception):
    """Exception raised for vehicle configuration errors."""
    pass


class Vehicle:
    """
    Represents a vehicle in the traffic simulation.
    
    The Vehicle class implements the Intelligent Driver Model (IDM) for
    realistic car-following behavior. Each vehicle has physical properties
    (length, width) and performance characteristics (max speed, acceleration,
    braking) determined by its vehicle type.
    
    Attributes:
        id: Unique identifier for the vehicle.
        vehicle_type: String identifier for the vehicle type (e.g., 'car', 'truck').
        l: Vehicle length in meters.
        w: Vehicle width in meters.
        s0: Minimum spacing to vehicle ahead in meters.
        T: Safe time headway in seconds.
        v_max: Maximum velocity in m/s.
        a_max: Maximum acceleration in m/s^2.
        b_max: Comfortable braking deceleration in m/s^2.
        color: RGBA color tuple for visualization.
        path: List of road segment indices defining the vehicle's route.
        current_road_index: Index into path for current road segment.
        x: Position along current road segment in meters.
        v: Current velocity in m/s.
        a: Current acceleration in m/s^2.
        stopped: Whether the vehicle is stopped (e.g., at traffic light).
    
    Example:
        >>> vehicle = Vehicle({'vehicle_type': 'car', 'path': [0, 1, 2]})
        >>> print(vehicle.vehicle_type)
        'car'
        >>> print(vehicle.l)
        4.5
    """
    
    def __init__(self, config=None):
        """
        Initialize a new Vehicle.
        
        Args:
            config: Optional dictionary of configuration parameters. Supported keys:
                - vehicle_type: Vehicle type identifier (default: 'car')
                - path: List of road segment indices
                - x: Initial position along road segment
                - v: Initial velocity
                - Any vehicle spec keys (l, w, s0, T, v_max, a_max, b_max) to override defaults
                
        Raises:
            UnknownVehicleTypeError: If specified vehicle_type is not registered.
            InvalidVehicleSpecError: If vehicle type has incomplete specifications.
        """
        if config is None:
            config = {}
            
        self._initialize_identity()
        self._initialize_from_type(config.get('vehicle_type', DEFAULT_VEHICLE_TYPE))
        self._initialize_state()
        self._apply_config_overrides(config)
        self._compute_derived_properties()
    
    def _initialize_identity(self):
        """Initialize vehicle identity."""
        self.id = uuid.uuid4()
    
    def _initialize_from_type(self, vehicle_type: str):
        """
        Initialize vehicle properties from type specifications.
        
        Args:
            vehicle_type: Vehicle type identifier string.
            
        Raises:
            UnknownVehicleTypeError: If vehicle type is not registered.
            InvalidVehicleSpecError: If specifications are incomplete.
        """
        self.vehicle_type = vehicle_type
        
        # Get specs - this will raise appropriate exceptions if invalid
        specs = get_vehicle_specs(vehicle_type)
        for attr, val in specs.items():
            setattr(self, attr, val)
        
        # Get color - this will raise if color not defined
        self.color = get_vehicle_color(vehicle_type)
    
    def _initialize_state(self):
        """Initialize vehicle dynamic state."""
        self.path = []
        self.current_road_index = 0
        self.x = 0
        self.v = 0
        self.a = 0
        self.stopped = False
    
    def _apply_config_overrides(self, config: dict):
        """
        Apply configuration overrides to vehicle properties.
        
        Args:
            config: Configuration dictionary with override values.
        """
        # Keys that should not be overridden from config
        protected_keys = {'vehicle_type', 'id'}
        
        for attr, val in config.items():
            if attr not in protected_keys:
                setattr(self, attr, val)
    
    def _compute_derived_properties(self):
        """Compute properties derived from base specifications."""
        self.sqrt_ab = 2 * np.sqrt(self.a_max * self.b_max)
        self._v_max = self.v_max

    def update(self, lead, dt):
        """
        Update vehicle state for one time step using the Intelligent Driver Model.
        
        Args:
            lead: The vehicle ahead (None if no vehicle ahead).
            dt: Time step in seconds.
        """
        # Update position and velocity
        if self.v + self.a * dt < 0:
            self.x -= 0.5 * self.v * self.v / self.a
            self.v = 0
        else:
            self.v += self.a * dt
            self.x += self.v * dt + self.a * dt * dt / 2
        
        # Update acceleration using IDM
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v
            alpha = (self.s0 + max(0, self.T * self.v + delta_v * self.v / self.sqrt_ab)) / delta_x

        self.a = self.a_max * (1 - (self.v / self.v_max) ** 4 - alpha ** 2)

        if self.stopped:
            self.a = -self.b_max * self.v / self.v_max


def create_vehicle(vehicle_type: str, **kwargs) -> Vehicle:
    """
    Factory function to create a vehicle of the specified type.
    
    This is the recommended way to create vehicles as it provides a cleaner
    interface than using the Vehicle class directly.
    
    Args:
        vehicle_type: Vehicle type identifier (e.g., 'car', 'truck', 'bus', 'motorcycle').
        **kwargs: Additional configuration parameters (path, x, v, etc.).
        
    Returns:
        A new Vehicle instance configured for the specified type.
        
    Raises:
        UnknownVehicleTypeError: If vehicle_type is not registered.
        InvalidVehicleSpecError: If vehicle type has incomplete specifications.
        
    Example:
        >>> car = create_vehicle('car', path=[0, 1], v=10)
        >>> truck = create_vehicle('truck', path=[0])
        >>> print(car.v_max)
        33.3
    """
    config = {'vehicle_type': vehicle_type, **kwargs}
    return Vehicle(config)

