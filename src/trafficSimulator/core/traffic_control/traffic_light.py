from abc import ABC, abstractmethod
from typing import Tuple, Optional
import uuid

from .light_state import ILightState, LightState, RedState, GreenState, YellowState
from .signal_timing import ISignalTiming, SignalTiming


class ITrafficLight(ABC):
    @abstractmethod
    def get_id(self) -> uuid.UUID:
        pass

    @abstractmethod
    def get_position(self) -> Tuple[float, float]:
        pass

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
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def set_state(self, state: LightState) -> None:
        pass

    @abstractmethod
    def get_segment_index(self) -> int:
        pass

    @abstractmethod
    def get_stop_distance(self) -> float:
        pass


class TrafficLight(ITrafficLight):
    def __init__(
        self,
        position: Tuple[float, float],
        segment_index: int,
        stop_distance: float,
        timing: Optional[ISignalTiming] = None,
        initial_state: LightState = LightState.RED,
    ):
        self._id = uuid.uuid4()
        self._position = position
        self._segment_index = segment_index
        self._stop_distance = stop_distance
        self._timing = timing or SignalTiming()
        self._state_time = 0.0
        self._set_light_state(initial_state)

    def _set_light_state(self, state: LightState) -> None:
        state_map = {
            LightState.RED: RedState,
            LightState.YELLOW: YellowState,
            LightState.GREEN: GreenState,
        }
        self._current_state: ILightState = state_map[state]()

    def get_id(self) -> uuid.UUID:
        return self._id

    def get_position(self) -> Tuple[float, float]:
        return self._position

    def get_color(self) -> Tuple[int, int, int]:
        return self._current_state.get_color()

    def get_state(self) -> LightState:
        return self._current_state.get_state()

    def allows_passage(self) -> bool:
        return self._current_state.allows_passage()

    def get_segment_index(self) -> int:
        return self._segment_index

    def get_stop_distance(self) -> float:
        return self._stop_distance

    def set_state(self, state: LightState) -> None:
        self._set_light_state(state)
        self._state_time = 0.0

    def update(self, dt: float) -> None:
        self._state_time += dt
        current_duration = self._timing.get_duration(self.get_state())
        if self._state_time >= current_duration:
            self._state_time = 0.0
            next_state = self._current_state.get_next_state()
            self._current_state = next_state
