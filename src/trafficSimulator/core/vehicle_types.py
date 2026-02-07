"""
Vehicle Type System - Strategy Pattern Implementation

Defines vehicle type specifications with distinct physical and behavioral characteristics.
Each vehicle type encapsulates its own parameters following the Strategy Pattern.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Tuple, Any


class VehicleType(Enum):
    """Enumeration of supported vehicle types."""
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"


class VehicleTypeSpecification(ABC):
    """
    Abstract base class defining the interface for vehicle type specifications.
    Implements the Strategy Pattern - each concrete specification provides
    type-specific parameters.
    """

    @property
    @abstractmethod
    def vehicle_type(self) -> VehicleType:
        """Returns the vehicle type enum value."""
        pass

    @property
    @abstractmethod
    def length(self) -> float:
        """Vehicle length in meters."""
        pass

    @property
    @abstractmethod
    def width(self) -> float:
        """Vehicle width in meters."""
        pass

    @property
    @abstractmethod
    def max_speed(self) -> float:
        """Maximum speed in m/s."""
        pass

    @property
    @abstractmethod
    def max_acceleration(self) -> float:
        """Maximum acceleration in m/s^2."""
        pass

    @property
    @abstractmethod
    def max_deceleration(self) -> float:
        """Maximum deceleration (braking) in m/s^2."""
        pass

    @property
    @abstractmethod
    def safe_distance(self) -> float:
        """Minimum safe following distance in meters."""
        pass

    @property
    @abstractmethod
    def time_headway(self) -> float:
        """Safe time headway in seconds."""
        pass

    @property
    @abstractmethod
    def color(self) -> Tuple[int, int, int]:
        """RGB color tuple for visualization."""
        pass

    def to_config(self) -> Dict[str, Any]:
        """Converts specification to vehicle configuration dictionary."""
        return {
            'vehicle_type': self.vehicle_type,
            'l': self.length,
            'w': self.width,
            'v_max': self.max_speed,
            'a_max': self.max_acceleration,
            'b_max': self.max_deceleration,
            's0': self.safe_distance,
            'T': self.time_headway,
            'color': self.color
        }


class CarSpecification(VehicleTypeSpecification):
    """Specification for standard passenger cars."""

    @property
    def vehicle_type(self) -> VehicleType:
        return VehicleType.CAR

    @property
    def length(self) -> float:
        return 4.5  # meters

    @property
    def width(self) -> float:
        return 1.8  # meters

    @property
    def max_speed(self) -> float:
        return 16.6  # ~60 km/h

    @property
    def max_acceleration(self) -> float:
        return 2.0  # m/s^2

    @property
    def max_deceleration(self) -> float:
        return 4.5  # m/s^2

    @property
    def safe_distance(self) -> float:
        return 4.0  # meters

    @property
    def time_headway(self) -> float:
        return 1.0  # seconds

    @property
    def color(self) -> Tuple[int, int, int]:
        return (0, 100, 255)  # Blue


class TruckSpecification(VehicleTypeSpecification):
    """Specification for heavy trucks."""

    @property
    def vehicle_type(self) -> VehicleType:
        return VehicleType.TRUCK

    @property
    def length(self) -> float:
        return 12.0  # meters

    @property
    def width(self) -> float:
        return 2.5  # meters

    @property
    def max_speed(self) -> float:
        return 13.9  # ~50 km/h

    @property
    def max_acceleration(self) -> float:
        return 0.8  # m/s^2 - slower acceleration

    @property
    def max_deceleration(self) -> float:
        return 3.0  # m/s^2 - longer braking distance

    @property
    def safe_distance(self) -> float:
        return 8.0  # meters - larger safe distance

    @property
    def time_headway(self) -> float:
        return 1.8  # seconds - more cautious

    @property
    def color(self) -> Tuple[int, int, int]:
        return (139, 69, 19)  # Brown


class BusSpecification(VehicleTypeSpecification):
    """Specification for public transit buses."""

    @property
    def vehicle_type(self) -> VehicleType:
        return VehicleType.BUS

    @property
    def length(self) -> float:
        return 10.0  # meters

    @property
    def width(self) -> float:
        return 2.5  # meters

    @property
    def max_speed(self) -> float:
        return 14.0  # ~50 km/h

    @property
    def max_acceleration(self) -> float:
        return 1.2  # m/s^2

    @property
    def max_deceleration(self) -> float:
        return 3.5  # m/s^2

    @property
    def safe_distance(self) -> float:
        return 6.0  # meters

    @property
    def time_headway(self) -> float:
        return 1.5  # seconds

    @property
    def color(self) -> Tuple[int, int, int]:
        return (0, 180, 0)  # Green


class MotorcycleSpecification(VehicleTypeSpecification):
    """Specification for motorcycles."""

    @property
    def vehicle_type(self) -> VehicleType:
        return VehicleType.MOTORCYCLE

    @property
    def length(self) -> float:
        return 2.2  # meters

    @property
    def width(self) -> float:
        return 0.8  # meters

    @property
    def max_speed(self) -> float:
        return 19.4  # ~70 km/h - faster

    @property
    def max_acceleration(self) -> float:
        return 3.5  # m/s^2 - quick acceleration

    @property
    def max_deceleration(self) -> float:
        return 6.0  # m/s^2 - quick braking

    @property
    def safe_distance(self) -> float:
        return 3.0  # meters - smaller

    @property
    def time_headway(self) -> float:
        return 0.8  # seconds - more aggressive

    @property
    def color(self) -> Tuple[int, int, int]:
        return (255, 50, 50)  # Red


class VehicleTypeRegistry:
    """
    Registry Pattern - Central registry for vehicle type specifications.
    Provides lookup and management of all registered vehicle types.
    """

    _specifications: Dict[VehicleType, VehicleTypeSpecification] = {}

    @classmethod
    def register(cls, specification: VehicleTypeSpecification) -> None:
        """Registers a vehicle type specification."""
        cls._specifications[specification.vehicle_type] = specification

    @classmethod
    def get(cls, vehicle_type: VehicleType) -> VehicleTypeSpecification:
        """Retrieves specification for a vehicle type."""
        if vehicle_type not in cls._specifications:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")
        return cls._specifications[vehicle_type]

    @classmethod
    def get_all(cls) -> Dict[VehicleType, VehicleTypeSpecification]:
        """Returns all registered specifications."""
        return cls._specifications.copy()

    @classmethod
    def initialize_defaults(cls) -> None:
        """Initializes registry with default vehicle type specifications."""
        cls.register(CarSpecification())
        cls.register(TruckSpecification())
        cls.register(BusSpecification())
        cls.register(MotorcycleSpecification())


# Initialize default vehicle types on module load
VehicleTypeRegistry.initialize_defaults()
