"""
Pedestrian crossing module for traffic simulation.

This module provides various types of pedestrian crossings commonly found
in the UK and other countries. Each crossing type has distinct behavior
regarding signal timing, pedestrian priority, and vehicle stopping rules.

Crossing Types:
    - ZebraCrossing: Uncontrolled crossing with pedestrian priority
    - PelicanCrossing: Signal-controlled with flashing amber phase
    - PuffinCrossing: Intelligent crossing with pedestrian detection sensors
    - ToucanCrossing: Shared crossing for pedestrians and cyclists
    - PegasusCrossing: Wide crossing accommodating horse riders
"""

import uuid
from collections import deque
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .pedestrian import Pedestrian
    from .geometry.segment import Segment


class CrossingState(Enum):
    """
    Enumeration of traffic signal states for controlled crossings.
    
    These states represent the phase of the traffic signal cycle and
    determine whether vehicles must stop and whether pedestrians may cross.
    
    Attributes:
        VEHICLES_GO: Green light for vehicles, red for pedestrians.
            Vehicles may proceed, pedestrians must wait.
        VEHICLES_STOPPING: Amber light for vehicles.
            Vehicles should prepare to stop, pedestrians still waiting.
        PEDESTRIANS_GO: Red light for vehicles, green for pedestrians.
            Vehicles must stop, pedestrians may cross.
        PEDESTRIANS_FINISHING: Flashing amber for vehicles (Pelican only).
            Vehicles may proceed if crossing is clear.
    """
    VEHICLES_GO = 'vehicles_go'
    VEHICLES_STOPPING = 'vehicles_stopping'
    PEDESTRIANS_GO = 'pedestrians_go'
    PEDESTRIANS_FINISHING = 'pedestrians_finishing'


class CrossingType(Enum):
    """
    Enumeration of supported pedestrian crossing types.
    
    Each type has distinct characteristics regarding signals, markings,
    and operational behavior.
    
    Attributes:
        GENERIC: Base crossing type with minimal functionality.
        ZEBRA: Uncontrolled crossing with black/white stripes and Belisha beacons.
        PELICAN: Pedestrian Light Controlled crossing with push button.
        PUFFIN: Pedestrian User-Friendly Intelligent crossing with sensors.
        TOUCAN: Two-can cross - shared pedestrian and cyclist crossing.
        PEGASUS: Equestrian crossing for pedestrians, cyclists, and horse riders.
    """
    GENERIC = 'generic'
    ZEBRA = 'zebra'
    PELICAN = 'pelican'
    PUFFIN = 'puffin'
    TOUCAN = 'toucan'
    PEGASUS = 'pegasus'


class PedestrianCrossing:
    """
    Base class for pedestrian crossings in the traffic simulation.
    
    Provides common functionality for all crossing types including pedestrian
    queue management, state machine updates, and vehicle stopping calculations.
    Subclasses implement specific behavior for different crossing types.
    
    Attributes:
        id: Unique identifier for this crossing.
        segment_index: Index of the road segment this crossing is on.
        position: Position along segment as fraction (0.0 to 1.0).
        width: Width of crossing perpendicular to road (meters).
        length: Length of crossing along road direction (meters).
        min_green_time: Minimum green time for vehicles before allowing change.
        pedestrian_green_time: Duration of pedestrian crossing phase.
        amber_time: Duration of amber/warning phase.
        all_red_time: Safety buffer with all signals red.
        state: Current signal state (CrossingState enum).
        state_timer: Time elapsed in current state.
        request_pending: Whether a pedestrian has requested to cross.
        waiting_pedestrians: Queue of pedestrians waiting to cross.
        crossing_pedestrians: List of pedestrians currently on crossing.
    
    Class Attributes:
        STRIPE_WIDTH: Width of zebra stripes in meters.
        STRIPE_GAP: Gap between zebra stripes in meters.
    """
    
    STRIPE_WIDTH: float = 0.5
    STRIPE_GAP: float = 0.5
    
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize a new PedestrianCrossing instance.
        
        Args:
            config: Optional dictionary of configuration overrides. Supported keys:
                - segment_index: Road segment index (default: 0)
                - position: Position along segment 0.0-1.0 (default: 0.5)
                - width: Crossing width in meters (default: 4.0)
                - length: Crossing length in meters (default: 3.0)
                - min_green_time: Min vehicle green in seconds (default: 5.0)
                - pedestrian_green_time: Pedestrian phase duration (default: 8.0)
                - amber_time: Amber phase duration (default: 3.0)
                - all_red_time: All-red safety buffer (default: 1.0)
        """
        if config is None:
            config = {}
        self._set_default_config()
        for attr, val in config.items():
            setattr(self, attr, val)
        self._init_properties()

    def _set_default_config(self) -> None:
        """Set default configuration values for the crossing."""
        self.id: uuid.UUID = uuid.uuid4()
        self.segment_index: int = 0
        self.position: float = 0.5
        self.width: float = 4.0
        self.length: float = 3.0
        
        self.min_green_time: float = 5.0
        self.pedestrian_green_time: float = 8.0
        self.amber_time: float = 3.0
        self.all_red_time: float = 1.0
        
        self.state: CrossingState = CrossingState.VEHICLES_GO
        self.state_timer: float = 0.0
        self.request_pending: bool = False
        
        self.waiting_pedestrians: deque['Pedestrian'] = deque()
        self.crossing_pedestrians: list['Pedestrian'] = []

    def _init_properties(self) -> None:
        """
        Initialize crossing-specific properties.
        
        Override in subclasses to set crossing type and features.
        """
        self.crossing_type: CrossingType = CrossingType.GENERIC
        self.has_signals: bool = False
        self.has_button: bool = False
        self.has_sensors: bool = False

    def get_crossing_length(self) -> float:
        """
        Get the distance pedestrians must traverse.
        
        Returns:
            The crossing width in meters, representing the road width
            that pedestrians must cross.
        """
        return self.width

    def request_crossing(self) -> None:
        """
        Register a request for pedestrians to cross.
        
        Called when a pedestrian arrives and wants to cross. For signal-
        controlled crossings, this triggers the signal change sequence.
        """
        self.request_pending = True

    def add_pedestrian(self, pedestrian: 'Pedestrian') -> None:
        """
        Add a pedestrian to the waiting queue.
        
        Associates the pedestrian with this crossing and adds them to
        the queue of waiting pedestrians. Automatically requests a
        crossing phase for signal-controlled crossings.
        
        Args:
            pedestrian: The Pedestrian instance to add to this crossing.
        """
        pedestrian.crossing_id = self.id
        self.waiting_pedestrians.append(pedestrian)
        self.request_crossing()

    def can_pedestrians_cross(self) -> bool:
        """
        Check if pedestrians are currently permitted to cross.
        
        Returns:
            True if the signal state allows pedestrians to cross,
            False otherwise.
        """
        return self.state == CrossingState.PEDESTRIANS_GO

    def should_vehicles_stop(self) -> bool:
        """
        Check if vehicles should stop at this crossing.
        
        Returns:
            True if vehicles must stop due to signal state or
            pedestrian presence, False if vehicles may proceed.
        """
        return self.state in (
            CrossingState.PEDESTRIANS_GO,
            CrossingState.PEDESTRIANS_FINISHING,
            CrossingState.VEHICLES_STOPPING
        )

    def get_stop_distance(self, segment: 'Segment') -> float:
        """
        Calculate the distance along the segment where vehicles must stop.
        
        Determines the stopping point for vehicles approaching this crossing,
        positioned before the crossing with a safety margin.
        
        Args:
            segment: The road segment this crossing is on.
        
        Returns:
            Distance in meters from segment start to the stop line.
            Returns 0 if calculated position would be negative.
        """
        segment_length = segment.get_length()
        stop_position = self.position * segment_length - self.length / 2 - 2.0
        return max(0.0, stop_position)

    def update(self, dt: float) -> None:
        """
        Update the crossing state for one time step.
        
        Advances the state timer, processes the state machine logic,
        and updates all pedestrians at this crossing.
        
        Args:
            dt: Time step in seconds since last update.
        """
        self.state_timer += dt
        self._update_state_machine()
        self._update_pedestrians(dt)

    def _update_state_machine(self) -> None:
        """
        Process state machine transitions.
        
        Override in subclasses to implement crossing-specific signal
        timing and state transition logic.
        """
        pass

    def _update_pedestrians(self, dt: float) -> None:
        """
        Update all pedestrians associated with this crossing.
        
        Moves waiting pedestrians to crossing when permitted, updates
        positions of crossing pedestrians, and removes finished pedestrians.
        
        Args:
            dt: Time step in seconds for pedestrian position updates.
        """
        if self.can_pedestrians_cross():
            while self.waiting_pedestrians:
                ped = self.waiting_pedestrians.popleft()
                ped.start_crossing()
                self.crossing_pedestrians.append(ped)

        crossing_length = self.get_crossing_length()
        for ped in self.crossing_pedestrians:
            ped.update(dt, crossing_length)

        self.crossing_pedestrians = [
            p for p in self.crossing_pedestrians if not p.is_finished()
        ]

    def has_active_pedestrians(self) -> bool:
        """
        Check if there are any pedestrians at this crossing.
        
        Returns:
            True if there are pedestrians waiting or currently
            crossing, False if the crossing is clear.
        """
        return len(self.waiting_pedestrians) > 0 or len(self.crossing_pedestrians) > 0


class ZebraCrossing(PedestrianCrossing):
    """
    Zebra crossing with pedestrian priority.
    
    A zebra crossing (UK) or crosswalk (US) is an uncontrolled crossing
    marked with alternating black and white stripes. Pedestrians have
    priority once they step onto the crossing, and vehicles must stop
    when pedestrians are waiting or crossing.
    
    Features:
        - Black and white striped road markings
        - Belisha beacons (flashing amber globes) on posts
        - No traffic signals - pedestrian priority at all times
        - Vehicles must stop when pedestrians are present
    
    Attributes:
        has_belisha_beacons: Always True for zebra crossings.
    
    Example:
        >>> crossing = ZebraCrossing({'segment_index': 0, 'position': 0.5})
        >>> crossing.should_vehicles_stop()  # True if pedestrians present
    """
    
    def _init_properties(self) -> None:
        """Initialize zebra crossing specific properties."""
        self.crossing_type: CrossingType = CrossingType.ZEBRA
        self.has_signals: bool = False
        self.has_button: bool = False
        self.has_sensors: bool = False
        self.has_belisha_beacons: bool = True
        self.state = CrossingState.PEDESTRIANS_GO

    def should_vehicles_stop(self) -> bool:
        """
        Check if vehicles should stop at this zebra crossing.
        
        Unlike signal-controlled crossings, zebra crossings require
        vehicles to stop whenever pedestrians are present, regardless
        of signal state.
        
        Returns:
            True if any pedestrians are waiting or crossing,
            False if the crossing is clear.
        """
        return self.has_active_pedestrians()

    def can_pedestrians_cross(self) -> bool:
        """
        Check if pedestrians may cross.
        
        Pedestrians always have right of way at zebra crossings.
        
        Returns:
            Always returns True for zebra crossings.
        """
        return True

    def _update_state_machine(self) -> None:
        """
        Update state machine (no-op for zebra crossings).
        
        Zebra crossings have no signal phases - pedestrians always
        have priority, so no state transitions are needed.
        """
        pass


class PelicanCrossing(PedestrianCrossing):
    """
    Pelican (Pedestrian Light Controlled) crossing.
    
    A signal-controlled crossing activated by pedestrians pressing a
    button. Features a distinctive flashing amber phase that allows
    vehicles to proceed if the crossing is clear while pedestrians
    finish crossing.
    
    Signal Sequence:
        1. VEHICLES_GO: Green for vehicles, red for pedestrians
        2. VEHICLES_STOPPING: Amber for vehicles (after button press)
        3. PEDESTRIANS_GO: Red for vehicles, green for pedestrians
        4. PEDESTRIANS_FINISHING: Flashing amber for vehicles
        5. Return to VEHICLES_GO
    
    Features:
        - Push button for pedestrians to request crossing
        - Traffic signals for both vehicles and pedestrians
        - Flashing amber phase unique to Pelican crossings
        - Fixed crossing time regardless of pedestrian presence
    
    Attributes:
        flashing_amber_time: Duration of flashing amber phase in seconds.
    
    Example:
        >>> crossing = PelicanCrossing({'segment_index': 0, 'position': 0.5})
        >>> crossing.state
        <CrossingState.VEHICLES_GO: 'vehicles_go'>
    """
    
    def _init_properties(self) -> None:
        """Initialize Pelican crossing specific properties."""
        self.crossing_type: CrossingType = CrossingType.PELICAN
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_sensors: bool = False
        self.flashing_amber_time: float = 6.0

    def _update_state_machine(self) -> None:
        """
        Process Pelican crossing signal state transitions.
        
        Implements the standard Pelican crossing signal sequence with
        fixed timing for each phase. The flashing amber phase is unique
        to Pelican crossings and allows vehicles to proceed cautiously.
        """
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and self.state_timer >= self.min_green_time:
                self.state = CrossingState.VEHICLES_STOPPING
                self.state_timer = 0.0
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0.0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                self.state = CrossingState.PEDESTRIANS_FINISHING
                self.state_timer = 0.0
                
        elif self.state == CrossingState.PEDESTRIANS_FINISHING:
            if self.state_timer >= self.flashing_amber_time:
                self.state = CrossingState.VEHICLES_GO
                self.state_timer = 0.0


class PuffinCrossing(PedestrianCrossing):
    """
    Puffin (Pedestrian User-Friendly Intelligent) crossing.
    
    An intelligent signal-controlled crossing that uses sensors to detect
    pedestrians waiting and crossing. The crossing time automatically
    extends if pedestrians are still on the crossing, and cancels the
    request if a waiting pedestrian walks away.
    
    Signal Sequence:
        1. VEHICLES_GO: Green for vehicles, red for pedestrians
        2. VEHICLES_STOPPING: Amber for vehicles (if pedestrians detected)
        3. PEDESTRIANS_GO: Red for vehicles, green for pedestrians
           (extends automatically if pedestrians still crossing)
        4. Return to VEHICLES_GO (no flashing amber phase)
    
    Features:
        - Push button with above-ground pedestrian signals
        - Kerbside sensors detect waiting pedestrians
        - On-crossing sensors detect pedestrians still crossing
        - Automatic extension of crossing time for slow pedestrians
        - Request cancellation if pedestrian walks away
        - No flashing amber phase (unlike Pelican)
    
    Attributes:
        max_extension_time: Maximum additional time for slow pedestrians.
        total_extended_time: Current accumulated extension time.
    
    Example:
        >>> crossing = PuffinCrossing({'segment_index': 0, 'position': 0.5})
        >>> crossing.has_sensors
        True
    """
    
    def _init_properties(self) -> None:
        """Initialize Puffin crossing specific properties."""
        self.crossing_type: CrossingType = CrossingType.PUFFIN
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_sensors: bool = True
        self.max_extension_time: float = 15.0
        self.total_extended_time: float = 0.0

    def _update_state_machine(self) -> None:
        """
        Process Puffin crossing signal state transitions.
        
        Implements intelligent signal control that responds to pedestrian
        presence. Key differences from Pelican:
        - Cancels request if waiting pedestrian walks away
        - Extends crossing time if pedestrians still on crossing
        - No flashing amber phase
        """
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and len(self.waiting_pedestrians) > 0:
                if self.state_timer >= self.min_green_time:
                    self.state = CrossingState.VEHICLES_STOPPING
                    self.state_timer = 0.0
            elif self.request_pending and len(self.waiting_pedestrians) == 0:
                self.request_pending = False
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0.0
                self.total_extended_time = 0.0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                if len(self.crossing_pedestrians) > 0:
                    self.total_extended_time = self.state_timer - self.pedestrian_green_time
                    if self.total_extended_time >= self.max_extension_time:
                        self.state = CrossingState.VEHICLES_GO
                        self.state_timer = 0.0
                else:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0


class ToucanCrossing(PedestrianCrossing):
    """
    Toucan (Two-can cross) crossing for pedestrians and cyclists.
    
    A signal-controlled crossing designed to be shared by pedestrians
    and cyclists. Wider than standard crossings to accommodate cyclists,
    who are permitted to cycle across rather than dismount.
    
    Signal Sequence:
        1. VEHICLES_GO: Green for vehicles
        2. VEHICLES_STOPPING: Amber for vehicles
        3. PEDESTRIANS_GO: Red for vehicles, green for pedestrians/cyclists
           (extends if users still crossing, up to 5 seconds)
        4. Return to VEHICLES_GO (no flashing amber)
    
    Features:
        - Wider crossing area (default 6.0m vs standard 4.0m)
        - Shared use by pedestrians and cyclists
        - Cyclists may ride across (no need to dismount)
        - Green cycle symbol alongside pedestrian signal
        - Sensor detection for crossing users
    
    Attributes:
        allows_cyclists: Always True for Toucan crossings.
    
    Example:
        >>> crossing = ToucanCrossing({'segment_index': 0, 'position': 0.5})
        >>> crossing.width
        6.0
    """
    
    def _set_default_config(self) -> None:
        """Set Toucan-specific default dimensions."""
        super()._set_default_config()
        self.width: float = 6.0
        self.length: float = 4.0

    def _init_properties(self) -> None:
        """Initialize Toucan crossing specific properties."""
        self.crossing_type: CrossingType = CrossingType.TOUCAN
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_sensors: bool = True
        self.allows_cyclists: bool = True

    def _update_state_machine(self) -> None:
        """
        Process Toucan crossing signal state transitions.
        
        Similar to Puffin but with shorter maximum extension time
        since cyclists cross faster than pedestrians.
        """
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and self.state_timer >= self.min_green_time:
                self.state = CrossingState.VEHICLES_STOPPING
                self.state_timer = 0.0
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0.0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                if len(self.crossing_pedestrians) == 0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0
                elif self.state_timer >= self.pedestrian_green_time + 5.0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0


class PegasusCrossing(PedestrianCrossing):
    """
    Pegasus (Equestrian) crossing for pedestrians, cyclists, and horse riders.
    
    The widest type of signal-controlled crossing, designed to accommodate
    horse riders in addition to pedestrians and cyclists. Features include
    a higher-mounted button for riders and longer crossing times.
    
    Signal Sequence:
        1. VEHICLES_GO: Green for vehicles
        2. VEHICLES_STOPPING: Amber for vehicles
        3. PEDESTRIANS_GO: Red for vehicles, extended crossing time
           (extends if users still crossing, up to 8 seconds)
        4. Return to VEHICLES_GO
    
    Features:
        - Extra wide crossing (default 8.0m) for horses
        - Longer default crossing time (12 seconds)
        - Two push buttons: standard height and 2m height for riders
        - Sensor detection for all crossing users
        - Also known as Equestrian crossing
    
    Attributes:
        has_high_button: True, indicating presence of rider-height button.
        allows_horses: Always True for Pegasus crossings.
    
    Example:
        >>> crossing = PegasusCrossing({'segment_index': 0, 'position': 0.5})
        >>> crossing.width
        8.0
        >>> crossing.pedestrian_green_time
        12.0
    """
    
    def _set_default_config(self) -> None:
        """Set Pegasus-specific default dimensions and timing."""
        super()._set_default_config()
        self.width: float = 8.0
        self.length: float = 5.0
        self.pedestrian_green_time: float = 12.0

    def _init_properties(self) -> None:
        """Initialize Pegasus crossing specific properties."""
        self.crossing_type: CrossingType = CrossingType.PEGASUS
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_high_button: bool = True
        self.has_sensors: bool = True
        self.allows_horses: bool = True

    def _update_state_machine(self) -> None:
        """
        Process Pegasus crossing signal state transitions.
        
        Similar to Toucan but with longer extension time to accommodate
        the slower crossing speed of horses.
        """
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and self.state_timer >= self.min_green_time:
                self.state = CrossingState.VEHICLES_STOPPING
                self.state_timer = 0.0
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0.0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                if len(self.crossing_pedestrians) == 0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0
                elif self.state_timer >= self.pedestrian_green_time + 8.0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0
