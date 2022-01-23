from typing import Optional, List
import json
import marshmallow

from clients.base import ClientError, Client
from clients.tg.dcs import UpdateObj, Message, GetUpdatesResponse


class TgClientError(ClientError):
    pass


class TgClient(Client):

    BASE_PATH = 'https://api.telegram.org'

    def __init__(self, token: str = ''):
        super().__init__()
        self.token = token

    def get_path(self, url: str) -> str:
        base_path = self.get_base_path().strip('/')
        url = url.lstrip('/')
        return f'{base_path}/bot{self.token}/{url}'

    async def get_me(self) -> dict:
        return await self._perform_request('get', self.get_path('getMe'))

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 0) -> dict:
        params = {'offset': offset, 'timeout': timeout}
        return await self._perform_request('get', self.get_path('getUpdates'),
                                           params={key: params.get(key) for key in params if params.get(key)})

    async def _handle_response(self, response):
        if not response.status == 200:
            raise TgClientError(response, f'status: {response.status}')
        try:
            data = await response.json()
            return data
        except json.decoder.JSONDecodeError as error:
            raise TgClientError(response, error)

    async def get_updates_in_objects(self, *args, **kwargs) -> List[UpdateObj]:
        response = await self.get_updates(*args, **kwargs)
        try:
            data = GetUpdatesResponse.Schema().load(response)
            return data.result
        except marshmallow.exceptions.ValidationError as error:
            raise TgClientError(response, error)

    async def send_message(self, chat_id: int, text: str) -> Message:
        message = {
            'chat_id': chat_id,
            'text': text
        }
        response = await self._perform_request('post', self.get_path('sendMessage'), json=message)
        try:
            data = Message.Schema().load(response.get('result'))
            return data
        except marshmallow.exceptions.ValidationError as error:
            raise TgClientError(response, error)
