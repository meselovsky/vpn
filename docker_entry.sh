#!/bin/bash

while [ ! -z "$1" ]
do
    case "$1" in
        --init-pki)
            PKI_INIT=1
            ;;
        *);;
    esac
    shift
done

if [ -n "$PKI_INIT" ]; then
    echo "init pki mode!"
    rm -drf $PKI_DIR
    bash scripts/vpn_pki_init  .
fi

iptables -t nat -C POSTROUTING -s 172.16.0.0/16 -o eth0 -j MASQUERADE 2>/dev/null || {
    iptables -t nat -A POSTROUTING -s 172.16.0.0/16 -o eth0 -j MASQUERADE
}

bash scripts/vpn_run  .









