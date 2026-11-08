from abc import ABC, abstractmethod

class Collector(ABC):
    """Base interface for all job collectors."""

    @abstractmethod
    def collect(self):
        """Return a list of Job objects."""
        raise NotImplementedError
