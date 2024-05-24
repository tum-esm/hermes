from pydantic import BaseModel


class BoardPortInfo(BaseModel):
    address: str
    label: str
    protocol: str
    protocol_label: str


class BoardInfo(BaseModel):
    port: BoardPortInfo


class BoardList(BaseModel):
    boards: list[BoardInfo]
