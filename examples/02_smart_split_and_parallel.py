from ikichunk import partition
import sys
import time

sys.path.insert(0, "src")


CATALOG_TSV = "/tmp/ikichunk_demo/catalog.tsv"


def demo_smart_split_goals():
    print("\n--- smart_split() across all three goals for a TSV catalog ---")
    for goal in ("parallel", "memory-safe", "storage"):
        parts, why = partition.smart_split(
            CATALOG_TSV, goal=goal, out_dir=f"/tmp/ikichunk_demo/smart_{goal}", explain=True
        )
        print(f"\ngoal='{goal}':")
        print(f"  chosen_strategy: {why['chosen_strategy']}")
        print(f"  cpu_count seen:  {why['cpu_count']}")
        print(f"  partition_count: {why['partition_count']}")


def category_counts(part_path: str) -> dict:
    rows = partition.read(part_path)
    totals = {}
    for row in rows:
        category = row["category"]
        totals[category] = totals.get(category, 0) + 1
    return totals


def demo_parallel_aggregation():
    print("\n--- smart_split(goal='parallel') -> pmap() category counts ---")
    parts, why = partition.smart_split(
        CATALOG_TSV, goal="parallel", out_dir="/tmp/ikichunk_demo/smart_parallel_agg", explain=True
    )
    print(
        f"partitioned into {len(parts)} pieces for {why['cpu_count']} CPU(s) (auto-detected)")

    t0 = time.perf_counter()
    partial_totals = partition.pmap(category_counts, parts, workers=len(parts))
    elapsed = time.perf_counter() - t0

    grand_total = {}
    for partial in partial_totals:
        for category, count in partial.items():
            grand_total[category] = grand_total.get(category, 0) + count

    print(f"aggregated {len(parts)} partition(s) in {elapsed:.2f}s")
    for category, count in sorted(grand_total.items(), key=lambda x: -x[1]):
        print(f"  {category:12s}: {count}")


def demo_forced_multi_partition():
    print("\n--- smart_split(workers=4) override + pmap(backend='process') ---")
    parts, why = partition.smart_split(
        CATALOG_TSV, goal="parallel", workers=4,
        out_dir="/tmp/ikichunk_demo/smart_forced4", explain=True
    )
    print(
        f"forced to {why['partition_count']} partitions regardless of detected CPU count")

    t0 = time.perf_counter()
    partial_totals = partition.pmap(
        category_counts, parts, workers=4, backend="process")
    elapsed = time.perf_counter() - t0
    print(
        f"backend='process' picklability check passed, aggregated in {elapsed:.2f}s")

    grand_total = sum(sum(p.values()) for p in partial_totals)
    print(f"grand total across {len(parts)} partitions: {grand_total}")


if __name__ == "__main__":
    demo_smart_split_goals()
    demo_parallel_aggregation()
    demo_forced_multi_partition()
