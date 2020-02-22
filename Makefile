SHELL = /bin/sh

WEECHAT_NAME=0b10/weechat:edge

host-packages:
	scripts/build.py --system-packages docker python3-docker

host-build-all:
	scripts/build.py --build weechat=$(WEECHAT_NAME)

host-all: host-packages host-build-all
