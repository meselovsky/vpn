FROM ubuntu:latest

ARG APP_DIR=/root/app
ARG CONFIG_DIR=.

VOLUME [ "/vpn_media" ]

RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}

COPY scripts ${APP_DIR}/scripts
COPY ${CONFIG_DIR}/config ${APP_DIR}
COPY ${CONFIG_DIR}/server.conf ${APP_DIR}
COPY ${CONFIG_DIR}/openssl.conf ${APP_DIR}
COPY ${CONFIG_DIR}/client.ovpn ${APP_DIR}

RUN apt-get update && apt-get install -y curl openssl openvpn iptables gettext nano

ENTRYPOINT [ "bash", "scripts/vpn_entry" ]




