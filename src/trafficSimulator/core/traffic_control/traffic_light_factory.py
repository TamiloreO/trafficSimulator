from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Dict

from .traffic_light import ITrafficLight, TrafficLight
from .traffic_light_controller import ITrafficLightController, TrafficLightController, ControllerMode
from .traffic_light_group import ITrafficLightGroup, TrafficLightGroup
from .phase import IPhase, Phase
from .phase_sequence import IPhaseSequence, PhaseSequence
from .signal_timing import ISignalTiming, SignalTiming
from .light_state import LightState


class ITrafficLightFactory(ABC):
    @abstractmethod
    def create_traffic_light(
        self,
        position: Tuple[float, float],
        segment_index: int,
        stop_distance: float,
        initial_state: LightState = LightState.RED,
    ) -> ITrafficLight:
        pass

    @abstractmethod
    def create_controller(self, mode: ControllerMode = ControllerMode.TIMED) -> ITrafficLightController:
        pass

    @abstractmethod
    def create_phase(self, duration: float, green_lights: List[int], yellow_duration: float = 3.0) -> IPhase:
        pass

    @abstractmethod
    def create_phase_sequence(self, phases: Optional[List[IPhase]] = None) -> IPhaseSequence:
        pass


class TrafficLightFactory(ITrafficLightFactory):
    def __init__(self, default_timing: Optional[ISignalTiming] = None):
        self._default_timing = default_timing or SignalTiming()

    def create_traffic_light(
        self,
        position: Tuple[float, float],
        segment_index: int,
        stop_distance: float,
        initial_state: LightState = LightState.RED,
    ) -> ITrafficLight:
        return TrafficLight(
            position=position,
            segment_index=segment_index,
            stop_distance=stop_distance,
            timing=self._default_timing,
            initial_state=initial_state,
        )

    def create_controller(self, mode: ControllerMode = ControllerMode.TIMED) -> ITrafficLightController:
        return TrafficLightController(mode=mode)

    def create_group(self) -> ITrafficLightGroup:
        return TrafficLightGroup()

    def create_phase(self, duration: float, green_lights: List[int], yellow_duration: float = 3.0) -> IPhase:
        return Phase(duration=duration, green_lights=green_lights, yellow_duration=yellow_duration)

    def create_phase_sequence(self, phases: Optional[List[IPhase]] = None) -> IPhaseSequence:
        return PhaseSequence(phases=phases)

    def create_intersection_controller(
        self,
        segment_configs: List[Dict],
        phase_configs: List[Dict],
    ) -> ITrafficLightController:
        controller = self.create_controller()
        
        for i, config in enumerate(segment_configs):
            light = self.create_traffic_light(
                position=config.get('position', (0, 0)),
                segment_index=config['segment_index'],
                stop_distance=config.get('stop_distance', 0),
                initial_state=config.get('initial_state', LightState.RED),
            )
            controller.add_traffic_light(light, group_index=config.get('group', 0))

        phases = []
        for phase_config in phase_configs:
            phase = self.create_phase(
                duration=phase_config['duration'],
                green_lights=phase_config['green_lights'],
                yellow_duration=phase_config.get('yellow_duration', 3.0),
            )
            phases.append(phase)

        sequence = self.create_phase_sequence(phases)
        controller.set_phase_sequence(sequence)

        return controller
