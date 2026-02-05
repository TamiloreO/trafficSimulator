import uuid
import numpy as np

class Vehicle:
    def __init__(self, config={}):
        self.set_default_config()

        for attr, val in config.items():
            setattr(self, attr, val)

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
        
        self.is_changing_lane = False
        self.last_lane_change_time = -10.0
        self.lane_change_progress = 0.0
        self.lane_change_source_segment = None
        self.lane_change_target_segment = None

    def init_properties(self):
        self.sqrt_ab = 2*np.sqrt(self.a_max*self.b_max)
        self._v_max = self.v_max

    def update(self, lead, dt):
        if self.v + self.a*dt < 0:
            self.x -= 1/2*self.v*self.v/self.a
            self.v = 0
        else:
            self.v += self.a*dt
            self.x += self.v*dt + self.a*dt*dt/2
        
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v

            alpha = (self.s0 + max(0, self.T*self.v + delta_v*self.v/self.sqrt_ab)) / delta_x

        self.a = self.a_max * (1-(self.v/self.v_max)**4 - alpha**2)

        if self.stopped: 
            self.a = -self.b_max*self.v/self.v_max
    
    def start_lane_change(self, source_segment, target_segment, current_time):
        self.is_changing_lane = True
        self.lane_change_progress = 0.0
        self.lane_change_source_segment = source_segment
        self.lane_change_target_segment = target_segment
        self.last_lane_change_time = current_time
    
    def update_lane_change(self, dt):
        if not self.is_changing_lane:
            return False
        
        self.lane_change_progress += dt * 0.5  # ~2 seconds to complete
        
        if self.lane_change_progress >= 1.0:
            self.is_changing_lane = False
            self.lane_change_progress = 1.0
            return True  # Lane change complete
        return False
