import dearpygui.dearpygui as dpg
import math
from typing import Tuple, Optional


class Window:
    def __init__(self, simulation):
        self.simulation = simulation

        self.zoom = 7
        self.offset = (0, 0)
        self.speed = 1

        self.is_running = False

        self.is_dragging = False
        self.old_offset = (0, 0)
        self.zoom_speed = 1
        
        # Visual settings
        self.lane_width = 3.5
        self.road_color = (180, 180, 220)
        self.lane_marking_color = (255, 255, 255)
        self.vehicle_color = (0, 0, 255)
        self.vehicle_changing_lane_color = (255, 165, 0)  # Orange for lane changing

        self.setup()
        self.setup_themes()
        self.create_windows()
        self.create_handlers()
        self.resize_windows()

    def setup(self):
        dpg.create_context()
        dpg.create_viewport(title="TrafficSimulator", width=1280, height=720)
        dpg.setup_dearpygui()

    def setup_themes(self):
        with dpg.theme() as global_theme:

            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (90, 90, 95))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (0, 91, 140))
            with dpg.theme_component(dpg.mvInputInt):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (90, 90, 95), category=dpg.mvThemeCat_Core)

        dpg.bind_theme(global_theme)

        with dpg.theme(tag="RunButtonTheme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (5, 150, 18))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (12, 207, 23))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (2, 120, 10))

        with dpg.theme(tag="StopButtonTheme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (150, 5, 18))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (207, 12, 23))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (120, 2, 10))


    def create_windows(self):
        dpg.add_window(
            tag="MainWindow",
            label="Simulation",
            no_close=True,
            no_collapse=True,
            no_resize=True,
            no_move=True
        )
        
        dpg.add_draw_node(tag="OverlayCanvas", parent="MainWindow")
        dpg.add_draw_node(tag="Canvas", parent="MainWindow")

        with dpg.window(
            tag="ControlsWindow",
            label="Controls",
            no_close=True,
            no_collapse=True,
            no_resize=True,
            no_move=True
        ):
            with dpg.collapsing_header(label="Simulation Control", default_open=True):

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Run", tag="RunStopButton", callback=self.toggle)
                    dpg.add_button(label="Next frame", callback=self.simulation.update)

                dpg.add_slider_int(tag="SpeedInput", label="Speed", min_value=1, max_value=100,default_value=1, callback=self.set_speed)
            
            with dpg.collapsing_header(label="Simulation Status", default_open=True):

                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("Status:")
                        dpg.add_text("_", tag="StatusText")

                    with dpg.table_row():
                        dpg.add_text("Time:")
                        dpg.add_text("_s", tag="TimeStatus")

                    with dpg.table_row():
                        dpg.add_text("Frame:")
                        dpg.add_text("_", tag="FrameStatus")
                    
                    with dpg.table_row():
                        dpg.add_text("Vehicles:")
                        dpg.add_text("_", tag="VehicleCount")
                    
                    with dpg.table_row():
                        dpg.add_text("Roads:")
                        dpg.add_text("_", tag="RoadCount")
            
            with dpg.collapsing_header(label="Statistics", default_open=True):
                
                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("Completed:")
                        dpg.add_text("0", tag="CompletedCount")
                    
                    with dpg.table_row():
                        dpg.add_text("Avg Travel Time:")
                        dpg.add_text("0.00s", tag="AvgTravelTime")
                    
                    with dpg.table_row():
                        dpg.add_text("Avg Speed:")
                        dpg.add_text("0.00 m/s", tag="AvgSpeed")
                    
                    with dpg.table_row():
                        dpg.add_text("Lane Changes:")
                        dpg.add_text("0", tag="LaneChangeCount")
            
            
            with dpg.collapsing_header(label="Camera Control", default_open=True):
    
                dpg.add_slider_float(tag="ZoomSlider", label="Zoom", min_value=0.1, max_value=100, default_value=self.zoom,callback=self.set_offset_zoom)            
                with dpg.group():
                    dpg.add_slider_float(tag="OffsetXSlider", label="X Offset", min_value=-100, max_value=100, default_value=self.offset[0], callback=self.set_offset_zoom)
                    dpg.add_slider_float(tag="OffsetYSlider", label="Y Offset", min_value=-100, max_value=100, default_value=self.offset[1], callback=self.set_offset_zoom)

    def resize_windows(self):
        width = dpg.get_viewport_width()
        height = dpg.get_viewport_height()

        dpg.set_item_width("ControlsWindow", 300)
        dpg.set_item_height("ControlsWindow", height-38)
        dpg.set_item_pos("ControlsWindow", (0, 0))

        dpg.set_item_width("MainWindow", width-315)
        dpg.set_item_height("MainWindow", height-38)
        dpg.set_item_pos("MainWindow", (300, 0))

    def create_handlers(self):
        with dpg.handler_registry():
            dpg.add_mouse_down_handler(callback=self.mouse_down)
            dpg.add_mouse_drag_handler(callback=self.mouse_drag)
            dpg.add_mouse_release_handler(callback=self.mouse_release)
            dpg.add_mouse_wheel_handler(callback=self.mouse_wheel)
        dpg.set_viewport_resize_callback(self.resize_windows)

    def update_panels(self):
        if self.is_running:
            dpg.set_value("StatusText", "Running")
            dpg.configure_item("StatusText", color=(0, 255, 0))
        else:
            dpg.set_value("StatusText", "Stopped")
            dpg.configure_item("StatusText", color=(255, 0, 0))
        
        dpg.set_value("TimeStatus", f"{self.simulation.t:.2f}s")
        dpg.set_value("FrameStatus", self.simulation.frame_count)
        dpg.set_value("VehicleCount", len(self.simulation.vehicles))
        dpg.set_value("RoadCount", len(self.simulation.roads))
        
        # Update statistics
        stats = self.simulation.statistics
        dpg.set_value("CompletedCount", stats.vehicles_completed)
        dpg.set_value("AvgTravelTime", f"{stats.average_travel_time:.2f}s")
        dpg.set_value("AvgSpeed", f"{stats.average_speed:.2f} m/s")
        dpg.set_value("LaneChangeCount", stats.lane_changes_completed)

    def mouse_down(self):
        if not self.is_dragging:
            if dpg.is_item_hovered("MainWindow"):
                self.is_dragging = True
                self.old_offset = self.offset
        
    def mouse_drag(self, sender, app_data):
        if self.is_dragging:
            self.offset = (
                self.old_offset[0] + app_data[1]/self.zoom,
                self.old_offset[1] + app_data[2]/self.zoom
            )

    def mouse_release(self):
        self.is_dragging = False

    def mouse_wheel(self, sender, app_data):
        if dpg.is_item_hovered("MainWindow"):
            self.zoom_speed = 1 + 0.01*app_data

    def update_inertial_zoom(self, clip=0.005):
        if self.zoom_speed != 1:
            self.zoom *= self.zoom_speed
            self.zoom_speed = 1 + (self.zoom_speed - 1) / 1.05
        if abs(self.zoom_speed - 1) < clip:
            self.zoom_speed = 1

    def update_offset_zoom_slider(self):
        dpg.set_value("ZoomSlider", self.zoom)
        dpg.set_value("OffsetXSlider", self.offset[0])
        dpg.set_value("OffsetYSlider", self.offset[1])

    def set_offset_zoom(self):
        self.zoom = dpg.get_value("ZoomSlider")
        self.offset = (dpg.get_value("OffsetXSlider"), dpg.get_value("OffsetYSlider"))

    def set_speed(self):
        self.speed = dpg.get_value("SpeedInput")


    def to_screen(self, x, y):
        return (
            self.canvas_width/2 + (x + self.offset[0] ) * self.zoom,
            self.canvas_height/2 + (y + self.offset[1]) * self.zoom
        )

    def to_world(self, x, y):
        return (
            (x - self.canvas_width/2) / self.zoom - self.offset[0],
            (y - self.canvas_height/2) / self.zoom - self.offset[1] 
        )
    
    @property
    def canvas_width(self):
        return dpg.get_item_width("MainWindow")

    @property
    def canvas_height(self):
        return dpg.get_item_height("MainWindow")


    def draw_bg(self, color=(250, 250, 250)):
        dpg.draw_rectangle(
            (-10, -10),
            (self.canvas_width+10, self.canvas_height+10), 
            thickness=0,
            fill=color,
            parent="OverlayCanvas"
        )

    def draw_axes(self, opacity=80):
        x_center, y_center = self.to_screen(0, 0)
        
        dpg.draw_line(
            (-10, y_center),
            (self.canvas_width+10, y_center),
            thickness=2, 
            color=(0, 0, 0, opacity),
            parent="OverlayCanvas"
        )
        dpg.draw_line(
            (x_center, -10),
            (x_center, self.canvas_height+10),
            thickness=2,
            color=(0, 0, 0, opacity),
            parent="OverlayCanvas"
        )

    def draw_grid(self, unit=10, opacity=50):
        x_start, y_start = self.to_world(0, 0)
        x_end, y_end = self.to_world(self.canvas_width, self.canvas_height)

        n_x = int(x_start / unit)
        n_y = int(y_start / unit)
        m_x = int(x_end / unit)+1
        m_y = int(y_end / unit)+1

        for i in range(n_x, m_x):
            dpg.draw_line(
                self.to_screen(unit*i, y_start - 10/self.zoom),
                self.to_screen(unit*i, y_end + 10/self.zoom),
                thickness=1,
                color=(0, 0, 0, opacity),
                parent="OverlayCanvas"
            )

        for i in range(n_y, m_y):
            dpg.draw_line(
                self.to_screen(x_start - 10/self.zoom, unit*i),
                self.to_screen(x_end + 10/self.zoom, unit*i),
                thickness=1,
                color=(0, 0, 0, opacity),
                parent="OverlayCanvas"
            )

    def draw_segments(self):
        """Draw all segments (lanes)."""
        for segment in self.simulation.segments:
            dpg.draw_polyline(
                segment.points, 
                color=self.road_color, 
                thickness=3.5*self.zoom, 
                parent="Canvas"
            )
    
    def draw_roads(self):
        """Draw multi-lane roads with lane markings."""
        drawn_segments = set()
        
        # Draw roads with proper lane markings
        for road_id, road in self.simulation.roads.items():
            for lane_index, lane in enumerate(road.lanes):
                # Draw the lane
                dpg.draw_polyline(
                    lane.points, 
                    color=self.road_color, 
                    thickness=3.5*self.zoom, 
                    parent="Canvas"
                )
                
                # Mark segment as drawn
                for seg_idx, rid in self.simulation.segment_to_road.items():
                    if rid == road_id:
                        lane_idx = self.simulation.segment_to_lane.get(seg_idx, 0)
                        if lane_idx == lane_index:
                            drawn_segments.add(seg_idx)
                
                # Draw lane markings between lanes
                if lane_index < road.lane_count - 1:
                    self._draw_lane_marking(lane, road.lanes[lane_index + 1])
        
        # Draw any remaining segments not part of roads
        for i, segment in enumerate(self.simulation.segments):
            if i not in drawn_segments:
                dpg.draw_polyline(
                    segment.points, 
                    color=self.road_color, 
                    thickness=3.5*self.zoom, 
                    parent="Canvas"
                )
    
    def _draw_lane_marking(self, lane1, lane2):
        """Draw dashed lane marking between two adjacent lanes."""
        num_points = min(len(lane1.points), len(lane2.points))
        dash_length = 3
        gap_length = 3
        
        for i in range(0, num_points - 1, dash_length + gap_length):
            end_i = min(i + dash_length, num_points - 1)
            
            points = []
            for j in range(i, end_i + 1):
                p1 = lane1.points[j]
                p2 = lane2.points[j]
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                points.append(mid)
            
            if len(points) >= 2:
                dpg.draw_polyline(
                    points,
                    color=self.lane_marking_color,
                    thickness=0.3 * self.zoom,
                    parent="Canvas"
                )

    def draw_vehicles(self):
        """Draw all vehicles with lane change visualization."""
        for segment_idx, segment in enumerate(self.simulation.segments):
            for vehicle_id in segment.vehicles:
                vehicle = self.simulation.vehicles[vehicle_id]
                self._draw_vehicle(segment, segment_idx, vehicle)
    
    def _draw_vehicle(self, segment, segment_idx: int, vehicle):
        """Draw a single vehicle with lane change offset if applicable."""
        progress = vehicle.x / segment.get_length()
        progress = max(0, min(1, progress))
        
        position = segment.get_point(progress)
        heading = segment.get_heading(progress)
        
        # Calculate lateral offset for lane changing vehicles
        lateral_offset = 0.0
        if vehicle.is_changing_lanes:
            lateral_offset = vehicle.lane_offset * self.lane_width
        
        # Apply lateral offset perpendicular to heading
        if lateral_offset != 0:
            offset_x = -math.sin(heading) * lateral_offset
            offset_y = math.cos(heading) * lateral_offset
            position = (position[0] + offset_x, position[1] + offset_y)
        
        # Choose color based on lane change state
        color = self.vehicle_changing_lane_color if vehicle.is_changing_lanes else self.vehicle_color
        
        node = dpg.add_draw_node(parent="Canvas")
        dpg.draw_line(
            (0, 0),
            (vehicle.l, 0),
            thickness=1.76*self.zoom,
            color=color,
            parent=node
        )

        translate = dpg.create_translation_matrix(position)
        rotate = dpg.create_rotation_matrix(heading, [0, 0, 1])
        dpg.apply_transform(node, translate*rotate)

    def apply_transformation(self):
        screen_center = dpg.create_translation_matrix([self.canvas_width/2, self.canvas_height/2, -0.01])
        translate = dpg.create_translation_matrix(self.offset)
        scale = dpg.create_scale_matrix([self.zoom, self.zoom])
        dpg.apply_transform("Canvas", screen_center*scale*translate)


    def render_loop(self):
        # Events
        self.update_inertial_zoom()
        self.update_offset_zoom_slider()

        # Remove old drawings
        dpg.delete_item("OverlayCanvas", children_only=True)
        dpg.delete_item("Canvas", children_only=True)
        
        # New drawings
        self.draw_bg()
        self.draw_axes()
        self.draw_grid(unit=10)
        self.draw_grid(unit=50)
        
        # Draw roads (handles both multi-lane roads and standalone segments)
        self.draw_roads()
        self.draw_vehicles()

        # Apply transformations
        self.apply_transformation()

        # Update panels
        self.update_panels()

        # Update simulation
        if self.is_running:
            self.simulation.run(self.speed)

    def show(self):
        dpg.show_viewport()
        while dpg.is_dearpygui_running():
            self.render_loop()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()

    def run(self):
        self.is_running = True
        dpg.set_item_label("RunStopButton", "Stop")
        dpg.bind_item_theme("RunStopButton", "StopButtonTheme")

    def stop(self):
        self.is_running = False
        dpg.set_item_label("RunStopButton", "Run")
        dpg.bind_item_theme("RunStopButton", "RunButtonTheme")

    def toggle(self):
        if self.is_running: self.stop()
        else: self.run()
