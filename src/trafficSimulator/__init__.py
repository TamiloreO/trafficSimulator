"""
TrafficSimulator - A traffic simulation library with pedestrian crossings.

This package provides tools for simulating traffic flow including vehicles,
road segments, and various types of pedestrian crossings.

Modules:
    core.geometry: Road segment geometry (straight lines, Bézier curves)
    core.vehicle: Vehicle representation and car-following model
    core.pedestrian: Pedestrian representation
    core.pedestrian_crossing: Various crossing types (Zebra, Pelican, etc.)
    core.simulation: Main simulation controller
    visualizer: Visualization using DearPyGui

Example:
    >>> import trafficSimulator as ts
    >>> sim = ts.Simulation()
    >>> sim.create_segment((-50, 0), (50, 0))
    >>> sim.create_zebra_crossing(segment_index=0, position=0.5)
    >>> win = ts.Window(sim)
    >>> win.show()
"""

from .core.geometry.segment import Segment
from .core.geometry.quadratic_curve import QuadraticCurve
from .core.geometry.cubic_curve import CubicCurve

from .core.vehicle import Vehicle
from .core.vehicle_generator import VehicleGenerator

from .core.pedestrian import Pedestrian, PedestrianState
from .core.pedestrian_generator import PedestrianGenerator
from .core.pedestrian_crossing import (
    PedestrianCrossing,
    ZebraCrossing,
    PelicanCrossing,
    PuffinCrossing,
    ToucanCrossing,
    PegasusCrossing,
    CrossingState,
    CrossingType,
)

from .core.simulation import Simulation
from .visualizer.window import Window

__all__ = [
    # Geometry
    'Segment',
    'QuadraticCurve',
    'CubicCurve',
    # Vehicles
    'Vehicle',
    'VehicleGenerator',
    # Pedestrians
    'Pedestrian',
    'PedestrianState',
    'PedestrianGenerator',
    # Crossings
    'PedestrianCrossing',
    'ZebraCrossing',
    'PelicanCrossing',
    'PuffinCrossing',
    'ToucanCrossing',
    'PegasusCrossing',
    'CrossingState',
    'CrossingType',
    # Core
    'Simulation',
    'Window',
]
