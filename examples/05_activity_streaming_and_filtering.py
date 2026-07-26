from ikichunk import partition
import sys

sys.path.insert(0, "src")


def demo_activity_filtering():
    print("\n--- stream() user activity events and aggregate by action ---")
    counts = {}
    purchases = 0
    for event in partition.stream("/tmp/ikichunk_demo/activity.jsonl", fmt="json"):
        counts[event["action"]] = counts.get(event["action"], 0) + 1
        if event["action"] == "purchase":
            purchases += 1
    print("action counts:", counts)
    print(f"purchase events: {purchases}")


def demo_catalog_summary():
    print("\n--- read YAML, TSV, parquet, and pickle catalogs ---")
    yaml_catalog = partition.read("/tmp/ikichunk_demo/catalog.yaml")
    tsv_catalog = partition.read("/tmp/ikichunk_demo/catalog.tsv")
    parquet_sales = partition.read("/tmp/ikichunk_demo/sales.parquet")
    pickle_catalog = partition.read("/tmp/ikichunk_demo/catalog.pkl")

    low_stock = [item for item in yaml_catalog if item["stock"] < 10]
    print(f"yaml catalog entries: {len(yaml_catalog)}")
    print(f"tsv catalog entries: {len(tsv_catalog)}")
    print(f"parquet sales rows: {len(parquet_sales)}")
    print(f"pickle catalog rows: {len(pickle_catalog['rows'])}")
    print(f"low-stock entries: {len(low_stock)}")
    print("sample sku:", yaml_catalog[0]["sku"])


if __name__ == "__main__":
    demo_activity_filtering()
    demo_catalog_summary()
