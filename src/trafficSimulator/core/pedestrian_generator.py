import uuid
import random
from typing import Dict, Any, Optional, List, Tuple

from .pedestrian import Pedestrian


class PedestrianGenerator:
    """
    Generates pedestrians at specified crossings at configurable rates.
    Supports multiple crossings with weighted random selection.
    """

    DEFAULT_RATE = 6  # pedestrians per minute
    MIN_RATE = 1
    MAX_RATE = 60

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}

        self._set_default_config()
        self._apply_config(config)
        self._validate_config()

    def _set_default_config(self) -> None:
        self.id = uuid.uuid4()
        
        # Generation rate (pedestrians per minute)
        self.pedestrian_rate = self.DEFAULT_RATE
        
        # Crossing configurations: list of (weight, crossing_index, pedestrian_config)
        # Weight determines relative probability of spawning at this crossing
        self.crossings: List[Tuple[int, int, Dict[str, Any]]] = []
        
        # Last generation time
        self.last_added_time = 0.0
        
        # Upcoming pedestrian
        self.upcoming_pedestrian: Optional[Pedestrian] = None
        self.upcoming_crossing_index: Optional[int] = None
        
        # Walk speed variation (for realistic variation)
        self.min_walk_speed = 1.0
        self.max_walk_speed = 1.8
        
        # Color variations for visual distinction
        self.colors = [
            (255, 100, 100),  # Red
            (100, 100, 255),  # Blue
            (100, 255, 100),  # Green
            (255, 200, 100),  # Orange
            (200, 100, 255),  # Purple
            (255, 255, 100),  # Yellow
            (100, 255, 255),  # Cyan
        ]

    def _apply_config(self, config: Dict[str, Any]) -> None:
        for attr, val in config.items():
            if hasattr(self, attr):
                setattr(self, attr, val)

    def _validate_config(self) -> None:
        if self.pedestrian_rate < self.MIN_RATE:
            self.pedestrian_rate = self.MIN_RATE
        elif self.pedestrian_rate > self.MAX_RATE:
            self.pedestrian_rate = self.MAX_RATE

        if self.min_walk_speed > self.max_walk_speed:
            self.min_walk_speed, self.max_walk_speed = self.max_walk_speed, self.min_walk_speed

        # Ensure there's at least a default crossing
        if not self.crossings:
            self.crossings = [(1, 0, {})]

    def _generate_pedestrian(self) -> Tuple[Pedestrian, int]:
        """
        Generate a random pedestrian for a random crossing.
        
        Returns:
            Tuple of (Pedestrian, crossing_index)
        """
        # Select crossing based on weights
        total_weight = sum(c[0] for c in self.crossings)
        if total_weight <= 0:
            total_weight = len(self.crossings)
            
        r = random.randint(1, total_weight)
        
        selected_crossing_index = 0
        selected_config = {}
        
        for weight, crossing_idx, ped_config in self.crossings:
            r -= max(1, weight)
            if r <= 0:
                selected_crossing_index = crossing_idx
                selected_config = ped_config.copy() if ped_config else {}
                break
        
        # Add random variations
        if 'walk_speed' not in selected_config:
            selected_config['walk_speed'] = random.uniform(
                self.min_walk_speed, self.max_walk_speed
            )
        
        if 'color' not in selected_config:
            selected_config['color'] = random.choice(self.colors)
        
        # Random direction (some pedestrians cross in reverse direction)
        if 'direction' not in selected_config:
            selected_config['direction'] = random.choice([1, -1])
            if selected_config['direction'] == -1:
                selected_config['progress'] = 1.0  # Start from other side
        
        pedestrian = Pedestrian(selected_config)
        return pedestrian, selected_crossing_index

    def update(self, simulation) -> None:
        """
        Update generator and add pedestrians to simulation as needed.
        
        Args:
            simulation: The simulation instance
        """
        # Check if we have crossings configured
        if not self.crossings:
            return

        # Generate upcoming pedestrian if needed
        if self.upcoming_pedestrian is None:
            try:
                self.upcoming_pedestrian, self.upcoming_crossing_index = self._generate_pedestrian()
            except Exception:
                return

        # Check if it's time to add a new pedestrian
        time_between_pedestrians = 60.0 / self.pedestrian_rate
        
        if simulation.t - self.last_added_time >= time_between_pedestrians:
            # Validate crossing index
            if self.upcoming_crossing_index is None:
                self._reset_upcoming()
                return
                
            if not hasattr(simulation, 'crossings') or not simulation.crossings:
                self._reset_upcoming()
                return
                
            if self.upcoming_crossing_index >= len(simulation.crossings):
                self._reset_upcoming()
                return

            crossing = simulation.crossings[self.upcoming_crossing_index]
            
            # Check if crossing can accept more pedestrians
            if len(crossing.pedestrians) < crossing.max_pedestrians:
                # Add to simulation
                if simulation.add_pedestrian(self.upcoming_pedestrian, self.upcoming_crossing_index):
                    self.last_added_time = simulation.t
                    
            # Generate next pedestrian
            self._reset_upcoming()

    def _reset_upcoming(self) -> None:
        """Reset the upcoming pedestrian state."""
        try:
            self.upcoming_pedestrian, self.upcoming_crossing_index = self._generate_pedestrian()
        except Exception:
            self.upcoming_pedestrian = None
            self.upcoming_crossing_index = None

    def add_crossing(self, crossing_index: int, weight: int = 1, 
                     pedestrian_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a crossing to this generator.
        
        Args:
            crossing_index: Index of crossing in simulation
            weight: Relative weight for random selection
            pedestrian_config: Optional config for pedestrians at this crossing
        """
        if pedestrian_config is None:
            pedestrian_config = {}
        
        weight = max(1, weight)
        self.crossings.append((weight, crossing_index, pedestrian_config))
