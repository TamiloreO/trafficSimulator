from abc import ABC, abstractmethod
from typing import Dict
from .light_state import LightState


class ISignalTiming(ABC):
    @abstractmethod
    def get_duration(self, state: LightState) -> float:
        pass

    @abstractmethod
    def get_total_cycle_duration(self) -> float:
        pass

    @abstractmethod
    def set_duration(self, state: LightState, duration: float) -> None:
        pass


class SignalTiming(ISignalTiming):
    def __init__(self, config: Dict = None):
        self._durations: Dict[LightState, float] = {
            LightState.GREEN: 30.0,
            LightState.YELLOW: 5.0,
            LightState.RED: 35.0,
        }
        if config:
            for state, duration in config.items():
                if isinstance(state, str):
                    state = LightState(state)
                self._durations[state] = duration

    def get_duration(self, state: LightState) -> float:
        return self._durations.get(state, 0.0)

    def get_total_cycle_duration(self) -> float:
        return sum(self._durations.values())

    def set_duration(self, state: LightState, duration: float) -> None:
        self._durations[state] = duration
