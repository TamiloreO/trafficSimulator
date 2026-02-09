from .pedestrian import Pedestrian
from numpy.random import randint, random


class PedestrianGenerator:
    """Generates pedestrians at crossings."""
    
    def __init__(self, config={}):
        self.set_default_config()
        for attr, val in config.items():
            setattr(self, attr, val)
        self.init_properties()

    def set_default_config(self):
        self.pedestrian_rate = 20  # Pedestrians per minute
        self.crossing_ids = []     # List of crossing IDs to spawn at
        self.pedestrians = [
            (1, {}),  # Weight and config for pedestrian types
        ]
        self.last_added_time = 0

    def init_properties(self):
        pass

    def generate_pedestrian(self):
        """Returns a random pedestrian with random config."""
        total = sum(pair[0] for pair in self.pedestrians)
        r = randint(1, total + 1)
        for (weight, config) in self.pedestrians:
            r -= weight
            if r <= 0:
                ped_config = config.copy()
                # Randomly choose direction (crossing from either side)
                if 'direction' not in ped_config:
                    ped_config['direction'] = 1 if random() > 0.5 else -1
                return Pedestrian(ped_config)
        return Pedestrian()

    def update(self, simulation):
        """Add pedestrians to crossings."""
        if not self.crossing_ids or not simulation.crossings:
            return
            
        if simulation.t - self.last_added_time >= 60 / self.pedestrian_rate:
            # Pick a random crossing from our list
            if self.crossing_ids:
                crossing_idx = self.crossing_ids[randint(0, len(self.crossing_ids))]
                if crossing_idx < len(simulation.crossings):
                    crossing = simulation.crossings[crossing_idx]
                    pedestrian = self.generate_pedestrian()
                    crossing.add_pedestrian(pedestrian)
                    simulation.add_pedestrian(pedestrian)
                    self.last_added_time = simulation.t
