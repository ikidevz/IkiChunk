from ikichunk import partition
import os
import sys

sys.path.insert(0, "src")


def demo_config_and_redaction():
    print("\n--- config() merge + secrets, inspect() redaction ---")
    cfg = partition.config(
        "/tmp/ikichunk_demo/config.json",
        secrets="/tmp/ikichunk_demo/secrets.env",
    )
    print("merged config keys:", list(cfg.keys()))
    info = partition.inspect(cfg, sample=len(cfg))
    print("inspect() output (DB_PASSWORD/API_KEY should show <redacted>, not their real values):")
    for k, v in info["sample"].items():
        print(f"  {k}: {v}")


def demo_streaming_activity_and_catalogs():
    print("\n--- stream() activity events and read the new catalog formats ---")
    error_count = 0
    total = 0
    purchases = 0
    for event in partition.stream("/tmp/ikichunk_demo/activity.jsonl", fmt="json"):
        total += 1
        if event["action"] == "purchase":
            purchases += 1
        if event["action"] == "refund":
            error_count += 1

    yaml_catalog = partition.read("/tmp/ikichunk_demo/catalog.yaml")
    tsv_catalog = partition.read("/tmp/ikichunk_demo/catalog.tsv")
    parquet_sales = partition.read("/tmp/ikichunk_demo/sales.parquet")
    pickle_catalog = partition.read("/tmp/ikichunk_demo/catalog.pkl")

    print(f"processed {total} activity events via streaming")
    print(f"  purchases: {purchases}")
    print(f"  refunds: {error_count}")
    print(
        f"  yaml rows: {len(yaml_catalog)} | tsv rows: {len(tsv_catalog)} | parquet rows: {len(parquet_sales)} | pickle rows: {len(pickle_catalog['rows'])}")


def demo_template_render():
    print("\n--- render() a deploy-style config from a template ---")
    tmpl = "app_name=$app\nregion=$region\nworkers=$workers\nbatch_size=$batch\n"
    rendered = partition.render(tmpl, {
        "app": "sales-pipeline", "region": "us-east", "workers": 4, "batch": 500,
    }, out="/tmp/ikichunk_demo/rendered.env")
    print("rendered:")
    print(rendered)

    print("strict=True correctly rejects a missing variable:")
    try:
        partition.render("region=$region port=$port", {"region": "us-east"})
    except KeyError as e:
        print(f"  KeyError: {e}")


def demo_process_and_shell():
    print("\n--- process checks + safe shell ---")
    print(
        f"is_running(self pid {os.getpid()}): {partition.is_running(os.getpid())}")
    print(
        f"is_port_open(127.0.0.1:1): {partition.is_port_open('127.0.0.1', 1, timeout=0.3)}")

    r = partition.run([sys.executable, "--version"])
    print(
        f"run(['python3','--version']): ok={r.ok}, stdout={r.stdout.strip()!r}")

    print("shell.run correctly rejects a piped command string:")
    try:
        partition.run("cat /etc/os-release | grep NAME")
    except Exception as e:
        print(f"  {type(e).__name__}: {e}")


if __name__ == "__main__":
    demo_config_and_redaction()
    demo_streaming_activity_and_catalogs()
    demo_template_render()
    demo_process_and_shell()
