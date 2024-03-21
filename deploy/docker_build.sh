#!/bin/bash

. ./config

DOCKER_IMAGE_NAME=vpn

docker build -t $DOCKER_IMAGE_NAME .

docker run --sysctl net.ipv4.ip_forward=1 -it vpn