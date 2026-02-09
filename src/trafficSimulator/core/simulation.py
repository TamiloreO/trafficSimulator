"""
Traffic simulation core module.

This module provides the Simulation class which orchestrates the traffic
simulation including vehicles, pedestrians, road segments, and crossings.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .vehicle_generator import VehicleGenerator
from .pedestrian_generator import PedestrianGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .pedestrian import Pedestrian, PedestrianState
from .pedestrian_crossing import (
    PedestrianCrossing,
    ZebraCrossing,
    PelicanCrossing,
    PuffinCrossing,
    ToucanCrossing,
    PegasusCrossing,
    CrossingType,
)

if TYPE_CHECKING:
    import uuid


class VirtualLead:
    """
    Virtual vehicle used to make real vehicles stop at crossings.
    
    Represents a stationary obstacle at a crossing position that the
    vehicle following model treats as a stopped vehicle ahead.
    
    Attributes:
        x (float): Position along the road segment.
        l (float): Length of the virtual vehicle (always 0).
        v (float): Velocity of the virtual vehicle (always 0).
    """
    
    __slots__ = ('x', 'l', 'v')
    
    def __init__(self, x: float, l: float = 0) -> None:
        """
        Initialize a virtual lead vehicle.
        
        Args:
            x: Position along the road segment in meters.
            l: Length of virtual vehicle (default 0).
        """
        self.x: float = x
        self.l: float = l
        self.v: float = 0.0


class Simulation:
    """
    Main traffic simulation orchestrator.
    
    Manages the simulation state including road segments, vehicles, pedestrians,
    crossings, and generators. Handles the update loop that advances the
    simulation state each time step.
    
    Attributes:
        segments (List[Segment]): Road segments in the simulation.
        vehicles (Dict[uuid.UUID, Vehicle]): Active vehicles indexed by ID.
        vehicle_generator (List[VehicleGenerator]): Vehicle spawn generators.
        crossings (List[PedestrianCrossing]): Pedestrian crossings.
        pedestrians (Dict[uuid.UUID, Pedestrian]): Active pedestrians by ID.
        pedestrian_generator (List[PedestrianGenerator]): Pedestrian spawn generators.
        t (float): Current simulation time in seconds.
        frame_count (int): Number of simulation frames processed.
        dt (float): Time step per frame in seconds (default 1/60).
    
    Example:
        >>> sim = Simulation()
        >>> sim.create_segment((-50, 0), (50, 0))
        >>> sim.create_zebra_crossing(segment_index=0, position=0.5)
        >>> sim.create_vehicle_generator(vehicle_rate=20, vehicles=[(1, {'path': [0]})])
        >>> sim.run(steps=100)
    """
    
    # Default simulation time step (60 FPS)
    DEFAULT_DT: float = 1.0 / 60.0
    
    def __init__(self) -> None:
        """
        Initialize a new simulation with empty state.
        
        Creates empty containers for all simulation entities and sets
        the initial time to zero.
        """
        self.segments: List[Segment] = []
        self.vehicles: Dict['uuid.UUID', Vehicle] = {}
        self.vehicle_generator: List[VehicleGenerator] = []
        
        # Pedestrian-related
        self.crossings: List[PedestrianCrossing] = []
        self.pedestrians: Dict['uuid.UUID', Pedestrian] = {}
        self.pedestrian_generator: List[PedestrianGenerator] = []

        self.t: float = 0.0
        self.frame_count: int = 0
        self.dt: float = self.DEFAULT_DT

    def add_vehicle(self, veh: Vehicle) -> None:
        """
        Add a vehicle to the simulation.
        
        Registers the vehicle in the vehicles dictionary and adds it to
        the first segment in its path.
        
        Args:
            veh: The Vehicle instance to add.
        
        Note:
            The vehicle must have a valid path with at least one segment index.
            Does nothing if veh is None.
        """
        if veh is None:
            return
        
        self.vehicles[veh.id] = veh
        
        if veh.path and len(veh.path) > 0:
            first_segment_idx = veh.path[0]
            if 0 <= first_segment_idx < len(self.segments):
                self.segments[first_segment_idx].add_vehicle(veh)

    def add_segment(self, seg: Segment) -> None:
        """
        Add a road segment to the simulation.
        
        Args:
            seg: The Segment instance to add.
        
        Note:
            Segments are indexed by their position in the list.
            Does nothing if seg is None.
        """
        if seg is None:
            return
        
        self.segments.append(seg)

    def add_vehicle_generator(self, gen: VehicleGenerator) -> None:
        """
        Add a vehicle generator to the simulation.
        
        Args:
            gen: The VehicleGenerator instance to add.
        
        Note:
            Does nothing if gen is None.
        """
        if gen is None:
            return
        
        self.vehicle_generator.append(gen)

    def add_crossing(self, crossing: PedestrianCrossing) -> int:
        """
        Add a pedestrian crossing to the simulation.
        
        Args:
            crossing: The PedestrianCrossing instance to add.
        
        Returns:
            The index of the added crossing in the crossings list.
            Returns -1 if crossing is None.
        """
        if crossing is None:
            return -1
        
        self.crossings.append(crossing)
        return len(self.crossings) - 1

    def add_pedestrian(self, ped: Pedestrian) -> None:
        """
        Add a pedestrian to the simulation.
        
        Args:
            ped: The Pedestrian instance to add.
        
        Note:
            Does nothing if ped is None.
        """
        if ped is None:
            return
        
        self.pedestrians[ped.id] = ped

    def add_pedestrian_generator(self, gen: PedestrianGenerator) -> None:
        """
        Add a pedestrian generator to the simulation.
        
        Args:
            gen: The PedestrianGenerator instance to add.
        
        Note:
            Does nothing if gen is None.
        """
        if gen is None:
            return
        
        self.pedestrian_generator.append(gen)

    def create_vehicle(self, **kwargs: Any) -> None:
        """
        Create and add a new vehicle to the simulation.
        
        Args:
            **kwargs: Configuration parameters passed to Vehicle constructor.
                     Common parameters include:
                     - 'path' (List[int]): Segment indices for route
                     - 'v' (float): Initial velocity
                     - 'x' (float): Initial position on first segment
        """
        veh = Vehicle(kwargs)
        self.add_vehicle(veh)

    def create_segment(self, *args: Any) -> None:
        """
        Create and add a new road segment to the simulation.
        
        Args:
            *args: Points defining the segment, typically two (x, y) tuples
                  for start and end points.
        
        Example:
            >>> sim.create_segment((-50, 0), (50, 0))
        """
        seg = Segment(args)
        self.add_segment(seg)

    def create_quadratic_bezier_curve(
        self,
        start: tuple,
        control: tuple,
        end: tuple
    ) -> None:
        """
        Create and add a quadratic Bezier curve segment.
        
        Args:
            start: Starting point (x, y) of the curve.
            control: Control point (x, y) that shapes the curve.
            end: Ending point (x, y) of the curve.
        
        Example:
            >>> sim.create_quadratic_bezier_curve((0, 0), (25, 25), (50, 0))
        """
        cur = QuadraticCurve(start, control, end)
        self.add_segment(cur)

    def create_cubic_bezier_curve(
        self,
        start: tuple,
        control_1: tuple,
        control_2: tuple,
        end: tuple
    ) -> None:
        """
        Create and add a cubic Bezier curve segment.
        
        Args:
            start: Starting point (x, y) of the curve.
            control_1: First control point (x, y).
            control_2: Second control point (x, y).
            end: Ending point (x, y) of the curve.
        
        Example:
            >>> sim.create_cubic_bezier_curve((0, 0), (10, 20), (40, 20), (50, 0))
        """
        cur = CubicCurve(start, control_1, control_2, end)
        self.add_segment(cur)

    def create_vehicle_generator(self, **kwargs: Any) -> None:
        """
        Create and add a new vehicle generator to the simulation.
        
        Args:
            **kwargs: Configuration parameters passed to VehicleGenerator.
                     Common parameters include:
                     - 'vehicle_rate' (float): Vehicles per minute
                     - 'vehicles' (List[Tuple[int, Dict]]): Weighted vehicle configs
        
        Example:
            >>> sim.create_vehicle_generator(
            ...     vehicle_rate=20,
            ...     vehicles=[(1, {'path': [0], 'v': 15.0})]
            ... )
        """
        gen = VehicleGenerator(kwargs)
        self.add_vehicle_generator(gen)

    def create_pedestrian_generator(self, **kwargs: Any) -> None:
        """
        Create and add a new pedestrian generator to the simulation.
        
        Args:
            **kwargs: Configuration parameters passed to PedestrianGenerator.
                     Common parameters include:
                     - 'pedestrian_rate' (float): Pedestrians per minute
                     - 'crossing_ids' (List[int]): Target crossing indices
                     - 'pedestrians' (List[Tuple[int, Dict]]): Weighted configs
        
        Example:
            >>> sim.create_pedestrian_generator(
            ...     pedestrian_rate=15,
            ...     crossing_ids=[0],
            ...     pedestrians=[(1, {'speed': 1.4})]
            ... )
        """
        gen = PedestrianGenerator(kwargs)
        self.add_pedestrian_generator(gen)

    def create_zebra_crossing(
        self,
        segment_index: int,
        position: float = 0.5,
        **kwargs: Any
    ) -> int:
        """
        Create and add a zebra crossing to the simulation.
        
        Zebra crossings give pedestrians priority - vehicles must stop
        when pedestrians are present.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction (0.0 to 1.0).
                     Default is 0.5 (middle of segment).
            **kwargs: Additional configuration parameters including:
                     - 'width' (float): Crossing width in meters
                     - 'length' (float): Crossing length in meters
        
        Returns:
            Index of the created crossing in the crossings list.
        
        Example:
            >>> crossing_idx = sim.create_zebra_crossing(0, position=0.5, width=6.0)
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
        Create and add a Pelican crossing to the simulation.
        
        Pelican crossings are signal-controlled with push button activation
        and a flashing amber phase.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction (0.0 to 1.0).
            **kwargs: Additional configuration parameters.
        
        Returns:
            Index of the created crossing in the crossings list.
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
        Create and add a Puffin crossing to the simulation.
        
        Puffin crossings have sensors to detect pedestrians and can
        extend crossing time for slow pedestrians.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction (0.0 to 1.0).
            **kwargs: Additional configuration parameters.
        
        Returns:
            Index of the created crossing in the crossings list.
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
        Create and add a Toucan crossing to the simulation.
        
        Toucan crossings are shared crossings for pedestrians and cyclists.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction (0.0 to 1.0).
            **kwargs: Additional configuration parameters.
        
        Returns:
            Index of the created crossing in the crossings list.
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
        Create and add a Pegasus crossing to the simulation.
        
        Pegasus crossings accommodate horse riders in addition to
        pedestrians and cyclists.
        
        Args:
            segment_index: Index of the road segment for this crossing.
            position: Position along segment as fraction (0.0 to 1.0).
            **kwargs: Additional configuration parameters.
        
        Returns:
            Index of the created crossing in the crossings list.
        """
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PegasusCrossing(config)
        return self.add_crossing(crossing)

    def run(self, steps: int) -> None:
        """
        Run the simulation for a specified number of steps.
        
        Args:
            steps: Number of simulation steps to execute.
        
        Note:
            Each step advances simulation time by self.dt seconds.
        """
        if steps <= 0:
            return
        
        for _ in range(steps):
            self.update()

    def _get_crossings_for_segment(self, segment_index: int) -> List[PedestrianCrossing]:
        """
        Get all crossings on a specific road segment.
        
        Args:
            segment_index: Index of the segment to query.
        
        Returns:
            List of crossings that are located on the specified segment.
        """
        return [c for c in self.crossings if c.segment_index == segment_index]

    def _create_virtual_lead_for_crossing(
        self,
        crossing: PedestrianCrossing,
        segment: Segment
    ) -> VirtualLead:
        """
        Create a virtual stopped vehicle at a crossing position.
        
        Used to make vehicles stop at crossings using the normal
        car-following model by treating the crossing as a stopped
        vehicle ahead.
        
        Args:
            crossing: The crossing requiring vehicles to stop.
            segment: The road segment containing the crossing.
        
        Returns:
            A VirtualLead positioned at the crossing's stop line.
        """
        stop_distance = crossing.get_stop_distance(segment)
        return VirtualLead(stop_distance, l=0)

    def _update_vehicle_on_segment(
        self,
        vehicle: Vehicle,
        lead_vehicle: Optional[Vehicle],
        active_crossing: Optional[PedestrianCrossing],
        segment: Segment
    ) -> None:
        """
        Update a single vehicle considering crossing and lead vehicle.
        
        Determines whether the vehicle should follow its lead vehicle or
        stop at an active crossing, whichever requires stopping first.
        
        Args:
            vehicle: The vehicle to update.
            lead_vehicle: The vehicle ahead (if any).
            active_crossing: An active crossing on this segment (if any).
            segment: The road segment the vehicle is on.
        """
        if active_crossing is not None:
            stop_distance = active_crossing.get_stop_distance(segment)
            
            # Only consider stopping if vehicle hasn't passed the crossing
            if vehicle.x < stop_distance:
                virtual_lead = self._create_virtual_lead_for_crossing(
                    active_crossing, segment
                )
                
                if lead_vehicle is not None:
                    # Use whichever obstacle is closer
                    if lead_vehicle.x < virtual_lead.x:
                        vehicle.update(lead_vehicle, self.dt)
                    else:
                        vehicle.update(virtual_lead, self.dt)
                else:
                    vehicle.update(virtual_lead, self.dt)
            else:
                # Past the crossing, follow lead normally
                vehicle.update(lead_vehicle, self.dt)
        else:
            # No active crossing, follow lead normally
            vehicle.update(lead_vehicle, self.dt)

    def update(self) -> None:
        """
        Advance the simulation by one time step.
        
        Performs the following updates in order:
        1. Update all crossing state machines
        2. Update all vehicles with crossing awareness
        3. Handle vehicles leaving segments
        4. Run vehicle generators
        5. Run pedestrian generators
        6. Remove finished pedestrians
        7. Increment simulation time
        """
        # Update crossings first
        for crossing in self.crossings:
            crossing.update(self.dt)

        # Update vehicles with crossing awareness
        for seg_idx, segment in enumerate(self.segments):
            if len(segment.vehicles) == 0:
                continue
            
            # Check for active crossings on this segment
            segment_crossings = self._get_crossings_for_segment(seg_idx)
            active_crossing: Optional[PedestrianCrossing] = None
            
            for crossing in segment_crossings:
                if crossing.should_vehicles_stop():
                    active_crossing = crossing
                    break

            # Update first vehicle (no lead)
            first_vehicle_id = segment.vehicles[0]
            first_vehicle = self.vehicles.get(first_vehicle_id)
            
            if first_vehicle is not None:
                self._update_vehicle_on_segment(
                    first_vehicle, None, active_crossing, segment
                )

            # Update following vehicles
            for i in range(1, len(segment.vehicles)):
                curr_id = segment.vehicles[i]
                prev_id = segment.vehicles[i - 1]
                
                curr_vehicle = self.vehicles.get(curr_id)
                prev_vehicle = self.vehicles.get(prev_id)
                
                if curr_vehicle is not None:
                    self._update_vehicle_on_segment(
                        curr_vehicle, prev_vehicle, active_crossing, segment
                    )

        # Check roads for out of bounds vehicle
        for segment in self.segments:
            if len(segment.vehicles) == 0:
                continue
            
            vehicle_id = segment.vehicles[0]
            vehicle = self.vehicles.get(vehicle_id)
            
            if vehicle is None:
                segment.vehicles.popleft()
                continue
            
            if vehicle.x >= segment.get_length():
                # Check if vehicle has more segments in path
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    vehicle.current_road_index += 1
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    
                    if 0 <= next_road_index < len(self.segments):
                        self.segments[next_road_index].vehicles.append(vehicle_id)
                
                vehicle.x = 0
                segment.vehicles.popleft()

        # Update vehicle generators
        for gen in self.vehicle_generator:
            gen.update(self)

        # Update pedestrian generators
        for gen in self.pedestrian_generator:
            gen.update(self)

        # Remove finished pedestrians
        finished_peds = [
            pid for pid, ped in self.pedestrians.items()
            if ped.state == PedestrianState.FINISHED
        ]
        for pid in finished_peds:
            del self.pedestrians[pid]

        # Increment time
        self.t += self.dt
        self.frame_count += 1

    def __repr__(self) -> str:
        """
        Return a string representation of the simulation state.
        
        Returns:
            String containing simulation time and entity counts.
        """
        return (
            f"Simulation(t={self.t:.2f}s, "
            f"vehicles={len(self.vehicles)}, "
            f"pedestrians={len(self.pedestrians)}, "
            f"segments={len(self.segments)}, "
            f"crossings={len(self.crossings)})"
        )
