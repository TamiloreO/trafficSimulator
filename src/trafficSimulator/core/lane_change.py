from enum import Enum, auto
from typing import Optional, List, Tuple, Dict, Any, Protocol, TYPE_CHECKING
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import uuid

if TYPE_CHECKING:
    from .vehicle import Vehicle
    from .road import Road
    from .geometry.segment import Segment


class LaneChangeDirection(Enum):
    LEFT = auto()
    RIGHT = auto()
    NONE = auto()


class LaneChangeState(Enum):
    IDLE = auto()
    EVALUATING = auto()
    PREPARING = auto()
    EXECUTING = auto()
    COMPLETING = auto()
    COOLDOWN = auto()


@dataclass
class LaneChangeParameters:
    """Configuration parameters for lane change behavior."""
    min_gap_front: float = 15.0
    min_gap_rear: float = 10.0
    safe_gap_front: float = 25.0
    safe_gap_rear: float = 20.0
    
    speed_threshold: float = 0.8  # Change lane if lead is slower than this ratio of own speed
    evaluation_distance: float = 50.0
    
    lane_change_duration: float = 2.0
    cooldown_duration: float = 3.0
    
    politeness_factor: float = 0.5
    max_deceleration_for_lane_change: float = 2.0


@dataclass
class LaneChangeContext:
    """Context information for lane change decision making."""
    current_lane_index: int
    current_road_id: str
    vehicle_position: float
    vehicle_speed: float
    vehicle_length: float
    
    lead_vehicle_gap: Optional[float] = None
    lead_vehicle_speed: Optional[float] = None
    
    left_lane_available: bool = False
    right_lane_available: bool = False
    
    left_front_gap: Optional[float] = None
    left_rear_gap: Optional[float] = None
    left_front_speed: Optional[float] = None
    left_rear_speed: Optional[float] = None
    
    right_front_gap: Optional[float] = None
    right_rear_gap: Optional[float] = None
    right_front_speed: Optional[float] = None
    right_rear_speed: Optional[float] = None


class ILaneChangeEvaluator(Protocol):
    def evaluate(self, context: LaneChangeContext) -> LaneChangeDirection:
        ...


class ILaneChangeExecutor(Protocol):
    def execute(self, vehicle: 'Vehicle', target_lane_index: int, road: 'Road') -> bool:
        ...


class LaneChangeEvaluator:
    """Evaluates whether a lane change is desirable and safe."""
    
    def __init__(self, params: Optional[LaneChangeParameters] = None):
        self.params = params or LaneChangeParameters()
    
    def evaluate(self, context: LaneChangeContext) -> LaneChangeDirection:
        """
        Evaluate if a lane change should be performed based on:
        1. Is there a slower vehicle ahead?
        2. Is there space in the adjacent lane?
        3. Is there sufficient gap in the target lane?
        """
        if not self._should_consider_lane_change(context):
            return LaneChangeDirection.NONE
        
        left_score = self._evaluate_lane(context, LaneChangeDirection.LEFT)
        right_score = self._evaluate_lane(context, LaneChangeDirection.RIGHT)
        
        if left_score > 0 and left_score >= right_score:
            return LaneChangeDirection.LEFT
        elif right_score > 0:
            return LaneChangeDirection.RIGHT
        
        return LaneChangeDirection.NONE
    
    def _should_consider_lane_change(self, context: LaneChangeContext) -> bool:
        """Check if there's motivation to change lanes (slower vehicle ahead)."""
        if context.lead_vehicle_gap is None:
            return False
        
        if context.lead_vehicle_gap > self.params.evaluation_distance:
            return False
        
        if context.lead_vehicle_speed is None:
            return False
        
        if context.vehicle_speed <= 0:
            return False
        
        speed_ratio = context.lead_vehicle_speed / context.vehicle_speed
        return speed_ratio < self.params.speed_threshold
    
    def _evaluate_lane(self, context: LaneChangeContext, direction: LaneChangeDirection) -> float:
        """Evaluate a specific lane for lane change suitability. Returns a score >= 0."""
        if direction == LaneChangeDirection.LEFT:
            if not context.left_lane_available:
                return -1.0
            front_gap = context.left_front_gap
            rear_gap = context.left_rear_gap
            front_speed = context.left_front_speed
            rear_speed = context.left_rear_speed
        elif direction == LaneChangeDirection.RIGHT:
            if not context.right_lane_available:
                return -1.0
            front_gap = context.right_front_gap
            rear_gap = context.right_rear_gap
            front_speed = context.right_front_speed
            rear_speed = context.right_rear_speed
        else:
            return -1.0
        
        # Check minimum gaps
        if front_gap is not None and front_gap < self.params.min_gap_front:
            return -1.0
        if rear_gap is not None and rear_gap < self.params.min_gap_rear:
            return -1.0
        
        # Calculate score based on available space
        score = 0.0
        
        # Bonus for large front gap or no vehicle ahead
        if front_gap is None:
            score += 2.0
        elif front_gap >= self.params.safe_gap_front:
            score += 1.5
        else:
            score += front_gap / self.params.safe_gap_front
        
        # Bonus for large rear gap or no vehicle behind
        if rear_gap is None:
            score += 1.0
        elif rear_gap >= self.params.safe_gap_rear:
            score += 0.8
        else:
            score += 0.5 * (rear_gap / self.params.safe_gap_rear)
        
        # Consider speed of vehicles in target lane
        if front_speed is not None and context.vehicle_speed > 0:
            if front_speed >= context.vehicle_speed:
                score += 0.5  # Target lane is faster
            elif front_speed < context.lead_vehicle_speed if context.lead_vehicle_speed else 0:
                score -= 1.0  # Target lane is even slower
        
        return max(0.0, score)


@dataclass
class LaneChangeRequest:
    """Represents a pending lane change request."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: Any = None
    source_lane_index: int = 0
    target_lane_index: int = 0
    direction: LaneChangeDirection = LaneChangeDirection.NONE
    road_id: str = ""
    initiated_at: float = 0.0
    state: LaneChangeState = LaneChangeState.IDLE
    progress: float = 0.0


class LaneChangeController:
    """
    Manages lane change operations for vehicles.
    Coordinates evaluation, execution, and state management.
    """
    
    def __init__(self, params: Optional[LaneChangeParameters] = None):
        self.params = params or LaneChangeParameters()
        self.evaluator = LaneChangeEvaluator(self.params)
        self.active_requests: Dict[Any, LaneChangeRequest] = {}
        self.cooldowns: Dict[Any, float] = {}
    
    def can_initiate_lane_change(self, vehicle_id: Any, current_time: float) -> bool:
        """Check if a vehicle can initiate a lane change."""
        if vehicle_id in self.active_requests:
            return False
        
        if vehicle_id in self.cooldowns:
            if current_time < self.cooldowns[vehicle_id]:
                return False
            del self.cooldowns[vehicle_id]
        
        return True
    
    def request_lane_change(
        self,
        vehicle: 'Vehicle',
        context: LaneChangeContext,
        current_time: float
    ) -> Optional[LaneChangeRequest]:
        """Request a lane change for a vehicle."""
        if not self.can_initiate_lane_change(vehicle.id, current_time):
            return None
        
        direction = self.evaluator.evaluate(context)
        if direction == LaneChangeDirection.NONE:
            return None
        
        target_lane_index = context.current_lane_index
        if direction == LaneChangeDirection.LEFT:
            target_lane_index -= 1
        elif direction == LaneChangeDirection.RIGHT:
            target_lane_index += 1
        
        request = LaneChangeRequest(
            vehicle_id=vehicle.id,
            source_lane_index=context.current_lane_index,
            target_lane_index=target_lane_index,
            direction=direction,
            road_id=context.current_road_id,
            initiated_at=current_time,
            state=LaneChangeState.EXECUTING
        )
        
        self.active_requests[vehicle.id] = request
        return request
    
    def update_lane_change(
        self,
        vehicle_id: Any,
        current_time: float,
        dt: float
    ) -> Optional[LaneChangeRequest]:
        """Update the progress of an active lane change."""
        if vehicle_id not in self.active_requests:
            return None
        
        request = self.active_requests[vehicle_id]
        
        if request.state == LaneChangeState.EXECUTING:
            elapsed = current_time - request.initiated_at
            request.progress = min(1.0, elapsed / self.params.lane_change_duration)
            
            if request.progress >= 1.0:
                request.state = LaneChangeState.COMPLETING
        
        return request
    
    def complete_lane_change(self, vehicle_id: Any, current_time: float) -> bool:
        """Mark a lane change as complete and start cooldown."""
        if vehicle_id not in self.active_requests:
            return False
        
        request = self.active_requests[vehicle_id]
        if request.state != LaneChangeState.COMPLETING:
            return False
        
        del self.active_requests[vehicle_id]
        self.cooldowns[vehicle_id] = current_time + self.params.cooldown_duration
        
        return True
    
    def cancel_lane_change(self, vehicle_id: Any) -> bool:
        """Cancel an active lane change."""
        if vehicle_id in self.active_requests:
            del self.active_requests[vehicle_id]
            return True
        return False
    
    def get_active_request(self, vehicle_id: Any) -> Optional[LaneChangeRequest]:
        """Get the active lane change request for a vehicle."""
        return self.active_requests.get(vehicle_id)
    
    def is_changing_lanes(self, vehicle_id: Any) -> bool:
        """Check if a vehicle is currently changing lanes."""
        return vehicle_id in self.active_requests


class LaneChangeContextBuilder:
    """Builds lane change context from simulation state."""
    
    def __init__(self):
        self._context = LaneChangeContext(
            current_lane_index=0,
            current_road_id="",
            vehicle_position=0.0,
            vehicle_speed=0.0,
            vehicle_length=4.0
        )
    
    def with_vehicle_info(
        self,
        position: float,
        speed: float,
        length: float
    ) -> 'LaneChangeContextBuilder':
        self._context.vehicle_position = position
        self._context.vehicle_speed = speed
        self._context.vehicle_length = length
        return self
    
    def with_current_lane(
        self,
        lane_index: int,
        road_id: str
    ) -> 'LaneChangeContextBuilder':
        self._context.current_lane_index = lane_index
        self._context.current_road_id = road_id
        return self
    
    def with_lead_vehicle(
        self,
        gap: Optional[float],
        speed: Optional[float]
    ) -> 'LaneChangeContextBuilder':
        self._context.lead_vehicle_gap = gap
        self._context.lead_vehicle_speed = speed
        return self
    
    def with_left_lane(
        self,
        available: bool,
        front_gap: Optional[float] = None,
        rear_gap: Optional[float] = None,
        front_speed: Optional[float] = None,
        rear_speed: Optional[float] = None
    ) -> 'LaneChangeContextBuilder':
        self._context.left_lane_available = available
        self._context.left_front_gap = front_gap
        self._context.left_rear_gap = rear_gap
        self._context.left_front_speed = front_speed
        self._context.left_rear_speed = rear_speed
        return self
    
    def with_right_lane(
        self,
        available: bool,
        front_gap: Optional[float] = None,
        rear_gap: Optional[float] = None,
        front_speed: Optional[float] = None,
        rear_speed: Optional[float] = None
    ) -> 'LaneChangeContextBuilder':
        self._context.right_lane_available = available
        self._context.right_front_gap = front_gap
        self._context.right_rear_gap = rear_gap
        self._context.right_front_speed = front_speed
        self._context.right_rear_speed = rear_speed
        return self
    
    def build(self) -> LaneChangeContext:
        return self._context
