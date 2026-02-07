"""
Vehicle Generator Module

Generates vehicles with configurable types and spawn rates.
Supports weighted random selection of vehicle types.
"""

from numpy.random import randint
from .vehicle import Vehicle
from .vehicle_factory import VehicleFactory
from .vehicle_types import VehicleType


class VehicleGenerator:
    """
    Generates vehicles at specified rates with configurable type distributions.
    
    Supports two configuration modes:
    1. Legacy mode: Using raw config dicts (backward compatible)
    2. Typed mode: Using VehicleType enum for type-specific vehicles
    """

    def __init__(self, config=None):
        if config is None:
            config = {}

        self.set_default_config()

        for attr, val in config.items():
            setattr(self, attr, val)

        self.init_properties()

    def set_default_config(self):
        """Sets default configuration."""
        self.vehicle_rate = 10  # vehicles per minute
        self.vehicles = [
            (1, {})
        ]
        self.last_added_time = 0

    def init_properties(self):
        """Initializes generator properties."""
        self.upcoming_vehicle = self.generate_vehicle()

    def generate_vehicle(self):
        """
        Generates a random vehicle based on configured weights.

        Returns
        -------
        Vehicle
            A new vehicle instance
        """
        total = sum(pair[0] for pair in self.vehicles)
        r = randint(1, total + 1)

        for (weight, config) in self.vehicles:
            r -= weight
            if r <= 0:
                return self._create_vehicle(config)

        # Fallback
        return self._create_vehicle(self.vehicles[0][1])

    def _create_vehicle(self, config):
        """
        Creates a vehicle from configuration.

        Supports both typed and legacy configurations:
        - If 'vehicle_type' key present: uses VehicleFactory
        - Otherwise: creates generic Vehicle (backward compatible)

        Parameters
        ----------
        config : dict
            Vehicle configuration

        Returns
        -------
        Vehicle
            Configured vehicle instance
        """
        if 'vehicle_type' in config:
            vehicle_type = config['vehicle_type']
            if isinstance(vehicle_type, str):
                vehicle_type = VehicleType(vehicle_type)

            # Extract non-type config for overrides
            overrides = {k: v for k, v in config.items() if k != 'vehicle_type'}
            return VehicleFactory.create(vehicle_type, overrides)
        else:
            return Vehicle(config)

    def update(self, simulation):
        """
        Updates generator state and adds vehicles when appropriate.

        Parameters
        ----------
        simulation : Simulation
            The simulation instance
        """
        if simulation.t - self.last_added_time >= 60 / self.vehicle_rate:
            segment = simulation.segments[self.upcoming_vehicle.path[0]]

            if (len(segment.vehicles) == 0 or
                simulation.vehicles[segment.vehicles[-1]].x > 
                self.upcoming_vehicle.s0 + self.upcoming_vehicle.l):
                
                simulation.add_vehicle(self.upcoming_vehicle)
                self.last_added_time = simulation.t

            self.upcoming_vehicle = self.generate_vehicle()
