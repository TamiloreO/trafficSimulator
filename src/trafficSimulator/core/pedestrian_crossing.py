import uuid
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any
from collections import deque
import math

from .pedestrian import Pedestrian, PedestrianState


class CrossingType(Enum):
    """Different types of pedestrian crossings found in the real world."""
    ZEBRA = "zebra"              # Basic striped crossing, pedestrians have priority
    PELICAN = "pelican"         # Signal-controlled with push button
    PUFFIN = "puffin"           # Pedestrian User-Friendly Intelligent crossing
    TOUCAN = "toucan"           # Two-can cross (pedestrians + cyclists)
    PEGASUS = "pegasus"         # Equestrian crossing (includes horses)
    TIGER = "tiger"             # Parallel zebra and cycle crossing


class SignalState(Enum):
    """Traffic signal states for controlled crossings."""
    RED = "red"                 # Vehicles stop, pedestrians cross
    AMBER = "amber"             # Warning - changing soon
    GREEN = "green"             # Vehicles go, pedestrians wait
    FLASHING_AMBER = "flashing_amber"  # Vehicles proceed with caution


class PedestrianCrossing:
    """
    Base class for all pedestrian crossing types.
    Handles pedestrian management, signal timing, and vehicle blocking.
    """

    DEFAULT_CROSSING_WIDTH = 4.0  # meters
    DEFAULT_STRIPE_WIDTH = 0.5    # meters
    DEFAULT_STRIPE_GAP = 0.5      # meters
    
    # Signal timing defaults (seconds)
    DEFAULT_RED_TIME = 15.0
    DEFAULT_AMBER_TIME = 3.0
    DEFAULT_GREEN_TIME = 30.0
    DEFAULT_MIN_GREEN_TIME = 7.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}

        self._set_default_config()
        self._apply_config(config)
        self._validate_config()
        self._calculate_geometry()

    def _set_default_config(self) -> None:
        self.id = uuid.uuid4()
        self.crossing_type = CrossingType.ZEBRA
        
        # Position on segment (0-1 progress along segment)
        self.segment_index: int = 0
        self.position_on_segment: float = 0.5  # middle of segment by default
        
        # Crossing geometry
        self.width = self.DEFAULT_CROSSING_WIDTH
        self.stripe_width = self.DEFAULT_STRIPE_WIDTH
        self.stripe_gap = self.DEFAULT_STRIPE_GAP
        
        # Crossing endpoints (calculated from segment)
        self.start_pos: Tuple[float, float] = (0.0, 0.0)
        self.end_pos: Tuple[float, float] = (0.0, 0.0)
        self.center_pos: Tuple[float, float] = (0.0, 0.0)
        self.heading: float = 0.0
        
        # Pedestrian management
        self.pedestrians: deque = deque()
        self.max_pedestrians = 20
        
        # Signal control
        self.is_signaled = False
        self.signal_state = SignalState.GREEN
        self.signal_timer = 0.0
        self.button_pressed = False
        self.button_press_time = 0.0
        
        # Timing configuration
        self.red_time = self.DEFAULT_RED_TIME
        self.amber_time = self.DEFAULT_AMBER_TIME
        self.green_time = self.DEFAULT_GREEN_TIME
        self.min_green_time = self.DEFAULT_MIN_GREEN_TIME
        
        # Detection zone for PUFFIN-type crossings
        self.has_detection = False
        self.detection_timeout = 5.0
        
        # Visual properties
        self.stripe_color = (255, 255, 255)
        self.signal_color = (0, 255, 0)
        
        # Cyclist support (TOUCAN/TIGER)
        self.allows_cyclists = False
        self.cycle_lane_width = 2.0
        
        # Equestrian support (PEGASUS)
        self.allows_horses = False

    def _apply_config(self, config: Dict[str, Any]) -> None:
        for attr, val in config.items():
            if hasattr(self, attr):
                setattr(self, attr, val)

        # Set type-specific properties
        if 'crossing_type' in config:
            self._apply_type_defaults()

    def _apply_type_defaults(self) -> None:
        """Apply defaults based on crossing type."""
        if self.crossing_type == CrossingType.ZEBRA:
            self.is_signaled = False
            self.has_detection = False
            self.allows_cyclists = False
            self.allows_horses = False

        elif self.crossing_type == CrossingType.PELICAN:
            self.is_signaled = True
            self.has_detection = False
            self.allows_cyclists = False
            self.allows_horses = False

        elif self.crossing_type == CrossingType.PUFFIN:
            self.is_signaled = True
            self.has_detection = True
            self.allows_cyclists = False
            self.allows_horses = False

        elif self.crossing_type == CrossingType.TOUCAN:
            self.is_signaled = True
            self.has_detection = True
            self.allows_cyclists = True
            self.allows_horses = False
            self.width = 6.0  # Wider for cyclists

        elif self.crossing_type == CrossingType.PEGASUS:
            self.is_signaled = True
            self.has_detection = True
            self.allows_cyclists = False
            self.allows_horses = True
            self.width = 5.0  # Wider for horses

        elif self.crossing_type == CrossingType.TIGER:
            self.is_signaled = False  # Like zebra, no signals
            self.has_detection = False
            self.allows_cyclists = True
            self.allows_horses = False
            self.width = 6.0

    def _validate_config(self) -> None:
        if self.width < 2.0:
            self.width = 2.0
        elif self.width > 10.0:
            self.width = 10.0

        if self.position_on_segment < 0.0:
            self.position_on_segment = 0.0
        elif self.position_on_segment > 1.0:
            self.position_on_segment = 1.0

        if self.red_time < 5.0:
            self.red_time = 5.0
        if self.green_time < 10.0:
            self.green_time = 10.0

    def _calculate_geometry(self) -> None:
        """Calculate crossing geometry. Should be called after setting segment."""
        pass  # Calculated when attached to segment

    def attach_to_segment(self, segment, position: float = 0.5) -> None:
        """
        Attach crossing to a road segment and calculate geometry.
        
        Args:
            segment: The road segment to attach to
            position: Position along segment (0-1)
        """
        self.position_on_segment = max(0.05, min(0.95, position))
        
        try:
            # Get center point on road
            center = segment.get_point(self.position_on_segment)
            self.center_pos = (float(center[0]), float(center[1]))
            
            # Get heading (direction of road)
            heading = segment.get_heading(self.position_on_segment)
            self.heading = float(heading)
            
            # Calculate crossing perpendicular to road
            # Crossing goes from one side of road to other
            perp_angle = self.heading + math.pi / 2
            half_width = self.width / 2
            
            self.start_pos = (
                self.center_pos[0] + half_width * math.cos(perp_angle),
                self.center_pos[1] + half_width * math.sin(perp_angle)
            )
            self.end_pos = (
                self.center_pos[0] - half_width * math.cos(perp_angle),
                self.center_pos[1] - half_width * math.sin(perp_angle)
            )
        except Exception:
            # Fallback to defaults if segment operations fail
            pass

    def get_crossing_length(self) -> float:
        """Get the length of the crossing path (width of road)."""
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        return math.sqrt(dx * dx + dy * dy)

    def add_pedestrian(self, pedestrian: Pedestrian) -> bool:
        """
        Add a pedestrian to the crossing queue.
        
        Returns:
            True if added successfully, False if crossing is full
        """
        if len(self.pedestrians) >= self.max_pedestrians:
            return False

        pedestrian.crossing_id = self.id
        self.pedestrians.append(pedestrian.id)
        return True

    def remove_pedestrian(self, pedestrian_id: uuid.UUID) -> bool:
        """Remove a pedestrian from the crossing."""
        try:
            self.pedestrians.remove(pedestrian_id)
            return True
        except ValueError:
            return False

    def press_button(self, current_time: float) -> None:
        """Simulate pressing the crossing button (for signaled crossings)."""
        if self.is_signaled and not self.button_pressed:
            self.button_pressed = True
            self.button_press_time = current_time

    def update(self, dt: float, current_time: float, pedestrians_dict: Dict) -> None:
        """
        Update crossing state and all pedestrians on it.
        
        Args:
            dt: Time delta
            current_time: Current simulation time
            pedestrians_dict: Dictionary of all pedestrians in simulation
        """
        # Update signal state for signaled crossings
        if self.is_signaled:
            self._update_signal(dt, current_time, pedestrians_dict)
        else:
            # For unsignaled crossings (Zebra, Tiger), pedestrians can always cross
            # when they arrive
            self._handle_unsignaled_crossing(pedestrians_dict)

        # Update pedestrian positions
        crossing_length = self.get_crossing_length()
        finished_pedestrians = []

        for ped_id in list(self.pedestrians):
            if ped_id not in pedestrians_dict:
                finished_pedestrians.append(ped_id)
                continue

            pedestrian = pedestrians_dict[ped_id]
            pedestrian.update(crossing_length, dt)

            if pedestrian.is_finished():
                finished_pedestrians.append(ped_id)

        # Remove finished pedestrians
        for ped_id in finished_pedestrians:
            self.remove_pedestrian(ped_id)

    def _update_signal(self, dt: float, current_time: float, 
                       pedestrians_dict: Dict) -> None:
        """Update traffic signal state machine."""
        self.signal_timer += dt

        if self.signal_state == SignalState.GREEN:
            # Check if button was pressed and minimum green time elapsed
            if self.button_pressed:
                time_since_press = current_time - self.button_press_time
                if time_since_press >= self.min_green_time:
                    self.signal_state = SignalState.AMBER
                    self.signal_timer = 0.0
            # Or if max green time exceeded with waiting pedestrians
            elif self.signal_timer >= self.green_time and self._has_waiting_pedestrians(pedestrians_dict):
                self.signal_state = SignalState.AMBER
                self.signal_timer = 0.0

        elif self.signal_state == SignalState.AMBER:
            if self.signal_timer >= self.amber_time:
                self.signal_state = SignalState.RED
                self.signal_timer = 0.0
                self.button_pressed = False
                # Start all waiting pedestrians crossing
                self._start_pedestrians_crossing(pedestrians_dict)

        elif self.signal_state == SignalState.RED:
            # Check if all pedestrians finished or timeout
            all_finished = not self._has_crossing_pedestrians(pedestrians_dict)
            
            # PUFFIN-type detection: extend if pedestrians still crossing
            if self.has_detection and self._has_crossing_pedestrians(pedestrians_dict):
                # Keep red while people are crossing
                pass
            elif all_finished or self.signal_timer >= self.red_time:
                self.signal_state = SignalState.FLASHING_AMBER
                self.signal_timer = 0.0

        elif self.signal_state == SignalState.FLASHING_AMBER:
            if self.signal_timer >= self.amber_time:
                self.signal_state = SignalState.GREEN
                self.signal_timer = 0.0

        # Update signal color for rendering
        self._update_signal_color()

    def _update_signal_color(self) -> None:
        """Update signal color based on current state."""
        if self.signal_state == SignalState.RED:
            self.signal_color = (255, 0, 0)
        elif self.signal_state == SignalState.AMBER:
            self.signal_color = (255, 165, 0)
        elif self.signal_state == SignalState.FLASHING_AMBER:
            # Flashing effect
            self.signal_color = (255, 165, 0) if int(self.signal_timer * 4) % 2 == 0 else (100, 70, 0)
        else:  # GREEN
            self.signal_color = (0, 255, 0)

    def _handle_unsignaled_crossing(self, pedestrians_dict: Dict) -> None:
        """Handle pedestrian crossing for unsignaled crossings (Zebra, Tiger)."""
        # Pedestrians can start crossing immediately at unsignaled crossings
        for ped_id in self.pedestrians:
            if ped_id in pedestrians_dict:
                pedestrian = pedestrians_dict[ped_id]
                if pedestrian.is_waiting():
                    pedestrian.start_crossing()

    def _has_waiting_pedestrians(self, pedestrians_dict: Dict) -> bool:
        """Check if any pedestrians are waiting to cross."""
        for ped_id in self.pedestrians:
            if ped_id in pedestrians_dict:
                if pedestrians_dict[ped_id].is_waiting():
                    return True
        return False

    def _has_crossing_pedestrians(self, pedestrians_dict: Dict) -> bool:
        """Check if any pedestrians are currently crossing."""
        for ped_id in self.pedestrians:
            if ped_id in pedestrians_dict:
                if pedestrians_dict[ped_id].is_crossing():
                    return True
        return False

    def _start_pedestrians_crossing(self, pedestrians_dict: Dict) -> None:
        """Start all waiting pedestrians crossing."""
        for ped_id in self.pedestrians:
            if ped_id in pedestrians_dict:
                pedestrians_dict[ped_id].start_crossing()

    def should_block_vehicles(self, pedestrians_dict: Dict) -> bool:
        """
        Determine if vehicles should be blocked at this crossing.
        
        Returns:
            True if vehicles should stop
        """
        if self.is_signaled:
            # For signaled crossings, block when not green
            return self.signal_state in (SignalState.RED, SignalState.AMBER)
        else:
            # For unsignaled (zebra), block when pedestrians are crossing or waiting
            return (self._has_crossing_pedestrians(pedestrians_dict) or 
                    self._has_waiting_pedestrians(pedestrians_dict))

    def get_stop_position(self, segment_length: float) -> float:
        """
        Get the position where vehicles should stop (in segment units).
        
        Args:
            segment_length: Total length of the segment
            
        Returns:
            Position in segment distance units where vehicles should stop
        """
        # Stop a bit before the crossing
        stop_margin = 2.0  # meters before crossing
        stop_position = self.position_on_segment * segment_length - stop_margin
        return max(0.0, stop_position)

    def get_stripe_positions(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Calculate positions for zebra stripes.
        
        Returns:
            List of (start, end) tuples for each stripe
        """
        stripes = []
        
        # Calculate crossing direction (along the road)
        road_dx = math.cos(self.heading)
        road_dy = math.sin(self.heading)
        
        # Calculate stripe direction (perpendicular, across the road)
        stripe_dx = self.end_pos[0] - self.start_pos[0]
        stripe_dy = self.end_pos[1] - self.start_pos[1]
        stripe_length = self.get_crossing_length()
        
        if stripe_length < 0.1:
            return stripes
            
        # Normalize
        stripe_dx /= stripe_length
        stripe_dy /= stripe_length
        
        # Total width along road direction for stripes
        stripe_total_width = 3.0  # meters of striped area
        num_stripes = int(stripe_total_width / (self.stripe_width + self.stripe_gap))
        
        if num_stripes < 1:
            num_stripes = 4
        
        start_offset = -stripe_total_width / 2
        
        for i in range(num_stripes):
            offset = start_offset + i * (self.stripe_width + self.stripe_gap)
            
            # Stripe center position
            cx = self.center_pos[0] + offset * road_dx
            cy = self.center_pos[1] + offset * road_dy
            
            # Stripe endpoints
            half_len = stripe_length / 2
            s_start = (cx + half_len * stripe_dx, cy + half_len * stripe_dy)
            s_end = (cx - half_len * stripe_dx, cy - half_len * stripe_dy)
            
            stripes.append((s_start, s_end))
        
        return stripes

    def get_cycle_lane_geometry(self) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Get cycle lane geometry for TOUCAN/TIGER crossings."""
        if not self.allows_cyclists:
            return None
            
        # Cycle lane runs parallel to pedestrian crossing
        # Offset from main crossing
        offset = self.width / 2 + self.cycle_lane_width / 2 + 0.5
        
        road_dx = math.cos(self.heading)
        road_dy = math.sin(self.heading)
        
        start = (
            self.start_pos[0] + offset * road_dx,
            self.start_pos[1] + offset * road_dy
        )
        end = (
            self.end_pos[0] + offset * road_dx,
            self.end_pos[1] + offset * road_dy
        )
        
        return (start, end)


def create_zebra_crossing(segment_index: int, position: float = 0.5) -> PedestrianCrossing:
    """Factory function to create a zebra crossing."""
    return PedestrianCrossing({
        'crossing_type': CrossingType.ZEBRA,
        'segment_index': segment_index,
        'position_on_segment': position
    })


def create_pelican_crossing(segment_index: int, position: float = 0.5,
                            red_time: float = 15.0, green_time: float = 30.0) -> PedestrianCrossing:
    """Factory function to create a pelican crossing."""
    return PedestrianCrossing({
        'crossing_type': CrossingType.PELICAN,
        'segment_index': segment_index,
        'position_on_segment': position,
        'red_time': red_time,
        'green_time': green_time
    })


def create_puffin_crossing(segment_index: int, position: float = 0.5) -> PedestrianCrossing:
    """Factory function to create a puffin crossing."""
    return PedestrianCrossing({
        'crossing_type': CrossingType.PUFFIN,
        'segment_index': segment_index,
        'position_on_segment': position
    })


def create_toucan_crossing(segment_index: int, position: float = 0.5) -> PedestrianCrossing:
    """Factory function to create a toucan crossing."""
    return PedestrianCrossing({
        'crossing_type': CrossingType.TOUCAN,
        'segment_index': segment_index,
        'position_on_segment': position
    })


def create_pegasus_crossing(segment_index: int, position: float = 0.5) -> PedestrianCrossing:
    """Factory function to create a pegasus crossing."""
    return PedestrianCrossing({
        'crossing_type': CrossingType.PEGASUS,
        'segment_index': segment_index,
        'position_on_segment': position
    })


def create_tiger_crossing(segment_index: int, position: float = 0.5) -> PedestrianCrossing:
    """Factory function to create a tiger crossing."""
    return PedestrianCrossing({
        'crossing_type': CrossingType.TIGER,
        'segment_index': segment_index,
        'position_on_segment': position
    })
