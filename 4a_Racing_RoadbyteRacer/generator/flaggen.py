# ep4_tools/flaggen.py
import hmac, hashlib, base64


SECRET_FLAG = b"\x9c\x1f\x02\xad\x77\x4b\xcc\x90\xea\xb5\x11\xde\x07\x44\xfa\x21"


def flag(user: str, seed: int, dodges: int, chal_id: str="EP4A") -> str:
    msg = f"{user}|{seed}|{dodges}|{chal_id}".encode()
    tag = hmac.new(SECRET_FLAG, msg, hashlib.sha256).digest()
    return f"{chal_id}-" + base64.b32encode(tag).decode().rstrip("=").lower()[:12]


if __name__ == "__main__":
    import sys
    u, s, d = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    print(flag(u,s,d))
