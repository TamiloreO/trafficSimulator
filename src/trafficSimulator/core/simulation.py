from .vehicle_generator import VehicleGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .road import Road
from .lane_change import LaneChangeStrategy


class Simulation:
    def __init__(self):
        self.segments = []
        self.vehicles = {}
        self.vehicle_generator = []
        self.roads = []
        self._segment_to_road_map = {}
        self.lane_change_strategy = LaneChangeStrategy()

        self.t = 0.0
        self.frame_count = 0
        self.dt = 1/60  

    def add_vehicle(self, veh):
        self.vehicles[veh.id] = veh
        if len(veh.path) > 0:
            self.segments[veh.path[0]].add_vehicle(veh)

    def add_segment(self, seg):
        self.segments.append(seg)

    def add_vehicle_generator(self, gen):
        self.vehicle_generator.append(gen)

    def add_road(self, road):
        self.roads.append(road)
        for seg_idx in road._segment_indices:
            self._segment_to_road_map[seg_idx] = road

    def get_road_for_segment(self, segment_index):
        return self._segment_to_road_map.get(segment_index)
    
    def create_vehicle(self, **kwargs):
        veh = Vehicle(kwargs)
        self.add_vehicle(veh)

    def create_segment(self, *args):
        seg = Segment(args)
        self.add_segment(seg)

    def create_quadratic_bezier_curve(self, start, control, end):
        cur = QuadraticCurve(start, control, end)
        self.add_segment(cur)

    def create_cubic_bezier_curve(self, start, control_1, control_2, end):
        cur = CubicCurve(start, control_1, control_2, end)
        self.add_segment(cur)

    def create_vehicle_generator(self, **kwargs):
        gen = VehicleGenerator(kwargs)
        self.add_vehicle_generator(gen)

    def create_road(self, segment_indices):
        road = Road(segment_indices)
        self.add_road(road)
        return road

    def run(self, steps):
        for _ in range(steps):
            self.update()

    def update(self):
        # Process lane changes first
        self._process_lane_changes()
        
        # Update vehicles
        for segment in self.segments:
            if len(segment.vehicles) != 0:
                self.vehicles[segment.vehicles[0]].update(None, self.dt)
            for i in range(1, len(segment.vehicles)):
                self.vehicles[segment.vehicles[i]].update(self.vehicles[segment.vehicles[i-1]], self.dt)

        # Check roads for out of bounds vehicle
        for segment in self.segments:
            if len(segment.vehicles) == 0: continue
            vehicle_id = segment.vehicles[0]
            vehicle = self.vehicles[vehicle_id]
            if vehicle.x >= segment.get_length():
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    vehicle.current_road_index += 1
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    self.segments[next_road_index].vehicles.append(vehicle_id)
                vehicle.x = 0
                segment.vehicles.popleft() 

        # Update vehicle generators
        for gen in self.vehicle_generator:
            gen.update(self)
        # Increment time
        self.t += self.dt
        self.frame_count += 1

    def _process_lane_changes(self):
        for vehicle_id, vehicle in self.vehicles.items():
            # Update ongoing lane changes
            if vehicle.is_changing_lane:
                completed = vehicle.update_lane_change(self.dt)
                if completed:
                    self._complete_lane_change(vehicle)
                continue
            
            # Check if vehicle should start a lane change
            target_segment = self.lane_change_strategy.should_change_lane(vehicle, self)
            if target_segment is not None:
                current_segment_index = vehicle.path[vehicle.current_road_index]
                self._start_lane_change(vehicle, current_segment_index, target_segment)

    def _start_lane_change(self, vehicle, source_segment_index, target_segment_index):
        vehicle.start_lane_change(source_segment_index, target_segment_index, self.t)
        
        # Update path to use target segment
        vehicle.path[vehicle.current_road_index] = target_segment_index
        
        # Move vehicle from source to target segment
        source_segment = self.segments[source_segment_index]
        target_segment = self.segments[target_segment_index]
        
        source_segment.remove_vehicle(vehicle)
        
        # Insert in correct position in target segment (sorted by x)
        inserted = False
        for i, vid in enumerate(target_segment.vehicles):
            if self.vehicles[vid].x > vehicle.x:
                target_segment.vehicles.insert(i, vehicle.id)
                inserted = True
                break
        if not inserted:
            target_segment.vehicles.append(vehicle.id)

    def _complete_lane_change(self, vehicle):
        vehicle.is_changing_lane = False
        vehicle.lane_change_progress = 1.0
