from multiprocessing import Process

from io_op_sync import send_request, time_analyzer, URL


@time_analyzer
def main():
    processes = []
    for number in range(1, 11):
        process = Process(target=send_request, args=(URL, number))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()


if __name__ == "__main__":
    main()
