from pydantic import BaseModel


class LookupItem(BaseModel):
    id: int
    label: str


class GroupLookupItem(LookupItem):
    code: str


class TeacherLookupItem(LookupItem):
    full_name: str


class RoomLookupItem(LookupItem):
    number: str


class SubjectLookupItem(LookupItem):
    name: str
