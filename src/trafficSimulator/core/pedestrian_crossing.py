"""
Pedestrian crossing module for traffic simulation.

This module provides various types of pedestrian crossings commonly found
in traffic systems, each with distinct behaviors and signal patterns.

Crossing Types:
    - ZebraCrossing: Unsignalized crossing where pedestrians have priority
    - PelicanCrossing: Signal-controlled with flashing amber phase
    - PuffinCrossing: Intelligent crossing with pedestrian detection sensors
    - ToucanCrossing: Shared crossing for pedestrians and cyclists
    - PegasusCrossing: Wide crossing accommodating horse riders

References:
    UK Highway Code for crossing specifications and behaviors.
"""

import uuid
from enum import Enum
from collections import deque
from typing import Any, Deque, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .pedestrian import Pedestrian
    from .geometry.segment import Segment


class CrossingState(Enum):
    """
    Enumeration of traffic signal states for pedestrian crossings.
    
    These states control the flow of both vehicular and pedestrian traffic
    at signal-controlled crossings.
    
    Attributes:
        VEHICLES_GO: Green light for vehicles, red for pedestrians.
                    Vehicles may proceed, pedestrians must wait.
        VEHICLES_STOPPING: Amber light for vehicles, red for pedestrians.
                          Vehicles should prepare to stop.
        PEDESTRIANS_GO: Red light for vehicles, green for pedestrians.
                       Pedestrians may cross, vehicles must stop.
        PEDESTRIANS_FINISHING: Flashing amber for vehicles (Pelican crossing).
                              Vehicles may proceed if crossing is clear.
    """
    VEHICLES_GO = 'vehicles_go'
    VEHICLES_STOPPING = 'vehicles_stopping'
    PEDESTRIANS_GO = 'pedestrians_go'
    PEDESTRIANS_FINISHING = 'pedestrians_finishing'


class CrossingType(Enum):
    """
    Enumeration of pedestrian crossing types.
    
    Each type has distinct visual appearance, signal patterns, and behavioral
    rules for both pedestrians and vehicles.
    
    Attributes:
        GENERIC: Basic crossing with no specific type designation.
        ZEBRA: Black and white striped crossing with pedestrian priority.
        PELICAN: Pedestrian Light Controlled crossing with push button.
        PUFFIN: Pedestrian User-Friendly Intelligent crossing with sensors.
        TOUCAN: Two-can cross - shared crossing for pedestrians and cyclists.
        PEGASUS: Equestrian crossing for horses, pedestrians, and cyclists.
    """
    GENERIC = 'generic'
    ZEBRA = 'zebra'
    PELICAN = 'pelican'
    PUFFIN = 'puffin'
    TOUCAN = 'toucan'
    PEGASUS = 'pegasus'


class PedestrianCrossing:
    """
    Base class for pedestrian crossings in traffic simulation.
    
    Provides common functionality for all crossing types including pedestrian
    queue management, state machine timing, and vehicle stop distance calculations.
    Subclasses implement specific crossing behaviors and signal patterns.
    
    Attributes:
        id (uuid.UUID): Unique identifier for this crossing.
        segment_index (int): Index of the road segment this crossing is on.
        position (float): Position along segment as fraction (0.0 to 1.0).
        width (float): Width of crossing perpendicular to road in meters.
        length (float): Length of crossing along road direction in meters.
        state (CrossingState): Current traffic signal state.
        crossing_type (CrossingType): Type of this crossing.
        waiting_pedestrians (Deque[Pedestrian]): Queue of pedestrians waiting to cross.
        crossing_pedestrians (List[Pedestrian]): Pedestrians currently on crossing.
    
    Timing Attributes:
        min_green_time (float): Minimum green time for vehicles in seconds.
        pedestrian_green_time (float): Duration of pedestrian crossing phase.
        amber_time (float): Duration of amber/warning phase.
        all_red_time (float): Safety buffer between phase changes.
    
    Example:
        >>> crossing = ZebraCrossing({'segment_index': 0, 'position': 0.5})
        >>> crossing.add_pedestrian(pedestrian)
        >>> crossing.update(dt=0.016)
    """
    
    # Class constants for stripe dimensions (used by subclasses)
    STRIPE_WIDTH: float = 0.5
    STRIPE_GAP: float = 0.5
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a new pedestrian crossing.
        
        Args:
            config: Optional dictionary of configuration parameters. Supported keys:
                   - 'segment_index' (int): Road segment index
                   - 'position' (float): Position along segment (0.0 to 1.0)
                   - 'width' (float): Crossing width in meters
                   - 'length' (float): Crossing length in meters
                   - 'min_green_time' (float): Minimum vehicle green time
                   - 'pedestrian_green_time' (float): Pedestrian phase duration
                   - 'amber_time' (float): Amber phase duration
        
        Raises:
            TypeError: If config is provided but is not a dictionary.
        """
        if config is None:
            config = {}
        
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dictionary, got {type(config).__name__}")
        
        self._set_default_config()
        
        for attr, val in config.items():
            setattr(self, attr, val)
        
        self._init_properties()

    def _set_default_config(self) -> None:
        """
        Set default configuration values for the crossing.
        
        Initializes all crossing attributes with safe default values.
        Called during __init__ before config overrides are applied.
        """
        self.id: uuid.UUID = uuid.uuid4()
        self.segment_index: int = 0  # Primary segment (kept for backward compatibility)
        self.segment_indices: List[int] = []  # All segments this crossing affects
        self.position: float = 0.5
        self.width: float = 4.0
        self.length: float = 3.0
        
        # Timing parameters (seconds)
        self.min_green_time: float = 5.0
        self.pedestrian_green_time: float = 8.0
        self.amber_time: float = 3.0
        self.all_red_time: float = 1.0
        
        # State management
        self.state: CrossingState = CrossingState.VEHICLES_GO
        self.state_timer: float = 0.0
        self.request_pending: bool = False
        
        # Pedestrian queues
        self.waiting_pedestrians: Deque['Pedestrian'] = deque()
        self.crossing_pedestrians: List['Pedestrian'] = []

    def _init_properties(self) -> None:
        """
        Initialize crossing-type-specific properties.
        
        Override in subclasses to set crossing_type and type-specific
        attributes like has_signals, has_button, has_sensors, etc.
        Also ensures segment_indices includes the primary segment_index.
        """
        self.crossing_type: CrossingType = CrossingType.GENERIC
        self.has_signals: bool = False
        self.has_button: bool = False
        self.has_sensors: bool = False
        
        # Ensure segment_indices is populated
        self._normalize_segment_indices()
    
    def _normalize_segment_indices(self) -> None:
        """
        Ensure segment_indices contains at least the primary segment_index.
        
        If segment_indices was not explicitly set, initializes it with
        the primary segment_index. If segment_indices was set, ensures
        segment_index is also in the list.
        """
        if not self.segment_indices:
            self.segment_indices = [self.segment_index]
        elif self.segment_index not in self.segment_indices:
            self.segment_indices.insert(0, self.segment_index)
    
    def affects_segment(self, segment_index: int) -> bool:
        """
        Check if this crossing affects a given segment.
        
        Args:
            segment_index: Index of the segment to check.
            
        Returns:
            True if vehicles on this segment should respect this crossing.
        """
        return segment_index in self.segment_indices

    def get_crossing_length(self) -> float:
        """
        Get the distance pedestrians must traverse to cross.
        
        Returns:
            The crossing width in meters, which is the distance a pedestrian
            must walk to get from one side to the other.
        """
        return self.width

    def request_crossing(self) -> None:
        """
        Register a request for pedestrian crossing phase.
        
        Called when a pedestrian arrives at the crossing and wants to cross.
        For signal-controlled crossings, this is equivalent to pressing the
        crossing button. Sets a flag that the state machine checks.
        """
        self.request_pending = True

    def add_pedestrian(self, pedestrian: 'Pedestrian') -> None:
        """
        Add a pedestrian to the waiting queue.
        
        Associates the pedestrian with this crossing and adds them to the
        queue of pedestrians waiting to cross. Automatically requests a
        crossing phase for signal-controlled crossings.
        
        Args:
            pedestrian: The Pedestrian instance to add to the queue.
        
        Note:
            The pedestrian's crossing_id attribute is set to this crossing's ID.
        """
        if pedestrian is None:
            return
        
        pedestrian.crossing_id = self.id
        self.waiting_pedestrians.append(pedestrian)
        self.request_crossing()

    def can_pedestrians_cross(self) -> bool:
        """
        Check if pedestrians are currently allowed to cross.
        
        Returns:
            True if the crossing state permits pedestrians to enter the
            crossing, False otherwise.
        
        Note:
            Override in subclasses for crossing-specific behavior.
            Zebra crossings always return True (pedestrian priority).
        """
        return self.state == CrossingState.PEDESTRIANS_GO

    def should_vehicles_stop(self) -> bool:
        """
        Check if vehicles should stop at this crossing.
        
        Returns:
            True if vehicles must stop before the crossing, False if they
            may proceed.
        
        Note:
            Override in subclasses for crossing-specific behavior.
            Considers multiple states where stopping is required.
        """
        return self.state in (
            CrossingState.PEDESTRIANS_GO,
            CrossingState.PEDESTRIANS_FINISHING,
            CrossingState.VEHICLES_STOPPING
        )

    def get_stop_distance(self, segment: 'Segment') -> float:
        """
        Calculate the distance along the segment where vehicles should stop.
        
        Computes the position before the crossing where vehicles must come
        to a stop when the crossing is active. Includes a safety buffer.
        
        Args:
            segment: The road segment containing this crossing.
        
        Returns:
            Distance in meters from the segment start to the stop line.
            Returns 0 if the calculated position would be negative.
        """
        if segment is None:
            return 0.0
        
        segment_length = segment.get_length()
        # Stop 2 meters before the crossing edge
        stop_position = self.position * segment_length - self.length / 2 - 2.0
        return max(0.0, stop_position)

    def update(self, dt: float) -> None:
        """
        Update the crossing state for one simulation step.
        
        Advances the state timer, updates the state machine, and moves
        pedestrians through the crossing process.
        
        Args:
            dt: Time elapsed since last update in seconds.
        """
        if dt <= 0:
            return
        
        self.state_timer += dt
        self._update_state_machine()
        self._update_pedestrians(dt)

    def _update_state_machine(self) -> None:
        """
        Update the traffic signal state machine.
        
        Override in subclasses to implement crossing-specific signal
        timing and state transitions. Base implementation does nothing.
        """
        pass

    def _update_pedestrians(self, dt: float) -> None:
        """
        Update all pedestrians associated with this crossing.
        
        Handles three pedestrian management tasks:
        1. Starts waiting pedestrians crossing when permitted
        2. Updates positions of pedestrians currently crossing
        3. Removes pedestrians who have finished crossing
        
        Args:
            dt: Time elapsed since last update in seconds.
        """
        # Start waiting pedestrians crossing if allowed
        if self.can_pedestrians_cross():
            while self.waiting_pedestrians:
                ped = self.waiting_pedestrians.popleft()
                ped.start_crossing()
                self.crossing_pedestrians.append(ped)

        # Update crossing pedestrians
        crossing_length = self.get_crossing_length()
        for ped in self.crossing_pedestrians:
            ped.update(dt, crossing_length)

        # Remove finished pedestrians
        self.crossing_pedestrians = [
            p for p in self.crossing_pedestrians if not p.is_finished()
        ]

    def has_active_pedestrians(self) -> bool:
        """
        Check if there are pedestrians waiting or currently crossing.
        
        Returns:
            True if any pedestrians are in the waiting queue or on the
            crossing surface, False if the crossing is empty.
        """
        return len(self.waiting_pedestrians) > 0 or len(self.crossing_pedestrians) > 0

    def __repr__(self) -> str:
        """
        Return a string representation of the crossing for debugging.
        
        Returns:
            String containing crossing type, position, and current state.
        """
        return (
            f"{self.__class__.__name__}("
            f"segment={self.segment_index}, "
            f"position={self.position:.2f}, "
            f"state={self.state.value})"
        )


class ZebraCrossing(PedestrianCrossing):
    """
    Zebra crossing with black and white stripes.
    
    A zebra crossing (known as a crosswalk in the US) is an unsignalized
    crossing where pedestrians have priority. Vehicles must stop when
    pedestrians are waiting or crossing. Typically marked with Belisha
    beacons (flashing amber globes on poles).
    
    Characteristics:
        - Black and white striped road markings
        - No traffic signals - pedestrians always have priority
        - Vehicles must yield when pedestrians are present
        - Often equipped with Belisha beacons for visibility
    
    Attributes:
        has_belisha_beacons (bool): Whether the crossing has amber beacons.
    
    Example:
        >>> zebra = ZebraCrossing({'segment_index': 0, 'position': 0.5})
        >>> zebra.can_pedestrians_cross()  # Always True
        True
    """
    
    def _init_properties(self) -> None:
        """
        Initialize zebra crossing specific properties.
        
        Sets crossing type to ZEBRA and configures for unsignalized operation
        with pedestrian priority and Belisha beacons.
        """
        self.crossing_type: CrossingType = CrossingType.ZEBRA
        self.has_signals: bool = False
        self.has_button: bool = False
        self.has_sensors: bool = False
        self.has_belisha_beacons: bool = True
        # Zebra crossings are always ready for pedestrians
        self.state = CrossingState.PEDESTRIANS_GO
        self._normalize_segment_indices()

    def should_vehicles_stop(self) -> bool:
        """
        Determine if vehicles should stop at the zebra crossing.
        
        At zebra crossings, vehicles must stop when pedestrians are present
        (either waiting or actively crossing). Unlike signal-controlled
        crossings, this is based on pedestrian presence, not signal state.
        
        Returns:
            True if any pedestrians are waiting or crossing, False if the
            crossing is clear and vehicles may proceed.
        """
        return self.has_active_pedestrians()

    def can_pedestrians_cross(self) -> bool:
        """
        Check if pedestrians may cross at the zebra crossing.
        
        At zebra crossings, pedestrians always have priority and may cross
        at any time. Vehicles are required to yield.
        
        Returns:
            Always returns True - pedestrians have unconditional priority.
        """
        return True

    def _update_state_machine(self) -> None:
        """
        Update state machine for zebra crossing.
        
        Zebra crossings don't have signal timing - they operate purely on
        pedestrian priority. This method is a no-op.
        """
        pass


class PelicanCrossing(PedestrianCrossing):
    """
    Pelican (Pedestrian Light Controlled) crossing.
    
    A signal-controlled crossing activated by pedestrians pressing a button.
    Features a distinctive flashing amber phase for vehicles while pedestrians
    finish crossing. The pedestrian signal shows a steady green man, then
    flashing green man during the clearance phase.
    
    Signal Sequence:
        1. VEHICLES_GO: Green for vehicles, red man for pedestrians
        2. VEHICLES_STOPPING: Amber for vehicles (button pressed)
        3. PEDESTRIANS_GO: Red for vehicles, green man for pedestrians
        4. PEDESTRIANS_FINISHING: Flashing amber for vehicles, flashing green man
        5. Return to VEHICLES_GO
    
    Characteristics:
        - Push button activated by pedestrians
        - Fixed pedestrian crossing time
        - Flashing amber phase allows vehicles to proceed if clear
        - Pedestrian signal visible from the opposite side of the road
    
    Attributes:
        flashing_amber_time (float): Duration of flashing amber phase in seconds.
    
    Example:
        >>> pelican = PelicanCrossing({'segment_index': 0, 'position': 0.5})
        >>> pelican.request_crossing()  # Simulates button press
    """
    
    def _init_properties(self) -> None:
        """
        Initialize Pelican crossing specific properties.
        
        Sets crossing type to PELICAN and configures for signal-controlled
        operation with push button and flashing amber phase.
        """
        self.crossing_type: CrossingType = CrossingType.PELICAN
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_sensors: bool = False
        self.flashing_amber_time: float = 6.0
        self._normalize_segment_indices()

    def _update_state_machine(self) -> None:
        """
        Update the Pelican crossing signal state machine.
        
        Implements the standard Pelican crossing signal sequence with
        minimum green times and a flashing amber clearance phase.
        
        State Transitions:
            VEHICLES_GO -> VEHICLES_STOPPING: When request pending and min green elapsed
            VEHICLES_STOPPING -> PEDESTRIANS_GO: After amber time
            PEDESTRIANS_GO -> PEDESTRIANS_FINISHING: After pedestrian green time
            PEDESTRIANS_FINISHING -> VEHICLES_GO: After flashing amber time
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
    
    An advanced signal-controlled crossing with sensors to detect pedestrians
    both waiting at the kerb and crossing the road. The sensors allow the
    crossing to extend the green phase for slow pedestrians and cancel
    requests if pedestrians walk away before the lights change.
    
    Intelligent Features:
        - Kerbside sensors detect waiting pedestrians
        - On-crossing sensors detect pedestrians still crossing
        - Automatically extends crossing time for slow pedestrians
        - Cancels request if pedestrian leaves before signal changes
        - No flashing amber phase (unlike Pelican)
    
    Signal Sequence:
        1. VEHICLES_GO: Green for vehicles, red for pedestrians
        2. VEHICLES_STOPPING: Amber for vehicles (request with pedestrian present)
        3. PEDESTRIANS_GO: Red for vehicles, green for pedestrians
           - Extends automatically while sensors detect pedestrians
        4. Return to VEHICLES_GO when sensors clear
    
    Attributes:
        max_extension_time (float): Maximum time to extend for slow pedestrians.
        total_extended_time (float): Accumulated extension time in current phase.
    
    Example:
        >>> puffin = PuffinCrossing({'segment_index': 0, 'position': 0.5})
        >>> # Slow pedestrian triggers automatic extension
    """
    
    def _init_properties(self) -> None:
        """
        Initialize Puffin crossing specific properties.
        
        Sets crossing type to PUFFIN and configures for intelligent
        signal-controlled operation with pedestrian detection sensors.
        """
        self.crossing_type: CrossingType = CrossingType.PUFFIN
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_sensors: bool = True
        self.max_extension_time: float = 15.0
        self.total_extended_time: float = 0.0
        self._normalize_segment_indices()

    def _update_state_machine(self) -> None:
        """
        Update the Puffin crossing signal state machine.
        
        Implements intelligent signal control with sensor-based decisions:
        - Only changes if pedestrians are actually detected waiting
        - Cancels request if pedestrian walks away
        - Extends pedestrian phase while sensors detect crossing pedestrians
        - Forces end after maximum extension time
        
        State Transitions:
            VEHICLES_GO -> VEHICLES_STOPPING: Request pending AND pedestrians detected
            VEHICLES_STOPPING -> PEDESTRIANS_GO: After amber time
            PEDESTRIANS_GO -> VEHICLES_GO: Sensors clear OR max extension reached
        """
        if self.state == CrossingState.VEHICLES_GO:
            # Only change if pedestrians are actually waiting (sensor check)
            if self.request_pending and len(self.waiting_pedestrians) > 0:
                if self.state_timer >= self.min_green_time:
                    self.state = CrossingState.VEHICLES_STOPPING
                    self.state_timer = 0.0
            elif self.request_pending and len(self.waiting_pedestrians) == 0:
                # Pedestrian walked away - cancel request
                self.request_pending = False
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0.0
                self.total_extended_time = 0.0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            # Base green time elapsed?
            if self.state_timer >= self.pedestrian_green_time:
                # Sensor detects pedestrians still on crossing - extend
                if len(self.crossing_pedestrians) > 0:
                    self.total_extended_time = self.state_timer - self.pedestrian_green_time
                    # Force end after max extension
                    if self.total_extended_time >= self.max_extension_time:
                        self.state = CrossingState.VEHICLES_GO
                        self.state_timer = 0.0
                else:
                    # No pedestrians on crossing, end phase
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0


class ToucanCrossing(PedestrianCrossing):
    """
    Toucan (Two-can cross) crossing for pedestrians and cyclists.
    
    A signal-controlled crossing designed to be shared by both pedestrians
    and cyclists. Wider than standard crossings to accommodate cyclists,
    who are permitted to ride across without dismounting.
    
    Characteristics:
        - Wider crossing (typically 4m vs 2.8m standard)
        - Cyclists may ride across without dismounting
        - Parallel green cycle and pedestrian signals
        - No flashing amber phase
        - Often part of cycle route networks
    
    Attributes:
        allows_cyclists (bool): Indicates cyclists may ride across.
    
    Note:
        Default width is 6.0m and length is 4.0m to accommodate cyclists.
    
    Example:
        >>> toucan = ToucanCrossing({'segment_index': 0, 'position': 0.5})
        >>> toucan.allows_cyclists
        True
    """
    
    def _set_default_config(self) -> None:
        """
        Set default configuration for Toucan crossing.
        
        Overrides base defaults with wider dimensions suitable for
        shared pedestrian and cyclist use.
        """
        super()._set_default_config()
        self.width: float = 6.0  # Wider for cyclists
        self.length: float = 4.0

    def _init_properties(self) -> None:
        """
        Initialize Toucan crossing specific properties.
        
        Sets crossing type to TOUCAN and configures for shared
        pedestrian/cyclist operation with sensors.
        """
        self.crossing_type: CrossingType = CrossingType.TOUCAN
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_sensors: bool = True
        self.allows_cyclists: bool = True
        self._normalize_segment_indices()

    def _update_state_machine(self) -> None:
        """
        Update the Toucan crossing signal state machine.
        
        Similar to Puffin crossing but without the request cancellation
        feature. Extends for pedestrians/cyclists still crossing.
        
        State Transitions:
            VEHICLES_GO -> VEHICLES_STOPPING: Request pending and min green elapsed
            VEHICLES_STOPPING -> PEDESTRIANS_GO: After amber time
            PEDESTRIANS_GO -> VEHICLES_GO: Clear or 5s after base time
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
                    # Force end after extension
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0


class PegasusCrossing(PedestrianCrossing):
    """
    Pegasus (Equestrian) crossing for horse riders, pedestrians, and cyclists.
    
    A specialized crossing designed to accommodate horse riders in addition
    to pedestrians and cyclists. Features include a higher-mounted push button
    for riders and extra width to safely accommodate horses.
    
    Characteristics:
        - Extra wide crossing (typically 4m or more)
        - Two push buttons: standard height and elevated for riders
        - Longer crossing time to accommodate horses
        - Often found near equestrian facilities or bridleways
        - Parallel signals for pedestrians, cyclists, and riders
    
    Attributes:
        has_high_button (bool): Whether elevated push button is present.
        allows_horses (bool): Indicates horses may cross.
    
    Note:
        Default width is 8.0m, length is 5.0m, and pedestrian green time
        is extended to 12.0 seconds.
    
    Example:
        >>> pegasus = PegasusCrossing({'segment_index': 0, 'position': 0.5})
        >>> pegasus.allows_horses
        True
    """
    
    def _set_default_config(self) -> None:
        """
        Set default configuration for Pegasus crossing.
        
        Overrides base defaults with wider dimensions and longer timing
        suitable for horse riders.
        """
        super()._set_default_config()
        self.width: float = 8.0  # Very wide for horses
        self.length: float = 5.0
        self.pedestrian_green_time: float = 12.0  # Longer crossing time

    def _init_properties(self) -> None:
        """
        Initialize Pegasus crossing specific properties.
        
        Sets crossing type to PEGASUS and configures for shared use
        including horse riders with elevated push button.
        """
        self.crossing_type: CrossingType = CrossingType.PEGASUS
        self.has_signals: bool = True
        self.has_button: bool = True
        self.has_high_button: bool = True  # For horse riders
        self.has_sensors: bool = True
        self.allows_horses: bool = True
        self._normalize_segment_indices()

    def _update_state_machine(self) -> None:
        """
        Update the Pegasus crossing signal state machine.
        
        Similar to Toucan crossing but with longer extension time to
        accommodate slower-moving horses.
        
        State Transitions:
            VEHICLES_GO -> VEHICLES_STOPPING: Request pending and min green elapsed
            VEHICLES_STOPPING -> PEDESTRIANS_GO: After amber time
            PEDESTRIANS_GO -> VEHICLES_GO: Clear or 8s after base time (longer for horses)
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
                    # Longer extension for horses
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0.0
