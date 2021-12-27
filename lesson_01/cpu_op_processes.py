from multiprocessing import Process

from io_op_sync import time_analyzer
from cpu_op_sync import countdown


@time_analyzer
def main():
    processes = []
    for number in range(1, 11):
        process = Process(target=countdown, args=(number,))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()
    print('Finaly')


if __name__ == "__main__":
    main()
