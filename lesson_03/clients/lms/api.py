from typing import Tuple
import json
import re

from aiohttp import ClientResponse, BasicAuth

from clients.base import ClientError, Client


class LmsClientError(ClientError):
    pass


class LmsClient(Client):
    BASE_PATH = 'https://lms.metaclass.kts.studio'

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    async def _handle_response(self, resp: ClientResponse) -> Tuple[dict, ClientResponse]:
        if not resp.status == 200:
            raise LmsClientError(resp, f'status: {resp.status}')
        try:
            response = await resp.json()
            if not response:
                raise LmsClientError(resp, 'empty response')
            return response, resp
        except json.decoder.JSONDecodeError as error:
            raise LmsClientError(resp, error)

    def get_path(self, url: str) -> str:
        base_path = self.get_base_path().strip('/')
        url = url.lstrip('/')
        return f'{base_path}/api/{url}'

    async def get_user_current(self) -> dict:
        cookies = {'sessionid': self.token}
        result = await self._perform_request('get', self.get_path('v2.user.current'), cookies=cookies)
        return result[0]

    async def login(self, email: str, password: str) -> str:
        payload = {'email': email, 'password': password}
        result = await self._perform_request('post', self.get_path('v2.user.login'), json=payload)
        cookies = result[1].headers.get('Set-Cookie')
        sessionid = re.findall(r'^sessionid=(\w+);\s', cookies)[0]
        return sessionid
