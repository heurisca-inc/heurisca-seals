#!/usr/bin/env python3
"""Verify a Heurisca reveal packet against the public seal record.

Standard library only. No installation, no dependencies, no Heurisca code --
that is the point. If checking this record required trusting Heurisca's own
software, it would not be a check.

Usage:
    python3 verify_seal.py REVEAL_PACKET.json [--roots DIR]

`--roots` defaults to ./roots, which is the layout of the public seal
repository (github.com/heurisca-inc/heurisca-seals). Clone that repo, drop the
packet you were given into it, and run this file.

Exit status is 0 only if every prediction in the packet verifies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def canonical(content) -> str:
    return json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint(content, salt_hex: str) -> str:
    return hashlib.sha256(canonical(content).encode() + bytes.fromhex(salt_hex)).hexdigest()


def leaf_hash(fp_hex: str) -> bytes:
    return hashlib.sha256(LEAF_PREFIX + bytes.fromhex(fp_hex)).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(NODE_PREFIX + left + right).digest()


def walk(fp_hex: str, proof: list[dict]) -> str:
    current = leaf_hash(fp_hex)
    for step in proof:
        sibling = bytes.fromhex(step["hash"])
        if step["side"] == "right":
            current = node_hash(current, sibling)
        elif step["side"] == "left":
            current = node_hash(sibling, current)
        else:
            raise ValueError(f"bad proof step side: {step['side']!r}")
    return current.hex()


def git_commit_date(root_file: Path) -> str | None:
    """When the root file was actually committed.

    This is the part that carries the date claim. The Merkle proof shows the
    prediction is in the tree; the commit history shows when that tree was
    published. Branch protection on the seal repo (no force-pushes, no
    deletions) is what makes the commit date meaningful.
    """
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", root_file.name],
            cwd=root_file.parent,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("packet", type=Path, help="the reveal packet JSON you were given")
    ap.add_argument("--roots", type=Path, default=Path("roots"),
                    help="directory of published daily roots (default: ./roots)")
    args = ap.parse_args()

    if not args.packet.exists():
        print(f"FAIL  reveal packet not found: {args.packet}", file=sys.stderr)
        return 2

    packet = json.loads(args.packet.read_text())
    sealed_date = packet["sealed_date"]
    year, month, _ = sealed_date.split("-")
    root_file = args.roots / year / month / f"{sealed_date}.json"

    if not root_file.exists():
        print(f"FAIL  no published root for {sealed_date} at {root_file}", file=sys.stderr)
        print("      Are you running this inside a clone of the seal repository?",
              file=sys.stderr)
        return 2

    published = json.loads(root_file.read_text())
    published_root = published["merkle_root"]

    print(f"Seal record for {sealed_date}")
    print(f"  published root : {published_root}")
    print(f"  leaves that day: {published['leaf_count']}")
    committed = git_commit_date(root_file)
    if committed:
        print(f"  committed to the public record at: {committed}")
    print()

    if packet.get("merkle_root") and packet["merkle_root"] != published_root:
        print("FAIL  the packet names a different root than the published record.",
              file=sys.stderr)
        return 1

    ok = 0
    bad = 0
    for item in packet["predictions"]:
        recomputed = fingerprint(item["content"], item["salt"])
        stated = item.get("fingerprint")

        if stated and recomputed != stated:
            print(f"  FAIL  {item.get('id', '?')}: content does not match its fingerprint")
            bad += 1
            continue

        reached = walk(recomputed, item["proof"])
        if reached == published_root:
            print(f"  OK    {item.get('id', '?')}")
            ok += 1
        else:
            print(f"  FAIL  {item.get('id', '?')}: proof does not reach the published root")
            bad += 1

    print()
    if bad:
        print(f"VERIFICATION FAILED: {ok} verified, {bad} failed.")
        return 1

    print(f"VERIFIED: all {ok} prediction(s) were committed to the public record "
          f"on {sealed_date}.")
    if committed:
        print(f"That record was published to GitHub at {committed} and the branch "
              f"cannot be force-pushed or deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
