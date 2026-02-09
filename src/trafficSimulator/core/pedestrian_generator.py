"""
Pedestrian generator module for traffic simulation.

This module provides the PedestrianGenerator class which spawns pedestrians
at designated crossing points at configurable rates.
"""

from typing import Any, Optional, TYPE_CHECKING
from numpy.random import randint, random

from .pedestrian import Pedestrian

if TYPE_CHECKING:
    from .simulation import Simulation


class PedestrianGenerator:
    """
    Generates pedestrians at crossing points during simulation.
    
    Spawns pedestrians at a configurable rate, distributing them among
    specified crossings. Supports weighted random selection of different
    pedestrian types (e.g., varying walking speeds).
    
    Attributes:
        pedestrian_rate: Number of pedestrians to generate per minute.
        crossing_ids: List of crossing indices where pedestrians spawn.
        pedestrians: List of (weight, config) tuples for pedestrian types.
        last_added_time: Simulation time when last pedestrian was added.
    
    Example:
        >>> gen = PedestrianGenerator({
        ...     'pedestrian_rate': 20,
        ...     'crossing_ids': [0, 1],
        ...     'pedestrians': [
        ...         (3, {'speed': 1.4}),  # Normal walker (75%)
        ...         (1, {'speed': 0.8}),  # Slow walker (25%)
        ...     ]
        ... })
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize a new PedestrianGenerator.
        
        Args:
            config: Optional dictionary of configuration overrides. Supported keys:
                - pedestrian_rate: Pedestrians per minute (default: 20)
                - crossing_ids: List of crossing indices to spawn at (default: [])
                - pedestrians: List of (weight, config) tuples defining
                  pedestrian types and their relative frequencies (default: [(1, {})])
        """
        if config is None:
            config = {}
        self._set_default_config()
        for attr, val in config.items():
            setattr(self, attr, val)
        self._init_properties()

    def _set_default_config(self) -> None:
        """Set default configuration values."""
        self.pedestrian_rate: float = 20.0
        self.crossing_ids: list[int] = []
        self.pedestrians: list[tuple[int, dict[str, Any]]] = [(1, {})]
        self.last_added_time: float = 0.0

    def _init_properties(self) -> None:
        """Initialize derived properties (placeholder for future use)."""
        pass

    def generate_pedestrian(self) -> Pedestrian:
        """
        Create a new pedestrian with randomly selected configuration.
        
        Selects a pedestrian configuration from the weighted list and
        creates a new Pedestrian instance. If direction is not specified
        in the config, randomly assigns direction (50% each way).
        
        Returns:
            A new Pedestrian instance configured according to the
            randomly selected configuration.
        
        Note:
            Uses weighted random selection based on the first element
            of each (weight, config) tuple in self.pedestrians.
        """
        total = sum(pair[0] for pair in self.pedestrians)
        r = randint(1, total + 1)
        
        selected_config: dict[str, Any] = {}
        for weight, config in self.pedestrians:
            r -= weight
            if r <= 0:
                selected_config = config.copy()
                break
        
        if 'direction' not in selected_config:
            selected_config['direction'] = 1 if random() > 0.5 else -1
            
        return Pedestrian(selected_config)

    def update(self, simulation: 'Simulation') -> None:
        """
        Attempt to generate and add a pedestrian to the simulation.
        
        Called each simulation frame. Generates a new pedestrian if
        sufficient time has elapsed since the last generation, based
        on the configured pedestrian_rate.
        
        Args:
            simulation: The Simulation instance to add pedestrians to.
        
        Note:
            - Does nothing if crossing_ids is empty or simulation has no crossings.
            - Randomly selects which crossing the pedestrian will use.
            - Generation rate is pedestrians per minute (e.g., rate=20 means
              one pedestrian every 3 seconds on average).
        """
        if not self.crossing_ids or not simulation.crossings:
            return
            
        time_between_pedestrians = 60.0 / self.pedestrian_rate
        
        if simulation.t - self.last_added_time >= time_between_pedestrians:
            crossing_idx = self.crossing_ids[randint(0, len(self.crossing_ids))]
            
            if crossing_idx < len(simulation.crossings):
                crossing = simulation.crossings[crossing_idx]
                pedestrian = self.generate_pedestrian()
                crossing.add_pedestrian(pedestrian)
                simulation.add_pedestrian(pedestrian)
                self.last_added_time = simulation.t
