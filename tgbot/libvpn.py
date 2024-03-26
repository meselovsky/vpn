import os
import asyncio

from pathlib import Path

_CERTS_PATH = Path(os.getenv("SERVER_PKI_CERTS_DIR"))

def is_client_exists(client_name: str) -> bool:
    for f in _CERTS_PATH.glob("*"):
            if f.is_file() and f.stem == client_name:
                return True
    return False

async def create_client(client_name: str):
    process = await asyncio.create_subprocess_shell(
         f"bash scripts/vpn_pki_client {client_name}",
         stderr=asyncio.subprocess.PIPE)
    
    code = await process.wait()
    if code != 0:
        _, err = await process.communicate()
        raise Exception(f"<stderr>\n{err.decode()}\ngen_client error code: {code}\n</stderr>\n")

async def revoke_client(client_name: str):
    process = await asyncio.create_subprocess_shell(
        f"bash scripts/vpn_pki_revoke {client_name}",
        stderr=asyncio.subprocess.PIPE)
    
    code = await process.wait()
    _, err = await process.communicate()
    if code != 0:
        raise Exception(f"<stderr>\n{err.decode()}\ngen_client error code: {code}\n</stderr>\n")
    
async def generate_client_config(client_name: str) -> bytes:
    process = await asyncio.create_subprocess_shell(
        f"bash scripts/vpn_client {client_name}",
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE)
    
    code = await process.wait()
    out, err = await process.communicate()
    if code != 0:
        raise Exception(f"<stderr>\n{err.decode()}\ngen_client error code: {code}\n</stderr>\n")
    else:
        return out
    
