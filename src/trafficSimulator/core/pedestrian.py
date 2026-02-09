"""
Pedestrian module for traffic simulation.

This module provides the Pedestrian class which represents individuals
crossing roads at designated crossing points.
"""

import uuid
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class PedestrianState(Enum):
    """
    Enumeration of possible pedestrian states during crossing.
    
    Attributes:
        WAITING: Pedestrian is waiting at the crossing edge for permission to cross.
        CROSSING: Pedestrian is actively crossing the road.
        FINISHED: Pedestrian has completed crossing and reached the other side.
    """
    WAITING = 'waiting'
    CROSSING = 'crossing'
    FINISHED = 'finished'


class Pedestrian:
    """
    Represents a pedestrian crossing the road at a designated crossing point.
    
    Pedestrians move at a constant speed across the crossing width. They start
    in a WAITING state, transition to CROSSING when the crossing permits, and
    reach FINISHED state upon completing the crossing.
    
    Attributes:
        id: Unique identifier for this pedestrian.
        width: Physical width of the pedestrian in meters.
        speed: Walking speed in meters per second.
        x: Progress along crossing path (0.0 = start edge, 1.0 = far edge).
        crossing_id: UUID of the crossing this pedestrian is using.
        state: Current state (WAITING, CROSSING, or FINISHED).
        direction: Direction of travel (1 = forward, -1 = reverse).
        color: RGB tuple for rendering this pedestrian.
    
    Example:
        >>> ped = Pedestrian({'speed': 1.5, 'direction': 1})
        >>> ped.start_crossing()
        >>> ped.update(dt=0.016, crossing_length=4.0)
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize a new Pedestrian instance.
        
        Args:
            config: Optional dictionary of configuration overrides. Supported keys:
                - id: UUID for this pedestrian (auto-generated if not provided)
                - width: Physical width in meters (default: 0.5)
                - speed: Walking speed in m/s (default: 1.4, ~5 km/h)
                - x: Initial position along crossing (default: 0.0)
                - crossing_id: UUID of assigned crossing (default: None)
                - state: Initial PedestrianState (default: WAITING)
                - direction: Travel direction, 1 or -1 (default: 1)
                - color: RGB tuple for rendering (default: (50, 50, 50))
        """
        if config is None:
            config = {}
        self._set_default_config()
        for attr, val in config.items():
            setattr(self, attr, val)
        self._init_properties()

    def _set_default_config(self) -> None:
        """Set default configuration values for all pedestrian attributes."""
        self.id: UUID = uuid.uuid4()
        self.width: float = 0.5
        self.speed: float = 1.4
        self.x: float = 0.0
        self.crossing_id: Optional[UUID] = None
        self.state: PedestrianState = PedestrianState.WAITING
        self.direction: int = 1
        self.color: tuple[int, int, int] = (50, 50, 50)

    def _init_properties(self) -> None:
        """
        Initialize derived properties based on configuration.
        
        Sets the starting position based on crossing direction:
        - direction=1: Start at x=0.0 (near edge)
        - direction=-1: Start at x=1.0 (far edge)
        """
        if self.direction == -1:
            self.x = 1.0

    def update(self, dt: float, crossing_length: float) -> None:
        """
        Update the pedestrian's position based on elapsed time.
        
        Moves the pedestrian along the crossing at their configured speed.
        Automatically transitions to FINISHED state when the pedestrian
        reaches the opposite edge.
        
        Args:
            dt: Time step in seconds since last update.
            crossing_length: Total width of the crossing in meters that
                the pedestrian must traverse.
        
        Note:
            Only updates position when state is CROSSING. Has no effect
            in WAITING or FINISHED states.
        """
        if self.state != PedestrianState.CROSSING:
            return
            
        distance = self.speed * dt
        progress = distance / crossing_length
        self.x += progress * self.direction
        
        if self.direction == 1 and self.x >= 1.0:
            self.x = 1.0
            self.state = PedestrianState.FINISHED
        elif self.direction == -1 and self.x <= 0.0:
            self.x = 0.0
            self.state = PedestrianState.FINISHED

    def start_crossing(self) -> None:
        """
        Transition the pedestrian from WAITING to CROSSING state.
        
        Should be called by the crossing controller when the pedestrian
        is permitted to begin crossing.
        """
        self.state = PedestrianState.CROSSING

    def is_finished(self) -> bool:
        """
        Check if the pedestrian has completed crossing.
        
        Returns:
            True if the pedestrian has reached the opposite edge
            and is in FINISHED state, False otherwise.
        """
        return self.state == PedestrianState.FINISHED

    def is_waiting(self) -> bool:
        """
        Check if the pedestrian is waiting to cross.
        
        Returns:
            True if the pedestrian is in WAITING state at the
            crossing edge, False otherwise.
        """
        return self.state == PedestrianState.WAITING

    def is_crossing(self) -> bool:
        """
        Check if the pedestrian is currently crossing.
        
        Returns:
            True if the pedestrian is actively traversing the
            crossing in CROSSING state, False otherwise.
        """
        return self.state == PedestrianState.CROSSING
