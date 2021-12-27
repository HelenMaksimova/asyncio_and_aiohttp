from threading import Thread

from io_op_sync import time_analyzer, send_request, URL


def create_thread(func, params):
    thread = Thread(target=func, args=params)
    thread.start()
    return thread


@time_analyzer
def main():
    threads = [create_thread(send_request, (URL, number)) for number in range(10)]
    for thread in threads:
        thread.join()
    print('Finaly')


if __name__ == "__main__":
    main()

