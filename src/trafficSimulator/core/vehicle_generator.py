"""
Vehicle Generator Module
========================

This module provides the VehicleGenerator class for spawning vehicles
in the traffic simulation based on configurable rates and type distributions.

Usage
-----
    sim.create_vehicle_generator(
        vehicle_rate=20,  # vehicles per minute
        vehicles=[
            (10, {'path': [0], 'vehicle_type': 'car'}),      # 10 weight for cars
            (2, {'path': [0], 'vehicle_type': 'truck'}),     # 2 weight for trucks
            (1, {'path': [0], 'vehicle_type': 'bus'}),       # 1 weight for buses
        ]
    )

The weight values determine the relative probability of each vehicle type being spawned.
"""

from numpy.random import randint

from .vehicle import Vehicle, create_vehicle
from .vehicle_types import (
    is_valid_vehicle_type,
    get_available_vehicle_types,
    UnknownVehicleTypeError,
)


class VehicleGeneratorConfigError(Exception):
    """Exception raised for vehicle generator configuration errors."""
    pass


class VehicleGenerator:
    """
    Generates vehicles at specified rates with configurable type distributions.
    
    The generator spawns vehicles based on a weighted random selection from
    a list of vehicle configurations. Each configuration specifies the vehicle
    type, path, and any other parameters.
    
    Attributes:
        vehicle_rate: Number of vehicles to generate per minute.
        vehicles: List of (weight, config) tuples defining vehicle distribution.
        last_added_time: Simulation time when last vehicle was added.
        upcoming_vehicle: Pre-generated vehicle waiting to be added.
    """
    
    def __init__(self, config=None):
        """
        Initialize a new VehicleGenerator.
        
        Args:
            config: Optional dictionary of configuration parameters:
                - vehicle_rate: Vehicles per minute (default: 10)
                - vehicles: List of (weight, config) tuples
                
        Raises:
            VehicleGeneratorConfigError: If configuration is invalid.
            UnknownVehicleTypeError: If a vehicle type is not registered.
        """
        if config is None:
            config = {}
            
        self.set_default_config()
        
        for attr, val in config.items():
            setattr(self, attr, val)
        
        self._validate_vehicle_configs()
        self.init_properties()

    def set_default_config(self):
        """Set default configuration values."""
        self.vehicle_rate = 10
        self.vehicles = [
            (1, {})
        ]
        self.last_added_time = 0

    def _validate_vehicle_configs(self):
        """
        Validate all vehicle configurations in the vehicles list.
        
        Raises:
            VehicleGeneratorConfigError: If vehicles list is empty or malformed.
            UnknownVehicleTypeError: If any vehicle type is not registered.
        """
        if not self.vehicles:
            raise VehicleGeneratorConfigError("vehicles list cannot be empty")
        
        for i, entry in enumerate(self.vehicles):
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                raise VehicleGeneratorConfigError(
                    f"Invalid vehicle entry at index {i}: expected (weight, config) tuple"
                )
            
            weight, vehicle_config = entry
            
            if not isinstance(weight, (int, float)) or weight <= 0:
                raise VehicleGeneratorConfigError(
                    f"Invalid weight at index {i}: must be a positive number"
                )
            
            if not isinstance(vehicle_config, dict):
                raise VehicleGeneratorConfigError(
                    f"Invalid config at index {i}: must be a dictionary"
                )
            
            vehicle_type = vehicle_config.get('vehicle_type')
            if vehicle_type and not is_valid_vehicle_type(vehicle_type):
                raise UnknownVehicleTypeError(
                    vehicle_type, 
                    available_types=get_available_vehicle_types()
                )

    def init_properties(self):
        """Initialize generator properties."""
        self.upcoming_vehicle = self.generate_vehicle()

    def generate_vehicle(self) -> Vehicle:
        """
        Generate a random vehicle based on weighted distribution.
        
        Returns:
            A new Vehicle instance selected randomly from the configured distribution.
            
        Raises:
            UnknownVehicleTypeError: If selected vehicle type is not registered.
        """
        total = sum(pair[0] for pair in self.vehicles)
        r = randint(1, total + 1)
        
        for (weight, config) in self.vehicles:
            r -= weight
            if r <= 0:
                return self._create_vehicle(config.copy())
        
        # Fallback (should not reach here with valid config)
        return self._create_vehicle(self.vehicles[0][1].copy())

    def _create_vehicle(self, config: dict) -> Vehicle:
        """
        Create a vehicle from the given configuration.
        
        Args:
            config: Vehicle configuration dictionary.
            
        Returns:
            A new Vehicle instance.
            
        Raises:
            UnknownVehicleTypeError: If vehicle type is not registered.
        """
        vehicle_type = config.get('vehicle_type')
        
        if vehicle_type:
            return create_vehicle(vehicle_type, **{k: v for k, v in config.items() if k != 'vehicle_type'})
        
        return Vehicle(config)

    def update(self, simulation):
        """
        Update the generator, potentially adding a new vehicle to the simulation.
        
        Args:
            simulation: The Simulation instance to add vehicles to.
        """
        if simulation.t - self.last_added_time >= 60 / self.vehicle_rate:
            print('adding vehicle')
            segment = simulation.segments[self.upcoming_vehicle.path[0]]
            
            if (len(segment.vehicles) == 0 or 
                simulation.vehicles[segment.vehicles[-1]].x > self.upcoming_vehicle.s0 + self.upcoming_vehicle.l):
                simulation.add_vehicle(self.upcoming_vehicle)
                self.last_added_time = simulation.t
            
            self.upcoming_vehicle = self.generate_vehicle()
