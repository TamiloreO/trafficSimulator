"""
Simple road example with pedestrian crossings.
Based on test3.py but with added crossings.
"""
import trafficSimulator as ts

sim = ts.Simulation()

# Add road segments (two parallel roads in opposite directions)
sim.create_segment((-100, 3), (100, 2))
sim.create_segment((100, -3), (-100, -2))

# Add zebra crossings on both roads
zebra1 = sim.create_zebra_crossing(0, 0.3)
zebra2 = sim.create_zebra_crossing(1, 0.7)

# Add a pelican crossing 
pelican1 = sim.create_pelican_crossing(0, 0.7, red_time=12, green_time=20)

# Add vehicle generator
sim.create_vehicle_generator(
    vehicle_rate=15,
    vehicles=[
        (10, {'path': [0], 'v': 14.0}),
        (1, {'path': [0], 'v': 14.0, 'l': 7}),
        (10, {'path': [1], 'v': 14.0}),
        (1, {'path': [1], 'v': 14.0, 'l': 7})
    ]
)

# Add pedestrian generators
sim.create_pedestrian_generator(
    pedestrian_rate=8,
    crossings=[
        (1, zebra1, {}),
        (1, zebra2, {}),
        (2, pelican1, {}),  # More pedestrians at the pelican
    ]
)

# Show simulation visualization
win = ts.Window(sim)
win.show()
