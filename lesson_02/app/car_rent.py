import asyncio
from asyncio import Queue, Event
from collections import defaultdict
from typing import Optional, Any, Dict, Set

from app.const import MAX_PARALLEL_AGG_REQUESTS_COUNT, WORKERS_COUNT


class PipelineContext:
    def __init__(self, user_id: int, data: Optional[Any] = None):
        self._user_id = user_id
        self.data = data

    @property
    def user_id(self):
        return self._user_id


CURRENT_AGG_REQUESTS_COUNT = 0
BOOKED_CARS: Dict[int, Set[str]] = defaultdict(set)
IS_RUNNING = False


async def get_offers(source: str) -> list[dict]:
    """
    Эта функция эмулирует асинхронных запрос по сети в сервис каршеринга source.
    Например source = "yandex" - запрашиваем список свободных автомобилей в сервисе yandex.

    Keyword arguments:
    source - сайт каршеринга
    """
    await asyncio.sleep(1)
    return [
        {"url": f"http://{source}/car?id=1", "price": 1_000, "brand": "LADA"},
        {"url": f"http://{source}/car?id=2", "price": 5_000, "brand": "MITSUBISHI"},
        {"url": f"http://{source}/car?id=3", "price": 3_000, "brand": "KIA"},
        {"url": f"http://{source}/car?id=4", "price": 2_000, "brand": "DAEWOO"},
        {"url": f"http://{source}/car?id=5", "price": 10_000, "brand": "PORSCHE"},
    ]


async def get_offers_from_sourses(sources: list[str]) -> list[dict]:
    """
    Эта функция агрегирует предложения из списка сервисов по каршерингу

    Keyword arguments:
    sources - список сайтов каршеринга ["yandex", "belka", "delimobil"]
    """

    global CURRENT_AGG_REQUESTS_COUNT
    if CURRENT_AGG_REQUESTS_COUNT >= MAX_PARALLEL_AGG_REQUESTS_COUNT:
        await asyncio.sleep(10.0)

    CURRENT_AGG_REQUESTS_COUNT += 1
    result = await asyncio.gather(*[get_offers(source) for source in sources])
    CURRENT_AGG_REQUESTS_COUNT -= 1

    out = list()
    for item in result:
        out.extend(item)

    return out


async def chain_combine_service_offers(inbound: Queue[PipelineContext], outbound: Queue[PipelineContext], **kw):
    """
    Запускает N функций worker-ов для обработки данных из очереди inbound и передачи результата в outbound очередь.
    N worker-ов == WORKERS_COUNT (константа из app/const.py)

    Нужно подобрать такой примитив синхронизации, который бы ограничивал вызов функции
    get_offers_from_sourses для N воркеров.
    Ограничение количества вызовов - MAX_PARALLEL_AGG_REQUESTS_COUNT (константа из app/const.py)

    Keyword arguments:
    inbound: Queue[PipelineContext] - очередь данных для обработки
    """
    sem = asyncio.Semaphore(MAX_PARALLEL_AGG_REQUESTS_COUNT)
    tasks = [asyncio.Task(get_offers_worker(sem, inbound, outbound)) for _ in range(WORKERS_COUNT)]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks)
        print('chain_combine_service_offers cancelled')


async def get_offers_worker(sem: asyncio.Semaphore, inbound: Queue[PipelineContext], outbound: Queue[PipelineContext]):
    """Функция-воркер для обработки элементов из очереди при опросе сервисов"""
    try:
        while IS_RUNNING:
            item = await inbound.get()
            async with sem:
                item.data = await get_offers_from_sourses(item.data)
            await outbound.put(item)
    except asyncio.CancelledError:
        print('get_offers_worker canceled')


async def chain_filter_offers(
        inbound: Queue,
        outbound: Queue,
        brand: Optional[str] = None,
        price: Optional[int] = None,
        **kw,
):
    """
    Функция обработывает данных из очереди inbound и передает результат в outbound очередь.
    Нужно при наличии параметров brand и price - отфильтровать список предожений.

    Keyword arguments:
    brand: Optional[str] - название бренда по которому фильруем предложение. Условие brand == offer["brand"]
    price: Optional[int] - максимальная стоимость предложения. Условие price >= offer["price"]

    inbound: Queue[PipelineContext] - очередь данных для обработки
    """
    try:
        while IS_RUNNING:
            item = await inbound.get()
            item.data = [element for element in item.data if
                         (not brand or element.get('brand') == brand)
                         and (not price or element.get('price') <= price)]
            await outbound.put(item)
    except asyncio.CancelledError:
        print('chain_filter_offers cancelled')


async def cancel_book_request(user_id: int, offer: dict):
    """
    Эмулирует запрос отмены бронирования  авто
    """
    await asyncio.sleep(1)
    BOOKED_CARS[user_id].remove(offer.get("url"))
    print('book_request cancelled')


async def book_request(user_id: int, offer: dict, event: Event) -> dict:
    """
    Эмулирует запрос бронирования авто. В случае отмены вызывает cancel_book_request.
    """
    try:
        BOOKED_CARS[user_id].add(offer.get("url"))
        await asyncio.sleep(1)
        if event.is_set():
            event.clear()
        else:
            await event.wait()
        return offer
    except asyncio.CancelledError:
        await cancel_book_request(user_id, offer)


async def chain_book_car(inbound: Queue[PipelineContext], outbound: Queue[PipelineContext], **kw):
    """
    Запускает N функций worker-ов для обработки данных из очереди inbound и передачи результата в outbound очередь.
    Worker должен параллельно вызвать book_request для каждого предложения.
    Первый отработавший запрос передать в PipelineContext.
    Остальные запросы нужно отменить и вызвать для них cancel_book_request.

    Keyword arguments:
    inbound: Queue[PipelineContext] - очередь данных для обработки
    """
    tasks = [asyncio.Task(book_car_worker(inbound, outbound)) for _ in range(WORKERS_COUNT)]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks)
        print('chain_book_car cancelled')


async def book_car_worker(inbound: Queue[PipelineContext], outbound: Queue[PipelineContext]):
    """Функция-воркер для обработки элементов из очереди при бронировании машины"""
    tasks = list()
    try:
        while IS_RUNNING:
            event = Event()
            event.set()
            item = await inbound.get()
            tasks = [asyncio.Task(book_request(item.user_id, element, event)) for element in item.data]
            result, pending = await asyncio.wait(
                tasks,
                return_when='FIRST_COMPLETED')
            item.data = result.pop().result()

            for task in pending:
                task.cancel()
            await asyncio.gather(*pending)

            await outbound.put(item)

    except asyncio.CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks)
        print('book_car_worker cancelled')


async def stop_program(event: Event):
    await asyncio.sleep(5)
    global IS_RUNNING
    IS_RUNNING = False
    event.set()
    print('IS_RUNNING', IS_RUNNING)


def run_pipeline(inbound: Queue[PipelineContext]) -> Queue[PipelineContext]:
    """
    Необходимо создать asyncio.Task для функций:
    - chain_combine_service_offers
    - chain_filter_offers
    - chain_book_car

    Создать необходимые очереди для обмена данными между звеньями (chain-ами)
    -> chain_combine_service_offers -> chain_filter_offers -> chain_book_car ->

    Вернуть outbound очередь для звена chain_book_car

    Keyword arguments:
    inbound: Queue[PipelineContext] - очередь данных для обработки
    """
    global IS_RUNNING
    IS_RUNNING = True
    data_queue = Queue()
    filtred_queue = Queue()
    outbound = Queue()

    asyncio.create_task(chain_combine_service_offers(inbound, data_queue), name='offers')
    asyncio.create_task(chain_filter_offers(data_queue, filtred_queue), name='filters')
    asyncio.create_task(chain_book_car(filtred_queue, outbound), name='book_cars')

    return outbound


async def main():
    start_queue = Queue()
    event = Event()

    for num in range(1, 11):
        start_queue.put_nowait(PipelineContext(num, ['some1', 'some2', 'some3]']))

    asyncio.create_task(stop_program(event), name='stop_program')
    outbound = run_pipeline(start_queue)

    await event.wait()

    while not outbound.empty():
        item = outbound.get_nowait()
        print(item.user_id, item.data)


asyncio.run(main())
