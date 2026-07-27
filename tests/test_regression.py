import csv
import importlib.util
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest

from ikichunk import Partition, partition
from ikichunk.exceptions import MissingDependencyError, PartitionParallelError, UnsafeArchiveError, UnsafeCommandError, UnknownFormatError


@pytest.fixture()
def temp_workspace(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


def write_csv(path: Path, rows: int):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "value"])
        for i in range(rows):
            writer.writerow([i, i * 2])


def test_read_write_and_inspect_roundtrip(temp_workspace):
    path = temp_workspace / "sample.json"
    partition.write(str(path), {"answer": 42})
    assert partition.read(str(path)) == {"answer": 42}
    info = partition.inspect(str(path))
    assert info["type"] == "dict"
    assert info["keys"] == ["answer"]
    assert partition.inspect({"api_key": "secret"})[
        "sample"]["api_key"] == "<redacted>"


def test_split_file_and_manifest(temp_workspace):
    src = temp_workspace / "big.csv"
    write_csv(src, 10)
    out_dir = temp_workspace / "parts"

    parts = partition.split_file(
        str(src), by="rows", rows=3, out_dir=str(out_dir))
    assert len(parts) == 4
    manifest = partition.manifest(parts)
    assert manifest["algo"] == "sha256"
    assert len(manifest["files"]) == 4
    assert all(Path(item["path"]).exists() for item in manifest["files"])

    single_manifest = partition.manifest(src)
    assert single_manifest["files"][0]["path"] == str(src)


def test_smart_split_and_parallel(temp_workspace):
    src = temp_workspace / "big.csv"
    write_csv(src, 20)

    parts, why = partition.smart_split(
        str(src), goal="parallel", explain=True, out_dir=str(temp_workspace / "smart"))
    assert len(parts) >= 1
    assert why["goal"] == "parallel"

    def transform(path):
        rows = partition.read(path)
        return len(rows)

    results = partition.pmap(transform, parts, workers=min(2, len(parts)))
    assert results == [3, 3, 3, 3, 3, 3, 3, 3] or results == [
        len(partition.read(p)) for p in parts]


def test_hash_verify_and_compress_roundtrip(temp_workspace):
    src = temp_workspace / "example.txt"
    src.write_text("hello world", encoding="utf-8")
    digest = partition.hash(str(src))
    assert partition.verify(str(src), digest)

    gz = partition.compress(str(src), algo="gzip", out=str(
        temp_workspace / "example.txt.gz"), keep_original=False)
    assert Path(gz).exists()
    restored = partition.decompress(
        gz, out=str(temp_workspace / "restored.txt"))
    assert Path(restored).read_text(encoding="utf-8") == "hello world"


def test_archive_and_extract_guard(temp_workspace):
    src_dir = temp_workspace / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("A", encoding="utf-8")
    archive = temp_workspace / "batch.tar.gz"
    partition.archive(str(src_dir), str(archive))
    extracted = temp_workspace / "extracted"
    partition.extract(str(archive), out_dir=str(extracted))
    assert (extracted / "a.txt").exists()

    malicious = temp_workspace / "malicious.tar.gz"
    with tarfile.open(malicious, "w:gz") as tar:
        payload = b"oops"
        info = tarfile.TarInfo("../payload.txt")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises(UnsafeArchiveError):
        partition.extract(str(malicious), out_dir=str(temp_workspace / "safe"))


def test_config_and_env(temp_workspace):
    config_path = temp_workspace / "config.yaml"
    config_path.write_text("app_name: demo\n", encoding="utf-8")
    secrets_path = temp_workspace / ".env"
    secrets_path.write_text("API_KEY=abc123\n", encoding="utf-8")
    cfg = partition.config(str(config_path), secrets=str(
        secrets_path), env_prefix="APP_")
    assert cfg["app_name"] == "demo"
    assert cfg["API_KEY"] == "abc123"
    os.environ["APP_API_KEY"] = "abc123"
    assert partition.env("APP_API_KEY", default="x") == "abc123"


def test_process_and_shell_safety():
    assert partition.which("python") is not None
    assert partition.is_running(os.getpid())
    assert partition.is_port_open("127.0.0.1", 1) is False
    result = partition.run([sys.executable, "--version"], check=True)
    assert result[0] == 0
    assert result.ok is True

    python3_result = partition.run(["python3", "--version"], check=True)
    assert python3_result.ok is True

    with pytest.raises(UnsafeCommandError):
        partition.run("cat /etc/os-release | grep NAME")


def test_render_template():
    rendered = partition.render("app=$app region=$region", {
                                "app": "demo", "region": "us-east"})
    assert rendered == "app=demo region=us-east"

    with pytest.raises(KeyError):
        partition.render("port=$port", {"region": "us-east"})


def test_example_aliases(temp_workspace):
    src = temp_workspace / "example.csv"
    write_csv(src, 6)

    parts = partition.split_file(str(src), parts=2)
    assert len(parts) == 2

    smart_parts = partition.smart_split(str(src), chunk_size=2)
    assert len(smart_parts) == 2


def test_synthetic_yaml_generator(temp_workspace):
    spec = importlib.util.spec_from_file_location(
        "synthetic_data",
        Path(__file__).resolve().parents[1] /
        "examples" / "00_synthetic_data.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    yaml_path = module.generate_product_catalog_yaml(
        str(temp_workspace / "catalog.yaml"), rows=8)
    assert Path(yaml_path).exists()
    data = partition.read(yaml_path)
    assert isinstance(data, list)
    assert len(data) == 8
    assert data[0]["sku"].startswith("SKU-")


def test_synthetic_tabular_and_binary_generators(temp_workspace):
    spec = importlib.util.spec_from_file_location(
        "synthetic_data",
        Path(__file__).resolve().parents[1] /
        "examples" / "00_synthetic_data.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    tsv_path = module.generate_product_catalog_tsv(
        str(temp_workspace / "catalog.tsv"), rows=8)
    assert Path(tsv_path).exists()
    tsv_rows = partition.read(tsv_path)
    assert len(tsv_rows) == 8
    assert tsv_rows[0]["sku"].startswith("SKU-")

    parquet_path = module.generate_sales_parquet(
        str(temp_workspace / "sales.parquet"), rows=8)
    assert Path(parquet_path).exists()
    parquet_data = partition.read(parquet_path)
    parquet_rows = parquet_data.to_dicts() if hasattr(
        parquet_data, "to_dicts") else parquet_data
    assert len(parquet_rows) == 8
    assert parquet_rows[0]["region"] in {
        "us-east", "us-west", "eu-west", "eu-central", "apac"}

    pickle_path = module.generate_catalog_pickle(
        str(temp_workspace / "catalog.pkl"), rows=8)
    assert Path(pickle_path).exists()
    payload = partition.read(pickle_path)
    assert payload["rows"][0]["sku"].startswith("SKU-")


def test_parquet_read_returns_polars_dataframe_and_inspects_cleanly(temp_workspace):
    pl = pytest.importorskip("polars")

    spec = importlib.util.spec_from_file_location(
        "synthetic_data",
        Path(__file__).resolve().parents[1] /
        "examples" / "00_synthetic_data.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    parquet_path = module.generate_sales_parquet(
        str(temp_workspace / "sales.parquet"), rows=5)
    df = partition.read(parquet_path)
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 5

    info = partition.inspect(df, sample=2)
    assert info["type"] == "DataFrame"
    assert info["shape"] == (5, 6)
    assert "region" in info["columns"]
    assert len(info["sample"]) == 2


def test_feather_and_avro_roundtrip(temp_workspace):
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"sku": ["SKU-1", "SKU-2"], "stock": [10, 20]})

    feather_path = temp_workspace / "catalog.feather"
    partition.write(str(feather_path), df)
    restored = partition.read(str(feather_path))
    assert isinstance(restored, pl.DataFrame)
    assert restored.to_dicts() == df.to_dicts()

    avro_path = temp_workspace / "catalog.avro"
    partition.write(str(avro_path), df)
    restored_avro = partition.read(str(avro_path))
    assert isinstance(restored_avro, pl.DataFrame)
    assert restored_avro.to_dicts() == df.to_dicts()


def test_excel_roundtrip(temp_workspace):
    pl = pytest.importorskip("polars")
    pytest.importorskip("fastexcel")
    pytest.importorskip("xlsxwriter")

    df = pl.DataFrame({"sku": ["SKU-1", "SKU-2"], "price": [9.99, 19.99]})
    excel_path = temp_workspace / "catalog.xlsx"
    partition.write(str(excel_path), df)
    restored = partition.read(str(excel_path))
    assert isinstance(restored, pl.DataFrame)
    assert restored.to_dicts() == df.to_dicts()


def test_split_tsv_file_preserves_columns(temp_workspace):
    src = temp_workspace / "catalog.tsv"
    src.write_text(
        "sku\tname\tcategory\nSKU-1\tWidget\tTools\nSKU-2\tGadget\tHome\n",
        encoding="utf-8",
    )

    parts = partition.split_file(
        str(src), by="count", count=2, out_dir=str(temp_workspace / "parts"), fmt="tsv")

    assert len(parts) == 2
    first_rows = partition.read(parts[0])
    assert first_rows[0]["sku"] == "SKU-1"
    assert first_rows[0]["category"] == "Tools"


def test_inspect_path_objects_and_recursive_redaction(temp_workspace):
    payload_path = temp_workspace / "payload.json"
    payload_path.write_text(
        json.dumps({"user": "alice", "api_key": "secret",
                   "nested": {"token": "abc"}}),
        encoding="utf-8",
    )

    file_info = partition.inspect(payload_path)
    assert file_info["type"] == "dict"
    assert file_info["sample"]["api_key"] == "<redacted>"
    assert file_info["sample"]["nested"]["token"] == "<redacted>"

    list_info = partition.inspect([{"api_key": "secret"}, {"user": "bob"}])
    assert list_info["sample"][0]["api_key"] == "<redacted>"


def test_unknown_format_raises():
    with pytest.raises(UnknownFormatError):
        partition.read(str(Path("does-not-exist.xyz")))


def test_process_pool_pickling_guard():
    def bad_func(x):
        return x

    with pytest.raises(PartitionParallelError):
        partition.pmap(bad_func, [1], workers=1, backend="process")
