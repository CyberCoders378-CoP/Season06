# Loader.py
import os, zlib, random


class Loader:
    def __init__(self, seed: int):
        self.seed = seed

        # Obfuscated salts split across constants & ops (not bulletproof, but fine for PCAP level)
        self._A = 0x51A ^ 0x1  # 0x51B
        self._B = (0xDEAD << 1) ^ 0xBEEF  # some noisy bits

    def _k(self, seed: int, name: str) -> int:
        return (seed ^ self._A ^ zlib.crc32(name.encode()) ^ self._B) & 0xFFFFFFFF


    def _keystream(self, seed_key: int):
        r = random.Random(seed_key)
        while True:
            # 32 bytes per chunk
            n = r.getrandbits(32)
            yield from n.to_bytes(4, 'little')

    def stream_decrypt_lines(self, path: str):
        fname = os.path.basename(path)
        ks = self._keystream(self._k(self.seed, fname))
        with open(path, 'rb') as f:
            # first 4 bytes = uncompressed size (uint32 little-endian), XOR’ed
            sz_enc = bytes([b ^ next(ks) for b in f.read(4)])
            target_sz = int.from_bytes(sz_enc, 'little')

            # rest = compressed payload XOR’ed
            enc = f.read()
            dec = bytes(b ^ next(ks) for b in enc)
            raw = zlib.decompress(dec)
            assert len(raw) == target_sz

            # yield fixed-width lines
            for i in range(0, len(raw), 13):  # W = 13
                yield raw[i:i+13].decode('ascii')
