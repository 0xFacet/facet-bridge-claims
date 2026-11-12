#!/usr/bin/env python3
"""Check Facet bridge claim data against its Merkle root. Python 3 standard library only.

  python3 verify.py claims/<token>/<address>.json    every leaf's proof against the file's claimRoot
  python3 verify.py packages/claims_<token>.json      rebuild the whole tree and compare with the package's root
  python3 verify.py --all                             both, for every file in this directory

Then compare the printed root with the token bridge's on-chain root: Etherscan → the bridge address → Contract →
Read as Proxy → settlement → claimRoot. Any copy of these files, from anywhere, is valid if the root matches.
The contract computes leaf = keccak256(abi.encode(leafIndex, recipient, ids)) and checks a sorted-pair Merkle proof.
"""
import glob, json, os, sys

# ---- Keccak-256 (the Ethereum variant, original padding)
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
       0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
       0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
       0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]   # [x][y]
_M = (1 << 64) - 1

def _rol(v, n): return ((v << n) | (v >> (64 - n))) & _M if n else v

def _f(A):
    for rc in _RC:
        C = [A[x] ^ A[x + 5] ^ A[x + 10] ^ A[x + 15] ^ A[x + 20] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        A = [A[i] ^ D[i % 5] for i in range(25)]
        B = [0] * 25
        for x in range(5):
            for y in range(5):
                B[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(A[x + 5 * y], _ROT[x][y])
        A = [B[x + 5 * y] ^ (~B[(x + 1) % 5 + 5 * y] & B[(x + 2) % 5 + 5 * y]) for y in range(5) for x in range(5)]
        A[0] ^= rc
    return A

def keccak256(data):
    rate = 136
    buf = bytearray(data) + b"\x01"
    buf += b"\x00" * ((-len(buf)) % rate)
    buf[-1] |= 0x80
    A = [0] * 25
    for off in range(0, len(buf), rate):
        for i in range(rate // 8):
            A[i] ^= int.from_bytes(buf[off + 8 * i: off + 8 * i + 8], "little")
        A = _f(A)
    return b"".join(A[i].to_bytes(8, "little") for i in range(4))

assert keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

# ---- leaves and proofs, as FacetEthscriptionBridgeV7.claim checks them
def _w(x): return int(x).to_bytes(32, "big")

def leaf_hash(index, recipient, ids):
    return keccak256(_w(index) + bytes(12) + bytes.fromhex(recipient[2:]) + _w(0x60) + _w(len(ids)) + b"".join(bytes.fromhex(i[2:]) for i in ids))

def pair(a, b): return keccak256(a + b) if a <= b else keccak256(b + a)

def root_from_proof(leaf, proof):
    h = leaf
    for p in proof: h = pair(h, bytes.fromhex(p[2:]))
    return h

def tree_root(leaves):
    layer = leaves[:]
    while len(layer) > 1:
        if len(layer) % 2: layer = layer + [layer[-1]]
        layer = [pair(layer[i], layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0]

def check_address_file(path):
    d = json.load(open(path))
    root = bytes.fromhex(d["claimRoot"][2:])
    for l in d["leaves"]:
        got = root_from_proof(leaf_hash(l["leafIndex"], d["recipient"], l["ids"]), l["proof"])
        if got != root: raise SystemExit(f"FAIL {path} leaf {l['leafIndex']}: proof gives 0x{got.hex()}, file says {d['claimRoot']}")
    return d

def check_package(path):
    d = json.load(open(path))
    leaves = sorted(d["leaves"], key=lambda l: l["index"])
    assert [l["index"] for l in leaves] == list(range(len(leaves))) == list(range(d["leafCount"])), "leaf indexes are not 0..leafCount-1"
    got = "0x" + tree_root([leaf_hash(l["index"], l["recipient"], l["ids"]) for l in leaves]).hex()
    if got != d["root"]: raise SystemExit(f"FAIL {path}: tree root {got} != package root {d['root']}")
    ids = [i for l in leaves for i in l["ids"]]
    assert len(ids) == len(set(ids)), "an inscription appears in two leaves"
    return d, len(ids)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    args = sys.argv[1:]
    if args == ["--all"]:
        for p in sorted(glob.glob(os.path.join(here, "packages", "claims_*.json"))):
            d, n = check_package(p); print(f"OK  {os.path.basename(p)}: root {d['root']}, {d['leafCount']} leaves, {n} inscriptions")
        files = sorted(glob.glob(os.path.join(here, "claims", "*", "*.json")))
        for p in files: check_address_file(p)
        print(f"OK  {len(files)} address files: every proof matches its root")
    elif len(args) == 1 and "packages" in args[0]:
        d, n = check_package(args[0]); print(f"OK  root {d['root']}: {d['leafCount']} leaves, {n} inscriptions")
    elif len(args) == 1:
        d = check_address_file(args[0])
        print(f"OK  {d['recipient']} on {d['token']}: {sum(len(l['ids']) for l in d['leaves'])} inscriptions in {len(d['leaves'])} leaf/leaves, root {d['claimRoot']}")
        print(f"    compare with settlement().claimRoot on {d['bridge']}")
    else:
        sys.exit(__doc__)
