from enum import Enum, auto

class ProcessingStatus(Enum):
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    ERROR = auto()

class ProcessFile:
    def __init__(self, name: str, status = ProcessingStatus.PENDING):
        self.name = name
        self.status = status
