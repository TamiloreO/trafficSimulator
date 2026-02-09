"""
Demonstration of all pedestrian crossing types in the traffic simulator.

Crossing Types:
1. ZEBRA - Basic striped crossing with belisha beacons, pedestrians have priority
2. PELICAN - Signal-controlled with push button (Pedestrian Light Controlled)
3. PUFFIN - Pedestrian User-Friendly Intelligent crossing with detection
4. TOUCAN - Two-can cross (pedestrians + cyclists)
5. PEGASUS - Equestrian crossing (includes horses)
6. TIGER - Parallel zebra and cycle crossing (unsignaled)
"""

from trafficSimulator import (
    Simulation, Window, VehicleGenerator, PedestrianGenerator,
    CrossingType
)


def create_demo():
    sim = Simulation()

    # Road parameters
    lane_space = 3.5
    road_length = 80

    # Create 6 parallel roads, each with a different crossing type
    road_spacing = 15
    
    # Road 1 - Zebra Crossing
    y_offset = 0
    sim.create_segment((-road_length, y_offset), (road_length, y_offset))
    zebra_idx = sim.create_zebra_crossing(segment_index=0, position=0.5)

    # Road 2 - Pelican Crossing
    y_offset = road_spacing
    sim.create_segment((-road_length, y_offset), (road_length, y_offset))
    pelican_idx = sim.create_pelican_crossing(
        segment_index=1, position=0.5,
        red_time=12.0, green_time=20.0
    )

    # Road 3 - Puffin Crossing
    y_offset = road_spacing * 2
    sim.create_segment((-road_length, y_offset), (road_length, y_offset))
    puffin_idx = sim.create_puffin_crossing(segment_index=2, position=0.5)

    # Road 4 - Toucan Crossing
    y_offset = road_spacing * 3
    sim.create_segment((-road_length, y_offset), (road_length, y_offset))
    toucan_idx = sim.create_toucan_crossing(segment_index=3, position=0.5)

    # Road 5 - Pegasus Crossing
    y_offset = road_spacing * 4
    sim.create_segment((-road_length, y_offset), (road_length, y_offset))
    pegasus_idx = sim.create_pegasus_crossing(segment_index=4, position=0.5)

    # Road 6 - Tiger Crossing
    y_offset = road_spacing * 5
    sim.create_segment((-road_length, y_offset), (road_length, y_offset))
    tiger_idx = sim.create_tiger_crossing(segment_index=5, position=0.5)

    # Add vehicle generators for each road
    for road_idx in range(6):
        vg = VehicleGenerator({
            'vehicle_rate': 8,
            'vehicles': [
                (1, {'path': [road_idx], 'v': 12.0}),
            ]
        })
        sim.add_vehicle_generator(vg)

    # Add pedestrian generators for each crossing
    # Zebra crossing pedestrians
    pg1 = PedestrianGenerator({
        'pedestrian_rate': 4,
        'crossings': [
            (1, zebra_idx, {}),
        ]
    })
    sim.add_pedestrian_generator(pg1)

    # Pelican crossing pedestrians
    pg2 = PedestrianGenerator({
        'pedestrian_rate': 5,
        'crossings': [
            (1, pelican_idx, {}),
        ]
    })
    sim.add_pedestrian_generator(pg2)

    # Puffin crossing pedestrians
    pg3 = PedestrianGenerator({
        'pedestrian_rate': 4,
        'crossings': [
            (1, puffin_idx, {}),
        ]
    })
    sim.add_pedestrian_generator(pg3)

    # Toucan crossing pedestrians (mix of walkers and faster cyclists)
    pg4 = PedestrianGenerator({
        'pedestrian_rate': 6,
        'crossings': [
            (2, toucan_idx, {'walk_speed': 1.4}),  # Pedestrians
            (1, toucan_idx, {'walk_speed': 2.5, 'color': (100, 200, 100)}),  # Cyclists (faster, green)
        ]
    })
    sim.add_pedestrian_generator(pg4)

    # Pegasus crossing pedestrians (mix of walkers and horse riders)
    pg5 = PedestrianGenerator({
        'pedestrian_rate': 3,
        'crossings': [
            (2, pegasus_idx, {'walk_speed': 1.4}),  # Pedestrians
            (1, pegasus_idx, {'walk_speed': 1.8, 'color': (139, 69, 19)}),  # Horse riders (brown)
        ]
    })
    sim.add_pedestrian_generator(pg5)

    # Tiger crossing pedestrians
    pg6 = PedestrianGenerator({
        'pedestrian_rate': 5,
        'crossings': [
            (2, tiger_idx, {'walk_speed': 1.4}),  # Pedestrians
            (1, tiger_idx, {'walk_speed': 2.2, 'color': (255, 200, 0)}),  # Cyclists (yellow)
        ]
    })
    sim.add_pedestrian_generator(pg6)

    return sim


if __name__ == "__main__":
    sim = create_demo()
    win = Window(sim)
    win.run()
    win.show()
