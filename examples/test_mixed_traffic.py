"""
Example: Mixed Traffic Simulation
=================================

Demonstrates mixed traffic with different vehicle types:
- Cars (blue) - most common, moderate speed
- Trucks (orange) - less common, slower, longer
- Buses (green) - occasional, slower
- Motorcycles (pink) - fast, small

Run with: python test_mixed_traffic.py
"""
import trafficSimulator as ts

sim = ts.Simulation()

# Create a multi-lane road setup
sim.create_segment((-150, 3), (150, 3))    # Lane 1 (top)
sim.create_segment((-150, 0), (150, 0))    # Lane 2 (middle)
sim.create_segment((-150, -3), (150, -3))  # Lane 3 (bottom)
sim.create_segment((150, -6), (-150, -6))  # Opposite direction

# Add vehicle generator with mixed traffic
# Weights determine relative spawn probability
sim.create_vehicle_generator(
    vehicle_rate=30,
    vehicles=[
        # Cars - most common
        (10, {'path': [0], 'vehicle_type': 'car'}),
        (10, {'path': [1], 'vehicle_type': 'car'}),
        (10, {'path': [2], 'vehicle_type': 'car'}),
        
        # Trucks - less common, slower
        (2, {'path': [0], 'vehicle_type': 'truck'}),
        (2, {'path': [1], 'vehicle_type': 'truck'}),
        
        # Buses - occasional
        (1, {'path': [1], 'vehicle_type': 'bus'}),
        (1, {'path': [2], 'vehicle_type': 'bus'}),
        
        # Motorcycles - fast, small
        (3, {'path': [0], 'vehicle_type': 'motorcycle'}),
        (3, {'path': [1], 'vehicle_type': 'motorcycle'}),
        (3, {'path': [2], 'vehicle_type': 'motorcycle'}),
        
        # Opposite direction traffic
        (8, {'path': [3], 'vehicle_type': 'car'}),
        (2, {'path': [3], 'vehicle_type': 'truck'}),
        (1, {'path': [3], 'vehicle_type': 'bus'}),
    ]
)

# Show simulation visualization
win = ts.Window(sim)
win.run()
win.show()
