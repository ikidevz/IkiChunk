from ikichunk import partition
import sys

sys.path.insert(0, "src")


def demo_compare_manifests():
    print("\n--- compare manifests between sales, activity, and catalog data ---")
    sales_manifest = partition.manifest(
        ["/tmp/ikichunk_demo/sales.csv", "/tmp/ikichunk_demo/events.jsonl"])
    activity_manifest = partition.manifest(
        ["/tmp/ikichunk_demo/activity.jsonl"])
    catalog_manifest = partition.manifest(["/tmp/ikichunk_demo/catalog.yaml"])
    tsv_manifest = partition.manifest(["/tmp/ikichunk_demo/catalog.tsv"])
    parquet_manifest = partition.manifest(["/tmp/ikichunk_demo/sales.parquet"])
    pickle_manifest = partition.manifest(["/tmp/ikichunk_demo/catalog.pkl"])
    print("sales/events manifest entries:", len(sales_manifest["files"]))
    print("activity manifest entries:", len(activity_manifest["files"]))
    print("yaml catalog manifest entries:", len(catalog_manifest["files"]))
    print("tsv catalog manifest entries:", len(tsv_manifest["files"]))
    print("parquet sales manifest entries:", len(parquet_manifest["files"]))
    print("pickle catalog manifest entries:", len(pickle_manifest["files"]))
    print("pickle manifest hash:", pickle_manifest["files"][0]["hash"][:16])


if __name__ == "__main__":
    demo_compare_manifests()
