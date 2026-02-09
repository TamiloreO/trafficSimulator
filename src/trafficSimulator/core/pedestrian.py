import uuid
import numpy as np


class Pedestrian:
    """Represents a pedestrian crossing the road."""
    
    def __init__(self, config={}):
        self.set_default_config()
        for attr, val in config.items():
            setattr(self, attr, val)
        self.init_properties()

    def set_default_config(self):
        self.id = uuid.uuid4()
        self.width = 0.5  # Pedestrian width in meters
        self.speed = 1.4  # Average walking speed m/s (about 5 km/h)
        self.x = 0  # Position along crossing path (0 = start, 1 = end)
        self.crossing_id = None
        self.state = 'waiting'  # 'waiting', 'crossing', 'finished'
        self.direction = 1  # 1 = forward, -1 = backward (crossing from other side)
        self.color = (50, 50, 50)  # Dark gray for pedestrians

    def init_properties(self):
        if self.direction == -1:
            self.x = 1.0

    def update(self, dt, crossing_length):
        """Update pedestrian position."""
        if self.state == 'crossing':
            distance = self.speed * dt
            progress = distance / crossing_length
            self.x += progress * self.direction
            
            # Check if finished crossing
            if self.direction == 1 and self.x >= 1.0:
                self.x = 1.0
                self.state = 'finished'
            elif self.direction == -1 and self.x <= 0.0:
                self.x = 0.0
                self.state = 'finished'

    def start_crossing(self):
        """Begin crossing the road."""
        self.state = 'crossing'

    def is_finished(self):
        return self.state == 'finished'

    def is_waiting(self):
        return self.state == 'waiting'

    def is_crossing(self):
        return self.state == 'crossing'
