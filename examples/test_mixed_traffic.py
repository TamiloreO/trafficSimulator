"""
Mixed Traffic Scenario

Demonstrates different vehicle types (Car, Truck, Bus, Motorcycle)
moving on roads with varying characteristics:
- Motorcycles (red): Fast acceleration, high speed, small size
- Cars (blue): Standard performance
- Buses (green): Moderate speed, large size
- Trucks (brown): Slow acceleration, low speed, largest size

Run this example to visualize how different vehicle types behave
in traffic with varying speeds, accelerations, and following distances.
"""

from trafficSimulator import (
    Simulation,
    Window,
    VehicleType,
    VehicleFactory
)


def create_mixed_traffic_scenario():
    """Creates a simulation with mixed vehicle types on multiple roads."""
    sim = Simulation()

    # Create road segments - two parallel roads
    sim.create_segment((-120, 5), (120, 5))    # Road 0 - Upper lane (eastbound)
    sim.create_segment((120, -5), (-120, -5))  # Road 1 - Lower lane (westbound)

    # Create a curved road section
    sim.create_quadratic_bezier_curve((-120, 20), (0, 40), (120, 20))  # Road 2 - Curved upper

    # Create vehicle generator with mixed types
    sim.create_vehicle_generator(
        vehicle_rate=30,  # 30 vehicles per minute
        vehicles=[
            # Cars - most common (40%)
            (4, {'vehicle_type': VehicleType.CAR, 'path': [0], 'v': 12.0}),
            (4, {'vehicle_type': VehicleType.CAR, 'path': [1], 'v': 12.0}),

            # Motorcycles - fast and small (20%)
            (2, {'vehicle_type': VehicleType.MOTORCYCLE, 'path': [0], 'v': 15.0}),
            (2, {'vehicle_type': VehicleType.MOTORCYCLE, 'path': [2], 'v': 15.0}),

            # Trucks - slow and large (20%)
            (2, {'vehicle_type': VehicleType.TRUCK, 'path': [0], 'v': 8.0}),
            (2, {'vehicle_type': VehicleType.TRUCK, 'path': [1], 'v': 8.0}),

            # Buses - moderate (20%)
            (2, {'vehicle_type': VehicleType.BUS, 'path': [1], 'v': 10.0}),
            (2, {'vehicle_type': VehicleType.BUS, 'path': [2], 'v': 10.0}),
        ]
    )

    return sim


def create_highway_scenario():
    """Creates a highway scenario showing speed differences."""
    sim = Simulation()

    # Long highway segment
    sim.create_segment((-150, 0), (150, 0))

    # Pre-place some vehicles to show interaction
    # Slow truck at front
    truck = VehicleFactory.create_truck({'path': [0], 'x': 50, 'v': 10.0})
    sim.add_vehicle(truck)

    # Car behind truck
    car = VehicleFactory.create_car({'path': [0], 'x': 30, 'v': 14.0})
    sim.add_vehicle(car)

    # Motorcycle approaching
    motorcycle = VehicleFactory.create_motorcycle({'path': [0], 'x': 10, 'v': 16.0})
    sim.add_vehicle(motorcycle)

    # Bus at back
    bus = VehicleFactory.create_bus({'path': [0], 'x': -20, 'v': 12.0})
    sim.add_vehicle(bus)

    # Another car
    car2 = VehicleFactory.create_car({'path': [0], 'x': -50, 'v': 14.0})
    sim.add_vehicle(car2)

    return sim


def create_intersection_scenario():
    """Creates an intersection with mixed vehicle types."""
    sim = Simulation()

    lane_space = 3.5
    intersection_size = 14
    length = 80

    # Intersection incoming roads
    sim.create_segment(
        (lane_space/2, length+intersection_size/2),
        (lane_space/2, intersection_size/2)
    )  # 0 - South incoming
    sim.create_segment(
        (length+intersection_size/2, -lane_space/2),
        (intersection_size/2, -lane_space/2)
    )  # 1 - East incoming

    # Intersection outgoing roads
    sim.create_segment(
        (-lane_space/2, intersection_size/2),
        (-lane_space/2, length+intersection_size/2)
    )  # 2 - North outgoing
    sim.create_segment(
        (intersection_size/2, lane_space/2),
        (length+intersection_size/2, lane_space/2)
    )  # 3 - East outgoing

    # Through intersection
    sim.create_segment(
        (lane_space/2, intersection_size/2),
        (lane_space/2, -intersection_size/2)
    )  # 4 - South to North through
    sim.create_segment(
        (intersection_size/2, -lane_space/2),
        (-intersection_size/2, -lane_space/2)
    )  # 5 - East to West through

    # Right turns
    sim.create_quadratic_bezier_curve(
        (lane_space/2, intersection_size/2),
        (lane_space/2, lane_space/2),
        (intersection_size/2, lane_space/2)
    )  # 6 - South to East

    sim.create_vehicle_generator(
        vehicle_rate=20,
        vehicles=[
            # Cars going straight
            (3, {'vehicle_type': VehicleType.CAR, 'path': [0, 4], 'v': 12.0}),

            # Trucks turning right (slower on curves)
            (1, {'vehicle_type': VehicleType.TRUCK, 'path': [0, 6, 3], 'v': 8.0}),

            # Motorcycles going straight
            (2, {'vehicle_type': VehicleType.MOTORCYCLE, 'path': [1, 5], 'v': 14.0}),

            # Buses going straight
            (1, {'vehicle_type': VehicleType.BUS, 'path': [0, 4], 'v': 10.0}),
        ]
    )

    return sim


if __name__ == '__main__':
    # Choose which scenario to run
    # sim = create_mixed_traffic_scenario()
    sim = create_highway_scenario()
    # sim = create_intersection_scenario()

    win = Window(sim)
    win.run()
    win.show()
