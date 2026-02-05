class LaneChangeStrategy:
    """Rule-based lane change strategy."""
    
    def __init__(self, min_front_gap=15.0, min_rear_gap=10.0, slower_threshold=0.8, lookahead=50.0, cooldown=3.0):
        self.min_front_gap = min_front_gap
        self.min_rear_gap = min_rear_gap
        self.slower_threshold = slower_threshold
        self.lookahead = lookahead
        self.cooldown = cooldown
    
    def should_change_lane(self, vehicle, simulation):
        """Returns target segment index or None if no lane change needed."""
        if vehicle.is_changing_lane:
            return None
        
        if simulation.t - vehicle.last_lane_change_time < self.cooldown:
            return None
        
        current_segment_index = vehicle.path[vehicle.current_road_index]
        road = simulation.get_road_for_segment(current_segment_index)
        
        if road is None:
            return None
        
        if not self._has_slower_vehicle_ahead(vehicle, current_segment_index, simulation):
            return None
        
        left_segment, right_segment = road.get_adjacent_segment_indices(current_segment_index)
        
        if right_segment is not None and self._is_lane_safe(vehicle, right_segment, simulation):
            return right_segment
        
        if left_segment is not None and self._is_lane_safe(vehicle, left_segment, simulation):
            return left_segment
        
        return None
    
    def _has_slower_vehicle_ahead(self, vehicle, segment_index, simulation):
        segment = simulation.segments[segment_index]
        
        for vid in segment.vehicles:
            if vid == vehicle.id:
                continue
            other = simulation.vehicles[vid]
            if other.x > vehicle.x:
                gap = other.x - vehicle.x - other.l
                if gap < self.lookahead:
                    speed_ratio = other.v / vehicle.v_max if vehicle.v_max > 0 else 1.0
                    if speed_ratio < self.slower_threshold:
                        return True
        return False
    
    def _is_lane_safe(self, vehicle, target_segment_index, simulation):
        target_segment = simulation.segments[target_segment_index]
        
        if len(target_segment.vehicles) == 0:
            return True
        
        for vid in target_segment.vehicles:
            other = simulation.vehicles[vid]
            if other.x > vehicle.x:
                gap = other.x - vehicle.x - other.l
                if gap < self.min_front_gap:
                    return False
            else:
                gap = vehicle.x - other.x - vehicle.l
                if gap < self.min_rear_gap:
                    return False
        
        return True
