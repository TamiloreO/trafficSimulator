"""
Simple example with a single zebra crossing on a two-lane road.
Both lanes respect the crossing.
"""
import trafficSimulator as ts

sim = ts.Simulation()

# Create a simple two-lane road
# Segment 0: Left to right (bottom lane)
# Segment 1: Right to left (top lane)
sim.create_segment((-80, 2), (80, 2))
sim.create_segment((80, -2), (-80, -2))

# Add a zebra crossing in the middle that affects BOTH segments
# For segment 0 (left-to-right), position 0.5 is at x=0
# For segment 1 (right-to-left), position 0.5 is also at x=0
crossing_idx = sim.create_zebra_crossing(
    segment_index=0,
    position=0.5,
    additional_segments=[1],  # Also affects segment 1
    additional_positions=[0.5],  # Same position on segment 1
    width=6.0,
    length=3.0
)

# Vehicle generator for both lanes
sim.create_vehicle_generator(
    vehicle_rate=20,
    vehicles=[
        (1, {'path': [0], 'v': 14.0}),  # Left to right
        (1, {'path': [1], 'v': 14.0}),  # Right to left
    ]
)

# Pedestrian generator
sim.create_pedestrian_generator(
    pedestrian_rate=15,
    crossing_ids=[crossing_idx],
    pedestrians=[
        (1, {'speed': 1.2}),
        (1, {'speed': 1.5}),
    ]
)

win = ts.Window(sim)
win.run()
win.show()
