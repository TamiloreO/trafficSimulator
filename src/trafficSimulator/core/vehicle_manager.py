from typing import Dict, List, Optional, TYPE_CHECKING
from .vehicle import Vehicle
from .vehicle_generator import VehicleGenerator

if TYPE_CHECKING:
    from .road_network import RoadNetwork


class VehicleManager:
    """Manages vehicles and vehicle generators."""
    
    def __init__(self, road_network: 'RoadNetwork'):
        self._road_network = road_network
        self._vehicles: Dict = {}
        self._generators: List[VehicleGenerator] = []
    
    @property
    def vehicles(self) -> Dict:
        return self._vehicles
    
    @property
    def generators(self) -> List[VehicleGenerator]:
        return self._generators
    
    def add_vehicle(self, vehicle: Vehicle) -> None:
        """Add a vehicle to the manager and place it on its starting segment."""
        self._vehicles[vehicle.id] = vehicle
        if len(vehicle.path) > 0:
            segment = self._road_network.get_segment(vehicle.path[0])
            if segment:
                segment.add_vehicle(vehicle)
    
    def get_vehicle(self, vehicle_id) -> Optional[Vehicle]:
        """Get a vehicle by its ID."""
        return self._vehicles.get(vehicle_id)
    
    def remove_vehicle(self, vehicle_id) -> Optional[Vehicle]:
        """Remove and return a vehicle by its ID."""
        return self._vehicles.pop(vehicle_id, None)
    
    def create_vehicle(self, **kwargs) -> Vehicle:
        """Create a new vehicle with given configuration and add it."""
        vehicle = Vehicle(kwargs)
        self.add_vehicle(vehicle)
        return vehicle
    
    def add_generator(self, generator: VehicleGenerator) -> None:
        """Add a vehicle generator."""
        self._generators.append(generator)
    
    def create_generator(self, **kwargs) -> VehicleGenerator:
        """Create and add a new vehicle generator."""
        generator = VehicleGenerator(kwargs)
        self.add_generator(generator)
        return generator
    
    def update_generators(self, t: float) -> None:
        """Update all generators to potentially spawn new vehicles."""
        for generator in self._generators:
            self._update_generator(generator, t)
    
    def _update_generator(self, generator: VehicleGenerator, t: float) -> None:
        """Update a single generator."""
        if t - generator.last_added_time >= 60 / generator.vehicle_rate:
            upcoming = generator.upcoming_vehicle
            segment = self._road_network.get_segment(upcoming.path[0])
            
            if segment is None:
                return
                
            # Check if there's space for the new vehicle
            if len(segment.vehicles) == 0:
                has_space = True
            else:
                last_vehicle_id = segment.vehicles[-1]
                last_vehicle = self._vehicles.get(last_vehicle_id)
                has_space = (
                    last_vehicle is not None and 
                    last_vehicle.x > upcoming.s0 + upcoming.l
                )
            
            if has_space:
                self.add_vehicle(upcoming)
                generator.last_added_time = t
            
            generator.upcoming_vehicle = generator.generate_vehicle()
    
    def get_vehicle_count(self) -> int:
        """Return the number of active vehicles."""
        return len(self._vehicles)
