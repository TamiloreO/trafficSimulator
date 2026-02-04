from typing import List, Optional
from .vehicle_generator import VehicleGenerator
from .vehicle import Vehicle
from .road_network import RoadNetwork
from .vehicle_manager import VehicleManager
from .traffic_control import TrafficLightController


class StopLead:
    """Virtual stopped vehicle used for IDM calculations at stop lines."""
    __slots__ = ('x', 'v', 'l')
    
    def __init__(self, x: float):
        self.x = x
        self.v = 0
        self.l = 0


class Simulation:
    """
    Main simulation orchestrator.
    
    Coordinates the road network, vehicles, and traffic control systems.
    Delegates specific responsibilities to specialized components.
    """
    
    def __init__(self):
        self._road_network = RoadNetwork()
        self._vehicle_manager = VehicleManager(self._road_network)
        self._traffic_light_controller: Optional[TrafficLightController] = None
        
        self.t = 0.0
        self.frame_count = 0
        self.dt = 1/60

    # --- Properties for backward compatibility ---
    
    @property
    def segments(self):
        """Access segments through road network (backward compatible)."""
        return self._road_network.segments
    
    @property
    def vehicles(self):
        """Access vehicles through vehicle manager (backward compatible)."""
        return self._vehicle_manager.vehicles
    
    @property
    def vehicle_generator(self):
        """Access generators through vehicle manager (backward compatible)."""
        return self._vehicle_manager.generators
    
    @property
    def road_network(self) -> RoadNetwork:
        return self._road_network
    
    @property
    def vehicle_manager(self) -> VehicleManager:
        return self._vehicle_manager
    
    @property
    def traffic_light_controller(self) -> Optional[TrafficLightController]:
        return self._traffic_light_controller

    # --- Vehicle methods (delegate to VehicleManager) ---
    
    def add_vehicle(self, vehicle: Vehicle) -> None:
        self._vehicle_manager.add_vehicle(vehicle)
    
    def create_vehicle(self, **kwargs) -> Vehicle:
        return self._vehicle_manager.create_vehicle(**kwargs)
    
    def add_vehicle_generator(self, generator: VehicleGenerator) -> None:
        self._vehicle_manager.add_generator(generator)
    
    def create_vehicle_generator(self, **kwargs) -> VehicleGenerator:
        return self._vehicle_manager.create_generator(**kwargs)

    # --- Road network methods (delegate to RoadNetwork) ---
    
    def add_segment(self, segment) -> int:
        return self._road_network.add_segment(segment)
    
    def create_segment(self, *args) -> int:
        return self._road_network.create_segment(*args)
    
    def create_quadratic_bezier_curve(self, start, control, end) -> int:
        return self._road_network.create_quadratic_bezier_curve(start, control, end)
    
    def create_cubic_bezier_curve(self, start, control_1, control_2, end) -> int:
        return self._road_network.create_cubic_bezier_curve(start, control_1, control_2, end)

    # --- Traffic control methods ---
    
    def set_traffic_light_controller(self, controller: TrafficLightController) -> None:
        self._traffic_light_controller = controller
    
    def get_traffic_lights(self) -> List:
        """Return all traffic lights for visualization."""
        if self._traffic_light_controller is None:
            return []
        return self._traffic_light_controller.get_all_lights()

    # --- Simulation control ---
    
    def run(self, steps: int) -> None:
        """Run the simulation for a number of steps."""
        for _ in range(steps):
            self.update()
    
    def update(self) -> None:
        """Advance the simulation by one time step."""
        self._update_traffic_lights()
        self._update_vehicles()
        self._handle_segment_transitions()
        self._vehicle_manager.update_generators(self.t)
        
        self.t += self.dt
        self.frame_count += 1
    
    def _update_traffic_lights(self) -> None:
        """Update traffic light controller."""
        if self._traffic_light_controller:
            self._traffic_light_controller.update(self.dt)
    
    def _update_vehicles(self) -> None:
        """Update all vehicles on all segments."""
        for segment_idx, segment in enumerate(self._road_network):
            if len(segment.vehicles) == 0:
                continue
            
            light = self._get_light_for_segment(segment_idx)
            self._update_vehicles_on_segment(segment, light)
    
    def _get_light_for_segment(self, segment_idx: int):
        """Get the traffic light for a segment, if any."""
        if self._traffic_light_controller:
            return self._traffic_light_controller.get_light_for_segment(segment_idx)
        return None
    
    def _update_vehicles_on_segment(self, segment, light) -> None:
        """Update all vehicles on a single segment."""
        vehicles = self._vehicle_manager.vehicles
        
        # Process first vehicle
        first_vehicle_id = segment.vehicles[0]
        first_vehicle = vehicles[first_vehicle_id]
        
        lead = self._get_lead_for_first_vehicle(first_vehicle, light)
        first_vehicle.update(lead, self.dt)
        
        # Process remaining vehicles
        for i in range(1, len(segment.vehicles)):
            vehicle = vehicles[segment.vehicles[i]]
            lead_vehicle = vehicles[segment.vehicles[i-1]]
            
            lead = self._get_lead_for_following_vehicle(vehicle, lead_vehicle, light)
            vehicle.update(lead, self.dt)
    
    def _get_lead_for_first_vehicle(self, vehicle, light):
        """Determine what the first vehicle should follow (stop line or nothing)."""
        if light and not light.allows_passage():
            stop_distance = light.get_stop_distance()
            if vehicle.x < stop_distance:
                return StopLead(stop_distance)
        return None
    
    def _get_lead_for_following_vehicle(self, vehicle, lead_vehicle, light):
        """Determine what a following vehicle should follow."""
        if light and not light.allows_passage():
            stop_distance = light.get_stop_distance()
            # If lead is past stop line but this vehicle isn't, stop at line
            if vehicle.x < stop_distance and lead_vehicle.x >= stop_distance:
                return StopLead(stop_distance)
        return lead_vehicle
    
    def _handle_segment_transitions(self) -> None:
        """Handle vehicles transitioning between segments."""
        for segment in self._road_network:
            if len(segment.vehicles) == 0:
                continue
            
            vehicle_id = segment.vehicles[0]
            vehicle = self._vehicle_manager.vehicles[vehicle_id]
            
            if vehicle.x >= segment.get_length():
                self._transition_vehicle(vehicle, segment)
    
    def _transition_vehicle(self, vehicle, current_segment) -> None:
        """Move a vehicle to its next segment or remove it from the network."""
        if vehicle.current_road_index + 1 < len(vehicle.path):
            vehicle.current_road_index += 1
            next_road_index = vehicle.path[vehicle.current_road_index]
            next_segment = self._road_network.get_segment(next_road_index)
            if next_segment:
                next_segment.vehicles.append(vehicle.id)
        
        vehicle.x = 0
        current_segment.vehicles.popleft()
