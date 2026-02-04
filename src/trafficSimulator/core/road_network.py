from typing import List, Optional, Tuple
from .geometry.segment import Segment
from .geometry.quadratic_curve import QuadraticCurve
from .geometry.cubic_curve import CubicCurve


class RoadNetwork:
    """Manages road segments and their connections."""
    
    def __init__(self):
        self._segments: List[Segment] = []
    
    @property
    def segments(self) -> List[Segment]:
        return self._segments
    
    def __len__(self) -> int:
        return len(self._segments)
    
    def __getitem__(self, index: int) -> Segment:
        return self._segments[index]
    
    def __iter__(self):
        return iter(self._segments)
    
    def add_segment(self, segment: Segment) -> int:
        """Add a segment and return its index."""
        self._segments.append(segment)
        return len(self._segments) - 1
    
    def get_segment(self, index: int) -> Optional[Segment]:
        """Get segment by index, returns None if out of bounds."""
        if 0 <= index < len(self._segments):
            return self._segments[index]
        return None
    
    def create_segment(self, *points: Tuple[float, float]) -> int:
        """Create a straight segment from points and return its index."""
        segment = Segment(points)
        return self.add_segment(segment)
    
    def create_quadratic_bezier_curve(
        self, 
        start: Tuple[float, float], 
        control: Tuple[float, float], 
        end: Tuple[float, float]
    ) -> int:
        """Create a quadratic Bezier curve and return its index."""
        curve = QuadraticCurve(start, control, end)
        return self.add_segment(curve)
    
    def create_cubic_bezier_curve(
        self,
        start: Tuple[float, float],
        control_1: Tuple[float, float],
        control_2: Tuple[float, float],
        end: Tuple[float, float]
    ) -> int:
        """Create a cubic Bezier curve and return its index."""
        curve = CubicCurve(start, control_1, control_2, end)
        return self.add_segment(curve)
    
    def get_segment_count(self) -> int:
        """Return the number of segments in the network."""
        return len(self._segments)
    
    def transfer_vehicle(self, vehicle_id, from_segment_idx: int, to_segment_idx: int) -> bool:
        """Transfer a vehicle from one segment to another."""
        from_segment = self.get_segment(from_segment_idx)
        to_segment = self.get_segment(to_segment_idx)
        
        if from_segment is None or to_segment is None:
            return False
        
        if vehicle_id in from_segment.vehicles:
            from_segment.vehicles.remove(vehicle_id)
        to_segment.vehicles.append(vehicle_id)
        return True
