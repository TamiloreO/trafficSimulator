from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from .vehicle_generator import VehicleGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .road import Road, RoadBuilder, create_straight_road
from .lane_change import (
    LaneChangeController,
    LaneChangeContextBuilder,
    LaneChangeParameters,
    LaneChangeState,
)


@dataclass
class SimulationStatistics:
    """Tracks simulation statistics for completed vehicles."""
    vehicles_completed: int = 0
    total_travel_time: float = 0.0
    total_distance_traveled: float = 0.0
    lane_changes_completed: int = 0
    
    @property
    def average_travel_time(self) -> float:
        if self.vehicles_completed == 0:
            return 0.0
        return self.total_travel_time / self.vehicles_completed
    
    @property
    def average_speed(self) -> float:
        if self.total_travel_time == 0:
            return 0.0
        return self.total_distance_traveled / self.total_travel_time
    
    def record_completed_vehicle(self, travel_time: float, distance: float):
        self.vehicles_completed += 1
        self.total_travel_time += travel_time
        self.total_distance_traveled += distance
    
    def record_lane_change(self):
        self.lane_changes_completed += 1


class Simulation:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.segments: List[Segment] = []
        self.vehicles: Dict[Any, Vehicle] = {}
        self.vehicle_generator: List[VehicleGenerator] = []
        
        # Road management
        self.roads: Dict[str, Road] = {}
        self.segment_to_road: Dict[int, str] = {}
        self.segment_to_lane: Dict[int, int] = {}
        
        # Lane change management
        lane_change_params = LaneChangeParameters(
            **config.get('lane_change_params', {})
        )
        self.lane_change_controller = LaneChangeController(lane_change_params)
        self.enable_lane_changes = config.get('enable_lane_changes', True)
        
        # Statistics tracking
        self.statistics = SimulationStatistics()
        self._vehicle_spawn_times: Dict[Any, float] = {}
        self._vehicle_spawn_positions: Dict[Any, float] = {}

        self.t = 0.0
        self.frame_count = 0
        self.dt = 1/60

    def add_vehicle(self, veh: Vehicle):
        self.vehicles[veh.id] = veh
        self._vehicle_spawn_times[veh.id] = self.t
        self._vehicle_spawn_positions[veh.id] = veh.x
        
        if len(veh.path) > 0:
            segment_index = veh.path[0]
            self.segments[segment_index].add_vehicle(veh)
            
            if segment_index in self.segment_to_road:
                veh.current_road_id = self.segment_to_road[segment_index]
                veh.current_lane_index = self.segment_to_lane.get(segment_index, 0)

    def remove_vehicle(self, vehicle_id: Any):
        """Remove a vehicle from the simulation and record statistics."""
        if vehicle_id not in self.vehicles:
            return
        
        vehicle = self.vehicles[vehicle_id]
        
        # Calculate travel time and distance
        spawn_time = self._vehicle_spawn_times.get(vehicle_id, 0.0)
        travel_time = self.t - spawn_time
        
        # Calculate total distance (sum of completed path segments)
        total_distance = 0.0
        for i in range(vehicle.current_road_index):
            if i < len(vehicle.path):
                seg_idx = vehicle.path[i]
                if seg_idx < len(self.segments):
                    total_distance += self.segments[seg_idx].get_length()
        
        # Add partial distance on current segment
        spawn_pos = self._vehicle_spawn_positions.get(vehicle_id, 0.0)
        if vehicle.current_road_index == 0:
            total_distance += vehicle.x - spawn_pos
        else:
            total_distance += vehicle.x
        
        self.statistics.record_completed_vehicle(travel_time, total_distance)
        
        # Clean up lane change state
        self.lane_change_controller.cancel_lane_change(vehicle_id)
        if vehicle_id in self.lane_change_controller.cooldowns:
            del self.lane_change_controller.cooldowns[vehicle_id]
        
        # Remove from tracking dictionaries
        del self.vehicles[vehicle_id]
        if vehicle_id in self._vehicle_spawn_times:
            del self._vehicle_spawn_times[vehicle_id]
        if vehicle_id in self._vehicle_spawn_positions:
            del self._vehicle_spawn_positions[vehicle_id]

    def add_segment(self, seg: Segment) -> int:
        index = len(self.segments)
        self.segments.append(seg)
        return index

    def add_vehicle_generator(self, gen: VehicleGenerator):
        self.vehicle_generator.append(gen)

    def add_road(self, road: Road) -> List[int]:
        self.roads[road.id] = road
        segment_indices = []
        
        starting_index = len(self.segments)
        for lane_index, lane in enumerate(road.lanes):
            segment_index = self.add_segment(lane)
            segment_indices.append(segment_index)
            self.segment_to_road[segment_index] = road.id
            self.segment_to_lane[segment_index] = lane_index
        
        road.register_segment_indices(starting_index)
        return segment_indices

    def create_vehicle(self, **kwargs):
        veh = Vehicle(kwargs)
        self.add_vehicle(veh)
        return veh

    def create_segment(self, *args) -> int:
        seg = Segment(args)
        return self.add_segment(seg)

    def create_quadratic_bezier_curve(self, start, control, end) -> int:
        cur = QuadraticCurve(start, control, end)
        return self.add_segment(cur)

    def create_cubic_bezier_curve(self, start, control_1, control_2, end) -> int:
        cur = CubicCurve(start, control_1, control_2, end)
        return self.add_segment(cur)

    def create_vehicle_generator(self, **kwargs):
        gen = VehicleGenerator(kwargs)
        self.add_vehicle_generator(gen)
        return gen

    def create_road(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        lane_count: int = 1,
        lane_width: float = 3.5,
        **kwargs
    ) -> Tuple[Road, List[int]]:
        road = create_straight_road(start, end, lane_count, lane_width, kwargs)
        segment_indices = self.add_road(road)
        return road, segment_indices

    def create_road_from_builder(self, builder: RoadBuilder) -> Tuple[Road, List[int]]:
        road = builder.build()
        segment_indices = self.add_road(road)
        return road, segment_indices

    def get_road_for_segment(self, segment_index: int) -> Optional[Road]:
        road_id = self.segment_to_road.get(segment_index)
        if road_id:
            return self.roads.get(road_id)
        return None

    def get_lane_index_for_segment(self, segment_index: int) -> int:
        return self.segment_to_lane.get(segment_index, 0)

    def run(self, steps: int):
        for _ in range(steps):
            self.update()

    def update(self):
        self._update_vehicle_movements()
        
        if self.enable_lane_changes:
            self._process_lane_changes()
        
        self._handle_segment_transitions()

        for gen in self.vehicle_generator:
            gen.update(self)
        
        self.t += self.dt
        self.frame_count += 1

    def _update_vehicle_movements(self):
        for segment in self.segments:
            if len(segment.vehicles) == 0:
                continue
            
            first_vid = segment.vehicles[0]
            if first_vid in self.vehicles:
                self.vehicles[first_vid].update(None, self.dt)
            
            for i in range(1, len(segment.vehicles)):
                current_vid = segment.vehicles[i]
                lead_vid = segment.vehicles[i-1]
                if current_vid in self.vehicles and lead_vid in self.vehicles:
                    self.vehicles[current_vid].update(self.vehicles[lead_vid], self.dt)

    def _process_lane_changes(self):
        vehicle_ids = list(self.vehicles.keys())
        for vehicle_id in vehicle_ids:
            if vehicle_id not in self.vehicles:
                continue
            vehicle = self.vehicles[vehicle_id]
            
            if self.lane_change_controller.is_changing_lanes(vehicle_id):
                self._update_active_lane_change(vehicle)
                continue
            
            if vehicle.current_road_id:
                self._evaluate_lane_change(vehicle)

    def _update_active_lane_change(self, vehicle: Vehicle):
        request = self.lane_change_controller.update_lane_change(
            vehicle.id, self.t, self.dt
        )
        
        if request:
            vehicle.update_lane_change_progress(request.progress)
            
            if request.state == LaneChangeState.COMPLETING:
                self._complete_lane_change(vehicle, request)

    def _complete_lane_change(self, vehicle: Vehicle, request):
        road = self.roads.get(request.road_id)
        if not road:
            self.lane_change_controller.cancel_lane_change(vehicle.id)
            vehicle.cancel_lane_change()
            return
        
        current_segment_index = None
        for seg_idx, road_id in self.segment_to_road.items():
            if road_id == request.road_id:
                lane_idx = self.segment_to_lane.get(seg_idx, 0)
                if lane_idx == request.source_lane_index:
                    if vehicle.id in self.segments[seg_idx].vehicles:
                        current_segment_index = seg_idx
                        break
        
        if current_segment_index is None:
            self.lane_change_controller.cancel_lane_change(vehicle.id)
            vehicle.cancel_lane_change()
            return
        
        target_segment_index = None
        for seg_idx, road_id in self.segment_to_road.items():
            if road_id == request.road_id:
                lane_idx = self.segment_to_lane.get(seg_idx, 0)
                if lane_idx == request.target_lane_index:
                    target_segment_index = seg_idx
                    break
        
        if target_segment_index is None:
            self.lane_change_controller.cancel_lane_change(vehicle.id)
            vehicle.cancel_lane_change()
            return
        
        self.segments[current_segment_index].remove_vehicle(vehicle)
        self._insert_vehicle_sorted(target_segment_index, vehicle)
        
        if len(vehicle.path) > 0:
            vehicle.path[vehicle.current_road_index] = target_segment_index
        
        self.lane_change_controller.complete_lane_change(vehicle.id, self.t)
        vehicle.complete_lane_change()
        self.statistics.record_lane_change()

    def _insert_vehicle_sorted(self, segment_index: int, vehicle: Vehicle):
        segment = self.segments[segment_index]
        insert_position = len(segment.vehicles)
        
        for i, vid in enumerate(segment.vehicles):
            if vid in self.vehicles and self.vehicles[vid].x < vehicle.x:
                insert_position = i
                break
        
        segment.vehicles.insert(insert_position, vehicle.id)

    def _evaluate_lane_change(self, vehicle: Vehicle):
        if not self.lane_change_controller.can_initiate_lane_change(vehicle.id, self.t):
            return
        
        road = self.roads.get(vehicle.current_road_id)
        if not road or road.lane_count <= 1:
            return
        
        context = self._build_lane_change_context(vehicle, road)
        if context is None:
            return
        
        request = self.lane_change_controller.request_lane_change(
            vehicle, context, self.t
        )
        
        if request:
            vehicle.start_lane_change(
                request.source_lane_index,
                request.target_lane_index,
                request.road_id
            )

    def _build_lane_change_context(self, vehicle: Vehicle, road: Road):
        current_lane_index = vehicle.current_lane_index
        
        current_segment_index = None
        for seg_idx, road_id in self.segment_to_road.items():
            if road_id == road.id:
                lane_idx = self.segment_to_lane.get(seg_idx, 0)
                if lane_idx == current_lane_index:
                    current_segment_index = seg_idx
                    break
        
        if current_segment_index is None:
            return None
        
        builder = LaneChangeContextBuilder()
        builder.with_vehicle_info(vehicle.x, vehicle.v, vehicle.l)
        builder.with_current_lane(current_lane_index, road.id)
        
        lead_gap, lead_speed = self._get_lead_vehicle_info(current_segment_index, vehicle)
        builder.with_lead_vehicle(lead_gap, lead_speed)
        
        left_lane = road.get_left_lane(current_lane_index)
        if left_lane:
            left_lane_idx, _ = left_lane
            left_segment_index = self._get_segment_for_lane(road.id, left_lane_idx)
            if left_segment_index is not None:
                front_gap, rear_gap, front_speed, rear_speed = self._get_adjacent_lane_info(
                    left_segment_index, vehicle.x
                )
                builder.with_left_lane(True, front_gap, rear_gap, front_speed, rear_speed)
        else:
            builder.with_left_lane(False)
        
        right_lane = road.get_right_lane(current_lane_index)
        if right_lane:
            right_lane_idx, _ = right_lane
            right_segment_index = self._get_segment_for_lane(road.id, right_lane_idx)
            if right_segment_index is not None:
                front_gap, rear_gap, front_speed, rear_speed = self._get_adjacent_lane_info(
                    right_segment_index, vehicle.x
                )
                builder.with_right_lane(True, front_gap, rear_gap, front_speed, rear_speed)
        else:
            builder.with_right_lane(False)
        
        return builder.build()

    def _get_segment_for_lane(self, road_id: str, lane_index: int) -> Optional[int]:
        for seg_idx, rid in self.segment_to_road.items():
            if rid == road_id:
                if self.segment_to_lane.get(seg_idx, 0) == lane_index:
                    return seg_idx
        return None

    def _get_lead_vehicle_info(
        self, segment_index: int, vehicle: Vehicle
    ) -> Tuple[Optional[float], Optional[float]]:
        segment = self.segments[segment_index]
        
        try:
            vehicle_pos = list(segment.vehicles).index(vehicle.id)
        except ValueError:
            return None, None
        
        if vehicle_pos == 0:
            return None, None
        
        lead_id = segment.vehicles[vehicle_pos - 1]
        if lead_id not in self.vehicles:
            return None, None
        lead = self.vehicles[lead_id]
        
        gap = lead.x - vehicle.x - lead.l
        return gap, lead.v

    def _get_adjacent_lane_info(
        self, segment_index: int, vehicle_x: float
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        segment = self.segments[segment_index]
        
        if len(segment.vehicles) == 0:
            return None, None, None, None
        
        front_vehicle = None
        rear_vehicle = None
        
        for vid in segment.vehicles:
            if vid not in self.vehicles:
                continue
            v = self.vehicles[vid]
            if v.x >= vehicle_x:
                if front_vehicle is None or v.x < front_vehicle.x:
                    front_vehicle = v
            else:
                if rear_vehicle is None or v.x > rear_vehicle.x:
                    rear_vehicle = v
        
        front_gap = None
        front_speed = None
        rear_gap = None
        rear_speed = None
        
        if front_vehicle:
            front_gap = front_vehicle.x - vehicle_x - front_vehicle.l
            front_speed = front_vehicle.v
        
        if rear_vehicle:
            rear_gap = vehicle_x - rear_vehicle.x - rear_vehicle.l
            rear_speed = rear_vehicle.v
        
        return front_gap, rear_gap, front_speed, rear_speed

    def _handle_segment_transitions(self):
        """Handle vehicles transitioning between segments or completing their path."""
        vehicles_to_remove = []
        
        for segment in self.segments:
            if len(segment.vehicles) == 0:
                continue
            
            vehicle_id = segment.vehicles[0]
            if vehicle_id not in self.vehicles:
                segment.vehicles.popleft()
                continue
            
            vehicle = self.vehicles[vehicle_id]
            
            if vehicle.x >= segment.get_length():
                # Check if vehicle has more segments in path
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    # Move to next segment
                    vehicle.current_road_index += 1
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    self.segments[next_road_index].vehicles.append(vehicle_id)
                    
                    if next_road_index in self.segment_to_road:
                        vehicle.current_road_id = self.segment_to_road[next_road_index]
                        vehicle.current_lane_index = self.segment_to_lane.get(next_road_index, 0)
                    
                    vehicle.x = 0
                else:
                    # Vehicle has completed its path - mark for removal
                    vehicles_to_remove.append(vehicle_id)
                
                segment.vehicles.popleft()
        
        # Remove completed vehicles
        for vehicle_id in vehicles_to_remove:
            self.remove_vehicle(vehicle_id)
