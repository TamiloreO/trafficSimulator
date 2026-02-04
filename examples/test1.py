from trafficSimulator import *

sim = Simulation()

lane_space = 3.5
intersection_size = 12
length = 100

# SOUTH, EAST, NORTH, WEST

# Intersection in (segments 0-3)
sim.create_segment((lane_space/2, length+intersection_size/2), (lane_space/2, intersection_size/2))
sim.create_segment((length+intersection_size/2, -lane_space/2), (intersection_size/2, -lane_space/2))
sim.create_segment((-lane_space/2, -length-intersection_size/2), (-lane_space/2, -intersection_size/2))
sim.create_segment((-length-intersection_size/2, lane_space/2), (-intersection_size/2, lane_space/2))
# Intersection out (segments 4-7)
sim.create_segment((-lane_space/2, intersection_size/2), (-lane_space/2, length+intersection_size/2))
sim.create_segment((intersection_size/2, lane_space/2), (length+intersection_size/2, lane_space/2))
sim.create_segment((lane_space/2, -intersection_size/2), (lane_space/2, -length-intersection_size/2))
sim.create_segment((-intersection_size/2, -lane_space/2), (-length-intersection_size/2, -lane_space/2))
# Straight (segments 8-11)
sim.create_segment((lane_space/2, intersection_size/2), (lane_space/2, -intersection_size/2))
sim.create_segment((intersection_size/2, -lane_space/2), (-intersection_size/2, -lane_space/2))
sim.create_segment((-lane_space/2, -intersection_size/2), (-lane_space/2, intersection_size/2))
sim.create_segment((-intersection_size/2, lane_space/2), (intersection_size/2, lane_space/2))
# Right turn (segments 12-15)
sim.create_quadratic_bezier_curve((lane_space/2, intersection_size/2), (lane_space/2, lane_space/2), (intersection_size/2, lane_space/2))
sim.create_quadratic_bezier_curve((intersection_size/2, -lane_space/2), (lane_space/2, -lane_space/2), (lane_space/2, -intersection_size/2))
sim.create_quadratic_bezier_curve((-lane_space/2, -intersection_size/2), (-lane_space/2, -lane_space/2), (-intersection_size/2, -lane_space/2))
sim.create_quadratic_bezier_curve((-intersection_size/2, lane_space/2), (-lane_space/2, lane_space/2), (-lane_space/2, intersection_size/2))
# Left turn (segments 16-19)
sim.create_quadratic_bezier_curve((lane_space/2, intersection_size/2), (lane_space/2, -lane_space/2), (-intersection_size/2, -lane_space/2))
sim.create_quadratic_bezier_curve((intersection_size/2, -lane_space/2), (-lane_space/2, -lane_space/2), (-lane_space/2, intersection_size/2))
sim.create_quadratic_bezier_curve((-lane_space/2, -intersection_size/2), (-lane_space/2, lane_space/2), (intersection_size/2, lane_space/2))
sim.create_quadratic_bezier_curve((-intersection_size/2, lane_space/2), (lane_space/2, lane_space/2), (lane_space/2, -intersection_size/2))

# Create traffic lights at the end of incoming segments (0, 1, 2, 3)
# Position them slightly offset from the road for visibility
sim.create_traffic_light(segment_index=0, position=(lane_space/2 + 3, intersection_size/2))      # South
sim.create_traffic_light(segment_index=1, position=(intersection_size/2, -lane_space/2 - 3))    # East
sim.create_traffic_light(segment_index=2, position=(-lane_space/2 - 3, -intersection_size/2))   # North
sim.create_traffic_light(segment_index=3, position=(-intersection_size/2, lane_space/2 + 3))    # West

# Configure signal phases:
# Phase 0: North-South green (lights 0 and 2)
# Phase 1: East-West green (lights 1 and 3)
sim.create_signal_phases([
    {'duration': 15.0, 'green_lights': [0, 2], 'yellow_duration': 3.0},
    {'duration': 15.0, 'green_lights': [1, 3], 'yellow_duration': 3.0},
])

vg = VehicleGenerator({
    'vehicles': [
        (1, {'path': [0, 8, 6], 'v': 16.6}),
        (1, {'path': [0, 12, 5], 'v': 16.6}),
        (1, {'path': [1, 9, 7], 'v': 16.6}),
        (1, {'path': [2, 10, 4], 'v': 16.6}),
        (1, {'path': [3, 11, 5], 'v': 16.6}),
        ]
    })
sim.add_vehicle_generator(vg)

win = Window(sim)
win.run()
win.show()
