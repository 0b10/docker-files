from os.path import isfile, join, realpath
from pathlib import Path


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

    def complete(self, msg):
        print(" ", Color.GREEN, "+", msg, "...ok", Color.ENDC)

    def failed(self, msg):
        print(" ", Color.RED, "ERROR:", msg, "...failed", Color.ENDC)
