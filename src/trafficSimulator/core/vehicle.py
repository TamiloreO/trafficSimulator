import uuid
import numpy as np
from .vehicle_types import VehicleType, get_vehicle_specs, get_vehicle_color


class Vehicle:
    def __init__(self, config={}):
        # Set default configuration
        self.set_default_config()

        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)

        # Apply vehicle type specifications if specified
        if 'vehicle_type' in config:
            self.apply_vehicle_type(config['vehicle_type'])

        # Calculate properties
        self.init_properties()
        
    def set_default_config(self):    
        self.id = uuid.uuid4()
        self.vehicle_type = VehicleType.CAR

        self.l = 4
        self.w = 1.8
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

        self.color = get_vehicle_color(VehicleType.CAR)

    def apply_vehicle_type(self, vehicle_type):
        """Apply specifications based on vehicle type."""
        if isinstance(vehicle_type, str):
            vehicle_type = VehicleType(vehicle_type)
        
        self.vehicle_type = vehicle_type
        specs = get_vehicle_specs(vehicle_type)
        
        for attr, val in specs.items():
            setattr(self, attr, val)
        
        self.color = get_vehicle_color(vehicle_type)

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


class Car(Vehicle):
    """A standard passenger car."""
    def __init__(self, config={}):
        config['vehicle_type'] = VehicleType.CAR
        super().__init__(config)


class Truck(Vehicle):
    """A heavy goods truck."""
    def __init__(self, config={}):
        config['vehicle_type'] = VehicleType.TRUCK
        super().__init__(config)


class Bus(Vehicle):
    """A passenger bus."""
    def __init__(self, config={}):
        config['vehicle_type'] = VehicleType.BUS
        super().__init__(config)


class Motorcycle(Vehicle):
    """A motorcycle."""
    def __init__(self, config={}):
        config['vehicle_type'] = VehicleType.MOTORCYCLE
        super().__init__(config)
