"""
Multi-lane road demonstration with lane changing behavior.

This example creates a 3-lane highway where vehicles will automatically
change lanes when:
1. There is a slower vehicle ahead
2. There is space available in an adjacent lane
3. The adjacent lane has sufficient gap (front and rear)
"""
import trafficSimulator as ts

sim = ts.Simulation({
    'enable_lane_changes': True,
    'lane_change_params': {
        'min_gap_front': 12.0,
        'min_gap_rear': 8.0,
        'safe_gap_front': 20.0,
        'safe_gap_rear': 15.0,
        'speed_threshold': 0.85,
        'lane_change_duration': 1.5,
        'cooldown_duration': 2.0,
    }
})

# Create a 3-lane highway
road, segment_indices = sim.create_road(
    start=(-100, 0),
    end=(100, 0),
    lane_count=3,
    lane_width=3.5
)

print(f"Created road '{road.name}' with {road.lane_count} lanes")
print(f"Segment indices: {segment_indices}")

# Create vehicle generator that spawns vehicles across all lanes
# with varying speeds to trigger lane changes
gen = ts.VehicleGenerator({
    'vehicle_rate': 25,
    'road_id': road.id,
    'lane_distribution': [
        (1, 0),  # Lane 0 (left)
        (2, 1),  # Lane 1 (middle) - more traffic
        (1, 2),  # Lane 2 (right)
    ],
    'vehicles': [
        # Fast vehicles (will want to overtake)
        (3, {'path': [segment_indices[0]], 'v': 16.6, 'v_max': 16.6}),
        (3, {'path': [segment_indices[1]], 'v': 16.6, 'v_max': 16.6}),
        (3, {'path': [segment_indices[2]], 'v': 16.6, 'v_max': 16.6}),
        
        # Slower vehicles (will be overtaken)
        (1, {'path': [segment_indices[0]], 'v': 10.0, 'v_max': 10.0}),
        (2, {'path': [segment_indices[1]], 'v': 11.0, 'v_max': 11.0}),
        (1, {'path': [segment_indices[2]], 'v': 9.0, 'v_max': 9.0}),
        
        # Trucks (slow, in right lane)
        (1, {'path': [segment_indices[2]], 'v': 8.0, 'v_max': 8.0, 'l': 8}),
    ]
})
sim.add_vehicle_generator(gen)

# Show simulation
win = ts.Window(sim)
win.run()
win.show()
