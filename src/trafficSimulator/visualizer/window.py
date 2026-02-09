"""
Traffic simulation visualization window.

This module provides the Window class which renders the traffic simulation
using the DearPyGui library.
"""

import dearpygui.dearpygui as dpg
import math
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

from ..core.pedestrian_crossing import CrossingState, CrossingType

if TYPE_CHECKING:
    from ..core.simulation import Simulation
    from ..core.pedestrian_crossing import PedestrianCrossing
    from ..core.pedestrian import Pedestrian


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
                        dpg.add_text("0", tag="VehicleCount")

                    with dpg.table_row():
                        dpg.add_text("Pedestrians:")
                        dpg.add_text("0", tag="PedestrianCount")
            
            
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
        dpg.set_value("PedestrianCount", len(self.simulation.pedestrians))

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
        for segment in self.simulation.segments:
            dpg.draw_polyline(segment.points, color=(180, 180, 220), thickness=3.5*self.zoom, parent="Canvas")

    def draw_crossings(self):
        """Draw pedestrian crossings on the road."""
        for crossing in self.simulation.crossings:
            # Draw on primary segment
            self._draw_crossing_on_segment(crossing, crossing.segment_index, crossing.position)
            
            # Draw on additional segments
            additional_indices = getattr(crossing, 'additional_segment_indices', [])
            additional_positions = getattr(crossing, 'additional_segment_positions', [])
            
            for i, seg_idx in enumerate(additional_indices):
                if 0 <= seg_idx < len(self.simulation.segments):
                    pos = additional_positions[i] if i < len(additional_positions) else crossing.position
                    self._draw_crossing_on_segment(crossing, seg_idx, pos)

    def _draw_crossing_on_segment(self, crossing, segment_index: int, position: float):
        """Draw a crossing on a specific segment at a given position."""
        if segment_index < 0 or segment_index >= len(self.simulation.segments):
            return
            
        segment = self.simulation.segments[segment_index]
        
        # Get position and heading at crossing location
        center_pos = segment.get_point(position)
        heading = segment.get_heading(min(position, 0.99))
        
        # Calculate perpendicular direction for crossing width
        perp_angle = heading + math.pi / 2
        
        # Draw based on crossing type
        if crossing.crossing_type == CrossingType.ZEBRA:
            self._draw_zebra_stripes(center_pos, heading, perp_angle, crossing)
            self._draw_belisha_beacons(center_pos, perp_angle, crossing)
        elif crossing.crossing_type == CrossingType.PELICAN:
            self._draw_signal_crossing_stripes(center_pos, heading, perp_angle, crossing)
            self._draw_traffic_signals(center_pos, perp_angle, crossing)
        elif crossing.crossing_type == CrossingType.PUFFIN:
            self._draw_signal_crossing_stripes(center_pos, heading, perp_angle, crossing)
            self._draw_traffic_signals(center_pos, perp_angle, crossing)
            self._draw_sensors(center_pos, perp_angle, crossing)
        elif crossing.crossing_type == CrossingType.TOUCAN:
            self._draw_toucan_stripes(center_pos, heading, perp_angle, crossing)
            self._draw_traffic_signals(center_pos, perp_angle, crossing)
        elif crossing.crossing_type == CrossingType.PEGASUS:
            self._draw_pegasus_stripes(center_pos, heading, perp_angle, crossing)
            self._draw_traffic_signals(center_pos, perp_angle, crossing)
        else:
            self._draw_generic_crossing(center_pos, heading, perp_angle, crossing)

    def _draw_zebra_stripes(self, center_pos, heading, perp_angle, crossing):
        """Draw black and white zebra stripes."""
        stripe_width = 0.6
        stripe_gap = 0.6
        half_width = crossing.width / 2
        half_length = crossing.length / 2
        
        # Calculate number of stripes
        num_stripes = int(crossing.length / (stripe_width + stripe_gap))
        
        for i in range(num_stripes + 1):
            # Position along road direction
            offset_along = -half_length + i * (stripe_width + stripe_gap)
            
            # Calculate stripe corners
            cx = center_pos[0] + offset_along * math.cos(heading)
            cy = center_pos[1] + offset_along * math.sin(heading)
            
            # Draw white stripe
            stripe_points = self._get_stripe_corners(
                cx, cy, heading, perp_angle, stripe_width, half_width
            )
            
            node = dpg.add_draw_node(parent="Canvas")
            dpg.draw_polygon(
                stripe_points,
                color=(255, 255, 255),
                fill=(255, 255, 255),
                thickness=1,
                parent=node
            )

    def _draw_signal_crossing_stripes(self, center_pos, heading, perp_angle, crossing):
        """Draw parallel dashed lines for signal-controlled crossings (stud pattern)."""
        half_width = crossing.width / 2
        half_length = crossing.length / 2
        
        # Draw two parallel lines of studs/dashes
        stud_size = 0.4
        stud_gap = 0.8
        num_studs = int(crossing.width / (stud_size + stud_gap))
        
        for side in [-1, 1]:  # Both edges of crossing
            line_offset = half_length * side * 0.8
            
            for i in range(num_studs + 1):
                stud_pos = -half_width + i * (stud_size + stud_gap)
                
                sx = center_pos[0] + line_offset * math.cos(heading) + stud_pos * math.cos(perp_angle)
                sy = center_pos[1] + line_offset * math.sin(heading) + stud_pos * math.sin(perp_angle)
                
                node = dpg.add_draw_node(parent="Canvas")
                dpg.draw_circle(
                    (sx, sy),
                    stud_size / 2,
                    color=(255, 255, 255),
                    fill=(255, 255, 255),
                    parent=node
                )

    def _draw_toucan_stripes(self, center_pos, heading, perp_angle, crossing):
        """Draw wider crossing with cycle symbols."""
        self._draw_signal_crossing_stripes(center_pos, heading, perp_angle, crossing)
        
        # Draw cycle lane indicator (simple dashed line in middle)
        half_width = crossing.width / 2
        dash_length = 0.5
        dash_gap = 0.5
        num_dashes = int(crossing.width / (dash_length + dash_gap))
        
        for i in range(num_dashes + 1):
            dash_pos = -half_width + i * (dash_length + dash_gap)
            
            dx1 = center_pos[0] + dash_pos * math.cos(perp_angle)
            dy1 = center_pos[1] + dash_pos * math.sin(perp_angle)
            dx2 = dx1 + dash_length * math.cos(perp_angle)
            dy2 = dy1 + dash_length * math.sin(perp_angle)
            
            node = dpg.add_draw_node(parent="Canvas")
            dpg.draw_line(
                (dx1, dy1),
                (dx2, dy2),
                color=(0, 200, 0),
                thickness=0.3 * self.zoom,
                parent=node
            )

    def _draw_pegasus_stripes(self, center_pos, heading, perp_angle, crossing):
        """Draw extra-wide crossing for horses."""
        self._draw_signal_crossing_stripes(center_pos, heading, perp_angle, crossing)
        
        # Draw additional boundary lines for horse lane
        half_width = crossing.width / 2
        half_length = crossing.length / 2
        
        for side in [-1, 1]:
            edge_offset = half_width * side
            
            x1 = center_pos[0] - half_length * math.cos(heading) + edge_offset * math.cos(perp_angle)
            y1 = center_pos[1] - half_length * math.sin(heading) + edge_offset * math.sin(perp_angle)
            x2 = center_pos[0] + half_length * math.cos(heading) + edge_offset * math.cos(perp_angle)
            y2 = center_pos[1] + half_length * math.sin(heading) + edge_offset * math.sin(perp_angle)
            
            node = dpg.add_draw_node(parent="Canvas")
            dpg.draw_line(
                (x1, y1),
                (x2, y2),
                color=(255, 200, 0),
                thickness=0.2 * self.zoom,
                parent=node
            )

    def _draw_generic_crossing(self, center_pos, heading, perp_angle, crossing):
        """Fallback crossing rendering."""
        self._draw_zebra_stripes(center_pos, heading, perp_angle, crossing)

    def _get_stripe_corners(self, cx, cy, heading, perp_angle, width, half_road_width):
        """Calculate the four corners of a stripe rectangle."""
        hw = width / 2
        
        corners = []
        for along in [-hw, hw]:
            for perp in [-half_road_width, half_road_width]:
                x = cx + along * math.cos(heading) + perp * math.cos(perp_angle)
                y = cy + along * math.sin(heading) + perp * math.sin(perp_angle)
                corners.append((x, y))
        
        # Reorder for proper polygon drawing
        return [corners[0], corners[1], corners[3], corners[2]]

    def _draw_belisha_beacons(self, center_pos, perp_angle, crossing):
        """Draw flashing amber beacons for zebra crossings."""
        half_width = crossing.width / 2 + 1.0  # Slightly outside crossing
        
        # Flashing effect based on time
        flash = int(self.simulation.t * 2) % 2 == 0
        beacon_color = (255, 200, 0) if flash else (200, 150, 0)
        
        for side in [-1, 1]:
            bx = center_pos[0] + (half_width + 0.5) * side * math.cos(perp_angle)
            by = center_pos[1] + (half_width + 0.5) * side * math.sin(perp_angle)
            
            node = dpg.add_draw_node(parent="Canvas")
            # Pole
            dpg.draw_line(
                (bx, by),
                (bx, by - 2),
                color=(50, 50, 50),
                thickness=0.15 * self.zoom,
                parent=node
            )
            # Beacon globe
            dpg.draw_circle(
                (bx, by - 2.5),
                0.5,
                color=beacon_color,
                fill=beacon_color,
                parent=node
            )

    def _draw_traffic_signals(self, center_pos, perp_angle, crossing):
        """Draw traffic light signals."""
        half_width = crossing.width / 2 + 1.5
        
        # Determine signal colors based on state
        if crossing.state == CrossingState.VEHICLES_GO:
            vehicle_color = (0, 255, 0)  # Green
            ped_color = (255, 0, 0)      # Red
        elif crossing.state == CrossingState.VEHICLES_STOPPING:
            vehicle_color = (255, 200, 0)  # Amber
            ped_color = (255, 0, 0)
        elif crossing.state == CrossingState.PEDESTRIANS_GO:
            vehicle_color = (255, 0, 0)    # Red
            ped_color = (0, 255, 0)        # Green
        elif crossing.state == CrossingState.PEDESTRIANS_FINISHING:
            # Flashing amber for Pelican
            flash = int(self.simulation.t * 2) % 2 == 0
            vehicle_color = (255, 200, 0) if flash else (100, 80, 0)
            ped_color = (255, 0, 0)
        else:
            vehicle_color = (100, 100, 100)
            ped_color = (100, 100, 100)
        
        for side in [-1, 1]:
            sx = center_pos[0] + (half_width + 0.5) * side * math.cos(perp_angle)
            sy = center_pos[1] + (half_width + 0.5) * side * math.sin(perp_angle)
            
            node = dpg.add_draw_node(parent="Canvas")
            
            # Signal pole
            dpg.draw_line(
                (sx, sy),
                (sx, sy - 3),
                color=(50, 50, 50),
                thickness=0.2 * self.zoom,
                parent=node
            )
            
            # Signal box
            dpg.draw_rectangle(
                (sx - 0.4, sy - 4.5),
                (sx + 0.4, sy - 2.5),
                color=(30, 30, 30),
                fill=(30, 30, 30),
                parent=node
            )
            
            # Vehicle signal light
            dpg.draw_circle(
                (sx, sy - 3.8),
                0.25,
                color=vehicle_color,
                fill=vehicle_color,
                parent=node
            )
            
            # Pedestrian signal (on opposite side)
            ped_sx = center_pos[0] + half_width * (-side) * math.cos(perp_angle)
            ped_sy = center_pos[1] + half_width * (-side) * math.sin(perp_angle)
            
            dpg.draw_rectangle(
                (ped_sx - 0.3, ped_sy - 1.8),
                (ped_sx + 0.3, ped_sy - 0.8),
                color=(30, 30, 30),
                fill=(30, 30, 30),
                parent=node
            )
            dpg.draw_circle(
                (ped_sx, ped_sy - 1.3),
                0.2,
                color=ped_color,
                fill=ped_color,
                parent=node
            )

    def _draw_sensors(self, center_pos, perp_angle, crossing):
        """Draw sensor indicators for Puffin crossings."""
        half_width = crossing.width / 2
        
        # Draw small sensor boxes at crossing edges
        for side in [-1, 1]:
            sx = center_pos[0] + (half_width + 0.3) * side * math.cos(perp_angle)
            sy = center_pos[1] + (half_width + 0.3) * side * math.sin(perp_angle)
            
            # Sensor active indicator
            active = len(crossing.waiting_pedestrians) > 0 or len(crossing.crossing_pedestrians) > 0
            sensor_color = (0, 200, 255) if active else (50, 50, 80)
            
            node = dpg.add_draw_node(parent="Canvas")
            dpg.draw_rectangle(
                (sx - 0.2, sy - 0.2),
                (sx + 0.2, sy + 0.2),
                color=sensor_color,
                fill=sensor_color,
                parent=node
            )

    def draw_pedestrians(self):
        """Draw pedestrians at crossings."""
        for crossing in self.simulation.crossings:
            segment = self.simulation.segments[crossing.segment_index]
            center_pos = segment.get_point(crossing.position)
            heading = segment.get_heading(min(crossing.position, 0.99))
            perp_angle = heading + math.pi / 2
            
            half_width = crossing.width / 2
            
            # Draw waiting pedestrians (clustered at edges)
            wait_offset = 0
            for i, ped in enumerate(crossing.waiting_pedestrians):
                # Position pedestrians in a small group at the edge
                row = i // 3
                col = i % 3
                
                if ped.direction == 1:
                    edge = -half_width - 1.0 - row * 0.8
                else:
                    edge = half_width + 1.0 + row * 0.8
                
                px = center_pos[0] + edge * math.cos(perp_angle) + (col - 1) * 0.6 * math.cos(heading)
                py = center_pos[1] + edge * math.sin(perp_angle) + (col - 1) * 0.6 * math.sin(heading)
                
                self._draw_pedestrian(px, py, ped.color)
            
            # Draw crossing pedestrians
            for ped in crossing.crossing_pedestrians:
                # Interpolate position across the crossing
                cross_pos = -half_width + ped.x * crossing.width
                
                px = center_pos[0] + cross_pos * math.cos(perp_angle)
                py = center_pos[1] + cross_pos * math.sin(perp_angle)
                
                self._draw_pedestrian(px, py, ped.color)

    def _draw_pedestrian(self, x, y, color=(50, 50, 50)):
        """Draw a single pedestrian as a simple figure."""
        node = dpg.add_draw_node(parent="Canvas")
        
        # Head
        dpg.draw_circle(
            (x, y - 0.8),
            0.25,
            color=color,
            fill=color,
            parent=node
        )
        
        # Body
        dpg.draw_line(
            (x, y - 0.5),
            (x, y + 0.3),
            color=color,
            thickness=0.15 * self.zoom,
            parent=node
        )
        
        # Legs
        dpg.draw_line(
            (x, y + 0.3),
            (x - 0.2, y + 0.7),
            color=color,
            thickness=0.1 * self.zoom,
            parent=node
        )
        dpg.draw_line(
            (x, y + 0.3),
            (x + 0.2, y + 0.7),
            color=color,
            thickness=0.1 * self.zoom,
            parent=node
        )

    def draw_vehicles(self):
        for segment in self.simulation.segments:
            for vehicle_id in segment.vehicles:
                vehicle = self.simulation.vehicles[vehicle_id]
                progress = vehicle.x / segment.get_length()

                position = segment.get_point(progress)
                heading = segment.get_heading(progress)

                node = dpg.add_draw_node(parent="Canvas")
                dpg.draw_line(
                    (0, 0),
                    (vehicle.l, 0),
                    thickness=1.76*self.zoom,
                    color=(0, 0, 255),
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
        self.draw_segments()
        self.draw_crossings()
        self.draw_pedestrians()
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
