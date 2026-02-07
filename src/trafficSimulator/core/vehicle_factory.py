"""
Vehicle Factory - Factory Pattern Implementation

Provides centralized vehicle creation with type-specific configuration.
Follows the Factory Pattern for proper abstraction of object creation.
"""

from typing import Dict, Any, Optional
from .vehicle import Vehicle
from .vehicle_types import VehicleType, VehicleTypeRegistry


class VehicleFactory:
    """
    Factory Pattern - Creates vehicles with type-specific configurations.
    Centralizes vehicle instantiation logic and applies appropriate specifications.
    """

    @staticmethod
    def create(
        vehicle_type: VehicleType,
        config: Optional[Dict[str, Any]] = None
    ) -> Vehicle:
        """
        Creates a vehicle of the specified type with optional configuration overrides.

        Parameters
        ----------
        vehicle_type : VehicleType
            The type of vehicle to create
        config : dict, optional
            Additional configuration to override type defaults

        Returns
        -------
        Vehicle
            A configured vehicle instance
        """
        specification = VehicleTypeRegistry.get(vehicle_type)
        type_config = specification.to_config()

        if config:
            type_config.update(config)

        return Vehicle(type_config)

    @staticmethod
    def create_car(config: Optional[Dict[str, Any]] = None) -> Vehicle:
        """Convenience method to create a car."""
        return VehicleFactory.create(VehicleType.CAR, config)

    @staticmethod
    def create_truck(config: Optional[Dict[str, Any]] = None) -> Vehicle:
        """Convenience method to create a truck."""
        return VehicleFactory.create(VehicleType.TRUCK, config)

    @staticmethod
    def create_bus(config: Optional[Dict[str, Any]] = None) -> Vehicle:
        """Convenience method to create a bus."""
        return VehicleFactory.create(VehicleType.BUS, config)

    @staticmethod
    def create_motorcycle(config: Optional[Dict[str, Any]] = None) -> Vehicle:
        """Convenience method to create a motorcycle."""
        return VehicleFactory.create(VehicleType.MOTORCYCLE, config)
