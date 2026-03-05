#!/usr/bin/env python3
"""CLI script to run batch tests directly (without the API server)."""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.batch.runner import run_batch_tests, load_scenarios
from backend.knowledge.kb_search import load_knowledge_base
from backend.knowledge.product_info import load_products


async def main():
    print("=" * 60)
    print("Reolink AI Agent - Batch Test Runner")
    print("=" * 60)

    # Initialize knowledge base
    print("\nLoading knowledge base...")
    load_knowledge_base()
    load_products()
    print("Knowledge base loaded.")

    # Parse arguments
    scenario_ids = None
    concurrency = 3

    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            scenarios = load_scenarios()
            print(f"\nAvailable scenarios ({len(scenarios)}):")
            for s in scenarios:
                print(f"  {s['id']}: {s['name']} ({s['product']})")
            return

        scenario_ids = sys.argv[1].split(",")
        print(f"Running specific scenarios: {scenario_ids}")

    if len(sys.argv) > 2:
        concurrency = int(sys.argv[2])

    # Run tests
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    scenarios = load_scenarios(scenario_ids)
    print(f"\nRunning {len(scenarios)} scenarios (concurrency: {concurrency})")
    print(f"Run ID: {run_id}")
    print("-" * 60)

    results = await run_batch_tests(
        run_id=run_id,
        scenario_ids=scenario_ids,
        concurrency=concurrency,
    )

    # Print results summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    for r in results.get("results", []):
        if "error" in r:
            print(f"\n  ERROR: {r['error']}")
            continue

        print(f"\n  Scenario: {r['scenario_name']}")
        print(f"  Product: {r['product']} | Category: {r['category']}")
        print(f"  Turns: {r['total_turns']} | Escalated: {r['escalated']}")
        summary = r.get("evaluations_summary", {})
        print(f"  Scores: Relevance={summary.get('avg_relevance', 'N/A')} "
              f"Accuracy={summary.get('avg_accuracy', 'N/A')} "
              f"Helpfulness={summary.get('avg_helpfulness', 'N/A')} "
              f"Tone={summary.get('avg_tone', 'N/A')} "
              f"Overall={summary.get('avg_overall', 'N/A')}")

    print(f"\n{'=' * 60}")
    print(f"Overall Average Score: {results.get('overall_avg_score', 'N/A')}")
    print(f"Results saved to: backend/batch/results/{run_id}.json")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
