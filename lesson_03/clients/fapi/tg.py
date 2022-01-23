import aiohttp
import json

from clients.tg.api import TgClient, TgClientError
from clients.tg.dcs import File, Message


class TgClientWithFile(TgClient):
    async def get_file(self, file_id: str) -> File:
        params = {'file_id': file_id}
        result = await self._perform_request('get', self.get_path('getFile'), params=params)
        return File.Schema().load(result.get('result'))

    async def download_file(self, file_path: str, destination_path: str):
        url = f'{self.get_base_path()}/file/bot{self.token}/{file_path}'
        async with self.session:
            async with self.session.get(url) as resp:
                if not resp.status == 200:
                    raise TgClientError(resp, f'status: {resp.status}')
                with open(destination_path, 'wb') as fd:
                    async for data in resp.content.iter_chunked(1024):
                        fd.write(data)

    async def send_document(self, chat_id: int, document_path) -> Message:
        async with self.session:
            data = aiohttp.FormData()
            data.add_field('chat_id', chat_id)
            data.add_field('document', open(document_path, 'rb'))
            async with self.session.post(self.get_path('sendDocument'), data=data) as resp:
                if not resp.status == 200:
                    raise TgClientError(resp, f'status: {resp.status}')
                try:
                    result = await resp.json()
                    return Message.Schema().load(result.get('result'))
                except json.decoder.JSONDecodeError as error:
                    raise TgClientError(resp, error)
