# Heurisca — public seal record

This repository is the tamper-evident record that Heurisca's predictions existed
before the decisions they predict.

## What is in here

Every day the machine publishes one file:

```
roots/YYYY/MM/YYYY-MM-DD.json
```

Each file contains the **Merkle root** of all predictions sealed that day, the
number of predictions in the batch, and the previous day's root (so the days form
a chain). The file is committed here, and the root is anchored into the Bitcoin
blockchain with [OpenTimestamps](https://opentimestamps.org). The `.ots` proof
lands beside it once the anchor confirms.

The predictions themselves are **not** here. Each leaf of the Merkle tree is a
fingerprint: a hash of one prediction's content together with a per-prediction
random salt held privately. That means:

- Publishing the root proves the predictions existed on that date.
- It reveals nothing about what they said.
- Nobody can guess a prediction and match it against a published fingerprint,
  because they do not have the salt.

When a prediction is deliberately disclosed, its **reveal packet** contains the
prediction, its salt, its stamp, and the Merkle proof connecting it to the root
published here on that date.

## How to check this yourself

You need the reveal packet someone gave you and this repository.

```
git clone https://github.com/heurisca-inc/heurisca-seals
cd heurisca-seals
python3 verify.py /path/to/reveal-packet.json
```

The script uses only the Python standard library. It recomputes each
fingerprint from the disclosed prediction and salt, walks the Merkle proof up to
the root, and checks that root against the file committed here — and tells you
the commit date of that file. It prints one line per prediction and a verdict.

To also check the Bitcoin anchor (optional, needs the `ots` client):

```
pip install opentimestamps-client
ots verify roots/2026/09/2026-09-01.json.ots
```

## Why the commit history matters

The commit history of this repository is part of the proof. Branch protection is
on: this branch cannot be force-pushed and cannot be deleted. Corrections are new
commits, never rewrites.

## Status

The record starts empty and grows daily. Its youth is not hidden — the count of
sealed days is published on the scoreboard alongside the results.
