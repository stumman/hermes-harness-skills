#!/usr/bin/env python3
"""Split a golden source manifest into training (60%) and held-out (40%) sets.

Usage:
  python3 scripts/split-manifest.py <manifest.md> [--seed 42]

Output: manifest-train.md and manifest-heldout.md in the same directory.

The split is DETERMINISTIC (seeded) and STRATIFIED by section to ensure
every bug category appears in both sets. Held-out entries MUST NOT be used
for skill training — only for unbiased validation by the meta-watcher.

This implements the agent-skill-evaluator 60/40 pattern:
  - Training (60%): used by the cron loop for skill improvement
  - Held-out (40%): used by the meta-watcher for unbiased evaluation
  - A skill that only improves on training but not held-out is OVERFITTING
"""

import sys
import re
import random
import os
from pathlib import Path
from collections import defaultdict


def parse_manifest_sections(path: str) -> dict[str, list[str]]:
    """Parse manifest into dict of section -> list of raw table rows."""
    with open(path) as f:
        text = f.read()

    sections = defaultdict(list)
    current_section = ""
    in_table = False

    for line in text.split('\n'):
        stripped = line.rstrip('\n')

        if stripped.startswith('## '):
            section_name = stripped.lstrip('# ').strip()
            if section_name not in ('TOTALS', 'Files by Issue Density',
                                     'Coverage Gaps Filled', 'GRAND TOTAL'):
                current_section = section_name
            else:
                current_section = ""
            in_table = False
            continue

        if stripped.startswith('| # | Sev'):
            in_table = True
            continue
        if in_table and stripped.startswith('|---'):
            continue

        if in_table and stripped.startswith('|') and stripped.strip() != '':
            parts = [p.strip() for p in stripped.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 3 and parts[0] and re.match(r'^[A-Z]+\d+$', parts[0]):
                sections[current_section].append(stripped)
            continue

        if in_table and not stripped.startswith('|'):
            in_table = False

    return dict(sections)


def split_stratified(sections: dict[str, list[str]], train_ratio: float = 0.6, seed: int = 42) -> tuple[dict, dict]:
    """Stratified split: each section gets train_ratio% in training, rest in held-out."""
    rng = random.Random(seed)
    train, heldout = {}, {}

    for section, rows in sections.items():
        shuffled = list(rows)
        rng.shuffle(shuffled)
        split_idx = max(1, int(len(shuffled) * train_ratio))
        train[section] = sorted(shuffled[:split_idx], key=lambda r: re.findall(r'[A-Z]+\d+', r)[0] if re.findall(r'[A-Z]+\d+', r) else '')
        heldout[section] = sorted(shuffled[split_idx:], key=lambda r: re.findall(r'[A-Z]+\d+', r)[0] if re.findall(r'[A-Z]+\d+', r) else '')

    return train, heldout


def write_manifest(sections: dict[str, list[str]], original_path: str, suffix: str) -> str:
    """Write a manifest file from section dict."""
    out_path = str(Path(original_path).parent / f"{Path(original_path).stem}-{suffix}.md")

    with open(out_path, 'w') as f:
        f.write(f"# Golden Source Manifest — {suffix.upper()} SET\n\n")
        f.write(f"> Split from: {os.path.basename(original_path)}\n")
        f.write(f"> {suffix} entries. DO NOT use for {'training' if suffix == 'heldout' else 'validation'}.\n\n")

        total = 0
        for section in sorted(sections.keys()):
            rows = sections[section]
            total += len(rows)
            f.write(f"## {section}\n\n")
            f.write("| # | Sev | Line | Issue |\n")
            f.write("|---|---|---|---|\n")
            for row in rows:
                f.write(f"{row}\n")
            f.write("\n")

        f.write(f"## TOTALS\n\n")
        f.write(f"Total entries: {total}\n")

    return out_path


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <manifest.md> [--seed 42]")
        sys.exit(2)

    manifest_path = sys.argv[1]
    seed = 42

    for i, arg in enumerate(sys.argv):
        if arg == '--seed' and i + 1 < len(sys.argv):
            seed = int(sys.argv[i + 1])

    sections = parse_manifest_sections(manifest_path)
    train, heldout = split_stratified(sections, train_ratio=0.6, seed=seed)

    train_path = write_manifest(train, manifest_path, 'train')
    heldout_path = write_manifest(heldout, manifest_path, 'heldout')

    train_total = sum(len(v) for v in train.values())
    heldout_total = sum(len(v) for v in heldout.values())
    total = train_total + heldout_total

    print(f"Split complete (seed={seed}):")
    print(f"  Training:  {train_total} entries ({train_total/total*100:.0f}%) → {train_path}")
    print(f"  Held-out:  {heldout_total} entries ({heldout_total/total*100:.0f}%) → {heldout_path}")
    print(f"  Total:     {total}")


if __name__ == "__main__":
    main()
