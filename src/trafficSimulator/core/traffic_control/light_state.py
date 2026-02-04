from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple


class LightState(Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class ILightState(ABC):
    @abstractmethod
    def get_color(self) -> Tuple[int, int, int]:
        pass

    @abstractmethod
    def get_state(self) -> LightState:
        pass

    @abstractmethod
    def allows_passage(self) -> bool:
        pass

    @abstractmethod
    def get_next_state(self) -> 'ILightState':
        pass


class RedState(ILightState):
    def get_color(self) -> Tuple[int, int, int]:
        return (255, 0, 0)

    def get_state(self) -> LightState:
        return LightState.RED

    def allows_passage(self) -> bool:
        return False

    def get_next_state(self) -> ILightState:
        return GreenState()


class YellowState(ILightState):
    def get_color(self) -> Tuple[int, int, int]:
        return (255, 255, 0)

    def get_state(self) -> LightState:
        return LightState.YELLOW

    def allows_passage(self) -> bool:
        return False

    def get_next_state(self) -> ILightState:
        return RedState()


class GreenState(ILightState):
    def get_color(self) -> Tuple[int, int, int]:
        return (0, 255, 0)

    def get_state(self) -> LightState:
        return LightState.GREEN

    def allows_passage(self) -> bool:
        return True

    def get_next_state(self) -> ILightState:
        return YellowState()
