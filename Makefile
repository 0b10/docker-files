SHELL = /bin/sh

host-packages:
	scripts/build.py --system-packages docker python3-docker ipset bind-utils

host-build-all:
	scripts/build.py --build weechat

host-all: host-packages host-build-all
