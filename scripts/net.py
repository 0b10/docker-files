#!/usr/bin/env python3
import sys
from os.path import realpath, dirname
sys.path.append(dirname(realpath(__file__)))
from subprocess import check_output, check_call, call
from ipaddress import ip_address
from config import Config
from common import Message
from docker.types import IPAMPool, IPAMConfig
from docker import DockerClient, APIClient


class Dns:
    def __init__(self, dig_opts=[]):
        self._dig_opts = dig_opts
        self._hostnames = []

    @property
    def hostnames(self):
        return self._hostnames

    def resolve(self, hostnames):
        assert isinstance(hostnames, list) and len(hostnames) > 0, \
            'hostnames should be a non-empty list'

        args = ['dig', '+short'] + self._dig_opts
        for hostname in hostnames:
            ip = check_output(args + [hostname]).decode('utf-8').split('\n')[0]
            assert ip_address(ip), 'invalid IP address returned for {}: {}'.format(hostname, ip)
            self._hostnames.append([hostname, ip, '32'])  # [2] is CIDR


class IPSet:
    def __init__(self, name, hostnames):
        assert isinstance(hostnames, list) and len(hostnames) > 0, \
            'hostnames should be a non-empty list'
        assert isinstance(name, str) and name, 'ipset name should be a non-empty string'

        self._name = name
        self._hostnames = hostnames

    @property
    def name(self):
        return self._name

    def create(self):
        call(['sudo', 'ipset', 'destroy', self._name])
        check_call(['sudo', 'ipset', 'create', self._name, 'hash:net'])
        for host in self._hostnames:
            ip = host[1]
            cidr = host[2]
            check_call(['sudo', 'ipset', 'add', self._name, '{}/{}'.format(ip, cidr)])


class HostFile:
    def __init__(self, out_path, hostnames):
        assert isinstance(hostnames, list) and len(hostnames) > 0, \
            'hostnames should be a non-empty list'
        self._out_path = out_path
        self._hostnames = hostnames

    def create(self):
        with open(self._out_path, 'w') as f:
            for host in self._hostnames:
                ip = host[1]
                hostname = host[0]

                assert ip_address(ip), 'invalid IP address returned for {}: {}'.format(hostname, ip)
                assert isinstance(hostname, str) and hostname, \
                    'hostname should be a non-empty string'

                f.write('{}\t{}\n'.format(ip, hostname))


class IPTables:
    # TODO: add logging
    def deny_all_out(self, name):
        return self

    def allow_output_set(self, name):
        args = ['iptables', '-I', 'OUTPUT', '-m', 'set', '--match-set',
                name, 'dst', '-j', 'ALLOW', ]
        check_call(args)
        return self


class DockerNet:
    def __init__(self, client, config, logger):
        assert isinstance(config, dict) and config, 'config should be a non-empty dict'

        self._client = client
        self._network = None
        self._logger = logger
        self._config = config

    def remove(self):
        if self._network:
            self._network.remove()
            self._logger.complete('existing network "{}" removed'.format(self._network.name))
        else:
            api = APIClient()
            bridge_name = self._config['bridge_name']
            nets = api.networks(names=[bridge_name])
            if nets:
                for net in nets:
                    api.remove_network(net['Id'])
                    self._logger.complete('existing network "{}" removed'.format(net['Name']))
        return self

    def create(self, replace=False):
        config = self._config
        pool = IPAMPool(
            subnet=config['subnet'],
            iprange=config['ip_range'],
            gateway=config['gateway'],
        )
        ipam_config = IPAMConfig(pool_configs=[pool])
        self._network = self._client.networks.create(
            name=config['bridge_name'],
            driver=config['driver'],
            ipam=ipam_config
        )
        self._logger.complete(config['bridge_name'], 'network created')
        return self


logger = Message()
dns = Dns()
dns.resolve(['freenode.net', 'example.com'])
ipset = IPSet('irc', dns.hostnames)
ipset.create()
hostfile = HostFile('/tmp/hosts', dns.hostnames).create()
net = DockerNet(client=DockerClient(base_url=Config.daemon_url()),
                config=Config.network('weechat'), logger=logger)
net.remove().create()

