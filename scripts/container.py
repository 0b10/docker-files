#!/usr/bin/env python3
from subprocess import check_call, PIPE, check_output
from pathlib import Path
import argparse
import re
from os import makedirs
from shutil import rmtree

WEECHAT_HOME = Path().home() / '.weechat'
WEECHAT_COW = Path().home() / '.weechat_cow'
WEECHAT_UPPERDIR = WEECHAT_COW / 'upperdir'
WEECHAT_WORKDIR = WEECHAT_COW / 'workdir'
WEECHAT_MERGED = WEECHAT_COW / 'merged'


CONFIG = {
    'global': {
        'run_options': [
            '--rm',
            '--interactive',
            '--tty',
            '--cap-drop=ALL',
            '--read-only',
            '--privileged=False'
        ]
    },
    'weechat': {
        'image': '0b10/weechat:edge',
        'run_options': [
            '--volume',
            '{}:/weechat:rw'.format(WEECHAT_MERGED)
        ],
        'pre': [
            {
                'description': 'discarding any previous overlay data',
                'job': lambda: _rm_dirs(dirs=[WEECHAT_UPPERDIR], ignore_errors=True)
            },
            {
                'description': 'creating overlay directories',
                'job': lambda: _make_dirs(
                    [WEECHAT_HOME, WEECHAT_UPPERDIR, WEECHAT_WORKDIR, WEECHAT_MERGED]
                )
            },
            {
                'description': 'mounting overlay fs',
                'job': lambda: _mount_overlay(lower=WEECHAT_HOME, upper=WEECHAT_UPPERDIR,
                                              work=WEECHAT_WORKDIR, merged=WEECHAT_MERGED)
            }
        ],
        'post': [
            {
                'description': 'unmounting overlay fs',
                'job': lambda: _unmount_overlay(mountpoint=WEECHAT_MERGED)
            },
            {
                'description': 'discarding overlay data',
                'job': lambda: _rm_dirs(dirs=[WEECHAT_UPPERDIR], clean=True)
            }
        ],
    }
}

ALIAS = {
    'weechat': 'weechat',
    'wc': 'weechat',
}


def _get_config(alias):
# {'tag': '0b10/weechat:edge', 'dir': 'weechat'}
    name = ALIAS.get(alias, alias)
    return CONFIG[name]


def _mount_overlay(lower, upper, work, merged):
    check_output(['sudo', 'mount', '-t', 'overlay', 'overlay', '-o',
                  'lowerdir={0},upperdir={1},workdir={2}'.format(lower, upper, work),
                  merged], stderr=PIPE)


def _unmount_overlay(mountpoint):
    check_output(['sudo', 'umount', mountpoint], stderr=PIPE)


def _make_dirs(dirs):
    assert type(dirs) is list, '"dirs" to be created should be a list'
    for dir_ in dirs:
        makedirs(dir_, mode=0o770, exist_ok=True)


def _rm_dirs(dirs, clean=False, ignore_errors=False):
    assert type(dirs) is list, '"dirs" to be removed should be a list'
    for dir_ in dirs:
        rmtree(dir_, ignore_errors=ignore_errors)

    if clean:
        _make_dirs(dirs)


def run(target):
    container_config = _get_config(target)
    image = container_config['image']
    name = ALIAS[target]
    pre = container_config['pre']
    container_run_opts = container_config.get('run_options', [])
    global_run_opts = _get_config('global').get('run_options', [])

    # run jobs before - mounting etc
    if pre is not None:
        for p in pre:
            print(p['description'])
            p['job']()

    args = ["docker", "run"] + global_run_opts + container_run_opts

    args.append(image)

    print("running '{}' in {}...".format(name, image))
    print('run options:', ' '.join(global_run_opts + container_run_opts))
    check_call(args)

    # run jobs after - unmounting etc
    post = container_config['post']
    if post is not None:
        for p in post:
            print(p['description'])
            p['job']()


def stop(target):
    config = _get_config(target)
    image = config['image']
    name = ALIAS[target]

    cid_args = ['docker', 'ps', '--quiet', '--filter', 'ancestor={}'.format(image)]

    # get container ids - there could be multiple. [''] returned when none found
    cids = check_output(cid_args, stderr=PIPE)\
        .decode('utf-8')\
        .split('\n')

    cids = [i for i in cids if i]  # strip falsy strings (newlines cause empty items)

    # must be after falsy strings are stripped, because cids==[''] when no id is found.
    if len(cids) == 0:
        print('No container for {} is running'.format(name))
        return

    for cid in cids:
        assert(re.fullmatch(r'[0-9a-f]{12}', cid, flags=re.I)), \
            "Invalid container ID: {}".format(cid)

        print("stopping '{}' - IMG:{}; ID:{}...".format(name, image, cid))
        check_output(['docker', 'stop', cid],  stderr=PIPE)


parser = argparse.ArgumentParser(description="Manage docker containers")

control_group = parser.add_argument_group('control')
control_group.add_argument("system", nargs=1, choices=["run", "stop"], help="action")
control_group.add_argument("target",
                           choices=["wc", "weechat"],
                           help="the name of the container")

args = parser.parse_args()


{
    'run': lambda: run(args.target),
    'stop': lambda: stop(args.target),
}[args.system[0]]()
