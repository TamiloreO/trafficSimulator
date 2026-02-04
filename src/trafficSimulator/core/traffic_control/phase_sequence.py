from abc import ABC, abstractmethod
from typing import List, Optional
from .phase import IPhase, Phase


class IPhaseSequence(ABC):
    @abstractmethod
    def get_current_phase(self) -> IPhase:
        pass

    @abstractmethod
    def get_phase_count(self) -> int:
        pass

    @abstractmethod
    def advance_phase(self) -> IPhase:
        pass

    @abstractmethod
    def get_current_phase_index(self) -> int:
        pass


class PhaseSequence(IPhaseSequence):
    def __init__(self, phases: Optional[List[IPhase]] = None):
        self._phases: List[IPhase] = phases or []
        self._current_index = 0

    def add_phase(self, phase: IPhase) -> None:
        self._phases.append(phase)

    def get_current_phase(self) -> IPhase:
        if not self._phases:
            return Phase(duration=30.0, green_lights=[])
        return self._phases[self._current_index]

    def get_phase_count(self) -> int:
        return len(self._phases)

    def advance_phase(self) -> IPhase:
        if self._phases:
            self._current_index = (self._current_index + 1) % len(self._phases)
        return self.get_current_phase()

    def get_current_phase_index(self) -> int:
        return self._current_index
