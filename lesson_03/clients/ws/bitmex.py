import aiohttp


async def fetch_10() -> list[float]:
    socket_url = 'wss://ws.bitmex.com/realtime'
    result = list()
    async with aiohttp.ClientSession() as session:
        ws = await session.ws_connect(socket_url)
        count = 10
        await ws.send_json({"op": "subscribe", "args": ['instrument:XBTUSD']})
        while count:
            item = await ws.receive_json()
            data = item.get('data')
            if data and 'fairPrice' in data[0]:
                result.append(data[0].get('fairPrice'))
                count -= 1
        return result


# Вариант для прохождения теста (у объекта мока не оказалось методов receive или receive_json):

async def fetch_10_for_test() -> list[float]:
    socket_url = 'wss://ws.bitmex.com/realtime'
    result = list()
    async with aiohttp.ClientSession() as session:
        ws = await session.ws_connect(socket_url)
        count = 0
        await ws.send_json({"op": "subscribe", "args": ['instrument:XBTUSD']})
        async for item in ws:
            data = item.json().get('data')
            if data and 'fairPrice' in data[0]:
                result.append(data[0].get('fairPrice'))
                count += 1
            if count == 10:
                break
        return result
