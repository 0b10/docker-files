#!/usr/bin/env python3
import sys
from os.path import realpath, isdir, join, dirname
sys.path.append(dirname(realpath(__file__)))
from common import Message, Project
from subprocess import check_call
from abc import ABC
from importlib import import_module
from re import match, fullmatch, I
from argparse import ArgumentParser


class Setup:
    def __init__(self, logger, system=None, docker=None):
        self._logger = logger
        self._system = system
        self._docker = docker

    def system_install(self, pkgs):
        assert isinstance(pkgs, list) and len(pkgs) > 0, \
            'system package list is empty or not a list'
        assert self._system is not None, 'system interface not set'
        self._logger.info("Installing:", pkgs)
        self._system.install(pkgs)
        self._logger.complete(pkgs)

    def docker_install(self, targets):
        assert self._docker is not None, "You must install/initilise the docker module first"
        self._logger.info("installing docker images")
        self._docker.install(targets=targets)


class DockerAbstract(ABC):
    def __init__(self, docker_module, base_url, logger):
        # ! must be initialised after python-docker is installed
        self._docker_module = docker_module
        self._logger = logger

        assert not match(r'/^unix:\/\//', base_url), \
            "The current docker configuration won't use TLS, aborting setup"
        self._client = docker_module.DockerClient(base_url=base_url)

    def install(self, targets):
        """
        targets: [{ 'tag': .., 'dir': .. }, ...]
        dir is only useful for building docker images, so it can be left out for pulling images.
        tag shall be used to pull images, or to tag the built image: base/name:tag
        """
        raise NotImplementedError


class DockerBuild(DockerAbstract):
    def __init__(self, docker_module, base_url, logger):
        super().__init__(docker_module=docker_module, base_url=base_url, logger=logger)

    def install(self, targets):
        assert isinstance(targets, list) and len(targets) > 0, \
            'docker targets should be a populated list'
        assert all([isinstance(t, dict) for t in targets]), 'targets should contain only dicts'
        for target in targets:
            path = join(Project.BASE, target['dir'])
            assert isdir(path), 'docker build directory doesn\'t exist: ' + path
            self._logger.info("building {}".format(target['tag']))
            self._client.images.build(path=path, tag=target['tag'], network_mode='host')
            self._logger.complete(target['tag'])


class PackageManagerAbstract(ABC):
    def install(self, pkgs):
        raise NotImplementedError


class Dnf(PackageManagerAbstract):
    def install(self, pkgs):
        check_call(["sudo", "dnf", "install", "-y"] + pkgs)


def _parse_build_targets(targets):
    result = []
    for target in targets:
        assert fullmatch(r'^[-\w]+=[-\w]+\/[-\w]+:[-\w]+$', target, I), \
            'build_target should be in the form foo=base/name:tag, not: {}'.format(target)
        pair = target.split('=')
        result.append({'dir': pair[0], 'tag': pair[1]})
    return result


def pm_factory(
        PackageManager=Dnf,
        logger=Message()):

    assert issubclass(PackageManager, PackageManagerAbstract), \
        'PackageManager param must be subclass of PackageManagerAbstract'

    pm_setup = Setup(logger=logger, system=PackageManager())

    return pm_setup


def docker_factory(
        logger=Message(),
        Docker=DockerBuild,
        docker_server_url='unix://var/run/docker.sock'):

    assert issubclass(Docker, DockerAbstract), 'Docker param must be subclass of DockerAbstract'

    sys.path.append(dirname(realpath(__file__)))

    docker_module = import_module('docker')
    docker = Docker(docker_module=docker_module, base_url=docker_server_url, logger=logger)
    docker_setup = Setup(logger=logger, docker=docker)

    return docker_setup


# pm_setup, docker_setup = factory()

# # pm_setup.system_install(pkgs=['python3-docker', 'docker'])
# # docker_setup.docker_install(targets=[{'tag': '0b10/weechat:edge', 'dir': 'weechat'}])

# # 'unix://var/run/docker.sock'
parser = ArgumentParser(description="Build/install docker images, and associated files/scripts")
parser.add_argument("--build",
                    action="store",
                    nargs="+",
                    dest="build_targets",
                    help="build the local docker files")

parser.add_argument("--system-packages",
                    action="store",
                    nargs="+",
                    dest="system_packages",
                    help="install packages into the system via the package manager")

args = parser.parse_args()

logger = Message()

if args.system_packages:
    pm_setup = pm_factory(logger=logger)
    pm_setup.system_install(pkgs=args.system_packages)

if args.build_targets:
    docker_setup = docker_factory(logger=logger)
    docker_setup.docker_install(targets=_parse_build_targets(args.build_targets))
