FROM ubuntu:latest

ARG APP_DIR=/root/app
ARG CONFIG_DIR=.

ENV PKI_DIR /etc/openvpn/server/keys
# ENV SERVER_LOCAL_IP 
ENV  SERVER_LOCAL_PORT 8888

ENV TGBOT_TOKEN 7153515581:AAGLgLq0HUYuXkjz5tzAozQ4_CjjbqxSAyg
ENV TGBOT_ADMIN_USERNAME meselovsky

EXPOSE $SERVER_LOCAL_PORT/udp

# VOLUME [ "${APP_DIR}" ]

RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}

COPY tgbot ${APP_DIR}/tgbot
COPY scripts ${APP_DIR}/scripts
COPY docker_entry.sh ${APP_DIR}
COPY ${CONFIG_DIR}/config ${APP_DIR}
COPY ${CONFIG_DIR}/server.conf ${APP_DIR}
COPY ${CONFIG_DIR}/client.ovpn ${APP_DIR}

RUN mkdir -p ${PKI_DIR}

COPY ${CONFIG_DIR}/pki* ${PKI_DIR}

RUN apt-get update
RUN apt-get install -y curl openssl openvpn iptables gettext python3 pip nano
RUN pip install python-telegram-bot
#RUN iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# ENTRYPOINT [ "./docker_entry.sh" ]
ENTRYPOINT [ "bash", "./docker_entry.sh" ]




