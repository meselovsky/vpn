docker run --sysctl net.ipv4.ip_forward=1 --cap-add=NET_ADMIN -it vpn
docker run --sysctl net.ipv4.ip_forward=1 --cap-add=NET_ADMIN -p 8888:8888/udp -it vpn --init-pki