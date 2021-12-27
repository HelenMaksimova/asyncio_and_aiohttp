from io_op_sync import time_analyzer


@time_analyzer
def countdown(number):
    print(f'Start {number} function')
    i = 0
    while i < 5_000_000:
        i += 1
    print(f'Finished {number} function')


@time_analyzer
def main():
    for number in range(1, 11):
        countdown(number)
    print('Finaly')


if __name__ == '__main__':
    main()
