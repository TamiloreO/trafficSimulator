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


class Simulation:
    def __init__(self):
        self.segments = []
        self.vehicles = {}
        self.vehicle_generator = []
        
        # Pedestrian-related
        self.crossings = []
        self.pedestrians = {}
        self.pedestrian_generator = []

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

    def add_crossing(self, crossing):
        self.crossings.append(crossing)
        return len(self.crossings) - 1

    def add_pedestrian(self, ped):
        self.pedestrians[ped.id] = ped

    def add_pedestrian_generator(self, gen):
        self.pedestrian_generator.append(gen)

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

    def create_pedestrian_generator(self, **kwargs):
        gen = PedestrianGenerator(kwargs)
        self.add_pedestrian_generator(gen)

    def create_zebra_crossing(self, segment_index, position=0.5, **kwargs):
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = ZebraCrossing(config)
        return self.add_crossing(crossing)

    def create_pelican_crossing(self, segment_index, position=0.5, **kwargs):
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PelicanCrossing(config)
        return self.add_crossing(crossing)

    def create_puffin_crossing(self, segment_index, position=0.5, **kwargs):
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PuffinCrossing(config)
        return self.add_crossing(crossing)

    def create_toucan_crossing(self, segment_index, position=0.5, **kwargs):
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = ToucanCrossing(config)
        return self.add_crossing(crossing)

    def create_pegasus_crossing(self, segment_index, position=0.5, **kwargs):
        config = {'segment_index': segment_index, 'position': position, **kwargs}
        crossing = PegasusCrossing(config)
        return self.add_crossing(crossing)

    def run(self, steps):
        for _ in range(steps):
            self.update()

    def _get_crossing_for_segment(self, segment_index):
        """Get crossings that affect a given segment."""
        return [c for c in self.crossings if c.segment_index == segment_index]

    def _create_virtual_lead_for_crossing(self, crossing, segment):
        """Create a virtual stopped vehicle at the crossing position."""
        class VirtualLead:
            def __init__(self, x, l=0):
                self.x = x
                self.l = l
                self.v = 0
        
        stop_distance = crossing.get_stop_distance(segment)
        # Place virtual lead at stop line with small length
        # This makes vehicle stop s0 meters before the virtual lead position
        return VirtualLead(stop_distance, l=0)

    def update(self):
        # Update crossings first
        for crossing in self.crossings:
            crossing.update(self.dt)

        # Update vehicles with crossing awareness
        for seg_idx, segment in enumerate(self.segments):
            if len(segment.vehicles) == 0:
                continue
                
            # Check for active crossings on this segment
            segment_crossings = self._get_crossing_for_segment(seg_idx)
            active_crossing = None
            for crossing in segment_crossings:
                if crossing.should_vehicles_stop():
                    active_crossing = crossing
                    break

            # Update first vehicle
            vehicle_id = segment.vehicles[0]
            vehicle = self.vehicles[vehicle_id]
            
            if active_crossing:
                stop_distance = active_crossing.get_stop_distance(segment)
                # Only stop if vehicle hasn't passed the crossing yet
                if vehicle.x < stop_distance:
                    virtual_lead = self._create_virtual_lead_for_crossing(active_crossing, segment)
                    vehicle.update(virtual_lead, self.dt)
                else:
                    vehicle.update(None, self.dt)
            else:
                vehicle.update(None, self.dt)

            # Update following vehicles
            for i in range(1, len(segment.vehicles)):
                curr_id = segment.vehicles[i]
                prev_id = segment.vehicles[i-1]
                curr_vehicle = self.vehicles[curr_id]
                prev_vehicle = self.vehicles[prev_id]
                
                if active_crossing:
                    stop_distance = active_crossing.get_stop_distance(segment)
                    if curr_vehicle.x < stop_distance:
                        virtual_lead = self._create_virtual_lead_for_crossing(active_crossing, segment)
                        # Use the closer of the two: real lead or virtual crossing lead
                        if prev_vehicle.x < virtual_lead.x:
                            curr_vehicle.update(prev_vehicle, self.dt)
                        else:
                            curr_vehicle.update(virtual_lead, self.dt)
                    else:
                        curr_vehicle.update(prev_vehicle, self.dt)
                else:
                    curr_vehicle.update(prev_vehicle, self.dt)

        # Check roads for out of bounds vehicle
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
                vehicle.x = 0
                segment.vehicles.popleft()

        # Update vehicle generators
        for gen in self.vehicle_generator:
            gen.update(self)

        # Update pedestrian generators
        for gen in self.pedestrian_generator:
            gen.update(self)

        # Remove finished pedestrians
        finished_peds = [pid for pid, ped in self.pedestrians.items() 
                        if ped.is_finished()]
        for pid in finished_peds:
            del self.pedestrians[pid]

        # Increment time
        self.t += self.dt
        self.frame_count += 1
