from os.path import isfile, join, realpath
from pathlib import Path
from subprocess import check_call, PIPE, check_output
from os import makedirs
from shutil import rmtree


class Project:
    BASE = realpath(Path(__file__) / '..' / '..')


assert isfile(join(Project.BASE, 'Makefile')), \
    'Project.BASE doesn\'t point to the correct location. Using Makefile existence as a reference'


class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'


class Message:
    def warn(self, msg):
        print(" ", Color.YELLOW, "WARN:", msg, Color.ENDC)

    def error(self, msg):
        print(" ", Color.RED, "ERROR:", msg, Color.ENDC)

    def info(self, *args):
        print(Color.ENDC, *args, Color.ENDC)

    def complete(self, *msg):
        print(" ", Color.GREEN, "+", *msg, "...ok", Color.ENDC)

    def failed(self, msg):
        print(" ", Color.RED, "ERROR:", msg, "...failed", Color.ENDC)


def mount_overlay(lower, upper, work, merged):
    check_output(['sudo', 'mount', '-t', 'overlay', 'overlay', '-o',
                  'lowerdir={0},upperdir={1},workdir={2}'.format(lower, upper, work),
                  merged], stderr=PIPE)


def unmount_overlay(mountpoint):
    check_output(['sudo', 'umount', mountpoint], stderr=PIPE)


def make_dirs(dirs):
    assert type(dirs) is list, '"dirs" to be created should be a list'
    for dir_ in dirs:
        makedirs(dir_, mode=0o770, exist_ok=True)


def rm_dirs(dirs, clean=False, ignore_errors=False):
    assert type(dirs) is list, '"dirs" to be removed should be a list'
    for dir_ in dirs:
        rmtree(dir_, ignore_errors=ignore_errors)

    if clean:
        make_dirs(dirs)
