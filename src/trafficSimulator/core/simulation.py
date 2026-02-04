from .vehicle_generator import VehicleGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .traffic_control import TrafficLightController, TrafficLight, LightState


class Simulation:
    def __init__(self):
        self.segments = []
        self.vehicles = {}
        self.vehicle_generator = []
        self.traffic_light_controller = None

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

    def set_traffic_light_controller(self, controller):
        self.traffic_light_controller = controller

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

    def run(self, steps):
        for _ in range(steps):
            self.update()

    def update(self):
        # Update traffic light controller
        if self.traffic_light_controller:
            self.traffic_light_controller.update(self.dt)

        # Update vehicles
        for segment_idx, segment in enumerate(self.segments):
            if len(segment.vehicles) == 0:
                continue
                
            # Process first vehicle - may need to stop for traffic light
            first_vehicle_id = segment.vehicles[0]
            first_vehicle = self.vehicles[first_vehicle_id]
            
            # Check if first vehicle should stop for traffic light
            light = None
            if self.traffic_light_controller:
                light = self.traffic_light_controller.get_light_for_segment(segment_idx)
            
            if light and not light.allows_passage():
                stop_distance = light.get_stop_distance()
                # Stop if vehicle hasn't significantly crossed the stop line
                # (allow small margin for vehicles already committed to crossing)
                if first_vehicle.x < stop_distance:
                    first_vehicle.update(self._create_stop_lead(stop_distance), self.dt)
                else:
                    # Vehicle already past stop line, continue normally
                    first_vehicle.update(None, self.dt)
            else:
                first_vehicle.update(None, self.dt)
            
            # Process remaining vehicles - follow the car ahead
            for i in range(1, len(segment.vehicles)):
                vehicle = self.vehicles[segment.vehicles[i]]
                lead = self.vehicles[segment.vehicles[i-1]]
                
                # Check if this vehicle also needs to stop for a red light
                if light and not light.allows_passage():
                    stop_distance = light.get_stop_distance()
                    # If lead vehicle is past the stop line but this one isn't
                    if vehicle.x < stop_distance and lead.x >= stop_distance:
                        vehicle.update(self._create_stop_lead(stop_distance), self.dt)
                    else:
                        vehicle.update(lead, self.dt)
                else:
                    vehicle.update(lead, self.dt)

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
        
        self.t += self.dt
        self.frame_count += 1

    def _create_stop_lead(self, stop_distance):
        """Create a virtual stopped vehicle at the stop line for IDM calculations."""
        class StopLead:
            def __init__(self, x):
                self.x = x
                self.v = 0
                self.l = 0
        return StopLead(stop_distance)

    def get_traffic_lights(self):
        """Return all traffic lights for visualization."""
        if self.traffic_light_controller is None:
            return []
        return self.traffic_light_controller.get_all_lights()
