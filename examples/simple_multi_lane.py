"""
Simple multi-lane road example.

Demonstrates:
- Creating a multi-lane road using sim.create_road()
- Vehicles automatically changing lanes to overtake slower vehicles
"""
import trafficSimulator as ts

# Create simulation with lane changes enabled
sim = ts.Simulation({'enable_lane_changes': True})

# Create a 2-lane road (simpler than 3 lanes)
road, segment_indices = sim.create_road(
    start=(-80, 0),
    end=(80, 0),
    lane_count=2,
    lane_width=3.5
)

# Add a slow vehicle in lane 0
slow_vehicle = ts.Vehicle({
    'path': [segment_indices[0]],
    'v': 8.0,
    'v_max': 8.0,
    'x': 40
})
sim.add_vehicle(slow_vehicle)

# Add a fast vehicle behind it in the same lane
fast_vehicle = ts.Vehicle({
    'path': [segment_indices[0]],
    'v': 16.0,
    'v_max': 16.0,
    'x': 10
})
sim.add_vehicle(fast_vehicle)

# Run the visualization
win = ts.Window(sim)
win.run()
win.show()
