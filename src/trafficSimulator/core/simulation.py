from .vehicle_generator import VehicleGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .pedestrian import Pedestrian, PedestrianState
from .pedestrian_crossing import (
    PedestrianCrossing, CrossingType, SignalState,
    create_zebra_crossing, create_pelican_crossing, create_puffin_crossing,
    create_toucan_crossing, create_pegasus_crossing, create_tiger_crossing
)
from .pedestrian_generator import PedestrianGenerator

from typing import Dict, List, Optional, Any
import uuid


class Simulation:
    """
    Main simulation class that manages vehicles, pedestrians, and road infrastructure.
    """
    
    def __init__(self):
        self.segments: List = []
        self.vehicles: Dict[uuid.UUID, Vehicle] = {}
        self.vehicle_generator: List[VehicleGenerator] = []
        
        # Pedestrian system
        self.pedestrians: Dict[uuid.UUID, Pedestrian] = {}
        self.crossings: List[PedestrianCrossing] = []
        self.pedestrian_generators: List[PedestrianGenerator] = []
        
        # Mapping of segments to crossings on them
        self._segment_crossings: Dict[int, List[int]] = {}

        self.t = 0.0
        self.frame_count = 0
        self.dt = 1/60

    # === Vehicle Management ===
    
    def add_vehicle(self, veh: Vehicle) -> bool:
        """Add a vehicle to the simulation."""
        if veh is None or veh.id is None:
            return False
            
        self.vehicles[veh.id] = veh
        if veh.path and len(veh.path) > 0:
            path_idx = veh.path[0]
            if 0 <= path_idx < len(self.segments):
                self.segments[path_idx].add_vehicle(veh)
        return True

    def add_segment(self, seg) -> int:
        """Add a road segment and return its index."""
        if seg is None:
            return -1
        self.segments.append(seg)
        return len(self.segments) - 1

    def add_vehicle_generator(self, gen: VehicleGenerator) -> None:
        """Add a vehicle generator."""
        if gen is not None:
            self.vehicle_generator.append(gen)

    def create_vehicle(self, **kwargs) -> Optional[Vehicle]:
        """Create and add a vehicle."""
        try:
            veh = Vehicle(kwargs)
            if self.add_vehicle(veh):
                return veh
        except Exception:
            pass
        return None

    def create_segment(self, *args) -> int:
        """Create and add a segment."""
        try:
            seg = Segment(args)
            return self.add_segment(seg)
        except Exception:
            return -1

    def create_quadratic_bezier_curve(self, start, control, end) -> int:
        """Create and add a quadratic bezier curve."""
        try:
            cur = QuadraticCurve(start, control, end)
            return self.add_segment(cur)
        except Exception:
            return -1

    def create_cubic_bezier_curve(self, start, control_1, control_2, end) -> int:
        """Create and add a cubic bezier curve."""
        try:
            cur = CubicCurve(start, control_1, control_2, end)
            return self.add_segment(cur)
        except Exception:
            return -1

    def create_vehicle_generator(self, **kwargs) -> Optional[VehicleGenerator]:
        """Create and add a vehicle generator."""
        try:
            gen = VehicleGenerator(kwargs)
            self.add_vehicle_generator(gen)
            return gen
        except Exception:
            return None

    # === Pedestrian Management ===
    
    def add_pedestrian(self, ped: Pedestrian, crossing_index: int) -> bool:
        """
        Add a pedestrian to a specific crossing.
        
        Args:
            ped: The pedestrian to add
            crossing_index: Index of the crossing in self.crossings
            
        Returns:
            True if successfully added
        """
        if ped is None or ped.id is None:
            return False
            
        if crossing_index < 0 or crossing_index >= len(self.crossings):
            return False
            
        crossing = self.crossings[crossing_index]
        
        if crossing.add_pedestrian(ped):
            self.pedestrians[ped.id] = ped
            ped.crossing_id = crossing.id
            return True
        return False

    def remove_pedestrian(self, ped_id: uuid.UUID) -> bool:
        """Remove a pedestrian from the simulation."""
        if ped_id not in self.pedestrians:
            return False
            
        ped = self.pedestrians[ped_id]
        
        # Remove from crossing
        for crossing in self.crossings:
            if crossing.id == ped.crossing_id:
                crossing.remove_pedestrian(ped_id)
                break
        
        del self.pedestrians[ped_id]
        return True

    def add_crossing(self, crossing: PedestrianCrossing) -> int:
        """
        Add a pedestrian crossing to the simulation.
        
        Args:
            crossing: The crossing to add
            
        Returns:
            Index of the crossing, or -1 on failure
        """
        if crossing is None:
            return -1
            
        seg_idx = crossing.segment_index
        if seg_idx < 0 or seg_idx >= len(self.segments):
            return -1
            
        # Attach crossing to segment
        crossing.attach_to_segment(
            self.segments[seg_idx], 
            crossing.position_on_segment
        )
        
        self.crossings.append(crossing)
        crossing_idx = len(self.crossings) - 1
        
        # Track which crossings are on which segments
        if seg_idx not in self._segment_crossings:
            self._segment_crossings[seg_idx] = []
        self._segment_crossings[seg_idx].append(crossing_idx)
        
        return crossing_idx

    def create_crossing(self, crossing_type: CrossingType, segment_index: int,
                        position: float = 0.5, **kwargs) -> int:
        """
        Create and add a pedestrian crossing.
        
        Args:
            crossing_type: Type of crossing
            segment_index: Index of segment to place crossing on
            position: Position along segment (0-1)
            **kwargs: Additional configuration
            
        Returns:
            Index of created crossing, or -1 on failure
        """
        try:
            config = {
                'crossing_type': crossing_type,
                'segment_index': segment_index,
                'position_on_segment': position,
                **kwargs
            }
            crossing = PedestrianCrossing(config)
            return self.add_crossing(crossing)
        except Exception:
            return -1

    def create_zebra_crossing(self, segment_index: int, position: float = 0.5) -> int:
        """Create a zebra crossing (basic striped, pedestrian priority)."""
        return self.create_crossing(CrossingType.ZEBRA, segment_index, position)

    def create_pelican_crossing(self, segment_index: int, position: float = 0.5,
                                 red_time: float = 15.0, green_time: float = 30.0) -> int:
        """Create a pelican crossing (signal-controlled with push button)."""
        return self.create_crossing(
            CrossingType.PELICAN, segment_index, position,
            red_time=red_time, green_time=green_time
        )

    def create_puffin_crossing(self, segment_index: int, position: float = 0.5) -> int:
        """Create a puffin crossing (intelligent with pedestrian detection)."""
        return self.create_crossing(CrossingType.PUFFIN, segment_index, position)

    def create_toucan_crossing(self, segment_index: int, position: float = 0.5) -> int:
        """Create a toucan crossing (pedestrians + cyclists)."""
        return self.create_crossing(CrossingType.TOUCAN, segment_index, position)

    def create_pegasus_crossing(self, segment_index: int, position: float = 0.5) -> int:
        """Create a pegasus crossing (includes horse riders)."""
        return self.create_crossing(CrossingType.PEGASUS, segment_index, position)

    def create_tiger_crossing(self, segment_index: int, position: float = 0.5) -> int:
        """Create a tiger crossing (parallel zebra and cycle crossing)."""
        return self.create_crossing(CrossingType.TIGER, segment_index, position)

    def add_pedestrian_generator(self, gen: PedestrianGenerator) -> None:
        """Add a pedestrian generator."""
        if gen is not None:
            self.pedestrian_generators.append(gen)

    def create_pedestrian_generator(self, **kwargs) -> Optional[PedestrianGenerator]:
        """Create and add a pedestrian generator."""
        try:
            gen = PedestrianGenerator(kwargs)
            self.add_pedestrian_generator(gen)
            return gen
        except Exception:
            return None

    # === Simulation Update ===
    
    def run(self, steps: int) -> None:
        """Run simulation for specified number of steps."""
        steps = max(0, min(steps, 10000))  # Sanity limit
        for _ in range(steps):
            self.update()

    def update(self) -> None:
        """Update one simulation step."""
        # Update crossings first (affects vehicle behavior)
        self._update_crossings()
        
        # Update vehicles with crossing awareness
        self._update_vehicles()
        
        # Check roads for out of bounds vehicles
        self._check_vehicle_bounds()
        
        # Update vehicle generators
        for gen in self.vehicle_generator:
            try:
                gen.update(self)
            except Exception:
                pass
        
        # Update pedestrian generators
        for gen in self.pedestrian_generators:
            try:
                gen.update(self)
            except Exception:
                pass
        
        # Clean up finished pedestrians
        self._cleanup_finished_pedestrians()
        
        # Increment time
        self.t += self.dt
        self.frame_count += 1

    def _update_crossings(self) -> None:
        """Update all pedestrian crossings."""
        for crossing in self.crossings:
            try:
                crossing.update(self.dt, self.t, self.pedestrians)
            except Exception:
                pass

    def _update_vehicles(self) -> None:
        """Update all vehicles with crossing awareness."""
        for segment_idx, segment in enumerate(self.segments):
            if len(segment.vehicles) == 0:
                continue
                
            # Check for crossings on this segment
            blocking_crossings = self._get_blocking_crossings(segment_idx)
            
            # Update each vehicle
            for i, vehicle_id in enumerate(segment.vehicles):
                if vehicle_id not in self.vehicles:
                    continue
                    
                vehicle = self.vehicles[vehicle_id]
                lead = None
                
                # Get lead vehicle
                if i > 0:
                    lead_id = segment.vehicles[i - 1]
                    lead = self.vehicles.get(lead_id)
                
                # Check if vehicle should stop for crossing
                should_stop = self._should_vehicle_stop_for_crossing(
                    vehicle, segment, segment_idx, blocking_crossings
                )
                
                if should_stop:
                    vehicle.stopped = True
                else:
                    vehicle.stopped = False
                
                vehicle.update(lead, self.dt)

    def _get_blocking_crossings(self, segment_idx: int) -> List[PedestrianCrossing]:
        """Get crossings on a segment that are blocking traffic."""
        blocking = []
        
        if segment_idx not in self._segment_crossings:
            return blocking
            
        for crossing_idx in self._segment_crossings[segment_idx]:
            if crossing_idx < len(self.crossings):
                crossing = self.crossings[crossing_idx]
                if crossing.should_block_vehicles(self.pedestrians):
                    blocking.append(crossing)
        
        return blocking

    def _should_vehicle_stop_for_crossing(self, vehicle: Vehicle, segment,
                                           segment_idx: int,
                                           blocking_crossings: List[PedestrianCrossing]) -> bool:
        """Determine if a vehicle should stop for a crossing."""
        if not blocking_crossings:
            return False
            
        try:
            segment_length = segment.get_length()
        except Exception:
            return False
        
        if segment_length <= 0:
            return False
            
        for crossing in blocking_crossings:
            stop_pos = crossing.get_stop_position(segment_length)
            
            # Vehicle should stop if it hasn't reached the stop line yet
            # and is within approach distance
            if vehicle.x < stop_pos:
                return True
        
        return False

    def _check_vehicle_bounds(self) -> None:
        """Check for vehicles that have left their segment."""
        for segment_idx, segment in enumerate(self.segments):
            if len(segment.vehicles) == 0:
                continue
                
            vehicle_id = segment.vehicles[0]
            if vehicle_id not in self.vehicles:
                try:
                    segment.vehicles.popleft()
                except Exception:
                    pass
                continue
                
            vehicle = self.vehicles[vehicle_id]
            
            try:
                seg_length = segment.get_length()
            except Exception:
                continue
            
            if vehicle.x >= seg_length:
                # Vehicle has reached end of segment
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    vehicle.current_road_index += 1
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    
                    if 0 <= next_road_index < len(self.segments):
                        self.segments[next_road_index].vehicles.append(vehicle_id)
                
                vehicle.x = 0
                
                try:
                    segment.vehicles.popleft()
                except Exception:
                    pass

    def _cleanup_finished_pedestrians(self) -> None:
        """Remove pedestrians that have finished crossing."""
        finished = []
        
        for ped_id, ped in self.pedestrians.items():
            if ped.is_finished():
                finished.append(ped_id)
        
        for ped_id in finished:
            self.remove_pedestrian(ped_id)

    # === Query Methods ===
    
    def get_crossing_at_segment(self, segment_idx: int) -> List[PedestrianCrossing]:
        """Get all crossings on a specific segment."""
        if segment_idx not in self._segment_crossings:
            return []
        
        result = []
        for crossing_idx in self._segment_crossings[segment_idx]:
            if crossing_idx < len(self.crossings):
                result.append(self.crossings[crossing_idx])
        return result

    def press_crossing_button(self, crossing_index: int) -> bool:
        """Press the button at a signaled crossing."""
        if crossing_index < 0 or crossing_index >= len(self.crossings):
            return False
            
        crossing = self.crossings[crossing_index]
        if crossing.is_signaled:
            crossing.press_button(self.t)
            return True
        return False
