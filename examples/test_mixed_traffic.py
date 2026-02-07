"""
Example demonstrating mixed traffic with different vehicle types.
Shows cars (blue), trucks (orange), buses (green), and motorcycles (pink).
"""
import trafficSimulator as ts
from trafficSimulator import VehicleType

sim = ts.Simulation()

# Create a multi-lane road setup
sim.create_segment((-150, 3), (150, 3))    # Lane 1 (top)
sim.create_segment((-150, 0), (150, 0))    # Lane 2 (middle)
sim.create_segment((-150, -3), (150, -3))  # Lane 3 (bottom)
sim.create_segment((150, -6), (-150, -6))  # Opposite direction

# Add vehicle generator with mixed traffic
sim.create_vehicle_generator(
    vehicle_rate=30,
    vehicles=[
        # Cars (most common)
        (10, {'path': [0], 'vehicle_type': VehicleType.CAR}),
        (10, {'path': [1], 'vehicle_type': VehicleType.CAR}),
        (10, {'path': [2], 'vehicle_type': VehicleType.CAR}),
        
        # Trucks (less common, slower)
        (2, {'path': [0], 'vehicle_type': VehicleType.TRUCK}),
        (2, {'path': [1], 'vehicle_type': VehicleType.TRUCK}),
        
        # Buses (occasional)
        (1, {'path': [1], 'vehicle_type': VehicleType.BUS}),
        (1, {'path': [2], 'vehicle_type': VehicleType.BUS}),
        
        # Motorcycles (fast, small)
        (3, {'path': [0], 'vehicle_type': VehicleType.MOTORCYCLE}),
        (3, {'path': [1], 'vehicle_type': VehicleType.MOTORCYCLE}),
        (3, {'path': [2], 'vehicle_type': VehicleType.MOTORCYCLE}),
        
        # Opposite direction traffic
        (8, {'path': [3], 'vehicle_type': VehicleType.CAR}),
        (2, {'path': [3], 'vehicle_type': VehicleType.TRUCK}),
        (1, {'path': [3], 'vehicle_type': VehicleType.BUS}),
    ]
)

# Show simulation visualization
win = ts.Window(sim)
win.run()
win.show()
