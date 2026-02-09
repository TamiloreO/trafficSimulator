"""
Pedestrian module for traffic simulation.

This module provides the Pedestrian class which represents individuals
crossing roads at designated crossing points.
"""

import uuid
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class PedestrianState(Enum):
    """
    Enumeration of possible pedestrian states during crossing.
    
    Attributes:
        WAITING: Pedestrian is waiting at the crossing edge for permission to cross.
        CROSSING: Pedestrian is actively traversing the crossing.
        FINISHED: Pedestrian has completed crossing and reached the other side.
    """
    WAITING = 'waiting'
    CROSSING = 'crossing'
    FINISHED = 'finished'


class Pedestrian:
    """
    Represents a pedestrian crossing the road at a designated crossing point.
    
    Pedestrians move at a constant pace across crossings, starting from one edge
    and proceeding to the opposite edge. They can cross in either direction and
    have configurable walking speeds to simulate different mobility levels.
    
    Attributes:
        id (uuid.UUID): Unique identifier for this pedestrian.
        width (float): Physical width of pedestrian in meters (used for spacing).
        speed (float): Walking speed in meters per second.
        x (float): Progress along crossing path (0.0 = start edge, 1.0 = end edge).
        crossing_id (Optional[uuid.UUID]): ID of the crossing this pedestrian is using.
        state (PedestrianState): Current state in the crossing process.
        direction (int): Direction of travel (1 = forward, -1 = reverse).
        color (Tuple[int, int, int]): RGB color for visual rendering.
    
    Example:
        >>> ped = Pedestrian({'speed': 1.2, 'direction': 1})
        >>> ped.start_crossing()
        >>> ped.update(dt=0.016, crossing_length=4.0)
    """
    
    # Default walking speed based on average pedestrian (approximately 5 km/h)
    DEFAULT_WALKING_SPEED: float = 1.4
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a new Pedestrian instance.
        
        Args:
            config: Optional dictionary of configuration parameters to override
                   defaults. Supported keys include:
                   - 'speed' (float): Walking speed in m/s
                   - 'direction' (int): 1 for forward, -1 for reverse
                   - 'color' (Tuple[int, int, int]): RGB color tuple
                   - 'width' (float): Pedestrian width in meters
        
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
        Set default configuration values for the pedestrian.
        
        Called during initialization before any config overrides are applied.
        Sets safe defaults for all pedestrian attributes.
        """
        self.id: uuid.UUID = uuid.uuid4()
        self.width: float = 0.5  # Pedestrian width in meters
        self.speed: float = self.DEFAULT_WALKING_SPEED
        self.x: float = 0.0  # Position along crossing path (0 = start, 1 = end)
        self.crossing_id: Optional[uuid.UUID] = None
        self.state: PedestrianState = PedestrianState.WAITING
        self.direction: int = 1  # 1 = forward, -1 = backward (crossing from other side)
        self.color: Tuple[int, int, int] = (50, 50, 50)  # Dark gray for pedestrians

    def _init_properties(self) -> None:
        """
        Initialize derived properties after configuration is applied.
        
        Sets the starting position based on crossing direction. Pedestrians
        crossing in reverse (direction=-1) start at position 1.0 instead of 0.0.
        """
        if self.direction == -1:
            self.x = 1.0

    def update(self, dt: float, crossing_length: float) -> None:
        """
        Update pedestrian position based on elapsed time.
        
        Advances the pedestrian's position along the crossing based on their
        walking speed and the time elapsed. Only updates position when the
        pedestrian is in the CROSSING state. Automatically transitions to
        FINISHED state when the pedestrian reaches the opposite edge.
        
        Args:
            dt: Time elapsed since last update in seconds. Should be positive.
            crossing_length: Total length of the crossing in meters. Used to
                           convert walking distance to progress (0-1 range).
        
        Note:
            This method has no effect if the pedestrian is not in CROSSING state.
            The position is clamped to [0.0, 1.0] range upon completion.
        
        Example:
            >>> ped = Pedestrian({'speed': 1.4})
            >>> ped.start_crossing()
            >>> ped.update(dt=1.0, crossing_length=7.0)  # Walk for 1 second
            >>> print(f"Progress: {ped.x:.2f}")  # ~0.2 (1.4m / 7.0m)
        """
        if self.state != PedestrianState.CROSSING:
            return
        
        if crossing_length <= 0:
            return
        
        distance = self.speed * dt
        progress = distance / crossing_length
        self.x += progress * self.direction
        
        # Check if finished crossing
        if self.direction == 1 and self.x >= 1.0:
            self.x = 1.0
            self.state = PedestrianState.FINISHED
        elif self.direction == -1 and self.x <= 0.0:
            self.x = 0.0
            self.state = PedestrianState.FINISHED

    def start_crossing(self) -> None:
        """
        Begin crossing the road.
        
        Transitions the pedestrian from WAITING to CROSSING state, allowing
        them to move during subsequent update() calls.
        
        Note:
            This method should only be called when the crossing signals that
            pedestrians are allowed to cross. Calling it multiple times has
            no additional effect.
        """
        self.state = PedestrianState.CROSSING

    def is_finished(self) -> bool:
        """
        Check if the pedestrian has completed crossing.
        
        Returns:
            True if the pedestrian has reached the opposite edge and is in
            FINISHED state, False otherwise.
        """
        return self.state == PedestrianState.FINISHED

    def is_waiting(self) -> bool:
        """
        Check if the pedestrian is waiting to cross.
        
        Returns:
            True if the pedestrian is in WAITING state at the crossing edge,
            False otherwise.
        """
        return self.state == PedestrianState.WAITING

    def is_crossing(self) -> bool:
        """
        Check if the pedestrian is currently crossing the road.
        
        Returns:
            True if the pedestrian is actively traversing the crossing in
            CROSSING state, False otherwise.
        """
        return self.state == PedestrianState.CROSSING

    def __repr__(self) -> str:
        """
        Return a string representation of the pedestrian for debugging.
        
        Returns:
            String containing the pedestrian's ID, state, position and speed.
        """
        return (
            f"Pedestrian(id={str(self.id)[:8]}..., "
            f"state={self.state.value}, x={self.x:.2f}, speed={self.speed})"
        )
