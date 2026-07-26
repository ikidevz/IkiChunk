from ikichunk import partition
import os
import sys
import time

sys.path.insert(0, "src")


SALES_CSV = "/tmp/ikichunk_demo/sales.csv"
CATALOG_TSV = "/tmp/ikichunk_demo/catalog.tsv"


def demo_split_by_size():
    print("\n--- split_file(by='size') on the sales CSV ---")
    t0 = time.perf_counter()
    parts = partition.split_file(
        SALES_CSV, by="size", size="20MB", out_dir="/tmp/ikichunk_demo/by_size")
    elapsed = time.perf_counter() - t0
    print(f"{len(parts)} partitions in {elapsed:.2f}s (streaming, byte-level — works on any format)")
    for p in parts:
        print(f"  {p}: {os.path.getsize(p)/1024/1024:.1f} MB")


def demo_split_by_rows():
    print("\n--- split_file(by='rows') on the sales CSV ---")
    t0 = time.perf_counter()
    parts = partition.split_file(
        SALES_CSV, by="rows", rows=250_000, out_dir="/tmp/ikichunk_demo/by_rows")
    elapsed = time.perf_counter() - t0
    print(f"{len(parts)} partitions in {elapsed:.2f}s (single-pass streaming)")
    for p in parts:
        rows = partition.read(p)
        print(f"  {p}: {len(rows)} rows, header ok: {list(rows[0].keys())}")


def demo_split_by_count():
    print("\n--- split_file(by='count') on the catalog TSV ---")
    t0 = time.perf_counter()
    parts = partition.split_file(
        CATALOG_TSV, by="count", count=4, out_dir="/tmp/ikichunk_demo/by_count_tsv")
    elapsed = time.perf_counter() - t0
    print(f"{len(parts)} partitions in {elapsed:.2f}s (two-pass streaming, exact even split)")
    sizes = [len(partition.read(p)) for p in parts]
    print(f"  row counts per partition: {sizes} (sum={sum(sizes)})")


if __name__ == "__main__":
    demo_split_by_size()
    demo_split_by_rows()
    demo_split_by_count()
