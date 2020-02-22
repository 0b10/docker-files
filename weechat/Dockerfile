FROM alpine:edge

RUN echo https://pkg.adfinis-sygroup.ch/alpine/edge/main/ > /etc/apk/repositories && \
  echo https://pkg.adfinis-sygroup.ch/alpine/edge/community/ >> /etc/apk/repositories

RUN apk update && apk upgrade && apk add weechat

ENV LANG C.UTF-8
ENV HOME /weechat

RUN mkdir -p $HOME/.weechat &&\
  addgroup weechat &&\
  adduser -h $HOME -D -s /bin/ash -G weechat weechat &&\
  chown -R weechat:weechat $HOME

WORKDIR $HOME
USER weechat
ENTRYPOINT ["weechat"]