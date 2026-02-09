"""
Simulation module for traffic simulation.

This module provides the core Simulation class that manages all entities
in the traffic simulation including road segments, vehicles, pedestrian
crossings, and pedestrians.
"""

from typing import Any, Optional
from uuid import UUID

from .vehicle_generator import VehicleGenerator
from .pedestrian_generator import PedestrianGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .pedestrian import Pedestrian
from .pedestrian_crossing import (
    PedestrianCrossing, ZebraCrossing, PelicanCrossing,
    PuffinCrossing, ToucanCrossing, PegasusCrossing
)


class _VirtualLead:
    """
    Virtual vehicle used to make real vehicles stop at crossings.
    
    Acts as an invisible stationary obstacle that triggers the IDM
    car-following model to bring vehicles to a stop.
    
    Attributes:
        x: Position along the road segment in meters.
        l: Length of the virtual vehicle (always 0).
        v: Velocity of the virtual vehicle (always 0).
    """
    
    def __init__(self, x: float) -> None:
        """
        Create a virtual lead vehicle at the specified position.
        
        Args:
            x: Position along road segment where vehicles should stop.
        """
        self.x: float = x
        self.l: float = 0.0
        self.v: float = 0.0


class Simulation:
    """
    Core simulation controller managing all traffic entities.
    
    Coordinates the simulation of road segments, vehicles, pedestrian
    crossings, and pedestrians. Handles entity interactions including
    vehicle car-following behavior and stopping for pedestrian crossings.
    
    Attributes:
        segments: List of road segments in the simulation.
        vehicles: Dictionary mapping vehicle IDs to Vehicle instances.
        vehicle_generator: List of VehicleGenerator instances.
        crossings: List of PedestrianCrossing instances.
        pedestrians: Dictionary mapping pedestrian IDs to Pedestrian instances.
        pedestrian_generator: List of PedestrianGenerator instances.
        t: Current simulation time in seconds.
        frame_count: Number of simulation frames executed.
        dt: Time step per frame in seconds (default: 1/60).
    
    Example:
        >>> sim = Simulation()
        >>> sim.create_segment((-50, 0), (50, 0))
        >>> sim.create_zebra_crossing(segment_index=0, position=0.5)
        >>> sim.create_vehicle_generator(vehicle_rate=20, vehicles=[(1, {'path': [0]})])
        >>> sim.run(steps=100)
    """
    
    def __init__(self) -> None:
        """Initialize a new empty Simulation."""
        self.segments: list[Segment] = []
        self.vehicles: dict[UUID, Vehicle] = {}
        self.vehicle_generator: list[VehicleGenerator] = []
        
        self.crossings: list[PedestrianCrossing] = []
        self.pedestrians: dict[UUID, Pedestrian] = {}
        self.pedestrian_generator: list[PedestrianGenerator] = []

        self.t: float = 0.0
        self.frame_count: int = 0
        self.dt: float = 1.0 / 60.0

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """
        Add a vehicle to the simulation.
        
        Registers the vehicle and places it on its first road segment
        if it has a defined path.
        
        Args:
            vehicle: The Vehicle instance to add.
        """
        self.vehicles[vehicle.id] = vehicle
        if len(vehicle.path) > 0:
            self.segments[vehicle.path[0]].add_vehicle(vehicle)

    def add_segment(self, segment: Segment) -> None:
        """
        Add a road segment to the simulation.
        
        Args:
            segment: The Segment instance to add.
        """
        self.segments.append(segment)

    def add_vehicle_generator(self, generator: VehicleGenerator) -> None:
        """
        Add a vehicle generator to the simulation.
        
        Args:
            generator: The VehicleGenerator instance to add.
        """
        self.vehicle_generator.append(generator)

    def add_crossing(self, crossing: PedestrianCrossing) -> int:
        """
        Add a pedestrian crossing to the simulation.
        
        Args:
            crossing: The PedestrianCrossing instance to add.
        
        Returns:
            The index of the newly added crossing in the crossings list.
        """
        self.crossings.append(crossing)
        return len(self.crossings) - 1

    def add_pedestrian(self, pedestrian: Pedestrian) -> None:
        """
        Add a pedestrian to the simulation.
        
        Args:
            pedestrian: The Pedestrian instance to add.
        """
        self.pedestrians[pedestrian.id] = pedestrian

    def add_pedestrian_generator(self, generator: PedestrianGenerator) -> None:
        """
        Add a pedestrian generator to the simulation.
        
        Args:
            generator: The PedestrianGenerator instance to add.
        """
        self.pedestrian_generator.append(generator)

    def create_vehicle(self, **kwargs: Any) -> None:
        """
        Create and add a new vehicle to the simulation.
        
        Args:
            **kwargs: Configuration parameters passed to Vehicle constructor.
                Common parameters include:
                - path: List of segment indices defining the vehicle's route
                - v: Initial velocity in m/s
                - x: Initial position along first segment
        """
        vehicle = Vehicle(kwargs)
        self.add_vehicle(vehicle)

    def create_segment(self, *args: tuple[float, float]) -> None:
        """
        Create and add a straight road segment.
        
        Args:
            *args: Two or more (x, y) coordinate tuples defining the
                segment's path from start to end.
        
        Example:
            >>> sim.create_segment((-50, 0), (50, 0))  # Horizontal road
        """
        segment = Segment(args)
        self.add_segment(segment)

    def create_quadratic_bezier_curve(
        self,
        start: tuple[float, float],
        control: tuple[float, float],
        end: tuple[float, float]
    ) -> None:
        """
        Create and add a quadratic Bézier curve road segment.
        
        Args:
            start: Starting point (x, y) coordinates.
            control: Control point (x, y) coordinates that defines the curve.
            end: Ending point (x, y) coordinates.
        
        Example:
            >>> sim.create_quadratic_bezier_curve((0, 0), (25, 25), (50, 0))
        """
        curve = QuadraticCurve(start, control, end)
        self.add_segment(curve)

    def create_cubic_bezier_curve(
        self,
        start: tuple[float, float],
        control_1: tuple[float, float],
        control_2: tuple[float, float],
        end: tuple[float, float]
    ) -> None:
        """
        Create and add a cubic Bézier curve road segment.
        
        Args:
            start: Starting point (x, y) coordinates.
            control_1: First control point (x, y) coordinates.
            control_2: Second control point (x, y) coordinates.
            end: Ending point (x, y) coordinates.
        
        Example:
            >>> sim.create_cubic_bezier_curve((0, 0), (10, 20), (40, 20), (50, 0))
        """
        curve = CubicCurve(start, control_1, control_2, end)
        self.add_segment(curve)

    def create_vehicle_generator(self, **kwargs: Any) -> None:
        """
        Create and add a vehicle generator.
        
        Args:
            **kwargs: Configuration parameters passed to VehicleGenerator.
                Common parameters include:
                - vehicle_rate: Vehicles per minute to generate
                - vehicles: List of (weight, config) tuples for vehicle types
        
        Example:
            >>> sim.create_vehicle_generator(
            ...     vehicle_rate=20,
            ...     vehicles=[(1, {'path': [0], 'v': 12.0})]
            ... )
        """
        generator = VehicleGenerator(kwargs)
        self.add_vehicle_generator(generator)

    def create_pedestrian_generator(self, **kwargs: Any) -> None:
        """
        Create and add a pedestrian generator.
        
        Args:
            **kwargs: Configuration parameters passed to PedestrianGenerator.
                Common parameters include:
                - pedestrian_rate: Pedestrians per minute to generate
                - crossing_ids: List of crossing indices to spawn pedestrians at
                - pedestrians: List of (weight, config) tuples for pedestrian types
        
        Example:
            >>> sim.create_pedestrian_generator(
            ...     pedestrian_rate=15,
            ...     crossing_ids=[0],
            ...     pedestrians=[(1, {'speed': 1.4})]
            ... )
        """
        generator = PedestrianGenerator(kwargs)
        self.add_pedestrian_generator(generator)

    def create_zebra_crossing(
        self,
        segment_index: int,
        position: float = 0.5,
        **kwargs: Any
    ) -> int:
        """
        Create and add a zebra crossing.
        
        Zebra crossings give pedestrians priority - vehicles must stop
        when pedestrians are present.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction 0.0-1.0 (default: 0.5).
            **kwargs: Additional configuration parameters (width, length, etc.).
        
        Returns:
            Index of the new crossing in the crossings list.
        
        Example:
            >>> idx = sim.create_zebra_crossing(segment_index=0, position=0.5, width=6.0)
        """
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = ZebraCrossing(config)
        return self.add_crossing(crossing)

    def create_pelican_crossing(
        self,
        segment_index: int,
        position: float = 0.5,
        **kwargs: Any
    ) -> int:
        """
        Create and add a Pelican (Pedestrian Light Controlled) crossing.
        
        Signal-controlled crossing with push button and flashing amber phase.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction 0.0-1.0 (default: 0.5).
            **kwargs: Additional configuration (width, timing parameters, etc.).
        
        Returns:
            Index of the new crossing in the crossings list.
        """
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PelicanCrossing(config)
        return self.add_crossing(crossing)

    def create_puffin_crossing(
        self,
        segment_index: int,
        position: float = 0.5,
        **kwargs: Any
    ) -> int:
        """
        Create and add a Puffin (Pedestrian User-Friendly Intelligent) crossing.
        
        Intelligent crossing with sensors that detect pedestrians and
        automatically extend crossing time for slow pedestrians.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction 0.0-1.0 (default: 0.5).
            **kwargs: Additional configuration (width, timing, max_extension_time, etc.).
        
        Returns:
            Index of the new crossing in the crossings list.
        """
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PuffinCrossing(config)
        return self.add_crossing(crossing)

    def create_toucan_crossing(
        self,
        segment_index: int,
        position: float = 0.5,
        **kwargs: Any
    ) -> int:
        """
        Create and add a Toucan (Two-can cross) crossing.
        
        Wider crossing shared by pedestrians and cyclists.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction 0.0-1.0 (default: 0.5).
            **kwargs: Additional configuration parameters.
        
        Returns:
            Index of the new crossing in the crossings list.
        """
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = ToucanCrossing(config)
        return self.add_crossing(crossing)

    def create_pegasus_crossing(
        self,
        segment_index: int,
        position: float = 0.5,
        **kwargs: Any
    ) -> int:
        """
        Create and add a Pegasus (Equestrian) crossing.
        
        Extra-wide crossing for pedestrians, cyclists, and horse riders.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction 0.0-1.0 (default: 0.5).
            **kwargs: Additional configuration parameters.
        
        Returns:
            Index of the new crossing in the crossings list.
        """
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PegasusCrossing(config)
        return self.add_crossing(crossing)

    def run(self, steps: int) -> None:
        """
        Run the simulation for a specified number of steps.
        
        Args:
            steps: Number of simulation frames to execute.
        
        Example:
            >>> sim.run(steps=600)  # Run for 10 seconds at 60 FPS
        """
        for _ in range(steps):
            self.update()

    def _get_crossings_for_segment(self, segment_index: int) -> list[PedestrianCrossing]:
        """
        Get all crossings on a specific road segment.
        
        Args:
            segment_index: Index of the segment to query.
        
        Returns:
            List of PedestrianCrossing instances on the specified segment.
        """
        return [c for c in self.crossings if c.segment_index == segment_index]

    def _create_virtual_lead_for_crossing(
        self,
        crossing: PedestrianCrossing,
        segment: Segment
    ) -> _VirtualLead:
        """
        Create a virtual obstacle to stop vehicles at a crossing.
        
        The virtual lead acts as a stationary vehicle that triggers
        the IDM car-following model to bring approaching vehicles to
        a stop before the crossing.
        
        Args:
            crossing: The crossing where vehicles should stop.
            segment: The road segment the crossing is on.
        
        Returns:
            A _VirtualLead instance positioned at the stop line.
        """
        stop_distance = crossing.get_stop_distance(segment)
        return _VirtualLead(stop_distance)

    def _update_vehicles_on_segment(
        self,
        segment_index: int,
        segment: Segment,
        active_crossing: Optional[PedestrianCrossing]
    ) -> None:
        """
        Update all vehicles on a specific road segment.
        
        Handles vehicle movement using the IDM car-following model,
        accounting for both leading vehicles and active crossings.
        
        Args:
            segment_index: Index of the segment being processed.
            segment: The Segment instance.
            active_crossing: Crossing requiring vehicles to stop, or None.
        """
        if len(segment.vehicles) == 0:
            return

        # Update first vehicle (no leading vehicle)
        first_vehicle_id = segment.vehicles[0]
        first_vehicle = self.vehicles[first_vehicle_id]
        
        if active_crossing:
            stop_distance = active_crossing.get_stop_distance(segment)
            if first_vehicle.x < stop_distance:
                virtual_lead = self._create_virtual_lead_for_crossing(active_crossing, segment)
                first_vehicle.update(virtual_lead, self.dt)
            else:
                first_vehicle.update(None, self.dt)
        else:
            first_vehicle.update(None, self.dt)

        # Update following vehicles
        for i in range(1, len(segment.vehicles)):
            curr_id = segment.vehicles[i]
            prev_id = segment.vehicles[i - 1]
            curr_vehicle = self.vehicles[curr_id]
            prev_vehicle = self.vehicles[prev_id]
            
            if active_crossing:
                stop_distance = active_crossing.get_stop_distance(segment)
                if curr_vehicle.x < stop_distance:
                    virtual_lead = self._create_virtual_lead_for_crossing(active_crossing, segment)
                    # Follow whichever is closer: real lead or virtual crossing lead
                    if prev_vehicle.x < virtual_lead.x:
                        curr_vehicle.update(prev_vehicle, self.dt)
                    else:
                        curr_vehicle.update(virtual_lead, self.dt)
                else:
                    curr_vehicle.update(prev_vehicle, self.dt)
            else:
                curr_vehicle.update(prev_vehicle, self.dt)

    def _handle_segment_transitions(self) -> None:
        """
        Handle vehicles transitioning between road segments.
        
        Checks if vehicles have reached the end of their current segment
        and moves them to the next segment in their path, or removes them
        from the simulation if they've completed their route.
        """
        for segment in self.segments:
            if len(segment.vehicles) == 0:
                continue
                
            vehicle_id = segment.vehicles[0]
            vehicle = self.vehicles[vehicle_id]
            
            if vehicle.x >= segment.get_length():
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    vehicle.current_road_index += 1
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    self.segments[next_road_index].vehicles.append(vehicle_id)
                vehicle.x = 0.0
                segment.vehicles.popleft()

    def _remove_finished_pedestrians(self) -> None:
        """
        Remove pedestrians that have finished crossing.
        
        Cleans up the pedestrians dictionary by removing entries for
        pedestrians that have reached FINISHED state.
        """
        finished_ids = [
            pid for pid, ped in self.pedestrians.items()
            if ped.is_finished()
        ]
        for pid in finished_ids:
            del self.pedestrians[pid]

    def update(self) -> None:
        """
        Execute one simulation time step.
        
        Performs the following in order:
        1. Update all crossing signal states
        2. Update vehicle positions (with crossing awareness)
        3. Handle vehicle segment transitions
        4. Generate new vehicles
        5. Generate new pedestrians
        6. Remove finished pedestrians
        7. Advance simulation time
        """
        # Update crossings
        for crossing in self.crossings:
            crossing.update(self.dt)

        # Update vehicles with crossing awareness
        for seg_idx, segment in enumerate(self.segments):
            segment_crossings = self._get_crossings_for_segment(seg_idx)
            active_crossing: Optional[PedestrianCrossing] = None
            
            for crossing in segment_crossings:
                if crossing.should_vehicles_stop():
                    active_crossing = crossing
                    break
            
            self._update_vehicles_on_segment(seg_idx, segment, active_crossing)

        # Handle segment transitions
        self._handle_segment_transitions()

        # Update generators
        for gen in self.vehicle_generator:
            gen.update(self)

        for gen in self.pedestrian_generator:
            gen.update(self)

        # Cleanup finished pedestrians
        self._remove_finished_pedestrians()

        # Advance time
        self.t += self.dt
        self.frame_count += 1
