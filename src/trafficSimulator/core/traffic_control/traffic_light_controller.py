from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum

from .traffic_light import ITrafficLight, TrafficLight
from .traffic_light_group import ITrafficLightGroup, TrafficLightGroup
from .phase import IPhase
from .phase_sequence import IPhaseSequence, PhaseSequence
from .light_state import LightState


class ControllerMode(Enum):
    TIMED = "timed"
    MANUAL = "manual"
    ADAPTIVE = "adaptive"


class ITrafficLightController(ABC):
    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def get_all_lights(self) -> List[ITrafficLight]:
        pass

    @abstractmethod
    def get_light_for_segment(self, segment_index: int) -> Optional[ITrafficLight]:
        pass

    @abstractmethod
    def add_traffic_light(self, light: ITrafficLight, group_index: int = 0) -> None:
        pass

    @abstractmethod
    def set_phase_sequence(self, sequence: IPhaseSequence) -> None:
        pass


class TrafficLightController(ITrafficLightController):
    def __init__(self, mode: ControllerMode = ControllerMode.TIMED):
        self._mode = mode
        self._groups: List[ITrafficLightGroup] = []
        self._all_lights: List[ITrafficLight] = []
        self._segment_to_light: Dict[int, ITrafficLight] = {}
        self._phase_sequence: IPhaseSequence = PhaseSequence()
        self._phase_time = 0.0
        self._in_yellow_transition = False
        self._yellow_time = 0.0
        self._current_yellow_duration = 3.0

    def add_group(self, group: ITrafficLightGroup) -> None:
        self._groups.append(group)
        for light in group.get_lights():
            self._register_light(light)

    def add_traffic_light(self, light: ITrafficLight, group_index: int = 0) -> None:
        while len(self._groups) <= group_index:
            self._groups.append(TrafficLightGroup())
        self._groups[group_index].add_light(light)
        self._register_light(light)

    def _register_light(self, light: ITrafficLight) -> None:
        self._all_lights.append(light)
        self._segment_to_light[light.get_segment_index()] = light

    def set_phase_sequence(self, sequence: IPhaseSequence) -> None:
        self._phase_sequence = sequence
        self._phase_time = 0.0
        self._apply_current_phase()

    def _apply_current_phase(self) -> None:
        phase = self._phase_sequence.get_current_phase()
        green_states = phase.get_light_states()
        for idx, light in enumerate(self._all_lights):
            if idx in green_states:
                light.set_state(LightState.GREEN)
            else:
                light.set_state(LightState.RED)

    def _apply_yellow_to_green_lights(self) -> None:
        phase = self._phase_sequence.get_current_phase()
        green_states = phase.get_light_states()
        for idx, light in enumerate(self._all_lights):
            if idx in green_states:
                light.set_state(LightState.YELLOW)

    def get_all_lights(self) -> List[ITrafficLight]:
        return list(self._all_lights)

    def get_light_for_segment(self, segment_index: int) -> Optional[ITrafficLight]:
        return self._segment_to_light.get(segment_index)

    def update(self, dt: float) -> None:
        if self._mode == ControllerMode.MANUAL:
            return

        if self._in_yellow_transition:
            self._yellow_time += dt
            if self._yellow_time >= self._current_yellow_duration:
                self._in_yellow_transition = False
                self._yellow_time = 0.0
                self._phase_sequence.advance_phase()
                self._apply_current_phase()
                self._phase_time = 0.0
        else:
            self._phase_time += dt
            current_phase = self._phase_sequence.get_current_phase()
            if self._phase_time >= current_phase.get_duration():
                self._in_yellow_transition = True
                self._current_yellow_duration = current_phase.get_yellow_duration()
                self._apply_yellow_to_green_lights()
