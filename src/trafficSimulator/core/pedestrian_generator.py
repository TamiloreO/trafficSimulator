"""
Pedestrian generator module for traffic simulation.

This module provides the PedestrianGenerator class which spawns pedestrians
at designated crossing points during simulation.
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from numpy.random import randint, random

from .pedestrian import Pedestrian

if TYPE_CHECKING:
    from .simulation import Simulation


class PedestrianGenerator:
    """
    Generates pedestrians at designated crossings during simulation.
    
    Spawns pedestrians at a configurable rate, distributing them among
    specified crossings. Supports weighted pedestrian types to simulate
    different walking speeds (e.g., elderly, children, cyclists).
    
    Attributes:
        pedestrian_rate (float): Number of pedestrians to generate per minute.
        crossing_ids (List[int]): Indices of crossings where pedestrians spawn.
        pedestrians (List[Tuple[int, Dict]]): Weighted list of pedestrian configs.
            Each tuple contains (weight, config_dict) where higher weights
            mean more frequent spawning of that pedestrian type.
        last_added_time (float): Simulation time when last pedestrian was added.
    
    Example:
        >>> gen = PedestrianGenerator({
        ...     'pedestrian_rate': 20,
        ...     'crossing_ids': [0, 1],
        ...     'pedestrians': [
        ...         (3, {'speed': 1.4}),  # Normal walker (weight 3)
        ...         (1, {'speed': 0.8}),  # Slow walker (weight 1)
        ...     ]
        ... })
        >>> gen.update(simulation)
    """
    
    # Default pedestrian generation rate (per minute)
    DEFAULT_RATE: float = 20.0
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a new pedestrian generator.
        
        Args:
            config: Optional dictionary of configuration parameters. Supported keys:
                   - 'pedestrian_rate' (float): Pedestrians per minute
                   - 'crossing_ids' (List[int]): Target crossing indices
                   - 'pedestrians' (List[Tuple[int, Dict]]): Weighted pedestrian types
        
        Raises:
            TypeError: If config is provided but is not a dictionary.
        """
        if config is None:
            config = {}
        
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dictionary, got {type(config).__name__}")
        
        self._set_default_config()
        
        for attr, val in config.items():
            setattr(self, attr, val)
        
        self._init_properties()

    def _set_default_config(self) -> None:
        """
        Set default configuration values for the generator.
        
        Initializes all generator attributes with safe default values.
        Called during __init__ before config overrides are applied.
        """
        self.pedestrian_rate: float = self.DEFAULT_RATE
        self.crossing_ids: List[int] = []
        self.pedestrians: List[Tuple[int, Dict[str, Any]]] = [
            (1, {}),  # Default: single pedestrian type with default config
        ]
        self.last_added_time: float = 0.0

    def _init_properties(self) -> None:
        """
        Initialize derived properties after configuration.
        
        Currently a no-op but available for subclass extension.
        """
        pass

    def generate_pedestrian(self) -> Pedestrian:
        """
        Generate a random pedestrian based on weighted configuration.
        
        Selects a pedestrian type from the configured list using weighted
        random selection, then creates a Pedestrian instance with that
        configuration. Randomly assigns crossing direction if not specified.
        
        Returns:
            A new Pedestrian instance with randomly selected configuration.
        
        Note:
            If no pedestrian types are configured, returns a default Pedestrian.
            Direction is randomly assigned (50% each direction) if not
            explicitly set in the pedestrian config.
        
        Example:
            >>> gen = PedestrianGenerator({
            ...     'pedestrians': [(2, {'speed': 1.4}), (1, {'speed': 0.8})]
            ... })
            >>> ped = gen.generate_pedestrian()
            >>> # 2/3 chance of speed 1.4, 1/3 chance of speed 0.8
        """
        if not self.pedestrians:
            return Pedestrian()
        
        total = sum(pair[0] for pair in self.pedestrians)
        if total <= 0:
            return Pedestrian()
        
        r = randint(1, total + 1)
        
        for (weight, config) in self.pedestrians:
            r -= weight
            if r <= 0:
                ped_config = config.copy() if config else {}
                # Randomly choose direction (crossing from either side)
                if 'direction' not in ped_config:
                    ped_config['direction'] = 1 if random() > 0.5 else -1
                return Pedestrian(ped_config)
        
        # Fallback (shouldn't reach here, but defensive)
        return Pedestrian()

    def update(self, simulation: 'Simulation') -> None:
        """
        Update the generator and potentially spawn a new pedestrian.
        
        Checks if enough time has elapsed since the last pedestrian was
        added (based on pedestrian_rate), and if so, spawns a new pedestrian
        at a randomly selected crossing from the configured list.
        
        Args:
            simulation: The Simulation instance to add pedestrians to.
        
        Note:
            Does nothing if:
            - No crossing_ids are configured
            - No crossings exist in the simulation
            - Not enough time has elapsed since last spawn
            
        Side Effects:
            - May add a pedestrian to a crossing's waiting queue
            - May add a pedestrian to simulation's pedestrian dictionary
            - Updates last_added_time on successful spawn
        """
        if simulation is None:
            return
        
        if not self.crossing_ids:
            return
        
        if not simulation.crossings:
            return
        
        if self.pedestrian_rate <= 0:
            return
        
        time_between_pedestrians = 60.0 / self.pedestrian_rate
        
        if simulation.t - self.last_added_time >= time_between_pedestrians:
            # Pick a random crossing from our list
            crossing_idx = self.crossing_ids[randint(0, len(self.crossing_ids))]
            
            if 0 <= crossing_idx < len(simulation.crossings):
                crossing = simulation.crossings[crossing_idx]
                pedestrian = self.generate_pedestrian()
                crossing.add_pedestrian(pedestrian)
                simulation.add_pedestrian(pedestrian)
                self.last_added_time = simulation.t

    def __repr__(self) -> str:
        """
        Return a string representation of the generator for debugging.
        
        Returns:
            String containing the generator's rate and target crossings.
        """
        return (
            f"PedestrianGenerator("
            f"rate={self.pedestrian_rate}/min, "
            f"crossings={self.crossing_ids})"
        )
