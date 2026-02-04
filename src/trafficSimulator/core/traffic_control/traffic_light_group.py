from abc import ABC, abstractmethod
from typing import List, Dict
import uuid

from .traffic_light import ITrafficLight
from .light_state import LightState


class ITrafficLightGroup(ABC):
    @abstractmethod
    def get_id(self) -> uuid.UUID:
        pass

    @abstractmethod
    def get_lights(self) -> List[ITrafficLight]:
        pass

    @abstractmethod
    def add_light(self, light: ITrafficLight) -> None:
        pass

    @abstractmethod
    def set_all_state(self, state: LightState) -> None:
        pass

    @abstractmethod
    def get_light_by_segment(self, segment_index: int) -> ITrafficLight:
        pass


class TrafficLightGroup(ITrafficLightGroup):
    def __init__(self):
        self._id = uuid.uuid4()
        self._lights: List[ITrafficLight] = []
        self._segment_to_light: Dict[int, ITrafficLight] = {}

    def get_id(self) -> uuid.UUID:
        return self._id

    def get_lights(self) -> List[ITrafficLight]:
        return list(self._lights)

    def add_light(self, light: ITrafficLight) -> None:
        self._lights.append(light)
        self._segment_to_light[light.get_segment_index()] = light

    def set_all_state(self, state: LightState) -> None:
        for light in self._lights:
            light.set_state(state)

    def get_light_by_segment(self, segment_index: int) -> ITrafficLight:
        return self._segment_to_light.get(segment_index)
