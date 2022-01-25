import ctypes
import os
import tempfile
from datetime import datetime
from signal import SIGINT
from time import sleep

from fuse import FUSE, fuse_exit
from threading import Thread

from main import Passthrough


def fuse_exit():
    """
    srced from https://github.com/fusepy/fusepy/issues/116#issuecomment-391090718
    """
    os.kill(os.getpid(), SIGINT)


def walk(path, pref=''):
    if os.path.isdir(path):
        for i in os.listdir(path):
            yield from walk(os.path.join(path, i), pref + '> ')
    else:
        print(f'{pref}{path}')
        yield path


def test(mountpoint):
    try:
        sleep(0.5)
        print('Starting tests')

        times = []
        for x in range(5):
            times.append(datetime.utcnow())
            print([*walk(mountpoint)])
        last = datetime.utcnow()

        for i, x in enumerate(times):
            print(i, '--', last - x)

        print('All tests done')
    finally:
        fuse_exit()


def main():
    token = open('token.txt').read().strip()
    with tempfile.TemporaryDirectory() as mountpoint:
        print('mountpoint = ', mountpoint)

        ops = Passthrough(token)

        t = Thread(target=test, args=(mountpoint, ))
        t.start()

        print('FUSE starting')
        FUSE(ops, mountpoint, debug=True)
        print('FUSE exited', flush=True)
        t.join()


if __name__ == '__main__':
    main()
