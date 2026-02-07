"""
Vehicle Module

Defines the Vehicle entity with IDM (Intelligent Driver Model) behavior.
Supports type-specific configurations for different vehicle categories.
"""

import uuid
import numpy as np


class Vehicle:
    """
    Vehicle entity implementing the Intelligent Driver Model (IDM).
    
    Supports configuration for different vehicle types with varying
    physical dimensions and behavioral parameters.
    """

    def __init__(self, config=None):
        if config is None:
            config = {}

        self.set_default_config()

        for attr, val in config.items():
            setattr(self, attr, val)

        self.init_properties()

    def set_default_config(self):
        """Sets default configuration values (car-like defaults)."""
        self.id = uuid.uuid4()

        # Vehicle type (None means legacy/untyped vehicle)
        self.vehicle_type = None

        # Physical dimensions
        self.l = 4.5      # length in meters
        self.w = 1.8      # width in meters

        # IDM parameters
        self.s0 = 4.0     # minimum safe distance (meters)
        self.T = 1.0      # safe time headway (seconds)
        self.v_max = 16.6 # maximum velocity (m/s)
        self.a_max = 1.44 # maximum acceleration (m/s^2)
        self.b_max = 4.61 # maximum deceleration (m/s^2)

        # Path and position
        self.path = []
        self.current_road_index = 0

        # State variables
        self.x = 0        # position along segment
        self.v = 0        # velocity
        self.a = 0        # acceleration
        self.stopped = False

        # Visualization
        self.color = (0, 0, 255)  # Default blue

    def init_properties(self):
        """Initializes derived properties."""
        self.sqrt_ab = 2 * np.sqrt(self.a_max * self.b_max)
        self._v_max = self.v_max

    def update(self, lead, dt):
        """
        Updates vehicle state using the Intelligent Driver Model.

        Parameters
        ----------
        lead : Vehicle or None
            The vehicle ahead (None if no lead vehicle)
        dt : float
            Time step in seconds
        """
        # Update position and velocity
        if self.v + self.a * dt < 0:
            self.x -= 0.5 * self.v * self.v / self.a
            self.v = 0
        else:
            self.v += self.a * dt
            self.x += self.v * dt + self.a * dt * dt / 2

        # Calculate acceleration using IDM
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v

            s_star = self.s0 + max(0, self.T * self.v + delta_v * self.v / self.sqrt_ab)
            alpha = s_star / delta_x if delta_x > 0 else 1

        self.a = self.a_max * (1 - (self.v / self.v_max) ** 4 - alpha ** 2)

        if self.stopped:
            self.a = -self.b_max * self.v / self.v_max

    def __repr__(self):
        type_str = self.vehicle_type.value if self.vehicle_type else "generic"
        return f"Vehicle(type={type_str}, id={self.id})"
