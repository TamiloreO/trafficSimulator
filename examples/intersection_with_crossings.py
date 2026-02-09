"""
Intersection example with pedestrian crossings.
Shows a 4-way intersection with different crossing types on each approach.
"""

from trafficSimulator import (
    Simulation, Window, VehicleGenerator, PedestrianGenerator,
    CrossingType
)


def create_intersection_with_crossings():
    sim = Simulation()

    lane_space = 3.5
    intersection_size = 12
    length = 100

    # SOUTH, EAST, NORTH, WEST

    # Intersection incoming roads (segments 0-3)
    sim.create_segment((lane_space/2, length+intersection_size/2), (lane_space/2, intersection_size/2))
    sim.create_segment((length+intersection_size/2, -lane_space/2), (intersection_size/2, -lane_space/2))
    sim.create_segment((-lane_space/2, -length-intersection_size/2), (-lane_space/2, -intersection_size/2))
    sim.create_segment((-length-intersection_size/2, lane_space/2), (-intersection_size/2, lane_space/2))

    # Intersection outgoing roads (segments 4-7)
    sim.create_segment((-lane_space/2, intersection_size/2), (-lane_space/2, length+intersection_size/2))
    sim.create_segment((intersection_size/2, lane_space/2), (length+intersection_size/2, lane_space/2))
    sim.create_segment((lane_space/2, -intersection_size/2), (lane_space/2, -length-intersection_size/2))
    sim.create_segment((-intersection_size/2, -lane_space/2), (-length-intersection_size/2, -lane_space/2))

    # Straight through intersection (segments 8-11)
    sim.create_segment((lane_space/2, intersection_size/2), (lane_space/2, -intersection_size/2))
    sim.create_segment((intersection_size/2, -lane_space/2), (-intersection_size/2, -lane_space/2))
    sim.create_segment((-lane_space/2, -intersection_size/2), (-lane_space/2, intersection_size/2))
    sim.create_segment((-intersection_size/2, lane_space/2), (intersection_size/2, lane_space/2))

    # Right turns (segments 12-15)
    sim.create_quadratic_bezier_curve((lane_space/2, intersection_size/2), (lane_space/2, lane_space/2), (intersection_size/2, lane_space/2))
    sim.create_quadratic_bezier_curve((intersection_size/2, -lane_space/2), (lane_space/2, -lane_space/2), (lane_space/2, -intersection_size/2))
    sim.create_quadratic_bezier_curve((-lane_space/2, -intersection_size/2), (-lane_space/2, -lane_space/2), (-intersection_size/2, -lane_space/2))
    sim.create_quadratic_bezier_curve((-intersection_size/2, lane_space/2), (-lane_space/2, lane_space/2), (-lane_space/2, intersection_size/2))

    # Left turns (segments 16-19)
    sim.create_quadratic_bezier_curve((lane_space/2, intersection_size/2), (lane_space/2, -lane_space/2), (-intersection_size/2, -lane_space/2))
    sim.create_quadratic_bezier_curve((intersection_size/2, -lane_space/2), (-lane_space/2, -lane_space/2), (-lane_space/2, intersection_size/2))
    sim.create_quadratic_bezier_curve((-lane_space/2, -intersection_size/2), (-lane_space/2, lane_space/2), (intersection_size/2, lane_space/2))
    sim.create_quadratic_bezier_curve((-intersection_size/2, lane_space/2), (lane_space/2, lane_space/2), (lane_space/2, -intersection_size/2))

    # Add pedestrian crossings on the incoming roads
    # Each approach gets a different crossing type
    
    # South approach - Zebra crossing
    zebra_idx = sim.create_zebra_crossing(segment_index=0, position=0.15)
    
    # East approach - Pelican crossing  
    pelican_idx = sim.create_pelican_crossing(segment_index=1, position=0.15, red_time=10.0, green_time=25.0)
    
    # North approach - Puffin crossing
    puffin_idx = sim.create_puffin_crossing(segment_index=2, position=0.15)
    
    # West approach - Toucan crossing
    toucan_idx = sim.create_toucan_crossing(segment_index=3, position=0.15)

    # Vehicle generators
    vg1 = VehicleGenerator({
        'vehicle_rate': 10,
        'vehicles': [
            (1, {'path': [0, 8, 6], 'v': 16.6}),   # South to North
            (1, {'path': [0, 12, 5], 'v': 16.6}),  # South turn right to East
            (1, {'path': [0, 16, 7], 'v': 16.6}),  # South turn left to West
        ]
    })
    sim.add_vehicle_generator(vg1)

    vg2 = VehicleGenerator({
        'vehicle_rate': 8,
        'vehicles': [
            (1, {'path': [1, 9, 7], 'v': 16.6}),   # East to West
            (1, {'path': [1, 13, 6], 'v': 16.6}),  # East turn right to South
        ]
    })
    sim.add_vehicle_generator(vg2)

    vg3 = VehicleGenerator({
        'vehicle_rate': 8,
        'vehicles': [
            (1, {'path': [2, 10, 4], 'v': 16.6}),  # North to South
            (1, {'path': [2, 14, 7], 'v': 16.6}),  # North turn right to West
        ]
    })
    sim.add_vehicle_generator(vg3)

    vg4 = VehicleGenerator({
        'vehicle_rate': 8,
        'vehicles': [
            (1, {'path': [3, 11, 5], 'v': 16.6}),  # West to East
            (1, {'path': [3, 15, 4], 'v': 16.6}),  # West turn right to North
        ]
    })
    sim.add_vehicle_generator(vg4)

    # Pedestrian generators for each crossing
    pg1 = PedestrianGenerator({
        'pedestrian_rate': 3,
        'crossings': [(1, zebra_idx, {})]
    })
    sim.add_pedestrian_generator(pg1)

    pg2 = PedestrianGenerator({
        'pedestrian_rate': 4,
        'crossings': [(1, pelican_idx, {})]
    })
    sim.add_pedestrian_generator(pg2)

    pg3 = PedestrianGenerator({
        'pedestrian_rate': 3,
        'crossings': [(1, puffin_idx, {})]
    })
    sim.add_pedestrian_generator(pg3)

    pg4 = PedestrianGenerator({
        'pedestrian_rate': 4,
        'crossings': [
            (2, toucan_idx, {'walk_speed': 1.4}),  # Pedestrians
            (1, toucan_idx, {'walk_speed': 2.2, 'color': (100, 200, 100)}),  # Cyclists
        ]
    })
    sim.add_pedestrian_generator(pg4)

    return sim


if __name__ == "__main__":
    sim = create_intersection_with_crossings()
    win = Window(sim)
    win.run()
    win.show()
