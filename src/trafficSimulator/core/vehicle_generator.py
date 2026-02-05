from typing import Dict, List, Any, Optional, Tuple
from .vehicle import Vehicle
from numpy.random import randint


class VehicleGenerator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.set_default_config()

        for attr, val in config.items():
            setattr(self, attr, val)

        self.init_properties()

    def set_default_config(self):
        self.vehicle_rate = 10
        self.vehicles: List[Tuple[int, Dict[str, Any]]] = [
            (1, {})
        ]
        self.last_added_time = 0
        
        # Road-based generation settings
        self.road_id: Optional[str] = None
        self.lane_distribution: Optional[List[Tuple[int, int]]] = None  # [(weight, lane_index), ...]

    def init_properties(self):
        self.upcoming_vehicle = self.generate_vehicle()

    def generate_vehicle(self) -> Vehicle:
        """Returns a random vehicle from self.vehicles with random proportions"""
        total = sum(pair[0] for pair in self.vehicles)
        r = randint(1, total+1)
        for (weight, config) in self.vehicles:
            r -= weight
            if r <= 0:
                return Vehicle(config)
        return Vehicle({})

    def _select_lane(self) -> Optional[int]:
        """Select a lane based on lane distribution weights."""
        if not self.lane_distribution:
            return None
        
        total = sum(pair[0] for pair in self.lane_distribution)
        r = randint(1, total + 1)
        for (weight, lane_index) in self.lane_distribution:
            r -= weight
            if r <= 0:
                return lane_index
        return self.lane_distribution[0][1] if self.lane_distribution else None

    def update(self, simulation):
        """Add vehicles to the simulation."""
        if simulation.t - self.last_added_time >= 60 / self.vehicle_rate:
            segment_index = self.upcoming_vehicle.path[0] if self.upcoming_vehicle.path else None
            
            # Handle road-based generation
            if self.road_id and self.road_id in simulation.roads:
                road = simulation.roads[self.road_id]
                
                # Select lane
                lane_index = self._select_lane()
                if lane_index is None:
                    lane_index = randint(0, road.lane_count)
                
                # Find the segment index for this lane
                for seg_idx, rid in simulation.segment_to_road.items():
                    if rid == self.road_id:
                        if simulation.segment_to_lane.get(seg_idx, 0) == lane_index:
                            segment_index = seg_idx
                            break
                
                if segment_index is not None:
                    # Update vehicle's path to use this segment
                    if self.upcoming_vehicle.path:
                        self.upcoming_vehicle.path[0] = segment_index
                    else:
                        self.upcoming_vehicle.path = [segment_index]
                    
                    # Set lane info
                    self.upcoming_vehicle.current_road_id = self.road_id
                    self.upcoming_vehicle.current_lane_index = lane_index
            
            if segment_index is None:
                self.upcoming_vehicle = self.generate_vehicle()
                return
            
            segment = simulation.segments[segment_index]
            
            # Check if there's space for the vehicle
            if len(segment.vehicles) == 0 or \
               simulation.vehicles[segment.vehicles[-1]].x > self.upcoming_vehicle.s0 + self.upcoming_vehicle.l:
                simulation.add_vehicle(self.upcoming_vehicle)
                self.last_added_time = simulation.t
            
            self.upcoming_vehicle = self.generate_vehicle()
