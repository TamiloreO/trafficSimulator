from .vehicle_generator import VehicleGenerator
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment
from .vehicle import Vehicle
from .traffic_control import TrafficLightController, TrafficLight, Phase, PhaseSequence, LightState


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

    def create_traffic_light(self, segment_index, position=None, stop_distance=None, initial_state=LightState.RED):
        """Create a traffic light at the end of a segment."""
        segment = self.segments[segment_index]
        if position is None:
            position = segment.points[-1]
        if stop_distance is None:
            stop_distance = segment.get_length()
        
        light = TrafficLight(
            position=position,
            segment_index=segment_index,
            stop_distance=stop_distance,
            initial_state=initial_state
        )
        
        if self.traffic_light_controller is None:
            self.traffic_light_controller = TrafficLightController()
        
        self.traffic_light_controller.add_traffic_light(light)
        return light

    def create_signal_phases(self, phase_configs):
        """Create signal phases for the traffic light controller.
        
        phase_configs: list of dicts with keys:
            - duration: float (seconds)
            - green_lights: list of light indices that should be green
            - yellow_duration: float (optional, default 3.0)
        """
        if self.traffic_light_controller is None:
            self.traffic_light_controller = TrafficLightController()
        
        phases = []
        for config in phase_configs:
            phase = Phase(
                duration=config['duration'],
                green_lights=config['green_lights'],
                yellow_duration=config.get('yellow_duration', 3.0)
            )
            phases.append(phase)
        
        sequence = PhaseSequence(phases)
        self.traffic_light_controller.set_phase_sequence(sequence)

    def get_traffic_lights(self):
        """Return all traffic lights in the simulation."""
        if self.traffic_light_controller is None:
            return []
        return self.traffic_light_controller.get_all_lights()

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

    def _get_traffic_light_for_vehicle(self, vehicle):
        """Get the traffic light affecting the vehicle's current segment."""
        if self.traffic_light_controller is None:
            return None
        if vehicle.current_road_index >= len(vehicle.path):
            return None
        segment_index = vehicle.path[vehicle.current_road_index]
        return self.traffic_light_controller.get_light_for_segment(segment_index)

    def _should_stop_for_light(self, vehicle, segment):
        """Check if vehicle should stop for a red/yellow light."""
        light = self._get_traffic_light_for_vehicle(vehicle)
        if light is None:
            return False
        
        if light.allows_passage():
            return False
        
        # Check if vehicle is approaching the stop line
        stop_distance = light.get_stop_distance()
        # Vehicle should stop with its front at stop_distance - s0 (safe gap)
        effective_stop = stop_distance - vehicle.s0
        
        if vehicle.x < effective_stop:
            # Vehicle should start slowing down when approaching
            distance_to_stop = effective_stop - vehicle.x
            # Calculate stopping distance at current velocity using comfortable deceleration
            if vehicle.v > 0:
                # Use comfortable deceleration (less than max) for smooth stopping
                comfortable_decel = vehicle.b_max * 0.6
                stopping_distance = (vehicle.v ** 2) / (2 * comfortable_decel)
                if distance_to_stop <= stopping_distance + 10:  # 10m lookahead buffer
                    return True
        return False

    def update(self):
        # Update traffic lights
        if self.traffic_light_controller is not None:
            self.traffic_light_controller.update(self.dt)

        # Update vehicles
        for segment in self.segments:
            if len(segment.vehicles) != 0:
                vehicle = self.vehicles[segment.vehicles[0]]
                # Check if lead vehicle should stop for traffic light
                if self._should_stop_for_light(vehicle, segment):
                    light = self._get_traffic_light_for_vehicle(vehicle)
                    stop_distance = light.get_stop_distance() - vehicle.s0
                    vehicle.update_with_stop(stop_distance, self.dt)
                else:
                    vehicle.stopped = False
                    vehicle.update(None, self.dt)
                    
            for i in range(1, len(segment.vehicles)):
                vehicle = self.vehicles[segment.vehicles[i]]
                lead = self.vehicles[segment.vehicles[i-1]]
                # Following vehicles check both lead vehicle and traffic light
                if self._should_stop_for_light(vehicle, segment):
                    light = self._get_traffic_light_for_vehicle(vehicle)
                    stop_distance = light.get_stop_distance() - vehicle.s0
                    vehicle.update_with_stop(stop_distance, self.dt, lead)
                else:
                    vehicle.stopped = False
                    vehicle.update(lead, self.dt)

        # Check roads for out of bounds vehicle
        for segment in self.segments:
            # If road has no vehicles, continue
            if len(segment.vehicles) == 0: continue
            # If not
            vehicle_id = segment.vehicles[0]
            vehicle = self.vehicles[vehicle_id]
            # If first vehicle is out of road bounds
            if vehicle.x >= segment.get_length():
                # If vehicle has a next road
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    # Update current road to next road
                    vehicle.current_road_index += 1
                    # Add it to the next road
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    self.segments[next_road_index].vehicles.append(vehicle_id)
                # Reset vehicle properties
                vehicle.x = 0
                # In all cases, remove it from its road
                segment.vehicles.popleft() 

        # Update vehicle generators
        for gen in self.vehicle_generator:
            gen.update(self)
        # Increment time
        self.t += self.dt
        self.frame_count += 1
