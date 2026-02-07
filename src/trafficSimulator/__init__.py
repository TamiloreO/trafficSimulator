"""
Traffic Simulator
=================

A traffic simulation library with support for multiple vehicle types.

Vehicle Types
-------------
The simulator supports the following vehicle types out of the box:
- car: Standard passenger car
- truck: Heavy goods truck  
- bus: Passenger bus
- motorcycle: Motorcycle

To add new vehicle types, update VEHICLE_SPECS and VEHICLE_COLORS in
trafficSimulator/core/vehicle_types.py. No other code changes required.

Basic Usage
-----------
    import trafficSimulator as ts
    
    sim = ts.Simulation()
    sim.create_segment((-100, 0), (100, 0))
    
    sim.create_vehicle_generator(
        vehicle_rate=20,
        vehicles=[
            (10, {'path': [0], 'vehicle_type': 'car'}),
            (2, {'path': [0], 'vehicle_type': 'truck'}),
        ]
    )
    
    win = ts.Window(sim)
    win.show()
"""

# Geometry
from .core.geometry.segment import Segment
from .core.geometry.quadratic_curve import QuadraticCurve
from .core.geometry.cubic_curve import CubicCurve

# Vehicle system
from .core.vehicle import Vehicle, create_vehicle
from .core.vehicle_types import (
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
from .core.vehicle_generator import VehicleGenerator

# Simulation
from .core.simulation import Simulation

# Visualization
from .visualizer.window import Window
