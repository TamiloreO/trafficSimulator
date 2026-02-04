from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve
from .geometry.segment import Segment


class RoadNetwork:
    """Manages the road network consisting of segments and curves."""
    
    def __init__(self):
        self._segments = []

    @property
    def segments(self):
        return self._segments

    def add_segment(self, segment):
        self._segments.append(segment)
        return len(self._segments) - 1

    def get_segment(self, index):
        return self._segments[index]

    def get_segment_count(self):
        return len(self._segments)

    def create_segment(self, *points):
        segment = Segment(points)
        return self.add_segment(segment)

    def create_quadratic_bezier_curve(self, start, control, end):
        curve = QuadraticCurve(start, control, end)
        return self.add_segment(curve)

    def create_cubic_bezier_curve(self, start, control_1, control_2, end):
        curve = CubicCurve(start, control_1, control_2, end)
        return self.add_segment(curve)

    def __iter__(self):
        return iter(self._segments)

    def __len__(self):
        return len(self._segments)

    def __getitem__(self, index):
        return self._segments[index]
