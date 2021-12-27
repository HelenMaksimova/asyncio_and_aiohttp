import requests
import time

URL = 'https://api.covidtracking.com/v1/us/current.json'


def time_analyzer(func):
    """Декоратор для расчёта времени выполнения функции"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        delta_time = time.time() - start_time
        print(f'Execution time: {delta_time}\n')
        return result
    return wrapper


@time_analyzer
def send_request(url: str, number=None):
    """Функция для отправки простого get-запроса"""
    print(f'Send {number} request' if number else 'Send request')
    response = requests.get(url)
    print(f'Status code: {response.status_code}')


@time_analyzer
def main():
    for number in range(1, 11):
        send_request(URL, number)


if __name__ == "__main__":
    main()
