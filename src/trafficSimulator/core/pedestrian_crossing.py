import uuid
from enum import Enum
from collections import deque


class CrossingState(Enum):
    VEHICLES_GO = 'vehicles_go'       # Green for vehicles, red for pedestrians
    VEHICLES_STOPPING = 'vehicles_stopping'  # Amber for vehicles
    PEDESTRIANS_GO = 'pedestrians_go'  # Red for vehicles, green for pedestrians
    PEDESTRIANS_FINISHING = 'pedestrians_finishing'  # Flashing for vehicles (Pelican)


class PedestrianCrossing:
    """Base class for pedestrian crossings."""
    
    STRIPE_WIDTH = 0.5  # Width of each zebra stripe
    STRIPE_GAP = 0.5    # Gap between stripes
    
    def __init__(self, config={}):
        self.set_default_config()
        for attr, val in config.items():
            setattr(self, attr, val)
        self.init_properties()

    def set_default_config(self):
        self.id = uuid.uuid4()
        self.segment_index = 0  # Which road segment this crossing is on
        self.position = 0.5     # Position along segment (0 to 1)
        self.width = 4.0        # Width of crossing (perpendicular to road)
        self.length = 3.0       # Length along road direction
        
        # Timing parameters (in seconds)
        self.min_green_time = 5.0      # Minimum time for vehicles
        self.pedestrian_green_time = 8.0  # Time for pedestrians to cross
        self.amber_time = 3.0          # Amber/warning time
        self.all_red_time = 1.0        # Safety buffer
        
        # State
        self.state = CrossingState.VEHICLES_GO
        self.state_timer = 0.0
        self.request_pending = False
        
        # Pedestrians waiting and crossing
        self.waiting_pedestrians = deque()
        self.crossing_pedestrians = []

    def init_properties(self):
        self.crossing_type = 'generic'
        self.has_signals = False
        self.has_button = False
        self.has_sensors = False

    def get_crossing_length(self):
        """Returns the width pedestrians need to cross (road width)."""
        return self.width

    def request_crossing(self):
        """Called when a pedestrian wants to cross."""
        self.request_pending = True

    def add_pedestrian(self, pedestrian):
        """Add a pedestrian to the waiting queue."""
        pedestrian.crossing_id = self.id
        self.waiting_pedestrians.append(pedestrian)
        self.request_crossing()

    def can_pedestrians_cross(self):
        """Check if pedestrians are allowed to cross."""
        return self.state == CrossingState.PEDESTRIANS_GO

    def should_vehicles_stop(self):
        """Check if vehicles should stop at this crossing."""
        return self.state in (CrossingState.PEDESTRIANS_GO, 
                              CrossingState.PEDESTRIANS_FINISHING,
                              CrossingState.VEHICLES_STOPPING)

    def get_stop_distance(self, segment):
        """Get the distance along the segment where vehicles should stop."""
        segment_length = segment.get_length()
        # Stop before the crossing
        stop_position = self.position * segment_length - self.length / 2 - 2.0
        return max(0, stop_position)

    def update(self, dt):
        """Update crossing state."""
        self.state_timer += dt
        self._update_state_machine()
        self._update_pedestrians(dt)

    def _update_state_machine(self):
        """Override in subclasses for specific behavior."""
        pass

    def _update_pedestrians(self, dt):
        """Update all pedestrians at this crossing."""
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
        self.crossing_pedestrians = [p for p in self.crossing_pedestrians 
                                      if not p.is_finished()]

    def has_active_pedestrians(self):
        """Check if there are pedestrians waiting or crossing."""
        return len(self.waiting_pedestrians) > 0 or len(self.crossing_pedestrians) > 0


class ZebraCrossing(PedestrianCrossing):
    """
    Zebra Crossing (UK) / Crosswalk (US)
    - Black and white stripes
    - Pedestrians have priority once on the crossing
    - Vehicles must stop when pedestrians are waiting/crossing
    - Often has Belisha beacons (flashing amber globes)
    """
    
    def init_properties(self):
        self.crossing_type = 'zebra'
        self.has_signals = False
        self.has_button = False
        self.has_sensors = False
        self.has_belisha_beacons = True
        # Zebra crossings are always ready for pedestrians
        self.state = CrossingState.PEDESTRIANS_GO

    def should_vehicles_stop(self):
        """Vehicles stop when pedestrians are present."""
        return self.has_active_pedestrians()

    def can_pedestrians_cross(self):
        """Pedestrians can always cross at zebra crossings."""
        return True

    def _update_state_machine(self):
        # Zebra crossings don't have a state machine - pedestrian priority
        pass


class PelicanCrossing(PedestrianCrossing):
    """
    Pelican Crossing (Pedestrian Light Controlled)
    - Signal controlled with push button
    - Has a flashing amber phase for vehicles while pedestrians finish
    - Fixed pedestrian crossing time
    """
    
    def init_properties(self):
        self.crossing_type = 'pelican'
        self.has_signals = True
        self.has_button = True
        self.has_sensors = False
        self.flashing_amber_time = 6.0  # Flashing phase duration

    def _update_state_machine(self):
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and self.state_timer >= self.min_green_time:
                self.state = CrossingState.VEHICLES_STOPPING
                self.state_timer = 0
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                self.state = CrossingState.PEDESTRIANS_FINISHING
                self.state_timer = 0
                
        elif self.state == CrossingState.PEDESTRIANS_FINISHING:
            # Flashing amber - vehicles can go if clear
            if self.state_timer >= self.flashing_amber_time:
                self.state = CrossingState.VEHICLES_GO
                self.state_timer = 0


class PuffinCrossing(PedestrianCrossing):
    """
    Puffin Crossing (Pedestrian User-Friendly Intelligent)
    - Has sensors to detect pedestrians waiting and crossing
    - Extends crossing time if pedestrians still on crossing
    - Cancels request if pedestrian walks away
    """
    
    def init_properties(self):
        self.crossing_type = 'puffin'
        self.has_signals = True
        self.has_button = True
        self.has_sensors = True
        self.max_extension_time = 15.0  # Maximum extension for slow pedestrians
        self.total_extended_time = 0.0

    def _update_state_machine(self):
        if self.state == CrossingState.VEHICLES_GO:
            # Only change if pedestrians are actually waiting (sensor check)
            if self.request_pending and len(self.waiting_pedestrians) > 0:
                if self.state_timer >= self.min_green_time:
                    self.state = CrossingState.VEHICLES_STOPPING
                    self.state_timer = 0
            elif self.request_pending and len(self.waiting_pedestrians) == 0:
                # Pedestrian walked away - cancel request
                self.request_pending = False
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0
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
                        self.state_timer = 0
                else:
                    # No pedestrians on crossing, end phase
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0


class ToucanCrossing(PedestrianCrossing):
    """
    Toucan Crossing (Two-can cross - pedestrians and cyclists)
    - Wider than other crossings to accommodate cyclists
    - Cyclists don't need to dismount
    - No flashing amber phase
    """
    
    def set_default_config(self):
        super().set_default_config()
        self.width = 6.0  # Wider for cyclists
        self.length = 4.0

    def init_properties(self):
        self.crossing_type = 'toucan'
        self.has_signals = True
        self.has_button = True
        self.has_sensors = True
        self.allows_cyclists = True

    def _update_state_machine(self):
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and self.state_timer >= self.min_green_time:
                self.state = CrossingState.VEHICLES_STOPPING
                self.state_timer = 0
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                if len(self.crossing_pedestrians) == 0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0
                elif self.state_timer >= self.pedestrian_green_time + 5.0:
                    # Force end after extension
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0


class PegasusCrossing(PedestrianCrossing):
    """
    Pegasus Crossing (also called Equestrian crossing)
    - For horse riders, pedestrians, and cyclists
    - Has higher push button for riders
    - Extra wide crossing
    """
    
    def set_default_config(self):
        super().set_default_config()
        self.width = 8.0  # Very wide for horses
        self.length = 5.0
        self.pedestrian_green_time = 12.0  # Longer crossing time

    def init_properties(self):
        self.crossing_type = 'pegasus'
        self.has_signals = True
        self.has_button = True
        self.has_high_button = True  # For horse riders
        self.has_sensors = True
        self.allows_horses = True

    def _update_state_machine(self):
        # Similar to Toucan but with longer timings
        if self.state == CrossingState.VEHICLES_GO:
            if self.request_pending and self.state_timer >= self.min_green_time:
                self.state = CrossingState.VEHICLES_STOPPING
                self.state_timer = 0
                
        elif self.state == CrossingState.VEHICLES_STOPPING:
            if self.state_timer >= self.amber_time:
                self.state = CrossingState.PEDESTRIANS_GO
                self.state_timer = 0
                self.request_pending = False
                
        elif self.state == CrossingState.PEDESTRIANS_GO:
            if self.state_timer >= self.pedestrian_green_time:
                if len(self.crossing_pedestrians) == 0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0
                elif self.state_timer >= self.pedestrian_green_time + 8.0:
                    self.state = CrossingState.VEHICLES_GO
                    self.state_timer = 0
