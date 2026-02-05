from typing import List, Optional, Tuple


class Road:
    """Represents a multi-lane road composed of parallel lane segments."""
    
    _id_counter = 0
    
    def __init__(self, segment_indices: List[int]):
        self.id = Road._id_counter
        Road._id_counter += 1
        self._segment_indices = segment_indices
        self._segment_to_lane_map = {
            seg_idx: lane_idx 
            for lane_idx, seg_idx in enumerate(segment_indices)
        }
    
    def get_lane_count(self) -> int:
        return len(self._segment_indices)
    
    def get_segment_index(self, lane_index: int) -> int:
        return self._segment_indices[lane_index]
    
    def get_lane_index_for_segment(self, segment_index: int) -> Optional[int]:
        return self._segment_to_lane_map.get(segment_index)
    
    def get_adjacent_segment_indices(self, segment_index: int) -> Tuple[Optional[int], Optional[int]]:
        lane_index = self.get_lane_index_for_segment(segment_index)
        if lane_index is None:
            return (None, None)
        
        left = self._segment_indices[lane_index - 1] if lane_index > 0 else None
        right = self._segment_indices[lane_index + 1] if lane_index < len(self._segment_indices) - 1 else None
        return (left, right)
    
    def contains_segment(self, segment_index: int) -> bool:
        return segment_index in self._segment_to_lane_map
