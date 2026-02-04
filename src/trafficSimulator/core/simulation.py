from .road_network import RoadNetwork
from .vehicle_manager import VehicleManager
from .vehicle_generator import VehicleGenerator
from .vehicle import Vehicle


class Simulation:
    """
    Main simulation orchestrator.
    
    Coordinates the road network, vehicle management, and traffic control.
    Delegates specialized responsibilities to dedicated components.
    """
    
    def __init__(self):
        self._road_network = RoadNetwork()
        self._vehicle_manager = VehicleManager(self._road_network)
        self._traffic_light_controller = None

        self.t = 0.0
        self.frame_count = 0
        self.dt = 1/60

    # Road network delegation (maintains backward compatibility)
    @property
    def segments(self):
        return self._road_network.segments

    def add_segment(self, segment):
        return self._road_network.add_segment(segment)

    def create_segment(self, *args):
        return self._road_network.create_segment(*args)

    def create_quadratic_bezier_curve(self, start, control, end):
        return self._road_network.create_quadratic_bezier_curve(start, control, end)

    def create_cubic_bezier_curve(self, start, control_1, control_2, end):
        return self._road_network.create_cubic_bezier_curve(start, control_1, control_2, end)

    # Vehicle management delegation (maintains backward compatibility)
    @property
    def vehicles(self):
        return self._vehicle_manager.vehicles

    def add_vehicle(self, vehicle):
        self._vehicle_manager.add_vehicle(vehicle)

    def create_vehicle(self, **kwargs):
        return self._vehicle_manager.create_vehicle(**kwargs)

    def add_vehicle_generator(self, generator):
        self._vehicle_manager.add_generator(generator)

    def create_vehicle_generator(self, **kwargs):
        return self._vehicle_manager.create_generator(**kwargs)

    # Traffic control
    def set_traffic_light_controller(self, controller):
        self._traffic_light_controller = controller

    @property
    def traffic_light_controller(self):
        return self._traffic_light_controller

    def get_traffic_lights(self):
        if self._traffic_light_controller is None:
            return []
        return self._traffic_light_controller.get_all_lights()

    # Simulation control
    def run(self, steps):
        for _ in range(steps):
            self.update()

    def update(self):
        if self._traffic_light_controller:
            self._traffic_light_controller.update(self.dt)

        self._vehicle_manager.update_vehicles(self.dt, self._traffic_light_controller)
        self._vehicle_manager.update_generators(self)

        self.t += self.dt
        self.frame_count += 1

    # Direct access to components for advanced usage
    @property
    def road_network(self):
        return self._road_network

    @property
    def vehicle_manager(self):
        return self._vehicle_manager
