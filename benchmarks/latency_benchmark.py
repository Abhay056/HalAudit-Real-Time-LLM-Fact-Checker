"""
HalAudit Latency Benchmark
Benchmarks claim verification with varying numbers of claims,
comparing sequential vs parallel processing.
Reports p50, p95, p99 latencies and per-component timing.
"""

import asyncio
import time
import statistics
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tabulate import tabulate


# Sample texts for benchmarking
BENCHMARK_TEXTS = [
    "The speed of light is approximately 300,000 kilometers per second.",
    "Albert Einstein was born in Germany in 1879 and developed the theory of relativity.",
    "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    "The Great Wall of China is visible from space with the naked eye.",
    "DNA was discovered by James Watson and Francis Crick in 1953.",
    "The Pacific Ocean is the largest ocean on Earth.",
    "Mount Everest is 8,849 meters tall and located on the Nepal-China border.",
    "Newton published his laws of motion in the Principia Mathematica in 1687.",
    "The human body has approximately 206 bones in the adult skeleton.",
    "Python was created by Guido van Rossum and first released in 1991.",
    "The Moon landing occurred on July 20, 1969 during the Apollo 11 mission.",
    "The Earth orbits the Sun at a distance of approximately 150 million kilometers.",
    "The periodic table was created by Dmitri Mendeleev in 1869.",
    "The Amazon River is the largest river by discharge volume in the world.",
    "World War II ended in 1945 with the surrender of Japan.",
    "The Eiffel Tower was built in 1889 and stands 330 meters tall.",
    "The human heart beats approximately 100,000 times per day.",
    "Pluto was reclassified as a dwarf planet in 2006.",
    "The Internet originated from ARPANET in the late 1960s.",
    "Gold has the atomic number 79 and the chemical symbol Au.",
]


async def benchmark_pipeline(num_claims: int, runs: int = 5) -> dict:
    """Run the pipeline benchmark for a given number of claims."""
    from app.core.pipeline import get_audit_pipeline
    from app.corpus.loader import load_seed_corpus

    # Ensure corpus is loaded
    await load_seed_corpus()

    pipeline = get_audit_pipeline()
    text = " ".join(BENCHMARK_TEXTS[:num_claims])

    latencies = []
    extraction_times = []
    retrieval_times = []
    nli_times = []

    for run_idx in range(runs):
        start = time.time()
        report = await pipeline.audit(text)
        total_ms = (time.time() - start) * 1000

        latencies.append(total_ms)
        if report.latency_breakdown:
            extraction_times.append(report.latency_breakdown.get("claim_extraction_ms", 0))
            retrieval_times.append(report.latency_breakdown.get("rag_retrieval_ms", 0))
            nli_times.append(report.latency_breakdown.get("nli_scoring_ms", 0))

    def calc_percentiles(data):
        if not data:
            return {"p50": 0, "p95": 0, "p99": 0, "mean": 0}
        sorted_data = sorted(data)
        n = len(sorted_data)
        return {
            "p50": round(sorted_data[int(n * 0.5)] if n > 0 else 0, 1),
            "p95": round(sorted_data[int(n * 0.95)] if n > 0 else 0, 1),
            "p99": round(sorted_data[int(n * 0.99)] if n > 0 else 0, 1),
            "mean": round(statistics.mean(data), 1),
        }

    return {
        "num_claims": num_claims,
        "runs": runs,
        "total": calc_percentiles(latencies),
        "extraction": calc_percentiles(extraction_times),
        "retrieval": calc_percentiles(retrieval_times),
        "nli": calc_percentiles(nli_times),
    }


async def run_benchmarks():
    """Run benchmarks for different claim counts."""
    print("\n" + "=" * 70)
    print("  HalAudit Latency Benchmark")
    print("=" * 70)

    claim_counts = [1, 3, 5, 10, 15, 20]
    results = []

    for count in claim_counts:
        if count > len(BENCHMARK_TEXTS):
            break
        print(f"\n  Benchmarking {count} claims ({5} runs)...")
        result = await benchmark_pipeline(count, runs=5)
        results.append(result)

    # Print results table
    print("\n" + "=" * 70)
    print("  Total Pipeline Latency (ms)")
    print("=" * 70)

    table_data = []
    for r in results:
        table_data.append([
            r["num_claims"],
            r["total"]["mean"],
            r["total"]["p50"],
            r["total"]["p95"],
            r["total"]["p99"],
        ])

    print(tabulate(
        table_data,
        headers=["Claims", "Mean", "P50", "P95", "P99"],
        tablefmt="grid",
        floatfmt=".1f"
    ))

    # Per-component breakdown
    print("\n" + "=" * 70)
    print("  Per-Component Breakdown - Mean Latency (ms)")
    print("=" * 70)

    breakdown_data = []
    for r in results:
        breakdown_data.append([
            r["num_claims"],
            r["extraction"]["mean"],
            r["retrieval"]["mean"],
            r["nli"]["mean"],
            r["total"]["mean"],
        ])

    print(tabulate(
        breakdown_data,
        headers=["Claims", "Extraction", "Retrieval", "NLI", "Total"],
        tablefmt="grid",
        floatfmt=".1f"
    ))

    # Throughput
    print("\n" + "=" * 70)
    print("  Throughput")
    print("=" * 70)

    throughput_data = []
    for r in results:
        claims_per_sec = (r["num_claims"] / r["total"]["mean"]) * 1000 if r["total"]["mean"] > 0 else 0
        throughput_data.append([
            r["num_claims"],
            f"{r['total']['mean']:.0f}ms",
            f"{claims_per_sec:.1f}",
        ])

    print(tabulate(
        throughput_data,
        headers=["Claims", "Total Time", "Claims/sec"],
        tablefmt="grid",
    ))

    print("\n" + "=" * 70)
    print("  Benchmark Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
