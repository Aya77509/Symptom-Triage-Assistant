"""
Runs every test case through BOTH pipelines (hybrid rule-based vs raw-LLM
baseline), compares them against your expected_level (derived from the
rule book you wrote), and saves everything to data/results.json plus a
printed summary.

This IS your evaluation / result for the writeup - run it, then look at
the "DISAGREEMENTS" section to find concrete examples where the raw LLM
got it wrong but the hybrid pipeline (thanks to the rules) got it right.

Usage:
    python compare.py
"""

import json
import time

from hybrid import run_hybrid
from baseline import run_baseline

TEST_CASES_PATH = "test_cases.json"
RESULTS_PATH = "data/results.json"


def main():
    with open(TEST_CASES_PATH) as f:
        cases = json.load(f)

    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] Running {case['id']}...", flush=True)
        t0 = time.time()

        hybrid_result = run_hybrid(case["text"])
        baseline_level = run_baseline(case["text"])

        elapsed = time.time() - t0
        row = {
            "id": case["id"],
            "text": case["text"],
            "expected_level": case["expected_level"],
            "hybrid_level": hybrid_result["level"],
            "hybrid_rule": hybrid_result["rule_id"],
            "baseline_level": baseline_level,
            "hybrid_correct": hybrid_result["level"] == case["expected_level"],
            "baseline_correct": baseline_level == case["expected_level"],
            "agree": hybrid_result["level"] == baseline_level,
            "seconds": round(elapsed, 1),
        }
        results.append(row)
        print(
            f"    expected={row['expected_level']:<10} "
            f"hybrid={row['hybrid_level']:<10} "
            f"baseline={row['baseline_level']:<10} "
            f"{'OK' if row['agree'] else 'DISAGREE'}"
        )

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    n = len(results)
    hybrid_acc = sum(r["hybrid_correct"] for r in results) / n
    baseline_acc = sum(r["baseline_correct"] for r in results) / n
    agree_rate = sum(r["agree"] for r in results) / n

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test cases:                {n}")
    print(f"Hybrid accuracy:           {hybrid_acc:.0%}")
    print(f"Raw-LLM baseline accuracy: {baseline_acc:.0%}")
    print(f"Agreement rate:            {agree_rate:.0%}")

    disagreements = [r for r in results if not r["agree"]]
    if disagreements:
        print(f"\nDISAGREEMENTS ({len(disagreements)}) - these are your best writeup examples:")
        for r in disagreements:
            flag = ""
            if r["hybrid_correct"] and not r["baseline_correct"]:
                flag = "  <-- hybrid caught what baseline missed"
            elif r["baseline_correct"] and not r["hybrid_correct"]:
                flag = "  <-- baseline was right, hybrid/rules need work"
            print(f"  {r['id']}: expected={r['expected_level']} "
                  f"hybrid={r['hybrid_level']} baseline={r['baseline_level']}{flag}")

    print(f"\nFull results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
