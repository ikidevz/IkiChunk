from __future__ import annotations

import csv
import json
import random
import time
from pathlib import Path

SEED = 42


def generate_sales_csv(path: str, rows: int, seed: int = SEED) -> str:
    rng = random.Random(seed)
    regions = ["us-east", "us-west", "eu-west", "eu-central", "apac"]
    weights = [0.40, 0.25, 0.15, 0.12, 0.08]
    products = ["widget-a", "widget-b", "gadget-x", "gadget-y", "tool-z"]

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "region", "product",
                        "quantity", "unit_price", "timestamp"])
        for i in range(rows):
            region = rng.choices(regions, weights=weights)[0]
            product = rng.choice(products)
            quantity = rng.randint(1, 20)
            unit_price = round(rng.uniform(4.99, 299.99), 2)
            timestamp = f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00Z"
            writer.writerow(
                [i, region, product, quantity, unit_price, timestamp])
    return str(p)


def generate_event_log_jsonl(path: str, rows: int, seed: int = SEED) -> str:
    rng = random.Random(seed + 1)
    levels = ["INFO", "INFO", "INFO", "WARN", "ERROR"]
    services = ["api-gateway", "auth-service",
                "billing-service", "worker-pool"]

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for i in range(rows):
            event = {
                "id": i,
                "level": rng.choice(levels),
                "service": rng.choice(services),
                "latency_ms": round(rng.uniform(1, 800), 1),
                "message": f"request handled in region {rng.choice(['us', 'eu', 'apac'])}",
            }
            f.write(json.dumps(event) + "\n")
    return str(p)


def generate_user_activity_jsonl(path: str, rows: int, seed: int = SEED) -> str:
    rng = random.Random(seed + 2)
    actions = ["view", "add_to_cart", "purchase", "refund", "logout"]
    weights = [0.45, 0.25, 0.15, 0.10, 0.05]
    products = ["widget-a", "widget-b", "gadget-x", "gadget-y", "tool-z"]

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for i in range(rows):
            event = {
                "id": i,
                "user_id": f"user-{rng.randint(1, 10000)}",
                "action": rng.choices(actions, weights=weights)[0],
                "product": rng.choice(products),
                "amount": round(rng.uniform(0, 500), 2),
                "timestamp": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00Z",
            }
            f.write(json.dumps(event) + "\n")
    return str(p)


def generate_product_catalog_yaml(path: str, rows: int, seed: int = SEED) -> str:
    rng = random.Random(seed + 3)
    products = ["widget-a", "widget-b", "gadget-x", "gadget-y", "tool-z"]
    categories = ["electronics", "home", "office", "outdoors"]

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for i in range(rows):
        records.append({
            "sku": f"SKU-{i+1:05d}",
            "name": f"{rng.choice(products)}-{rng.randint(100, 999)}",
            "category": rng.choice(categories),
            "price": round(rng.uniform(10.0, 250.0), 2),
            "stock": rng.randint(0, 120),
        })

    lines = []
    for item in records:
        first = True
        for key, value in item.items():
            prefix = "- " if first else "  "
            lines.append(f"{prefix}{key}: {value}")
            first = False
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def generate_product_catalog_tsv(path: str, rows: int, seed: int = SEED) -> str:
    rng = random.Random(seed + 4)
    products = ["widget-a", "widget-b", "gadget-x", "gadget-y", "tool-z"]
    categories = ["electronics", "home", "office", "outdoors"]

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["sku", "name", "category", "price", "stock"])
        for i in range(rows):
            writer.writerow([
                f"SKU-{i+1:05d}",
                f"{rng.choice(products)}-{rng.randint(100, 999)}",
                rng.choice(categories),
                round(rng.uniform(10.0, 250.0), 2),
                rng.randint(0, 120),
            ])
    return str(p)


def generate_sales_parquet(path: str, rows: int, seed: int = SEED) -> str:
    import polars as pl

    rng = random.Random(seed + 5)
    regions = ["us-east", "us-west", "eu-west", "eu-central", "apac"]
    products = ["widget-a", "widget-b", "gadget-x", "gadget-y", "tool-z"]
    data = []
    for i in range(rows):
        data.append({
            "transaction_id": i,
            "region": rng.choice(regions),
            "product": rng.choice(products),
            "quantity": rng.randint(1, 20),
            "unit_price": round(rng.uniform(4.99, 299.99), 2),
            "timestamp": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00Z",
        })
    df = pl.DataFrame(data)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(p)
    return str(p)


def generate_catalog_pickle(path: str, rows: int, seed: int = SEED) -> str:
    import pickle

    rng = random.Random(seed + 6)
    products = ["widget-a", "widget-b", "gadget-x", "gadget-y", "tool-z"]
    payload = {
        "rows": [],
        "meta": {"generated_by": "examples/00_synthetic_data.py", "seed": seed},
    }
    for i in range(rows):
        payload["rows"].append({
            "sku": f"SKU-{i+1:05d}",
            "name": f"{rng.choice(products)}-{rng.randint(100, 999)}",
            "price": round(rng.uniform(10.0, 250.0), 2),
        })
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("wb") as fh:
        pickle.dump(payload, fh)
    return str(p)


def generate_config_secrets_demo(config_path: str, secrets_path: str) -> tuple:
    p_cfg = Path(config_path)
    p_cfg.parent.mkdir(parents=True, exist_ok=True)
    p_cfg.write_text(json.dumps({
        "app_name": "sales-pipeline",
        "batch_size": 500,
        "retry_attempts": 3,
    }, indent=2))

    p_secrets = Path(secrets_path)
    p_secrets.write_text(
        "DB_PASSWORD=hunter2\n"
        "API_KEY=sk-demo-not-a-real-key\n"
        "DB_HOST=db.internal.example.com\n"
    )
    return str(p_cfg), str(p_secrets)


if __name__ == "__main__":
    print("Generating synthetic sales CSV (2,000,000 rows)...")
    t0 = time.perf_counter()
    sales_path = generate_sales_csv(
        "/tmp/ikichunk_demo/sales.csv", rows=2_000_000)
    size_mb = Path(sales_path).stat().st_size / 1024 / 1024
    print(
        f"  -> {sales_path} ({size_mb:.1f} MB) in {time.perf_counter()-t0:.1f}s")

    print("Generating synthetic event log JSONL (200,000 rows)...")
    log_path = generate_event_log_jsonl(
        "/tmp/ikichunk_demo/events.jsonl", rows=200_000)
    size_mb = Path(log_path).stat().st_size / 1024 / 1024
    print(f"  -> {log_path} ({size_mb:.1f} MB)")

    print("Generating synthetic user activity JSONL (200,000 rows)...")
    activity_path = generate_user_activity_jsonl(
        "/tmp/ikichunk_demo/activity.jsonl", rows=200_000)
    size_mb = Path(activity_path).stat().st_size / 1024 / 1024
    print(f"  -> {activity_path} ({size_mb:.1f} MB)")

    print("Generating synthetic product catalog YAML (200 rows)...")
    catalog_path = generate_product_catalog_yaml(
        "/tmp/ikichunk_demo/catalog.yaml", rows=200)
    size_mb = Path(catalog_path).stat().st_size / 1024 / 1024
    print(f"  -> {catalog_path} ({size_mb:.1f} MB)")

    print("Generating synthetic product catalog TSV (200 rows)...")
    tsv_path = generate_product_catalog_tsv(
        "/tmp/ikichunk_demo/catalog.tsv", rows=200)
    size_mb = Path(tsv_path).stat().st_size / 1024 / 1024
    print(f"  -> {tsv_path} ({size_mb:.1f} MB)")

    print("Generating synthetic sales parquet (200 rows)...")
    parquet_path = generate_sales_parquet(
        "/tmp/ikichunk_demo/sales.parquet", rows=200)
    size_mb = Path(parquet_path).stat().st_size / 1024 / 1024
    print(f"  -> {parquet_path} ({size_mb:.1f} MB)")

    print("Generating synthetic catalog pickle (200 rows)...")
    pickle_path = generate_catalog_pickle(
        "/tmp/ikichunk_demo/catalog.pkl", rows=200)
    size_mb = Path(pickle_path).stat().st_size / 1024 / 1024
    print(f"  -> {pickle_path} ({size_mb:.1f} MB)")

    cfg, secrets = generate_config_secrets_demo(
        "/tmp/ikichunk_demo/config.json", "/tmp/ikichunk_demo/secrets.env"
    )
    print(f"Generated config demo files: {cfg}, {secrets}")
