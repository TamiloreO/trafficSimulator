from enum import Enum, auto
from typing import List, Optional, Dict, Any, Protocol, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import uuid

from .geometry.segment import Segment
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve


class LaneType(Enum):
    REGULAR = auto()
    HOV = auto()
    EMERGENCY = auto()
    TURNING = auto()


class RoadDirection(Enum):
    FORWARD = auto()
    BACKWARD = auto()
    BIDIRECTIONAL = auto()


@dataclass
class LaneConfiguration:
    lane_type: LaneType = LaneType.REGULAR
    speed_limit: float = 16.6
    allow_lane_change_left: bool = True
    allow_lane_change_right: bool = True
    width: float = 3.5


class ILaneProvider(Protocol):
    def get_lane(self, index: int) -> Optional[Segment]:
        ...
    
    def get_lane_count(self) -> int:
        ...


class IAdjacentLaneResolver(Protocol):
    def get_left_lane(self, current_lane_index: int) -> Optional[Tuple[int, Segment]]:
        ...
    
    def get_right_lane(self, current_lane_index: int) -> Optional[Tuple[int, Segment]]:
        ...


class Road:
    """
    Represents a multi-lane road that groups multiple parallel segments (lanes).
    Each lane is a Segment with vehicles traveling along it.
    """
    
    def __init__(self, road_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.id = road_id or str(uuid.uuid4())
        self.lanes: List[Segment] = []
        self.lane_configs: List[LaneConfiguration] = []
        self.lane_indices: Dict[int, int] = {}  # Maps segment index to lane index within road
        
        self._config = config or {}
        self._direction = self._config.get('direction', RoadDirection.FORWARD)
        self._default_lane_width = self._config.get('lane_width', 3.5)
        self._name = self._config.get('name', f'Road_{self.id[:8]}')
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def lane_count(self) -> int:
        return len(self.lanes)
    
    @property
    def direction(self) -> RoadDirection:
        return self._direction
    
    def add_lane(self, segment: Segment, config: Optional[LaneConfiguration] = None) -> int:
        """Add a lane (segment) to this road. Returns the lane index."""
        lane_index = len(self.lanes)
        self.lanes.append(segment)
        self.lane_configs.append(config or LaneConfiguration())
        return lane_index
    
    def get_lane(self, index: int) -> Optional[Segment]:
        if 0 <= index < len(self.lanes):
            return self.lanes[index]
        return None
    
    def get_lane_config(self, index: int) -> Optional[LaneConfiguration]:
        if 0 <= index < len(self.lane_configs):
            return self.lane_configs[index]
        return None
    
    def get_left_lane(self, current_lane_index: int) -> Optional[Tuple[int, Segment]]:
        """Get the lane to the left (lower index) of the current lane."""
        left_index = current_lane_index - 1
        if left_index >= 0:
            config = self.get_lane_config(current_lane_index)
            if config and config.allow_lane_change_left:
                return (left_index, self.lanes[left_index])
        return None
    
    def get_right_lane(self, current_lane_index: int) -> Optional[Tuple[int, Segment]]:
        """Get the lane to the right (higher index) of the current lane."""
        right_index = current_lane_index + 1
        if right_index < len(self.lanes):
            config = self.get_lane_config(current_lane_index)
            if config and config.allow_lane_change_right:
                return (right_index, self.lanes[right_index])
        return None
    
    def get_adjacent_lanes(self, current_lane_index: int) -> List[Tuple[int, Segment]]:
        """Get all adjacent lanes that allow lane changes."""
        adjacent = []
        left = self.get_left_lane(current_lane_index)
        if left:
            adjacent.append(left)
        right = self.get_right_lane(current_lane_index)
        if right:
            adjacent.append(right)
        return adjacent
    
    def get_road_length(self) -> float:
        """Returns the length of the road (assumes all lanes have similar length)."""
        if self.lanes:
            return self.lanes[0].get_length()
        return 0.0
    
    def register_segment_indices(self, starting_index: int) -> Dict[int, int]:
        """
        Register the global segment indices for each lane.
        Returns a mapping from global segment index to lane index.
        """
        self.lane_indices.clear()
        for i in range(len(self.lanes)):
            global_index = starting_index + i
            self.lane_indices[global_index] = i
        return self.lane_indices


class RoadBuilder:
    """Builder for creating multi-lane roads with proper lane offsets."""
    
    def __init__(self):
        self._start_point: Optional[Tuple[float, float]] = None
        self._end_point: Optional[Tuple[float, float]] = None
        self._control_point_1: Optional[Tuple[float, float]] = None
        self._control_point_2: Optional[Tuple[float, float]] = None
        self._lane_count: int = 1
        self._lane_width: float = 3.5
        self._road_config: Dict[str, Any] = {}
        self._lane_configs: List[Optional[LaneConfiguration]] = []
        self._curve_type: str = 'segment'
    
    def with_start(self, point: Tuple[float, float]) -> 'RoadBuilder':
        self._start_point = point
        return self
    
    def with_end(self, point: Tuple[float, float]) -> 'RoadBuilder':
        self._end_point = point
        return self
    
    def with_control_point(self, point: Tuple[float, float]) -> 'RoadBuilder':
        self._control_point_1 = point
        self._curve_type = 'quadratic'
        return self
    
    def with_control_points(self, cp1: Tuple[float, float], cp2: Tuple[float, float]) -> 'RoadBuilder':
        self._control_point_1 = cp1
        self._control_point_2 = cp2
        self._curve_type = 'cubic'
        return self
    
    def with_lane_count(self, count: int) -> 'RoadBuilder':
        self._lane_count = count
        return self
    
    def with_lane_width(self, width: float) -> 'RoadBuilder':
        self._lane_width = width
        return self
    
    def with_road_config(self, config: Dict[str, Any]) -> 'RoadBuilder':
        self._road_config = config
        return self
    
    def with_lane_config(self, lane_index: int, config: LaneConfiguration) -> 'RoadBuilder':
        while len(self._lane_configs) <= lane_index:
            self._lane_configs.append(None)
        self._lane_configs[lane_index] = config
        return self
    
    def _compute_perpendicular_offset(
        self, 
        point: Tuple[float, float], 
        direction: Tuple[float, float], 
        offset: float
    ) -> Tuple[float, float]:
        """Compute a point offset perpendicular to the direction."""
        import math
        length = math.sqrt(direction[0]**2 + direction[1]**2)
        if length == 0:
            return point
        nx = -direction[1] / length
        ny = direction[0] / length
        return (point[0] + nx * offset, point[1] + ny * offset)
    
    def build(self) -> Road:
        if not self._start_point or not self._end_point:
            raise ValueError("Start and end points are required")
        
        road = Road(config=self._road_config)
        
        direction = (
            self._end_point[0] - self._start_point[0],
            self._end_point[1] - self._start_point[1]
        )
        
        center_offset = (self._lane_count - 1) * self._lane_width / 2
        
        for i in range(self._lane_count):
            offset = i * self._lane_width - center_offset
            
            start = self._compute_perpendicular_offset(self._start_point, direction, offset)
            end = self._compute_perpendicular_offset(self._end_point, direction, offset)
            
            if self._curve_type == 'segment':
                segment = Segment((start, end))
            elif self._curve_type == 'quadratic':
                control = self._compute_perpendicular_offset(self._control_point_1, direction, offset)
                segment = QuadraticCurve(start, control, end)
            elif self._curve_type == 'cubic':
                cp1 = self._compute_perpendicular_offset(self._control_point_1, direction, offset)
                cp2 = self._compute_perpendicular_offset(self._control_point_2, direction, offset)
                segment = CubicCurve(start, cp1, cp2, end)
            else:
                segment = Segment((start, end))
            
            config = None
            if i < len(self._lane_configs) and self._lane_configs[i]:
                config = self._lane_configs[i]
            
            road.add_lane(segment, config)
        
        return road


def create_straight_road(
    start: Tuple[float, float],
    end: Tuple[float, float],
    lane_count: int = 1,
    lane_width: float = 3.5,
    config: Optional[Dict[str, Any]] = None
) -> Road:
    """Factory function for creating a straight multi-lane road."""
    return (
        RoadBuilder()
        .with_start(start)
        .with_end(end)
        .with_lane_count(lane_count)
        .with_lane_width(lane_width)
        .with_road_config(config or {})
        .build()
    )


def create_curved_road(
    start: Tuple[float, float],
    control: Tuple[float, float],
    end: Tuple[float, float],
    lane_count: int = 1,
    lane_width: float = 3.5,
    config: Optional[Dict[str, Any]] = None
) -> Road:
    """Factory function for creating a curved (quadratic) multi-lane road."""
    return (
        RoadBuilder()
        .with_start(start)
        .with_control_point(control)
        .with_end(end)
        .with_lane_count(lane_count)
        .with_lane_width(lane_width)
        .with_road_config(config or {})
        .build()
    )
