from io_op_sync import time_analyzer
from cpu_op_sync import countdown
from io_op_threads import create_thread


@time_analyzer
def main():
    threads = [create_thread(countdown, (number,)) for number in range(1, 11)]
    for thread in threads:
        thread.join()
    print('Finaly')


if __name__ == '__main__':
    main()
