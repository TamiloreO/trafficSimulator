from trafficSimulator import *

sim = Simulation()

lane_space = 3.5
intersection_size = 12
length = 100

# SOUTH, EAST, NORTH, WEST

# Intersection in
sim.create_segment((lane_space/2, length+intersection_size/2), (lane_space/2, intersection_size/2))  # 0: South in
sim.create_segment((length+intersection_size/2, -lane_space/2), (intersection_size/2, -lane_space/2))  # 1: East in
sim.create_segment((-lane_space/2, -length-intersection_size/2), (-lane_space/2, -intersection_size/2))  # 2: North in
sim.create_segment((-length-intersection_size/2, lane_space/2), (-intersection_size/2, lane_space/2))  # 3: West in

# Intersection out
sim.create_segment((-lane_space/2, intersection_size/2), (-lane_space/2, length+intersection_size/2))  # 4: North out
sim.create_segment((intersection_size/2, lane_space/2), (length+intersection_size/2, lane_space/2))  # 5: East out
sim.create_segment((lane_space/2, -intersection_size/2), (lane_space/2, -length-intersection_size/2))  # 6: South out
sim.create_segment((-intersection_size/2, -lane_space/2), (-length-intersection_size/2, -lane_space/2))  # 7: West out

# Straight
sim.create_segment((lane_space/2, intersection_size/2), (lane_space/2, -intersection_size/2))  # 8: South to North
sim.create_segment((intersection_size/2, -lane_space/2), (-intersection_size/2, -lane_space/2))  # 9: East to West
sim.create_segment((-lane_space/2, -intersection_size/2), (-lane_space/2, intersection_size/2))  # 10: North to South
sim.create_segment((-intersection_size/2, lane_space/2), (intersection_size/2, lane_space/2))  # 11: West to East

# Right turn
sim.create_quadratic_bezier_curve((lane_space/2, intersection_size/2), (lane_space/2, lane_space/2), (intersection_size/2, lane_space/2))  # 12
sim.create_quadratic_bezier_curve((intersection_size/2, -lane_space/2), (lane_space/2, -lane_space/2), (lane_space/2, -intersection_size/2))  # 13
sim.create_quadratic_bezier_curve((-lane_space/2, -intersection_size/2), (-lane_space/2, -lane_space/2), (-intersection_size/2, -lane_space/2))  # 14
sim.create_quadratic_bezier_curve((-intersection_size/2, lane_space/2), (-lane_space/2, lane_space/2), (-lane_space/2, intersection_size/2))  # 15

# Left turn
sim.create_quadratic_bezier_curve((lane_space/2, intersection_size/2), (lane_space/2, -lane_space/2), (-intersection_size/2, -lane_space/2))  # 16
sim.create_quadratic_bezier_curve((intersection_size/2, -lane_space/2), (-lane_space/2, -lane_space/2), (-lane_space/2, intersection_size/2))  # 17
sim.create_quadratic_bezier_curve((-lane_space/2, -intersection_size/2), (-lane_space/2, lane_space/2), (intersection_size/2, lane_space/2))  # 18
sim.create_quadratic_bezier_curve((-intersection_size/2, lane_space/2), (lane_space/2, lane_space/2), (lane_space/2, -intersection_size/2))  # 19

# Create traffic light controller with factory
factory = TrafficLightFactory()
controller = factory.create_controller()

# Create traffic lights at the entrance of each approach to the intersection
# Position the lights just before the intersection, with stop_distance set to where cars should stop

# South approach (segment 0)
light_south = factory.create_traffic_light(
    position=(lane_space/2 + 3, intersection_size/2 + 5),
    segment_index=0,
    stop_distance=length - 5,  # Stop 5 units before the intersection
    initial_state=LightState.RED
)
controller.add_traffic_light(light_south, group_index=0)

# East approach (segment 1)
light_east = factory.create_traffic_light(
    position=(intersection_size/2 + 5, -lane_space/2 - 3),
    segment_index=1,
    stop_distance=length - 5,
    initial_state=LightState.RED
)
controller.add_traffic_light(light_east, group_index=1)

# North approach (segment 2)
light_north = factory.create_traffic_light(
    position=(-lane_space/2 - 3, -intersection_size/2 - 5),
    segment_index=2,
    stop_distance=length - 5,
    initial_state=LightState.RED
)
controller.add_traffic_light(light_north, group_index=0)

# West approach (segment 3)
light_west = factory.create_traffic_light(
    position=(-intersection_size/2 - 5, lane_space/2 + 3),
    segment_index=3,
    stop_distance=length - 5,
    initial_state=LightState.RED
)
controller.add_traffic_light(light_west, group_index=1)

# Set up phase sequence: North-South green, then East-West green
# Phase 1: North-South (lights 0 and 2)
phase_ns = factory.create_phase(duration=15, green_lights=[0, 2], yellow_duration=3)
# Phase 2: East-West (lights 1 and 3)
phase_ew = factory.create_phase(duration=15, green_lights=[1, 3], yellow_duration=3)

sequence = factory.create_phase_sequence([phase_ns, phase_ew])
controller.set_phase_sequence(sequence)

sim.set_traffic_light_controller(controller)

# Vehicle generators for each approach
vg_south = VehicleGenerator({
    'vehicle_rate': 8,
    'vehicles': [
        (1, {'path': [0, 8, 6], 'v': 16.6}),  # Go straight
        (1, {'path': [0, 12, 5], 'v': 16.6}),  # Turn right
    ]
})
sim.add_vehicle_generator(vg_south)

vg_north = VehicleGenerator({
    'vehicle_rate': 8,
    'vehicles': [
        (1, {'path': [2, 10, 4], 'v': 16.6}),  # Go straight
        (1, {'path': [2, 14, 7], 'v': 16.6}),  # Turn right
    ]
})
sim.add_vehicle_generator(vg_north)

vg_east = VehicleGenerator({
    'vehicle_rate': 6,
    'vehicles': [
        (1, {'path': [1, 9, 7], 'v': 16.6}),  # Go straight
        (1, {'path': [1, 13, 6], 'v': 16.6}),  # Turn right
    ]
})
sim.add_vehicle_generator(vg_east)

vg_west = VehicleGenerator({
    'vehicle_rate': 6,
    'vehicles': [
        (1, {'path': [3, 11, 5], 'v': 16.6}),  # Go straight
        (1, {'path': [3, 15, 4], 'v': 16.6}),  # Turn right
    ]
})
sim.add_vehicle_generator(vg_west)

win = Window(sim)
win.run()
win.show()
