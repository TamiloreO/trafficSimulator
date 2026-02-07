from enum import Enum


class VehicleType(Enum):
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"


# Vehicle specifications for each type
# l: length (meters)
# w: width (meters)
# s0: minimum spacing (meters)
# T: safe time headway (seconds)
# v_max: maximum velocity (m/s)
# a_max: maximum acceleration (m/s^2)
# b_max: comfortable braking deceleration (m/s^2)

VEHICLE_SPECS = {
    VehicleType.CAR: {
        'l': 4.5,
        'w': 1.8,
        's0': 4,
        'T': 1.0,
        'v_max': 33.3,  # ~120 km/h
        'a_max': 2.5,
        'b_max': 4.5,
    },
    VehicleType.TRUCK: {
        'l': 12.0,
        'w': 2.5,
        's0': 6,
        'T': 1.5,
        'v_max': 25.0,  # ~90 km/h
        'a_max': 1.0,
        'b_max': 3.0,
    },
    VehicleType.BUS: {
        'l': 10.0,
        'w': 2.5,
        's0': 5,
        'T': 1.4,
        'v_max': 22.2,  # ~80 km/h
        'a_max': 1.2,
        'b_max': 3.5,
    },
    VehicleType.MOTORCYCLE: {
        'l': 2.2,
        'w': 0.8,
        's0': 2.5,
        'T': 0.8,
        'v_max': 38.9,  # ~140 km/h
        'a_max': 3.5,
        'b_max': 6.0,
    },
}

# Colors for visualization (RGBA)
VEHICLE_COLORS = {
    VehicleType.CAR: (0, 100, 255, 255),        # Blue
    VehicleType.TRUCK: (255, 140, 0, 255),      # Orange
    VehicleType.BUS: (34, 139, 34, 255),        # Green
    VehicleType.MOTORCYCLE: (255, 0, 100, 255), # Pink/Magenta
}


def get_vehicle_specs(vehicle_type: VehicleType) -> dict:
    """Get the specifications for a given vehicle type."""
    return VEHICLE_SPECS.get(vehicle_type, VEHICLE_SPECS[VehicleType.CAR]).copy()


def get_vehicle_color(vehicle_type: VehicleType) -> tuple:
    """Get the color for a given vehicle type."""
    return VEHICLE_COLORS.get(vehicle_type, VEHICLE_COLORS[VehicleType.CAR])
