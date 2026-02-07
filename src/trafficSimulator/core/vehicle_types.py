"""
Vehicle Type System
===================

This module defines the vehicle type registry for the traffic simulator. It provides
a centralized location for defining vehicle specifications and colors.

Adding a New Vehicle Type
-------------------------
To add a new vehicle type, you only need to update two dictionaries in this file:

1. Add an entry to VEHICLE_SPECS with the vehicle's physical and performance characteristics
2. Add an entry to VEHICLE_COLORS with the vehicle's visualization color

Example - Adding a "VAN" vehicle type:

    VEHICLE_SPECS["van"] = {
        'l': 5.5,           # Length in meters
        'w': 2.0,           # Width in meters
        's0': 4.5,          # Minimum spacing in meters
        'T': 1.2,           # Safe time headway in seconds
        'v_max': 30.0,      # Maximum velocity in m/s (~108 km/h)
        'a_max': 2.0,       # Maximum acceleration in m/s^2
        'b_max': 4.0,       # Comfortable braking deceleration in m/s^2
    }

    VEHICLE_COLORS["van"] = (128, 0, 128, 255)  # Purple (RGBA)

No other code changes are required. The system will automatically recognize the new
vehicle type and make it available for use in simulations.

Usage
-----
Creating vehicles with specific types:

    from trafficSimulator import Vehicle
    
    # Using string identifier
    car = Vehicle({'vehicle_type': 'car', 'path': [0]})
    truck = Vehicle({'vehicle_type': 'truck', 'path': [0]})
    
    # In vehicle generator configuration
    sim.create_vehicle_generator(
        vehicle_rate=20,
        vehicles=[
            (10, {'path': [0], 'vehicle_type': 'car'}),
            (2, {'path': [0], 'vehicle_type': 'truck'}),
        ]
    )

Specification Reference
-----------------------
Each vehicle type requires the following specifications:

    l       : float - Vehicle length in meters
    w       : float - Vehicle width in meters  
    s0      : float - Minimum spacing/gap to vehicle ahead in meters
    T       : float - Safe time headway in seconds (reaction time factor)
    v_max   : float - Maximum velocity in meters per second
    a_max   : float - Maximum acceleration in meters per second squared
    b_max   : float - Comfortable braking deceleration in meters per second squared

Color format is RGBA tuple with values 0-255: (red, green, blue, alpha)
"""

# Required keys that must be present in every vehicle specification
REQUIRED_SPEC_KEYS = frozenset(['l', 'w', 's0', 'T', 'v_max', 'a_max', 'b_max'])


class VehicleTypeError(Exception):
    """Exception raised for vehicle type related errors."""
    pass


class UnknownVehicleTypeError(VehicleTypeError):
    """Exception raised when an unknown vehicle type is requested."""
    
    def __init__(self, vehicle_type, available_types=None):
        self.vehicle_type = vehicle_type
        self.available_types = available_types or []
        message = f"Unknown vehicle type: '{vehicle_type}'"
        if self.available_types:
            message += f". Available types: {sorted(self.available_types)}"
        super().__init__(message)


class InvalidVehicleSpecError(VehicleTypeError):
    """Exception raised when a vehicle specification is invalid or incomplete."""
    
    def __init__(self, vehicle_type, missing_keys=None, message=None):
        self.vehicle_type = vehicle_type
        self.missing_keys = missing_keys or []
        if message:
            full_message = message
        elif self.missing_keys:
            full_message = (
                f"Invalid specification for vehicle type '{vehicle_type}': "
                f"missing required keys: {sorted(self.missing_keys)}"
            )
        else:
            full_message = f"Invalid specification for vehicle type '{vehicle_type}'"
        super().__init__(full_message)


class MissingVehicleColorError(VehicleTypeError):
    """Exception raised when a vehicle type has no color defined."""
    
    def __init__(self, vehicle_type):
        self.vehicle_type = vehicle_type
        super().__init__(
            f"No color defined for vehicle type '{vehicle_type}'. "
            f"Please add an entry to VEHICLE_COLORS."
        )


# =============================================================================
# VEHICLE SPECIFICATIONS REGISTRY
# =============================================================================
# To add a new vehicle type, add an entry here with all required keys.
# The system will automatically validate and make it available.

VEHICLE_SPECS = {
    "car": {
        'l': 4.5,           # Length: typical sedan
        'w': 1.8,           # Width: standard car width
        's0': 4,            # Minimum spacing: ~1 car length
        'T': 1.0,           # Time headway: standard reaction time
        'v_max': 33.3,      # Max speed: ~120 km/h
        'a_max': 2.5,       # Acceleration: good performance
        'b_max': 4.5,       # Braking: standard car brakes
    },
    "truck": {
        'l': 12.0,          # Length: standard semi-truck
        'w': 2.5,           # Width: maximum legal width
        's0': 6,            # Minimum spacing: longer stopping distance
        'T': 1.5,           # Time headway: slower reaction due to mass
        'v_max': 25.0,      # Max speed: ~90 km/h (limited)
        'a_max': 1.0,       # Acceleration: heavy vehicle, slow acceleration
        'b_max': 3.0,       # Braking: air brakes, longer stopping distance
    },
    "bus": {
        'l': 10.0,          # Length: standard city bus
        'w': 2.5,           # Width: standard bus width
        's0': 5,            # Minimum spacing: passenger comfort consideration
        'T': 1.4,           # Time headway: professional driver but heavy
        'v_max': 22.2,      # Max speed: ~80 km/h (urban speed limit)
        'a_max': 1.2,       # Acceleration: moderate, passenger comfort
        'b_max': 3.5,       # Braking: good brakes but gradual for passengers
    },
    "motorcycle": {
        'l': 2.2,           # Length: typical motorcycle
        'w': 0.8,           # Width: narrow profile
        's0': 2.5,          # Minimum spacing: smaller vehicle
        'T': 0.8,           # Time headway: quick reactions, exposed rider
        'v_max': 38.9,      # Max speed: ~140 km/h (high performance)
        'a_max': 3.5,       # Acceleration: excellent power-to-weight ratio
        'b_max': 6.0,       # Braking: excellent braking capability
    },
}


# =============================================================================
# VEHICLE COLORS REGISTRY
# =============================================================================
# To add a new vehicle type color, add an entry here.
# Format: (Red, Green, Blue, Alpha) with values 0-255

VEHICLE_COLORS = {
    "car": (0, 100, 255, 255),              # Blue
    "truck": (255, 140, 0, 255),            # Orange
    "bus": (34, 139, 34, 255),              # Forest Green
    "motorcycle": (255, 0, 100, 255),       # Pink/Magenta
}


# =============================================================================
# VALIDATION AND ACCESS FUNCTIONS
# =============================================================================

def _validate_vehicle_type(vehicle_type: str) -> None:
    """
    Validate that a vehicle type exists in the registry.
    
    Args:
        vehicle_type: The vehicle type identifier string.
        
    Raises:
        UnknownVehicleTypeError: If the vehicle type is not registered.
    """
    if vehicle_type not in VEHICLE_SPECS:
        raise UnknownVehicleTypeError(vehicle_type, available_types=list(VEHICLE_SPECS.keys()))


def _validate_specs(vehicle_type: str, specs: dict) -> None:
    """
    Validate that a vehicle specification contains all required keys.
    
    Args:
        vehicle_type: The vehicle type identifier for error messages.
        specs: The specification dictionary to validate.
        
    Raises:
        InvalidVehicleSpecError: If required keys are missing.
    """
    missing_keys = REQUIRED_SPEC_KEYS - set(specs.keys())
    if missing_keys:
        raise InvalidVehicleSpecError(vehicle_type, missing_keys=list(missing_keys))


def _validate_color_exists(vehicle_type: str) -> None:
    """
    Validate that a color is defined for the vehicle type.
    
    Args:
        vehicle_type: The vehicle type identifier.
        
    Raises:
        MissingVehicleColorError: If no color is defined.
    """
    if vehicle_type not in VEHICLE_COLORS:
        raise MissingVehicleColorError(vehicle_type)


def get_vehicle_specs(vehicle_type: str) -> dict:
    """
    Get the specifications for a given vehicle type.
    
    Args:
        vehicle_type: The vehicle type identifier (e.g., 'car', 'truck').
        
    Returns:
        A copy of the specification dictionary for the vehicle type.
        
    Raises:
        UnknownVehicleTypeError: If the vehicle type is not registered.
        InvalidVehicleSpecError: If the specification is incomplete.
        
    Example:
        >>> specs = get_vehicle_specs('car')
        >>> print(specs['v_max'])
        33.3
    """
    _validate_vehicle_type(vehicle_type)
    specs = VEHICLE_SPECS[vehicle_type]
    _validate_specs(vehicle_type, specs)
    return specs.copy()


def get_vehicle_color(vehicle_type: str) -> tuple:
    """
    Get the visualization color for a given vehicle type.
    
    Args:
        vehicle_type: The vehicle type identifier (e.g., 'car', 'truck').
        
    Returns:
        RGBA color tuple with values 0-255.
        
    Raises:
        UnknownVehicleTypeError: If the vehicle type is not registered in VEHICLE_SPECS.
        MissingVehicleColorError: If no color is defined for the vehicle type.
        
    Example:
        >>> color = get_vehicle_color('car')
        >>> print(color)
        (0, 100, 255, 255)
    """
    _validate_vehicle_type(vehicle_type)
    _validate_color_exists(vehicle_type)
    return VEHICLE_COLORS[vehicle_type]


def get_available_vehicle_types() -> list:
    """
    Get a list of all registered vehicle types.
    
    Returns:
        Sorted list of vehicle type identifier strings.
        
    Example:
        >>> types = get_available_vehicle_types()
        >>> print(types)
        ['bus', 'car', 'motorcycle', 'truck']
    """
    return sorted(VEHICLE_SPECS.keys())


def is_valid_vehicle_type(vehicle_type: str) -> bool:
    """
    Check if a vehicle type is registered and valid.
    
    Args:
        vehicle_type: The vehicle type identifier to check.
        
    Returns:
        True if the vehicle type is registered with complete specs and color.
        
    Example:
        >>> is_valid_vehicle_type('car')
        True
        >>> is_valid_vehicle_type('spaceship')
        False
    """
    if vehicle_type not in VEHICLE_SPECS:
        return False
    if vehicle_type not in VEHICLE_COLORS:
        return False
    specs = VEHICLE_SPECS[vehicle_type]
    if not REQUIRED_SPEC_KEYS.issubset(set(specs.keys())):
        return False
    return True


def validate_registry_integrity() -> None:
    """
    Validate the entire vehicle type registry for consistency.
    
    This function checks that:
    - All vehicle types in VEHICLE_SPECS have complete specifications
    - All vehicle types in VEHICLE_SPECS have corresponding colors
    
    Raises:
        InvalidVehicleSpecError: If any specification is incomplete.
        MissingVehicleColorError: If any vehicle type lacks a color.
        
    This is useful for validating the registry after adding new vehicle types,
    and can be called at application startup to catch configuration errors early.
    
    Example:
        >>> validate_registry_integrity()  # Raises exception if invalid
    """
    for vehicle_type, specs in VEHICLE_SPECS.items():
        _validate_specs(vehicle_type, specs)
        _validate_color_exists(vehicle_type)
output
