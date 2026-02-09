import uuid
from enum import Enum
from typing import Optional, Tuple, Dict, Any


class PedestrianState(Enum):
    WAITING = "waiting"
    CROSSING = "crossing"
    FINISHED = "finished"


class Pedestrian:
    """
    Represents a pedestrian that can cross roads at designated crossings.
    Pedestrians move at a constant pace and have various states during crossing.
    """

    DEFAULT_WALK_SPEED = 1.4  # meters per second (average walking speed)
    MIN_WALK_SPEED = 0.8
    MAX_WALK_SPEED = 2.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}

        self._set_default_config()
        self._apply_config(config)
        self._validate_config()

    def _set_default_config(self) -> None:
        self.id = uuid.uuid4()
        self.walk_speed = self.DEFAULT_WALK_SPEED
        self.width = 0.5  # meters - pedestrian width for rendering
        self.height = 0.5  # meters - pedestrian height for rendering
        
        self.crossing_id: Optional[uuid.UUID] = None
        self.state = PedestrianState.WAITING
        
        # Position along crossing (0 = start side, 1 = end side)
        self.progress = 0.0
        
        # Direction: 1 = forward, -1 = backward (returning)
        self.direction = 1
        
        # Time spent waiting
        self.wait_time = 0.0
        
        # Color for rendering (RGB)
        self.color = (255, 100, 100)

    def _apply_config(self, config: Dict[str, Any]) -> None:
        for attr, val in config.items():
            if hasattr(self, attr):
                setattr(self, attr, val)

    def _validate_config(self) -> None:
        if self.walk_speed < self.MIN_WALK_SPEED:
            self.walk_speed = self.MIN_WALK_SPEED
        elif self.walk_speed > self.MAX_WALK_SPEED:
            self.walk_speed = self.MAX_WALK_SPEED

        if self.progress < 0.0:
            self.progress = 0.0
        elif self.progress > 1.0:
            self.progress = 1.0

    def update(self, crossing_length: float, dt: float) -> None:
        """
        Update pedestrian position based on current state.
        
        Args:
            crossing_length: Total length of the crossing in meters
            dt: Time delta in seconds
        """
        if crossing_length <= 0:
            return

        if self.state == PedestrianState.WAITING:
            self.wait_time += dt
            return

        if self.state == PedestrianState.CROSSING:
            distance_moved = self.walk_speed * dt
            progress_delta = distance_moved / crossing_length

            self.progress += progress_delta * self.direction

            # Clamp and check completion
            if self.progress >= 1.0:
                self.progress = 1.0
                self.state = PedestrianState.FINISHED
            elif self.progress <= 0.0:
                self.progress = 0.0
                self.state = PedestrianState.FINISHED

    def start_crossing(self) -> None:
        """Begin crossing the road."""
        if self.state == PedestrianState.WAITING:
            self.state = PedestrianState.CROSSING

    def stop_crossing(self) -> None:
        """Stop crossing (e.g., light changed)."""
        if self.state == PedestrianState.CROSSING:
            self.state = PedestrianState.WAITING

    def is_finished(self) -> bool:
        return self.state == PedestrianState.FINISHED

    def is_crossing(self) -> bool:
        return self.state == PedestrianState.CROSSING

    def is_waiting(self) -> bool:
        return self.state == PedestrianState.WAITING

    def get_position(self, start_pos: Tuple[float, float], 
                     end_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calculate current world position based on progress.
        
        Args:
            start_pos: (x, y) start position of crossing
            end_pos: (x, y) end position of crossing
            
        Returns:
            (x, y) current position
        """
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * self.progress
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * self.progress
        return (x, y)

    def reset(self) -> None:
        """Reset pedestrian for reuse."""
        self.state = PedestrianState.WAITING
        self.progress = 0.0
        self.direction = 1
        self.wait_time = 0.0
