from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    surname: str
    tg_id: str
    course: int
    group: int
    type: str
    admin: bool
    superadmin: bool