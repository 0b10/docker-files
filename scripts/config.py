#!/usr/bin/env python3
import sys
from os.path import join, realpath, dirname
sys.path.append(dirname(realpath(__file__)))
from pathlib import Path
from common import rm_dirs, make_dirs, mount_overlay, unmount_overlay

WEECHAT_CONTAINER_DIR = Path().home() / '.weechat'
WEECHAT_HOME = WEECHAT_CONTAINER_DIR / 'client'
WEECHAT_COW = WEECHAT_CONTAINER_DIR / 'cow'
WEECHAT_UPPERDIR = WEECHAT_COW / 'upperdir'
WEECHAT_WORKDIR = WEECHAT_COW / 'workdir'
WEECHAT_MERGED = WEECHAT_COW / 'merged'
WEECHAT_NET = WEECHAT_CONTAINER_DIR / '.weechat_net'
WEECHAT_HOSTS_FILE = WEECHAT_NET / 'hosts'

CONFIG = {
    'alias': {
        'weechat': 'weechat',
        'wc': 'weechat',
    },
    'global': {
        'run_options': [
            '--rm',
            '--interactive',
            '--tty',
            '--cap-drop=ALL',
            '--read-only',
            '--privileged=False'
        ],
        'daemon_url': 'unix://var/run/docker.sock'
    },
    'weechat': {
        'image': '0b10/weechat:edge',
        'project_dir': 'weechat',
        'run_options': [
            '--volume',
            '{}:/weechat:rw'.format(WEECHAT_MERGED)
        ],
        # docker network create --driver=bridge --subnet=172.18.0.0/30 --ip-range=172.18.0.0/30 --gateway=172.18.0.1 weechat-bridge
        'network': {
            'bridge_name': 'weechat-bridge',
            'driver': 'bridge',
            'subnet': '172.18.0.0/30',
            'ip_range': '172.18.0.0/30',
            'gateway': '172.18.0.1'
        },
        'pre': [
            {
                'description': 'discarding any previous overlay data',
                'job': lambda: rm_dirs(dirs=[WEECHAT_UPPERDIR], ignore_errors=True)
            },
            {
                'description': 'creating overlay directories',
                'job': lambda: make_dirs(
                    [WEECHAT_HOME, WEECHAT_UPPERDIR, WEECHAT_WORKDIR, WEECHAT_MERGED]
                )
            },
            {
                'description': 'mounting overlay fs',
                'job': lambda: mount_overlay(lower=WEECHAT_HOME, upper=WEECHAT_UPPERDIR,
                                             work=WEECHAT_WORKDIR, merged=WEECHAT_MERGED)
            }
        ],
        'post': [
            {
                'description': 'unmounting overlay fs',
                'job': lambda: unmount_overlay(mountpoint=WEECHAT_MERGED)
            },
            {
                'description': 'discarding overlay data',
                'job': lambda: rm_dirs(dirs=[WEECHAT_UPPERDIR], clean=True)
            }
        ],
    }
}


class Config:
    @classmethod
    def alias(cls, alias):
        return CONFIG['alias'].get(alias, alias)

    @classmethod
    def get(cls, alias):
        return CONFIG[cls.alias(alias)]

    @classmethod
    def daemon_url(cls):
        return CONFIG['global']['daemon_url']

    @classmethod
    def network(cls, alias):
        name = cls.alias(alias)
        return CONFIG[name]['network']

    @classmethod
    def image_name(cls, alias):
        name = cls.alias(alias)
        return CONFIG[name]['image']

    @classmethod
    def project_dir(cls, alias):
        name = cls.alias(alias)
        return CONFIG[name]['project_dir']

    @classmethod
    def all_aliases(cls):
        return CONFIG['alias'].keys()
