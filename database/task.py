from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: str
    title: str
    type: str
    description: str
    deadline: datetime
    assignet_to: list
    who_created: str
    status: bool
    notify: bool