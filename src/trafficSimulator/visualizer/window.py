import dearpygui.dearpygui as dpg
import math
from typing import Tuple, List, Optional

from ..core.pedestrian_crossing import CrossingType, SignalState


class Window:
    """
    Visualization window for the traffic simulation.
    Renders roads, vehicles, pedestrians, and crossings.
    """
    
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

                dpg.add_slider_int(tag="SpeedInput", label="Speed", min_value=1, max_value=100, default_value=1, callback=self.set_speed)
            
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
                    
                    with dpg.table_row():
                        dpg.add_text("Crossings:")
                        dpg.add_text("0", tag="CrossingCount")
            
            with dpg.collapsing_header(label="Camera Control", default_open=True):
    
                dpg.add_slider_float(tag="ZoomSlider", label="Zoom", min_value=0.1, max_value=100, default_value=self.zoom, callback=self.set_offset_zoom)            
                with dpg.group():
                    dpg.add_slider_float(tag="OffsetXSlider", label="X Offset", min_value=-100, max_value=100, default_value=self.offset[0], callback=self.set_offset_zoom)
                    dpg.add_slider_float(tag="OffsetYSlider", label="Y Offset", min_value=-100, max_value=100, default_value=self.offset[1], callback=self.set_offset_zoom)

            # Crossing controls
            with dpg.collapsing_header(label="Crossing Controls", default_open=True):
                dpg.add_text("Press buttons for signaled crossings:")
                dpg.add_button(label="Press All Crossing Buttons", callback=self._press_all_crossing_buttons)

    def _press_all_crossing_buttons(self):
        """Press buttons on all signaled crossings."""
        if hasattr(self.simulation, 'crossings'):
            for i, crossing in enumerate(self.simulation.crossings):
                if crossing.is_signaled:
                    self.simulation.press_crossing_button(i)

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
        # Update status text
        if self.is_running:
            dpg.set_value("StatusText", "Running")
            dpg.configure_item("StatusText", color=(0, 255, 0))
        else:
            dpg.set_value("StatusText", "Stopped")
            dpg.configure_item("StatusText", color=(255, 0, 0))
        
        # Update time and frame text
        dpg.set_value("TimeStatus", f"{self.simulation.t:.2f}s")
        dpg.set_value("FrameStatus", self.simulation.frame_count)
        
        # Update counts
        vehicle_count = len(self.simulation.vehicles) if hasattr(self.simulation, 'vehicles') else 0
        dpg.set_value("VehicleCount", str(vehicle_count))
        
        pedestrian_count = len(self.simulation.pedestrians) if hasattr(self.simulation, 'pedestrians') else 0
        dpg.set_value("PedestrianCount", str(pedestrian_count))
        
        crossing_count = len(self.simulation.crossings) if hasattr(self.simulation, 'crossings') else 0
        dpg.set_value("CrossingCount", str(crossing_count))

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
            try:
                if hasattr(segment, 'points') and segment.points:
                    dpg.draw_polyline(segment.points, color=(180, 180, 220), thickness=3.5*self.zoom, parent="Canvas")
            except Exception:
                pass

    def draw_crossings(self):
        """Draw all pedestrian crossings with their markings."""
        if not hasattr(self.simulation, 'crossings'):
            return
            
        for crossing in self.simulation.crossings:
            try:
                self._draw_crossing(crossing)
            except Exception:
                pass

    def _draw_crossing(self, crossing):
        """Draw a single pedestrian crossing."""
        crossing_type = crossing.crossing_type
        
        # Draw based on crossing type
        if crossing_type == CrossingType.ZEBRA:
            self._draw_zebra_crossing(crossing)
        elif crossing_type == CrossingType.PELICAN:
            self._draw_pelican_crossing(crossing)
        elif crossing_type == CrossingType.PUFFIN:
            self._draw_puffin_crossing(crossing)
        elif crossing_type == CrossingType.TOUCAN:
            self._draw_toucan_crossing(crossing)
        elif crossing_type == CrossingType.PEGASUS:
            self._draw_pegasus_crossing(crossing)
        elif crossing_type == CrossingType.TIGER:
            self._draw_tiger_crossing(crossing)

    def _draw_zebra_crossing(self, crossing):
        """Draw zebra crossing with white stripes."""
        stripes = crossing.get_stripe_positions()
        
        for start, end in stripes:
            dpg.draw_line(
                start, end,
                thickness=0.5 * self.zoom,
                color=(255, 255, 255),
                parent="Canvas"
            )
        
        # Draw crossing boundary lines (give way lines)
        self._draw_crossing_boundary(crossing, color=(255, 255, 255))
        
        # Draw belisha beacon indicators (orange circles at ends)
        self._draw_belisha_beacons(crossing)

    def _draw_pelican_crossing(self, crossing):
        """Draw pelican crossing with signals."""
        # Draw stripes
        stripes = crossing.get_stripe_positions()
        for start, end in stripes:
            dpg.draw_line(
                start, end,
                thickness=0.5 * self.zoom,
                color=(255, 255, 255),
                parent="Canvas"
            )
        
        self._draw_crossing_boundary(crossing, color=(255, 255, 255))
        
        # Draw signal posts
        self._draw_signal_posts(crossing)

    def _draw_puffin_crossing(self, crossing):
        """Draw puffin crossing with signals and detection zone."""
        # Draw stripes
        stripes = crossing.get_stripe_positions()
        for start, end in stripes:
            dpg.draw_line(
                start, end,
                thickness=0.5 * self.zoom,
                color=(255, 255, 255),
                parent="Canvas"
            )
        
        self._draw_crossing_boundary(crossing, color=(255, 255, 255))
        
        # Draw signal posts
        self._draw_signal_posts(crossing)
        
        # Draw detection zone indicator (subtle)
        self._draw_detection_zone(crossing)

    def _draw_toucan_crossing(self, crossing):
        """Draw toucan crossing with cycle lane."""
        # Draw pedestrian stripes
        stripes = crossing.get_stripe_positions()
        for start, end in stripes:
            dpg.draw_line(
                start, end,
                thickness=0.5 * self.zoom,
                color=(255, 255, 255),
                parent="Canvas"
            )
        
        # Draw cycle lane (green tinted)
        cycle_geom = crossing.get_cycle_lane_geometry()
        if cycle_geom:
            start, end = cycle_geom
            # Draw cycle lane background
            dpg.draw_line(
                start, end,
                thickness=2.0 * self.zoom,
                color=(0, 150, 0, 100),
                parent="Canvas"
            )
            # Draw cycle lane markings (dashed)
            self._draw_dashed_line(start, end, color=(255, 255, 255), dash_length=0.5)
        
        self._draw_crossing_boundary(crossing, color=(255, 255, 255))
        self._draw_signal_posts(crossing)

    def _draw_pegasus_crossing(self, crossing):
        """Draw pegasus crossing (equestrian)."""
        # Draw stripes
        stripes = crossing.get_stripe_positions()
        for start, end in stripes:
            dpg.draw_line(
                start, end,
                thickness=0.5 * self.zoom,
                color=(255, 255, 255),
                parent="Canvas"
            )
        
        self._draw_crossing_boundary(crossing, color=(255, 255, 255))
        self._draw_signal_posts(crossing)
        
        # Draw horse symbol indicator (small brown circle)
        heading = crossing.heading
        offset_dist = crossing.width / 2 + 2.0
        perp_angle = heading + math.pi / 2
        
        horse_x = crossing.center_pos[0] + offset_dist * math.cos(perp_angle)
        horse_y = crossing.center_pos[1] + offset_dist * math.sin(perp_angle)
        
        dpg.draw_circle(
            (horse_x, horse_y),
            0.8,
            color=(139, 69, 19),
            fill=(139, 69, 19, 150),
            parent="Canvas"
        )

    def _draw_tiger_crossing(self, crossing):
        """Draw tiger crossing (parallel zebra and cycle)."""
        # Draw pedestrian stripes (white)
        stripes = crossing.get_stripe_positions()
        for start, end in stripes:
            dpg.draw_line(
                start, end,
                thickness=0.5 * self.zoom,
                color=(255, 255, 255),
                parent="Canvas"
            )
        
        # Draw cycle lane (with yellow/gold stripes)
        cycle_geom = crossing.get_cycle_lane_geometry()
        if cycle_geom:
            start, end = cycle_geom
            
            # Calculate stripe positions for cycle lane
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > 0.1:
                # Normalize
                dx /= length
                dy /= length
                
                # Draw yellow stripes perpendicular to cycle path
                road_dx = math.cos(crossing.heading)
                road_dy = math.sin(crossing.heading)
                
                num_stripes = 4
                stripe_spacing = 0.7
                
                for i in range(num_stripes):
                    offset = (i - num_stripes/2 + 0.5) * stripe_spacing
                    cx = (start[0] + end[0]) / 2 + offset * road_dx
                    cy = (start[1] + end[1]) / 2 + offset * road_dy
                    
                    half_len = 1.0
                    s_start = (cx + half_len * dx, cy + half_len * dy)
                    s_end = (cx - half_len * dx, cy - half_len * dy)
                    
                    dpg.draw_line(
                        s_start, s_end,
                        thickness=0.4 * self.zoom,
                        color=(255, 215, 0),  # Gold/yellow for cycle
                        parent="Canvas"
                    )
        
        self._draw_crossing_boundary(crossing, color=(255, 255, 255))
        self._draw_belisha_beacons(crossing)

    def _draw_crossing_boundary(self, crossing, color=(255, 255, 255)):
        """Draw the boundary/give-way lines at crossing edges."""
        heading = crossing.heading
        half_stripe_area = 1.8  # Half width of striped area along road
        
        # Calculate boundary line positions (perpendicular to road)
        road_dx = math.cos(heading)
        road_dy = math.sin(heading)
        
        # Start boundary (before crossing)
        for sign in [-1, 1]:
            offset = sign * half_stripe_area
            
            line_center_x = crossing.center_pos[0] + offset * road_dx
            line_center_y = crossing.center_pos[1] + offset * road_dy
            
            perp_angle = heading + math.pi / 2
            half_width = crossing.width / 2
            
            line_start = (
                line_center_x + half_width * math.cos(perp_angle),
                line_center_y + half_width * math.sin(perp_angle)
            )
            line_end = (
                line_center_x - half_width * math.cos(perp_angle),
                line_center_y - half_width * math.sin(perp_angle)
            )
            
            # Draw dashed give-way line
            self._draw_dashed_line(line_start, line_end, color=color, dash_length=0.3)

    def _draw_dashed_line(self, start: Tuple[float, float], end: Tuple[float, float],
                          color=(255, 255, 255), dash_length=0.5):
        """Draw a dashed line."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 0.1:
            return
            
        dx /= length
        dy /= length
        
        num_dashes = int(length / (dash_length * 2))
        if num_dashes < 1:
            num_dashes = 1
        
        for i in range(num_dashes):
            t_start = i * 2 * dash_length
            t_end = t_start + dash_length
            
            if t_end > length:
                t_end = length
            
            dash_start = (start[0] + t_start * dx, start[1] + t_start * dy)
            dash_end = (start[0] + t_end * dx, start[1] + t_end * dy)
            
            dpg.draw_line(
                dash_start, dash_end,
                thickness=0.2 * self.zoom,
                color=color,
                parent="Canvas"
            )

    def _draw_belisha_beacons(self, crossing):
        """Draw belisha beacons (orange globes) at zebra crossing ends."""
        # Beacons are placed at both ends of the crossing
        # Flashing orange color
        flash_on = int(self.simulation.t * 2) % 2 == 0
        beacon_color = (255, 165, 0) if flash_on else (200, 130, 0)
        
        for pos in [crossing.start_pos, crossing.end_pos]:
            # Beacon post
            dpg.draw_circle(
                pos,
                0.4,
                color=beacon_color,
                fill=beacon_color,
                parent="Canvas"
            )

    def _draw_signal_posts(self, crossing):
        """Draw traffic signal posts for signaled crossings."""
        signal_color = crossing.signal_color
        
        # Posts at both ends
        for pos in [crossing.start_pos, crossing.end_pos]:
            # Signal housing
            dpg.draw_rectangle(
                (pos[0] - 0.3, pos[1] - 0.6),
                (pos[0] + 0.3, pos[1] + 0.6),
                color=(50, 50, 50),
                fill=(30, 30, 30),
                thickness=0.1 * self.zoom,
                parent="Canvas"
            )
            
            # Signal light
            dpg.draw_circle(
                pos,
                0.25,
                color=signal_color,
                fill=signal_color,
                parent="Canvas"
            )
        
        # Draw signal state indicator near crossing center
        state_text_pos = (
            crossing.center_pos[0],
            crossing.center_pos[1] - crossing.width / 2 - 1.5
        )

    def _draw_detection_zone(self, crossing):
        """Draw detection zone indicator for PUFFIN crossings."""
        # Subtle indicator showing detection area
        heading = crossing.heading
        perp_angle = heading + math.pi / 2
        
        detection_length = crossing.width + 2.0
        detection_width = 4.0
        
        # Draw subtle detection zone boundary
        corners = []
        for dx_sign in [-1, 1]:
            for dy_sign in [-1, 1]:
                x = crossing.center_pos[0] + dx_sign * (detection_width/2) * math.cos(heading)
                y = crossing.center_pos[1] + dx_sign * (detection_width/2) * math.sin(heading)
                x += dy_sign * (detection_length/2) * math.cos(perp_angle)
                y += dy_sign * (detection_length/2) * math.sin(perp_angle)
                corners.append((x, y))
        
        # Reorder corners for proper rectangle
        if len(corners) == 4:
            ordered = [corners[0], corners[1], corners[3], corners[2], corners[0]]
            dpg.draw_polyline(
                ordered,
                color=(100, 100, 255, 50),
                thickness=0.1 * self.zoom,
                parent="Canvas"
            )

    def draw_vehicles(self):
        for segment in self.simulation.segments:
            for vehicle_id in segment.vehicles:
                if vehicle_id not in self.simulation.vehicles:
                    continue
                    
                vehicle = self.simulation.vehicles[vehicle_id]
                
                try:
                    seg_length = segment.get_length()
                    if seg_length <= 0:
                        continue
                    progress = vehicle.x / seg_length
                    progress = max(0.0, min(1.0, progress))

                    position = segment.get_point(progress)
                    heading = segment.get_heading(progress)
                except Exception:
                    continue

                node = dpg.add_draw_node(parent="Canvas")
                
                # Vehicle color - red if stopped, blue if moving
                veh_color = (255, 0, 0) if vehicle.stopped else (0, 0, 255)
                
                dpg.draw_line(
                    (0, 0),
                    (vehicle.l, 0),
                    thickness=1.76*self.zoom,
                    color=veh_color,
                    parent=node
                )

                translate = dpg.create_translation_matrix(position)
                rotate = dpg.create_rotation_matrix(heading, [0, 0, 1])
                dpg.apply_transform(node, translate*rotate)

    def draw_pedestrians(self):
        """Draw all pedestrians at their crossings."""
        if not hasattr(self.simulation, 'pedestrians'):
            return
        if not hasattr(self.simulation, 'crossings'):
            return
            
        for ped_id, pedestrian in self.simulation.pedestrians.items():
            try:
                self._draw_pedestrian(pedestrian)
            except Exception:
                pass

    def _draw_pedestrian(self, pedestrian):
        """Draw a single pedestrian."""
        # Find the crossing this pedestrian is on
        crossing = None
        for c in self.simulation.crossings:
            if c.id == pedestrian.crossing_id:
                crossing = c
                break
        
        if crossing is None:
            return
        
        # Get pedestrian position
        pos = pedestrian.get_position(crossing.start_pos, crossing.end_pos)
        
        # Draw pedestrian as a small circle
        color = pedestrian.color if hasattr(pedestrian, 'color') else (255, 100, 100)
        
        # Outer circle (body)
        dpg.draw_circle(
            pos,
            0.3,
            color=color,
            fill=color,
            parent="Canvas"
        )
        
        # Head (smaller circle on top)
        head_offset = 0.25
        heading_to_end = math.atan2(
            crossing.end_pos[1] - crossing.start_pos[1],
            crossing.end_pos[0] - crossing.start_pos[0]
        )
        
        if pedestrian.direction == -1:
            heading_to_end += math.pi
        
        head_pos = (
            pos[0] + head_offset * math.cos(heading_to_end),
            pos[1] + head_offset * math.sin(heading_to_end)
        )
        
        dpg.draw_circle(
            head_pos,
            0.15,
            color=(255, 220, 180),  # Skin tone
            fill=(255, 220, 180),
            parent="Canvas"
        )

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
        
        # New drawings - order matters for layering
        self.draw_bg()
        self.draw_axes()
        self.draw_grid(unit=10)
        self.draw_grid(unit=50)
        self.draw_segments()
        self.draw_crossings()      # Draw crossings on top of road
        self.draw_vehicles()
        self.draw_pedestrians()    # Draw pedestrians on top

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
