import uuid
import numpy as np

class Vehicle:
    def __init__(self, config={}):
        # Set default configuration
        self.set_default_config()

        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)

        # Calculate properties
        self.init_properties()
        
    def set_default_config(self):    
        self.id = uuid.uuid4()

        self.l = 4
        self.s0 = 4
        self.T = 1
        self.v_max = 16.6
        self.a_max = 1.44
        self.b_max = 4.61

        self.path = []
        self.current_road_index = 0

        self.x = 0
        self.v = 0
        self.a = 0
        self.stopped = False

    def init_properties(self):
        self.sqrt_ab = 2*np.sqrt(self.a_max*self.b_max)
        self._v_max = self.v_max

    def update(self, lead, dt):
        # Update position and velocity
        if self.v + self.a*dt < 0:
            self.x -= 1/2*self.v*self.v/self.a
            self.v = 0
        else:
            self.v += self.a*dt
            self.x += self.v*dt + self.a*dt*dt/2
        
        # Update acceleration
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v

            alpha = (self.s0 + max(0, self.T*self.v + delta_v*self.v/self.sqrt_ab)) / delta_x

        self.a = self.a_max * (1-(self.v/self.v_max)**4 - alpha**2)

        if self.stopped: 
            self.a = -self.b_max*self.v/self.v_max

    def update_with_stop(self, stop_position, dt, lead=None):
        """Update vehicle considering a stop position (e.g., traffic light)."""
        # Update position and velocity
        if self.v + self.a*dt < 0:
            self.x -= 1/2*self.v*self.v/self.a
            self.v = 0
        else:
            self.v += self.a*dt
            self.x += self.v*dt + self.a*dt*dt/2
        
        # Calculate alpha for IDM (Intelligent Driver Model)
        alpha = 0
        
        # Consider lead vehicle if present
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v
            if delta_x > 0:
                alpha = (self.s0 + max(0, self.T*self.v + delta_v*self.v/self.sqrt_ab)) / delta_x
        
        # Consider traffic light stop position as a virtual stationary vehicle
        distance_to_stop = stop_position - self.x
        if distance_to_stop > 0:
            # Treat stop line as stationary vehicle (delta_v = self.v)
            alpha_stop = (self.s0 + max(0, self.T*self.v + self.v*self.v/self.sqrt_ab)) / distance_to_stop
            # Use the more restrictive constraint
            alpha = max(alpha, alpha_stop)
        
        self.a = self.a_max * (1-(self.v/self.v_max)**4 - alpha**2)
        
        # Ensure we don't overshoot the stop position
        if distance_to_stop <= self.s0 and self.v < 0.5:
            self.v = 0
            self.a = 0
            self.stopped = True
        