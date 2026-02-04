from .vehicle import Vehicle
from .vehicle_generator import VehicleGenerator


class StopLead:
    """Virtual stopped vehicle at a stop line for IDM calculations."""
    def __init__(self, x):
        self.x = x
        self.v = 0
        self.l = 0


class VehicleManager:
    """Manages vehicles, their movement, and generation."""
    
    def __init__(self, road_network):
        self._road_network = road_network
        self._vehicles = {}
        self._generators = []

    @property
    def vehicles(self):
        return self._vehicles

    def add_vehicle(self, vehicle):
        self._vehicles[vehicle.id] = vehicle
        if len(vehicle.path) > 0:
            first_segment = self._road_network.get_segment(vehicle.path[0])
            first_segment.add_vehicle(vehicle)

    def get_vehicle(self, vehicle_id):
        return self._vehicles.get(vehicle_id)

    def create_vehicle(self, **config):
        vehicle = Vehicle(config)
        self.add_vehicle(vehicle)
        return vehicle

    def add_generator(self, generator):
        self._generators.append(generator)

    def create_generator(self, **config):
        generator = VehicleGenerator(config)
        self.add_generator(generator)
        return generator

    def update_generators(self, simulation):
        for generator in self._generators:
            generator.update(simulation)

    def update_vehicles(self, dt, traffic_light_controller=None):
        """Update all vehicle positions and handle traffic light interactions."""
        for segment_idx, segment in enumerate(self._road_network):
            if len(segment.vehicles) == 0:
                continue

            light = None
            if traffic_light_controller:
                light = traffic_light_controller.get_light_for_segment(segment_idx)

            self._update_vehicles_on_segment(segment, light, dt)

        self._handle_segment_transitions()

    def _update_vehicles_on_segment(self, segment, light, dt):
        """Update vehicles on a single segment."""
        first_vehicle_id = segment.vehicles[0]
        first_vehicle = self._vehicles[first_vehicle_id]

        # Update first vehicle
        if light and not light.allows_passage():
            stop_distance = light.get_stop_distance()
            if first_vehicle.x < stop_distance:
                first_vehicle.update(StopLead(stop_distance), dt)
            else:
                first_vehicle.update(None, dt)
        else:
            first_vehicle.update(None, dt)

        # Update following vehicles
        for i in range(1, len(segment.vehicles)):
            vehicle = self._vehicles[segment.vehicles[i]]
            lead = self._vehicles[segment.vehicles[i-1]]

            if light and not light.allows_passage():
                stop_distance = light.get_stop_distance()
                if vehicle.x < stop_distance and lead.x >= stop_distance:
                    vehicle.update(StopLead(stop_distance), dt)
                else:
                    vehicle.update(lead, dt)
            else:
                vehicle.update(lead, dt)

    def _handle_segment_transitions(self):
        """Handle vehicles transitioning between segments."""
        for segment in self._road_network:
            if len(segment.vehicles) == 0:
                continue
                
            vehicle_id = segment.vehicles[0]
            vehicle = self._vehicles[vehicle_id]
            
            if vehicle.x >= segment.get_length():
                if vehicle.current_road_index + 1 < len(vehicle.path):
                    vehicle.current_road_index += 1
                    next_road_index = vehicle.path[vehicle.current_road_index]
                    next_segment = self._road_network.get_segment(next_road_index)
                    next_segment.vehicles.append(vehicle_id)
                vehicle.x = 0
                segment.vehicles.popleft()

    def __iter__(self):
        return iter(self._vehicles.values())

    def __len__(self):
        return len(self._vehicles)
