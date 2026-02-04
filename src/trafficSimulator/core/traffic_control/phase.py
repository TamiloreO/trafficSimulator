from abc import ABC, abstractmethod
from typing import List, Dict
from .light_state import LightState


class IPhase(ABC):
    @abstractmethod
    def get_duration(self) -> float:
        pass

    @abstractmethod
    def get_light_states(self) -> Dict[int, LightState]:
        pass

    @abstractmethod
    def get_yellow_duration(self) -> float:
        pass


class Phase(IPhase):
    def __init__(
        self,
        duration: float,
        green_lights: List[int],
        yellow_duration: float = 3.0,
    ):
        self._duration = duration
        self._green_lights = set(green_lights)
        self._yellow_duration = yellow_duration

    def get_duration(self) -> float:
        return self._duration

    def get_yellow_duration(self) -> float:
        return self._yellow_duration

    def get_light_states(self) -> Dict[int, LightState]:
        return {light_idx: LightState.GREEN for light_idx in self._green_lights}

    def is_light_green(self, light_index: int) -> bool:
        return light_index in self._green_lights
