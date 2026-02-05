import uuid
import numpy as np
from typing import Optional, List, Any, Dict
from dataclasses import dataclass


@dataclass
class LaneChangeInfo:
    """Tracks lane change state for a vehicle."""
    is_changing: bool = False
    source_lane_index: int = -1
    target_lane_index: int = -1
    progress: float = 0.0
    road_id: Optional[str] = None


class Vehicle:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
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
        
        # Lane change properties
        self.current_lane_index: int = 0
        self.current_road_id: Optional[str] = None
        self.lane_change_info = LaneChangeInfo()
        
        # Lane offset for visual representation during lane change
        self.lane_offset: float = 0.0
        
        # Tracking
        self.spawn_time: float = 0.0

    def init_properties(self):
        self.sqrt_ab = 2*np.sqrt(self.a_max*self.b_max)
        self._v_max = self.v_max

    def update(self, lead: Optional['Vehicle'], dt: float):
        # Update position and velocity
        if self.v + self.a*dt < 0:
            self.x -= 1/2*self.v*self.v/self.a
            self.v = 0
        else:
            self.v += self.a*dt
            self.x += self.v*dt + self.a*dt*dt/2
        
        # Update acceleration using IDM
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.l
            delta_v = self.v - lead.v

            alpha = (self.s0 + max(0, self.T*self.v + delta_v*self.v/self.sqrt_ab)) / delta_x

        self.a = self.a_max * (1-(self.v/self.v_max)**4 - alpha**2)

        if self.stopped: 
            self.a = -self.b_max*self.v/self.v_max
    
    def start_lane_change(self, source_lane: int, target_lane: int, road_id: str):
        """Initialize a lane change maneuver."""
        self.lane_change_info = LaneChangeInfo(
            is_changing=True,
            source_lane_index=source_lane,
            target_lane_index=target_lane,
            progress=0.0,
            road_id=road_id
        )
    
    def update_lane_change_progress(self, progress: float):
        """Update the lane change progress (0.0 to 1.0)."""
        if self.lane_change_info.is_changing:
            self.lane_change_info.progress = progress
            # Calculate lateral offset based on progress (smooth interpolation)
            direction = 1 if self.lane_change_info.target_lane_index > self.lane_change_info.source_lane_index else -1
            # Use smooth step for natural movement
            t = progress
            smooth_t = t * t * (3 - 2 * t)  # Smoothstep function
            self.lane_offset = direction * smooth_t
    
    def complete_lane_change(self):
        """Complete the lane change and update current lane."""
        if self.lane_change_info.is_changing:
            self.current_lane_index = self.lane_change_info.target_lane_index
            self.lane_change_info = LaneChangeInfo()
            self.lane_offset = 0.0
    
    def cancel_lane_change(self):
        """Cancel an in-progress lane change."""
        self.lane_change_info = LaneChangeInfo()
        self.lane_offset = 0.0
    
    @property
    def is_changing_lanes(self) -> bool:
        return self.lane_change_info.is_changing
    
    def get_effective_lane_index(self) -> int:
        """Get the effective lane index considering lane change progress."""
        if self.lane_change_info.is_changing and self.lane_change_info.progress >= 0.5:
            return self.lane_change_info.target_lane_index
        return self.current_lane_index
