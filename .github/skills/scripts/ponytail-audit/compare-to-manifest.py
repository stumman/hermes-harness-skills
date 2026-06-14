#!/usr/bin/env python3
"""Compare a ponytail-audit report against an ISSUE-MANIFEST.md to compute detection metrics.

Usage:
  python3 scripts/compare-to-manifest.py <audit_file> <manifest_file> [--baseline <prev_audit>] [--clean-audit <clean_audit>]

Output: detection count, missed items list, detection percentage, Youden's Index, delta vs baseline.
Exit code 0 if detection rate > 90%, 1 otherwise (for CI gating).

NEW (v2.0 — adopted from agent-skill-evaluator):
  - --baseline <file>: Compare against a previous audit to measure WITH_SKILL vs BASELINE delta.
    A skill that produces the same output as baseline is a no-op.
  - --clean-audit <file>: Audit of clean/ code (same code minus bugs). Any finding = false positive.
    Enables Youden's Index = Sensitivity + Specificity - 1 (OWASP Benchmark standard).
"""

import sys
import re
import json
from pathlib import Path


def parse_manifest(path: str) -> list[tuple[str, str]]:
    """Parse an ISSUE-MANIFEST.md into list of (section, description) entries.

    Supports two manifest formats:
    1. Pipe table format (primary — used by java-bug-hunt, ts-bug-hunt)
    2. Numbered list format (legacy)
    """
    with open(path) as f:
        text = f.read()

    entries = []
    current_section = ""
    in_table = False

    for raw_line in text.split('\n'):
        # Strip read_file line-number prefixes (format: "NUMBER|...")
        # Manifest files read via read_file tool may have embedded prefixes like "     1|"
        # that survive write_file and compound across sessions. Strip them before parsing.
        raw_line = re.sub(r'^\s*\d+\|', '', raw_line)
        line = raw_line.strip()

        if line.startswith('## '):
            section_name = line.lstrip('# ').strip()
            if section_name not in ('TOTALS', 'Files by Issue Density',
                                     'Coverage Gaps Filled', 'GRAND TOTAL'):
                current_section = section_name
            else:
                current_section = ""
            in_table = False
            continue

        if line.startswith('| # | Sev'):
            in_table = True
            continue
        if in_table and line.startswith('|---'):
            continue

        if in_table and line.startswith('|') and line != '':
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 3 and parts[0] and re.match(r'^[A-Z]+\d+$', parts[0]):
                desc = parts[-1]
                entries.append((current_section, desc))
            continue

        if in_table and not line.startswith('|'):
            in_table = False

        if re.match(r'^\d+\.', line):
            desc = re.sub(r'^\d+\.\s*', '', line)
            entries.append((current_section, desc))

    return entries


def check_coverage(audit_text: str, manifest_entries: list[tuple[str, str]]) -> tuple[int, list[tuple[str, str]]]:
    """Check which manifest entries are covered by the audit text."""
    audit_lower = audit_text.lower()

    skip_words = {
        'the', 'a', 'an', 'of', 'to', 'is', 'in', 'for', 'and', 'or',
        'with', 'on', 'at', 'by', 'as', 'no', 'all', 'not', 'any',
        'this', 'has', 'that', 'are', 'its', 'it', 'be', 'but', 'from',
        'each', 'also', 'can', 'into', 'was', 'been', 'have', 'will',
        'use', 'set', 'may', 'using', 'via', 'when', 'where', 'true',
        'null', 'fix', 'low', 'add', 'see', 'into', 'there', 'should',
        'does', 'miss', 'must', 'like', 'per', 'one', 'used'
    }

    matched = 0
    missed = []

    for section, desc in manifest_entries:
        words = re.findall(r'[a-zA-Z0-9_]+', desc.lower())
        key_terms = [w for w in words if w not in skip_words and len(w) > 2]

        found = False

        for i in range(len(key_terms) - 2):
            trigram = f"{key_terms[i]} {key_terms[i+1]} {key_terms[i+2]}"
            if trigram in audit_lower:
                found = True
                break

        if not found:
            for i in range(len(key_terms) - 1):
                bigram = f"{key_terms[i]} {key_terms[i + 1]}"
                if bigram in audit_lower:
                    found = True
                    break

        if not found:
            hits = sum(1 for t in key_terms if t in audit_lower)
            if hits >= max(1, len(key_terms) * 0.5):
                found = True

        if found:
            matched += 1
        else:
            missed.append((section, desc))

    return matched, missed


def count_findings_in_clean_audit(clean_audit_path: str) -> int:
    """Count findings in a clean/ audit. Each finding = a false positive.

    Counts lines matching [CONFIRMED], [DETECTED], or [INFERRED] severity tags.
    """
    with open(clean_audit_path) as f:
        text = f.read()

    # Count lines with finding markers
    finding_patterns = [
        r'\[CONFIRMED\]',
        r'\[DETECTED\]',
        r'\[INFERRED\]',
        r'### Critical',
        r'### High',
        r'### Medium',
    ]

    count = 0
    for pattern in finding_patterns:
        count += len(re.findall(pattern, text))

    return count


def compute_metrics(matched: int, total_manifest: int, fp_count: int = 0,
                    baseline_matched: int = 0, baseline_total: int = 0) -> dict:
    """Compute all detection metrics including Youden's Index and delta.

    Args:
        matched: Number of manifest entries detected in current audit
        total_manifest: Total entries in manifest
        fp_count: Number of false positives (findings in clean audit)
        baseline_matched: Matched count from previous audit (for delta)
        baseline_total: Total entries in baseline manifest

    Returns:
        Dict with all metrics
    """
    metrics = {
        "manifest_total": total_manifest,
        "matched": matched,
        "missed": total_manifest - matched,
        "detection_rate": round(matched / total_manifest * 100, 1) if total_manifest > 0 else 0.0,
    }

    # Sensitivity (True Positive Rate) = matched / total
    metrics["sensitivity"] = round(matched / total_manifest, 4) if total_manifest > 0 else 0.0

    # Specificity (True Negative Rate) = 1 - (FP / clean_findings)
    # We approximate: if fp_count is provided, specificity = 1 - (fp / total_manifest)
    if fp_count > 0:
        metrics["false_positives"] = fp_count
        # Specificity: how many non-bugs were correctly NOT flagged
        # Approximate: total_manifest is our "non-bug population" for clean audit
        metrics["specificity"] = round(1.0 - (fp_count / total_manifest), 4) if total_manifest > 0 else 1.0
        # Youden's Index = Sensitivity + Specificity - 1 (OWASP Benchmark standard)
        metrics["youden_index"] = round(metrics["sensitivity"] + metrics["specificity"] - 1.0, 4)
        metrics["false_positive_rate"] = round(fp_count / total_manifest * 100, 1) if total_manifest > 0 else 0.0
    else:
        metrics["false_positives"] = 0
        metrics["specificity"] = None
        metrics["youden_index"] = None
        metrics["false_positive_rate"] = None

    # Delta vs baseline (with_skill vs baseline)
    if baseline_total > 0:
        baseline_rate = baseline_matched / baseline_total * 100 if baseline_total > 0 else 0
        metrics["baseline_detection_rate"] = round(baseline_rate, 1)
        metrics["baseline_matched"] = baseline_matched
        metrics["baseline_total"] = baseline_total
        metrics["with_skill_vs_baseline_delta"] = round(metrics["detection_rate"] - baseline_rate, 1)
        metrics["is_improvement"] = metrics["with_skill_vs_baseline_delta"] > 0
        metrics["is_noop"] = abs(metrics["with_skill_vs_baseline_delta"]) < 0.5
    else:
        metrics["baseline_detection_rate"] = None
        metrics["baseline_matched"] = 0
        metrics["baseline_total"] = 0
        metrics["with_skill_vs_baseline_delta"] = None
        metrics["is_improvement"] = None
        metrics["is_noop"] = None

    return metrics


def print_metrics(metrics: dict, missed: list = None):
    """Print all metrics in a readable format."""
    print(f"Manifest entries:          {metrics['manifest_total']}")
    print(f"Matched:                   {metrics['matched']}")
    print(f"Missed:                    {metrics['missed']}")
    print(f"Detection rate (Recall):   {metrics['detection_rate']}%")
    print(f"Sensitivity (TPR):         {metrics['sensitivity']:.4f}")

    if metrics['false_positives'] > 0:
        print(f"False positives:           {metrics['false_positives']}")
        print(f"False positive rate:       {metrics['false_positive_rate']}%")
        print(f"Specificity (TNR):         {metrics['specificity']:.4f}")
        print(f"Youden's Index:            {metrics['youden_index']:.4f}  (Sensitivity + Specificity - 1)")
        if metrics['youden_index'] is not None:
            if metrics['youden_index'] >= 0.8:
                print(f"  → EXCELLENT (≥0.8)")
            elif metrics['youden_index'] >= 0.6:
                print(f"  → GOOD (≥0.6)")
            else:
                print(f"  → NEEDS IMPROVEMENT (<0.6)")

    if metrics['baseline_total'] > 0:
        print(f"\n--- Delta vs Baseline ---")
        print(f"Baseline detection:        {metrics['baseline_detection_rate']}% ({metrics['baseline_matched']}/{metrics['baseline_total']})")
        print(f"Current detection:         {metrics['detection_rate']}% ({metrics['matched']}/{metrics['manifest_total']})")
        delta = metrics['with_skill_vs_baseline_delta']
        sign = "+" if delta > 0 else ""
        print(f"Delta (with_skill − base): {sign}{delta}%")
        if metrics['is_noop']:
            print(f"  ⚠️  NO-OP: Skill version produces same output as baseline. This version is dead weight.")
        elif metrics['is_improvement']:
            print(f"  ✅ IMPROVEMENT: Skill version detects {delta}% more issues than baseline.")
        else:
            print(f"  ❌ REGRESSION: Skill version detects {abs(delta)}% fewer issues than baseline.")

    if missed:
        print(f"\nPotentially missed entries:")
        for section, desc in missed:
            short = desc[:100] + ('...' if len(desc) > 100 else '')
            print(f"  [{section}] {short}")

    # JSON output for machine consumption
    print(f"\n--- JSON ---")
    print(json.dumps(metrics, indent=2))


def main():
    args = sys.argv[1:]
    baseline_path = None
    clean_audit_path = None
    positional = []

    i = 0
    while i < len(args):
        if args[i] == '--baseline' and i + 1 < len(args):
            baseline_path = args[i + 1]
            i += 2
        elif args[i] == '--clean-audit' and i + 1 < len(args):
            clean_audit_path = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if len(positional) != 2:
        print(f"Usage: {sys.argv[0]} <audit.md> <manifest.md> [--baseline <prev_audit.md>] [--clean-audit <clean_audit.md>]")
        sys.exit(2)

    audit_path, manifest_path = positional
    manifest_entries = parse_manifest(manifest_path)

    with open(audit_path) as f:
        audit_text = f.read()

    matched, missed = check_coverage(audit_text, manifest_entries)
    total = len(manifest_entries)

    # False positive count from clean audit
    fp_count = 0
    if clean_audit_path:
        fp_count = count_findings_in_clean_audit(clean_audit_path)

    # Baseline comparison
    baseline_matched = 0
    baseline_total = 0
    if baseline_path:
        with open(baseline_path) as f:
            baseline_text = f.read()
        baseline_matched, _ = check_coverage(baseline_text, manifest_entries)
        baseline_total = total

    metrics = compute_metrics(matched, total, fp_count, baseline_matched, baseline_total)
    print_metrics(metrics, missed if missed else None)

    if metrics['detection_rate'] >= 90:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
