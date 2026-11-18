"""给发布二进制附加已有内嵌 payload 的偏移与校验和，不重复保存运行时。"""
import hashlib
from pathlib import Path
import struct
import sys


def index(binary: bytes, payload: bytes) -> bytes:
    offset = binary.find(payload)
    if not payload or offset < 0:
        raise ValueError('二进制中未找到完整 payload')
    return binary + struct.pack('<QQ', offset, len(payload)) + hashlib.sha256(payload).digest() + b'EASYSUB_PAYLOAD1'


if __name__ == '__main__':
    path = Path(sys.argv[1])
    path.write_bytes(index(path.read_bytes(), Path(sys.argv[2]).read_bytes()))
