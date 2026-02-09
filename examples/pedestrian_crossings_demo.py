"""
Demonstration of different pedestrian crossing types:
- Zebra Crossing: Pedestrians always have priority
- Pelican Crossing: Signal-controlled with flashing amber phase
- Puffin Crossing: Intelligent crossing with pedestrian sensors
- Toucan Crossing: Shared crossing for pedestrians and cyclists
- Pegasus Crossing: Wide crossing for horse riders

Each crossing affects both lanes of a two-way road.
"""
import trafficSimulator as ts

sim = ts.Simulation()

# Create parallel two-lane roads to demonstrate different crossing types
road_length = 150
road_spacing = 25
lane_width = 3.5
lane_offset = lane_width / 2

# Road 1 - Zebra Crossing (segments 0 and 1)
sim.create_segment((-road_length/2, lane_offset), (road_length/2, lane_offset))
sim.create_segment((road_length/2, -lane_offset), (-road_length/2, -lane_offset))

# Road 2 - Pelican Crossing (segments 2 and 3)
sim.create_segment((-road_length/2, road_spacing + lane_offset), (road_length/2, road_spacing + lane_offset))
sim.create_segment((road_length/2, road_spacing - lane_offset), (-road_length/2, road_spacing - lane_offset))

# Road 3 - Puffin Crossing (segments 4 and 5)
sim.create_segment((-road_length/2, 2*road_spacing + lane_offset), (road_length/2, 2*road_spacing + lane_offset))
sim.create_segment((road_length/2, 2*road_spacing - lane_offset), (-road_length/2, 2*road_spacing - lane_offset))

# Road 4 - Toucan Crossing (segments 6 and 7)
sim.create_segment((-road_length/2, 3*road_spacing + lane_offset), (road_length/2, 3*road_spacing + lane_offset))
sim.create_segment((road_length/2, 3*road_spacing - lane_offset), (-road_length/2, 3*road_spacing - lane_offset))

# Road 5 - Pegasus Crossing (segments 8 and 9)
sim.create_segment((-road_length/2, 4*road_spacing + lane_offset), (road_length/2, 4*road_spacing + lane_offset))
sim.create_segment((road_length/2, 4*road_spacing - lane_offset), (-road_length/2, 4*road_spacing - lane_offset))

# Add crossings at the middle of each road - each crossing affects BOTH lanes
zebra_idx = sim.create_zebra_crossing(
    segment_index=0, position=0.5,
    additional_segments=[1], additional_positions=[0.5],
    width=lane_width*2
)

pelican_idx = sim.create_pelican_crossing(
    segment_index=2, position=0.5,
    additional_segments=[3], additional_positions=[0.5],
    width=lane_width*2
)

puffin_idx = sim.create_puffin_crossing(
    segment_index=4, position=0.5,
    additional_segments=[5], additional_positions=[0.5],
    width=lane_width*2
)

toucan_idx = sim.create_toucan_crossing(
    segment_index=6, position=0.5,
    additional_segments=[7], additional_positions=[0.5],
    width=lane_width*2
)

pegasus_idx = sim.create_pegasus_crossing(
    segment_index=8, position=0.5,
    additional_segments=[9], additional_positions=[0.5],
    width=lane_width*2
)

# Vehicle generators for all roads (both directions)
sim.create_vehicle_generator(
    vehicle_rate=15,
    vehicles=[
        # Road 1 - both directions
        (1, {'path': [0], 'v': 12.0}),
        (1, {'path': [1], 'v': 12.0}),
        # Road 2 - both directions
        (1, {'path': [2], 'v': 12.0}),
        (1, {'path': [3], 'v': 12.0}),
        # Road 3 - both directions
        (1, {'path': [4], 'v': 12.0}),
        (1, {'path': [5], 'v': 12.0}),
        # Road 4 - both directions
        (1, {'path': [6], 'v': 12.0}),
        (1, {'path': [7], 'v': 12.0}),
        # Road 5 - both directions
        (1, {'path': [8], 'v': 12.0}),
        (1, {'path': [9], 'v': 12.0}),
    ]
)

# Pedestrian generators for each crossing type
sim.create_pedestrian_generator(
    pedestrian_rate=10,
    crossing_ids=[zebra_idx],
    pedestrians=[
        (1, {'speed': 1.2}),
        (1, {'speed': 1.5}),
        (1, {'speed': 0.8}),  # Slower pedestrian
    ]
)

sim.create_pedestrian_generator(
    pedestrian_rate=8,
    crossing_ids=[pelican_idx],
    pedestrians=[
        (1, {'speed': 1.4}),
    ]
)

sim.create_pedestrian_generator(
    pedestrian_rate=8,
    crossing_ids=[puffin_idx],
    pedestrians=[
        (1, {'speed': 1.4}),
        (1, {'speed': 0.6}),  # Slow pedestrian to test sensor extension
    ]
)

sim.create_pedestrian_generator(
    pedestrian_rate=6,
    crossing_ids=[toucan_idx],
    pedestrians=[
        (1, {'speed': 1.4}),  # Pedestrian
        (1, {'speed': 4.0}),  # Cyclist (faster)
    ]
)

sim.create_pedestrian_generator(
    pedestrian_rate=4,
    crossing_ids=[pegasus_idx],
    pedestrians=[
        (1, {'speed': 1.4}),  # Pedestrian
        (1, {'speed': 2.0}),  # Horse rider
    ]
)

# Create and show window
win = ts.Window(sim)
win.offset = (0, -50)  # Center view on the roads
win.zoom = 5
win.run()
win.show()
