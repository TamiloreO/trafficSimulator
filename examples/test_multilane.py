from trafficSimulator import *

sim = Simulation()

lane_width = 3.5
length = 200

# Create a 3-lane road going right
# Lane 0 (top)
sim.create_segment((-length/2, lane_width), (length/2, lane_width))
# Lane 1 (middle)
sim.create_segment((-length/2, 0), (length/2, 0))
# Lane 2 (bottom)
sim.create_segment((-length/2, -lane_width), (length/2, -lane_width))

# Group segments into a Road
sim.create_road([0, 1, 2])

# Create a slow vehicle in the middle lane
slow_vehicle = Vehicle({'path': [1], 'x': 50, 'v': 5, 'v_max': 8})
sim.add_vehicle(slow_vehicle)

# Create a faster vehicle behind in middle lane (should try to change lanes)
fast_vehicle = Vehicle({'path': [1], 'x': 10, 'v': 16, 'v_max': 16.6})
sim.add_vehicle(fast_vehicle)

# Another vehicle to demonstrate
fast_vehicle2 = Vehicle({'path': [1], 'x': 0, 'v': 14, 'v_max': 16.6})
sim.add_vehicle(fast_vehicle2)

win = Window(sim)
win.run()
win.show()
