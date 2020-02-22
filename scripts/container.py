#!/usr/bin/env python3
import sys
from os.path import join, realpath, dirname
sys.path.append(dirname(realpath(__file__)))
from subprocess import check_call, PIPE, check_output
from pathlib import Path
import argparse
import re
from os import makedirs
from shutil import rmtree
from config import Config


def run(target):
    container_config = Config.get(target)
    image = container_config['image']
    name = Config.alias(target)
    pre = container_config['pre']
    container_run_opts = container_config.get('run_options', [])
    global_run_opts = Config.get('global').get('run_options', [])

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
    config = Config.get(target)
    image = config['image']
    name = Config.alias(target)

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
