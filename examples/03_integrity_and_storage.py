from ikichunk import partition
import shutil
import sys

sys.path.insert(0, "src")


CATALOG_TSV = "/tmp/ikichunk_demo/catalog.tsv"


def demo_manifest_and_verify():
    print("\n--- partition -> manifest -> simulated transfer -> verify (TSV catalog) ---")
    parts = partition.split_file(
        CATALOG_TSV, by="count", count=4, out_dir="/tmp/ikichunk_demo/integrity_src")
    m = partition.manifest(parts)
    partition.write("/tmp/ikichunk_demo/integrity_src/manifest.json", m)
    print(f"manifest built for {len(m['files'])} files (algo={m['algo']})")
    for entry in m["files"]:
        print(
            f"  {entry['path']}: {entry['size_bytes']/1024/1024:.1f} MB, hash={entry['hash'][:12]}...")

    shutil.copytree("/tmp/ikichunk_demo/integrity_src",
                    "/tmp/ikichunk_demo/integrity_dst", dirs_exist_ok=True)

    corrupted_path = m["files"][1]["path"].replace(
        "integrity_src", "integrity_dst")
    with open(corrupted_path, "a") as f:
        f.write("CORRUPTED_BYTES_INJECTED_FOR_DEMO\n")

    print("\nVerifying transferred files against the original manifest:")
    received_manifest = partition.read(
        "/tmp/ikichunk_demo/integrity_dst/manifest.json")
    all_ok = True
    for entry in received_manifest["files"]:
        dst_path = entry["path"].replace("integrity_src", "integrity_dst")
        ok = partition.verify(dst_path, entry["hash"])
        status = "OK" if ok else "CORRUPTED"
        print(f"  {dst_path}: {status}")
        all_ok = all_ok and ok
    print(
        f"\nResult: {'all files intact' if all_ok else 'integrity check correctly caught corruption'}")


def demo_compress_and_archive():
    print("\n--- compress each TSV partition, then archive + extract the batch ---")
    parts = partition.list_files(
        "/tmp/ikichunk_demo/integrity_src", pattern="*.tsv")
    for p in parts:
        gz_path = partition.compress(p, algo="gzip")
        import os
        ratio = os.path.getsize(gz_path) / os.path.getsize(p)
        print(f"  {p} -> {gz_path} ({ratio*100:.1f}% of original size)")

    arc = partition.archive(
        "/tmp/ikichunk_demo/integrity_src", "/tmp/ikichunk_demo/catalog_batch.tar.gz")
    print(f"\narchived batch: {arc}")

    extracted = partition.extract(
        arc, out_dir="/tmp/ikichunk_demo/extracted_batch")
    extracted_files = partition.list_files(extracted, recursive=True)
    print(f"extracted {len(extracted_files)} files to {extracted}")


if __name__ == "__main__":
    demo_manifest_and_verify()
    demo_compress_and_archive()
