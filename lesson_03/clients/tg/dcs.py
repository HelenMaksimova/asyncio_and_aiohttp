from typing import ClassVar, Type, List, Optional
from dataclasses import field

from marshmallow_dataclass import dataclass
from marshmallow import Schema, EXCLUDE


@dataclass
class Entity:
    offset: int
    length: int
    type: str

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class From:
    id: int
    is_bot: bool
    first_name: str
    username: str
    last_name: Optional[str] = None
    language_code: Optional[str] = None

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class Chat:
    id: int
    first_name: str
    last_name: str
    username: str
    type: str

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: From = field(metadata={'data_key': 'from'})
    chat: Chat
    date: int
    text: Optional[str] = None
    entities: Optional[List[Entity]] = None
    document: Optional['File'] = None

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class UpdateObj:
    update_id: int
    message: Message

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class GetUpdatesResponse:
    ok: bool
    result: List[UpdateObj]

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class SendMessageResponse:
    ok: bool
    result: Message

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class File:
    file_id: str
    file_unique_id: str
    file_size: int
    thumb: Optional['File'] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class GetFileResponse:
    ok: bool
    result: File

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE
