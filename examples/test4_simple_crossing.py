"""
Simple example with a single zebra crossing on a straight road.
"""
import trafficSimulator as ts

sim = ts.Simulation()

# Create a simple two-lane road
sim.create_segment((-80, 2), (80, 2))
sim.create_segment((80, -2), (-80, -2))

# Add a zebra crossing in the middle
crossing_idx = sim.create_zebra_crossing(
    segment_index=0,
    position=0.5,
    width=6.0,
    length=3.0
)

# Vehicle generator
sim.create_vehicle_generator(
    vehicle_rate=20,
    vehicles=[
        (1, {'path': [0], 'v': 14.0}),
        (1, {'path': [1], 'v': 14.0}),
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
