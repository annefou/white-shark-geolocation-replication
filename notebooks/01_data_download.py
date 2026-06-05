# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 01 — Data download (all recovered-PAT tags)
#
# Fetches all inputs for the **geolocation replication** of O'Sullivan et al.
# 2022 (*Scientific Data* 9:142,
# [10.1038/s41597-022-01235-3](https://doi.org/10.1038/s41597-022-01235-3)):
# **"A biologging database of juvenile white sharks from the northeast Pacific."**
#
# This notebook scales the proven single-tag pipeline (shark `07_05`) to the
# **seven recovered-PAT tags** that have a full depth + temperature time series:
#
# | Tag | PAT ZIP | Co-deployed SPOT (Argos referee) |
# |---|---|---|
# | `07_05` | `07_05-66885.zip` | `07_05-77272.zip` |
# | `08_01` | `08_01-40561.zip` | `08_01-77274.zip` |
# | `08_02` | `08_02-55716.zip` | `08_02-77273.zip` |
# | `08_09` | `08_09-83066.zip` | `08_09-83076.zip` |
# | `02_01` | `02_01-18616.zip` | — (PAT-only) |
# | `06_10` | `06_10-40564.zip` | — (PAT-only) |
# | `07_01` | `07_01-64272.zip` | — (PAT-only) |
#
# Three sources are pulled here:
#
# 1. **Biologging archive** (dataset DOI
#    [10.24431/rw1k6c3](https://doi.org/10.24431/rw1k6c3), CC-BY), hosted on the
#    ATN DAC / Research Workspace, a DataONE member node. We resolve the DOI to a
#    DataONE data package, list every aggregated object, download the deployment
#    metadata table, and for each tag the per-deployment ZIP packages (depth +
#    temperature series, the GPE3 baseline track, the SPOT Argos fixes).
# 2. **GLORYS12V1 `thetao`** 3-D ocean temperature reanalysis (Copernicus Marine
#    `GLOBAL_MULTIYEAR_PHY_001_030`), the reference field the pangeo-fish HMM
#    matches each tag's temperature-at-depth against. Subset **per tag** to its
#    deployment window and a per-tag NE-Pacific bounding box (GPE3 extent + a
#    margin), so compact tracks download a small box and basin-scale roamers
#    (06_10) get a box that actually covers the track.
# 3. **GLORYS static bathymetry** (`deptho` + land/ocean `mask`) over the union
#    NE-Pacific box, downloaded once and reused for every tag.
#
# **Credentials:** the archive is public CC-BY (no credentials). Copernicus
# Marine needs `~/.copernicusmarine/.copernicusmarine-credentials` (created once
# with `copernicusmarine login`, or supplied in CI from a secret).
#
# All downloads are **cached**: re-running this notebook skips files already on
# disk, so scaling from one tag to seven never re-downloads the proven 07_05.

# %%
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import requests

# %%
RAW_DIR = Path("../data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
TAG_DIR = RAW_DIR / "tag_packages"
TAG_DIR.mkdir(parents=True, exist_ok=True)
GLORYS_DIR = RAW_DIR / "glorys"
GLORYS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_DOI = "10.24431/rw1k6c3"
CN_SOLR = "https://cn.dataone.org/cn/v2/query/solr/"
CN_RESOLVE = "https://cn.dataone.org/cn/v2/resolve/"

# %% [markdown]
# ## The seven recovered-PAT tags
#
# Selection: the recovered-PAT tags with a full depth + temperature time series
# (`out-Archive.csv`) inside their ZIP. Four have a co-deployed SPOT tag that
# supplies the Argos accuracy referee; three are PAT-only (no referee — for
# those the pangeo-fish track can only be compared to GPE3, which is itself an
# estimate). `PAT_DEPLOY_ID` / `SPOT_DEPLOY_ID` give the ZIP filenames.

# %%
# Registry: shark_id -> (PAT_DEPLOY_ID, SPOT_DEPLOY_ID or None, has_referee).
TAGS = {
    "07_05": ("07_05-66885", "07_05-77272", True),
    "08_01": ("08_01-40561", "08_01-77274", True),
    "08_02": ("08_02-55716", "08_02-77273", True),
    "08_09": ("08_09-83066", "08_09-83076", True),
    "02_01": ("02_01-18616", None, False),
    "06_10": ("06_10-40564", None, False),
    "07_01": ("07_01-64272", None, False),
}

# GLORYS12V1 (GLOBAL_MULTIYEAR_PHY_001_030) Copernicus Marine dataset IDs.
GLORYS_THETAO = "cmems_mod_glo_phy_my_0.083deg_P1D-m_202311"
GLORYS_STATIC = "cmems_mod_glo_phy_my_0.083deg_static_202311"

# Per-tag GLORYS box = GPE3 track extent + this margin (deg), clamped to a sane
# NE-Pacific envelope. Keeps compact tracks cheap and covers basin-scale roamers.
BBOX_MARGIN = 2.0
NE_PACIFIC_ENVELOPE = {"longitude": (-135.0, -105.0), "latitude": (18.0, 42.0)}
MAX_DEPTH = 900.0  # m; deeper than any tag's max recorded depth

# %% [markdown]
# ## Step 1 — resolve the DOI to a DataONE data package

# %%
def solr_query(q: str, fl: str, rows: int = 500) -> list[dict]:
    """Query the DataONE CN solr index and return the matching docs."""
    resp = requests.get(
        CN_SOLR,
        params={"q": q, "fl": fl, "rows": rows, "wt": "json"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]["docs"]


doi_token = DATASET_DOI.replace("/", "_")
meta_docs = solr_query(
    q=f"id:*{doi_token.split('_')[-1]}*",
    fl="identifier,formatId,title,resourceMap,dateUploaded",
)
meta_docs = [d for d in meta_docs if "isotc211" in d.get("formatId", "")]
meta_docs.sort(key=lambda d: d.get("dateUploaded", ""))
metadata = meta_docs[-1]
resource_map = metadata["resourceMap"][0]

print(f"Dataset DOI:    {DATASET_DOI}")
print(f"Title:          {metadata['title']}")
print(f"Resource map:   {resource_map}")

# %% [markdown]
# ## Step 2 — list every data object in the package

# %%
objs = solr_query(
    q=f'resourceMap:"{resource_map}"',
    fl="identifier,fileName,formatId,size",
)
manifest = pd.DataFrame(
    [
        {
            "identifier": o["identifier"],
            "fileName": o.get("fileName"),
            "formatId": o.get("formatId"),
            "size": o.get("size"),
            "dataUrl": CN_RESOLVE + o["identifier"],
        }
        for o in objs
        if "isotc211" not in o.get("formatId", "")
    ]
).sort_values("fileName", na_position="first").reset_index(drop=True)
manifest.to_csv(RAW_DIR / "package_manifest.csv", index=False)

zip_pkgs = manifest[manifest["formatId"] == "application/zip"]
print(f"Package objects: {len(manifest)}  (ZIP data packages: {len(zip_pkgs)})")

# %% [markdown]
# ## Step 3 — download the deployment metadata table

# %%
def resolve_object(pid: str) -> list[str]:
    """Return member-node download URLs for a DataONE PID (no redirect-follow)."""
    r = requests.get(CN_RESOLVE + pid, timeout=120, allow_redirects=False)
    urls = re.findall(r"<url>(.*?)</url>", r.text)
    return urls or [f"https://cn.dataone.org/cn/v2/object/{pid}"]


def download_object(pid: str, out_path: Path) -> Path:
    """Stream a DataONE object to disk if not already cached, trying MN mirrors."""
    if out_path.exists():
        print(f"  cached: {out_path.name}")
        return out_path
    last_err = None
    for u in resolve_object(pid):
        try:
            resp = requests.get(u, stream=True, timeout=900)
            resp.raise_for_status()
            with open(out_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    fh.write(chunk)
            print(f"  downloaded: {out_path.name} "
                  f"({out_path.stat().st_size} bytes)")
            return out_path
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"all mirrors failed for {out_path.name}: {last_err}")


WANTED_CSVS = {
    "JWS_metadata.csv",
    "JWS_metadata_README.csv",
    "PAT_programming_table.csv",
    "PAT_programming_table_README.csv",
}
print("Downloading metadata tables:")
for _, r in manifest[manifest["fileName"].isin(WANTED_CSVS)].iterrows():
    download_object(r["identifier"], RAW_DIR / r["fileName"])

# %% [markdown]
# ## Step 4 — download every tag's ZIP packages (recovered PAT + co-deployed SPOT)
#
# Each recovered-PAT package holds `out-Archive.csv` (depth + external-water
# temperature) and the published `*-GPE3.csv` baseline track. Each co-deployed
# SPOT package holds the Argos fixes used as the accuracy referee.

# %%
def download_zip(zip_name: str) -> Path:
    row = manifest[manifest["fileName"] == zip_name]
    if row.empty:
        raise FileNotFoundError(f"{zip_name} not in package manifest")
    pid = row.iloc[0]["identifier"]
    return download_object(pid, TAG_DIR / zip_name)


print("Downloading tag packages:")
for shark, (pat_dep, spot_dep, has_referee) in TAGS.items():
    print(f"  {shark}:")
    download_zip(f"{pat_dep}.zip")
    if spot_dep is not None:
        download_zip(f"{spot_dep}.zip")

# %% [markdown]
# ## Step 5 — per-tag GLORYS box from the GPE3 extent
#
# Each tag's GLORYS subset is sized to the GPE3 track's geographic extent plus a
# margin (clamped to the NE-Pacific envelope), and to the tag's deployment window
# (`DATE_START` → `PAT_END` + 1 day). We read the GPE3 extent straight from each
# PAT ZIP so the box is data-driven, not hardcoded.

# %%
import zipfile  # noqa: E402
from io import StringIO  # noqa: E402

sharks = pd.read_csv(RAW_DIR / "JWS_metadata.csv", dtype=str, encoding="latin-1")
sharks = sharks.apply(lambda c: c.str.strip() if c.dtype == "object" else c)


def gpe3_extent(pat_dep: str) -> tuple[float, float, float, float]:
    """(lon_min, lon_max, lat_min, lat_max) of a tag's GPE3 most-likely track."""
    zf = zipfile.ZipFile(TAG_DIR / f"{pat_dep}.zip")
    name = next(n for n in zf.namelist() if n.endswith("-GPE3.csv"))
    raw = zf.open(name).read().decode("latin-1")
    lines = raw.splitlines()
    hdr = next(i for i, ln in enumerate(lines)
               if (not ln.startswith(";")) and ("Most Likely Latitude" in ln))
    df = pd.read_csv(StringIO("\n".join(lines[hdr:])))
    df = df.dropna(subset=["Most Likely Latitude", "Most Likely Longitude"])
    return (df["Most Likely Longitude"].min(), df["Most Likely Longitude"].max(),
            df["Most Likely Latitude"].min(), df["Most Likely Latitude"].max())


def tag_bbox(shark: str, pat_dep: str) -> dict:
    """Per-tag GLORYS box: GPE3 extent + release/popup + margin, clamped."""
    row = sharks[sharks["SHARK_ID"] == shark].iloc[0]
    lon0, lon1, lat0, lat1 = gpe3_extent(pat_dep)
    lons = [lon0, lon1, float(row["LON_REL"])]
    lats = [lat0, lat1, float(row["LAT_REL"])]
    if row["LON_END_PAT"] not in ("DNT", "ND", "NA", ""):
        lons.append(float(row["LON_END_PAT"]))
        lats.append(float(row["LAT_END_PAT"]))
    elon = NE_PACIFIC_ENVELOPE["longitude"]
    elat = NE_PACIFIC_ENVELOPE["latitude"]
    return {
        "longitude": (max(min(lons) - BBOX_MARGIN, elon[0]),
                      min(max(lons) + BBOX_MARGIN, elon[1])),
        "latitude": (max(min(lats) - BBOX_MARGIN, elat[0]),
                     min(max(lats) + BBOX_MARGIN, elat[1])),
    }


def tag_window(shark: str) -> tuple[str, str]:
    row = sharks[sharks["SHARK_ID"] == shark].iloc[0]
    t0 = pd.to_datetime(row["DATE_START"]).strftime("%Y-%m-%d")
    t1 = (pd.to_datetime(row["PAT_END"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    return t0, t1


# %% [markdown]
# ## Step 6 — download the GLORYS `thetao` subset for each tag
#
# Cached per tag to `glorys_thetao_<shark>.nc`. The static bathymetry/mask is
# downloaded once over the full NE-Pacific envelope and reused for every tag.
#
# **Hard wall-clock timeout (robustness, kept in the committed notebook).**
# `copernicusmarine.subset()` has no socket/wall-clock timeout of its own and can
# wedge indefinitely on an oversized box (a basin-scale roamer like `06_10` builds
# a very large box). A signal-based timeout is ignored by `cm.subset` inside a
# notebook. We therefore run each subset as a **separate OS process** — the
# `copernicusmarine subset ...` console script — under
# `subprocess.run(..., timeout=...)`, which is the one robust way to enforce a hard
# wall-clock kill: a child OS process can be killed regardless of what it is doing,
# and `subprocess` will not re-import this notebook (unlike `multiprocessing`'s
# `spawn`, which would re-run the whole download loop in every child). On timeout
# we kill the child, remove the `.nc.<tmp>` partials for that tag, and mark the tag
# failed — it can never wedge the whole run. Downloads are strictly **serial** (one
# subprocess at a time); the orchestrator must confirm no other
# `01_data_download` / `copernicusmarine` process is running before starting.

# %%
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

import copernicusmarine as cm  # noqa: E402  (used for the small cached static subset)

# Resolve the copernicusmarine console script (sits next to the interpreter in
# the same env); fall back to PATH lookup so the notebook works under pixi + CI.
CMC_BIN = (str(Path(sys.executable).with_name("copernicusmarine"))
           if Path(sys.executable).with_name("copernicusmarine").exists()
           else shutil.which("copernicusmarine") or "copernicusmarine")

# Per-tag hard wall-clock budget for a single cm.subset() attempt.
SUBSET_TIMEOUT_S = 600
# Best-effort tags (PAT-only roamers): one attempt at the data-driven box, then a
# single retry with a tightened box (drop the bbox margin); if both time out the
# tag is recorded FAILED and the run continues. 06_10 is the basin-scale roamer.
BEST_EFFORT_TAGS = {"06_10"}
# Download order: 07_01 (well-behaved) before 06_10 (oversized) so the roamer can
# never starve the well-behaved tag. Remaining tags keep registry order.
DOWNLOAD_ORDER = ["07_05", "08_01", "08_02", "08_09", "02_01", "07_01", "06_10"]


def _clean_partials(out_nc: Path) -> None:
    """Remove any `<name>.nc.<tmp>` partials left by an aborted cm.subset()."""
    for p in GLORYS_DIR.glob(out_nc.name + ".*"):
        try:
            p.unlink()
        except OSError:
            pass


def subset_cmd(bbox: dict, t0: str, t1: str, out_nc: Path) -> list[str]:
    """Build the `copernicusmarine subset ...` argv for one tag."""
    return [
        CMC_BIN, "subset",
        "--dataset-id", GLORYS_THETAO,
        "--variable", "thetao", "--variable", "zos",
        "--minimum-longitude", str(bbox["longitude"][0]),
        "--maximum-longitude", str(bbox["longitude"][1]),
        "--minimum-latitude", str(bbox["latitude"][0]),
        "--maximum-latitude", str(bbox["latitude"][1]),
        "--start-datetime", t0, "--end-datetime", t1,
        "--minimum-depth", "0", "--maximum-depth", str(MAX_DEPTH),
        "--output-filename", out_nc.name,
        "--output-directory", str(GLORYS_DIR),
        "--coordinates-selection-method", "outside",
        "--overwrite", "--disable-progress-bar",
    ]


def subset_with_timeout(cmd: list[str], out_nc: Path, timeout_s: int) -> bool:
    """Run a cm.subset CLI invocation with a hard wall-clock timeout.

    Returns True iff the output file was produced. On timeout the child OS process
    is killed, partials are cleaned, and False is returned. Never wedges.
    """
    try:
        r = subprocess.run(cmd, timeout=timeout_s, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        _clean_partials(out_nc)
        print(f"  TIMEOUT after {timeout_s}s — killed child, cleaned partials")
        return False
    if r.returncode != 0:
        _clean_partials(out_nc)
        print(f"  cm.subset exited {r.returncode}: "
              f"{(r.stderr or '').strip()[-300:]}")
        return False
    return out_nc.exists()


def tight_bbox(pat_dep: str) -> dict:
    """Tightened box = GPE3 high-confidence extent with NO margin (retry box)."""
    lon0, lon1, lat0, lat1 = gpe3_extent(pat_dep)
    return {"longitude": (lon0, lon1), "latitude": (lat0, lat1)}


download_status = {}
tag_boxes = {}
for shark in DOWNLOAD_ORDER:
    pat_dep, spot_dep, has_referee = TAGS[shark]
    bbox = tag_bbox(shark, pat_dep)
    t0, t1 = tag_window(shark)
    tag_boxes[shark] = {"bbox": bbox, "window": [t0, t1]}
    out_nc = GLORYS_DIR / f"glorys_thetao_{shark}.nc"
    print(f"{shark}: window {t0}->{t1}  "
          f"lon{bbox['longitude']} lat{bbox['latitude']}")
    if out_nc.exists():
        print(f"  cached: {out_nc.name}")
        download_status[shark] = "cached"
        continue
    # Clean any stale partial from a previously-wedged attempt before retrying.
    _clean_partials(out_nc)
    print(f"  downloading GLORYS thetao subset "
          f"(<= {SUBSET_TIMEOUT_S}s, child process) ...")
    ok = subset_with_timeout(
        subset_cmd(bbox, t0, t1, out_nc), out_nc, SUBSET_TIMEOUT_S)
    if not ok and shark in BEST_EFFORT_TAGS:
        tb = tight_bbox(pat_dep)
        print(f"  retry (best-effort) with tightened box "
              f"lon{tb['longitude']} lat{tb['latitude']} ...")
        _clean_partials(out_nc)
        ok = subset_with_timeout(
            subset_cmd(tb, t0, t1, out_nc), out_nc, SUBSET_TIMEOUT_S)
    if ok:
        print(f"  downloaded: {out_nc.name} ({out_nc.stat().st_size} bytes)")
        download_status[shark] = "downloaded"
    else:
        reason = ("GLORYS subset timeout — oversized basin box"
                  if shark in BEST_EFFORT_TAGS
                  else f"GLORYS subset failed within {SUBSET_TIMEOUT_S}s")
        print(f"  FAILED: {reason} (continuing — tag dropped)")
        download_status[shark] = f"failed: {reason}"

# %%
# Static is downloaded over the full NE-Pacific envelope (filename carries the
# "nepac" tag so it is not confused with any earlier, smaller-box static cache).
glorys_static_nc = GLORYS_DIR / "glorys_static_nepac.nc"
if not glorys_static_nc.exists():
    print("Downloading GLORYS static bathymetry/mask (NE-Pacific envelope) ...")
    cm.subset(
        dataset_id=GLORYS_STATIC,
        variables=["deptho", "mask"],
        minimum_longitude=NE_PACIFIC_ENVELOPE["longitude"][0],
        maximum_longitude=NE_PACIFIC_ENVELOPE["longitude"][1],
        minimum_latitude=NE_PACIFIC_ENVELOPE["latitude"][0],
        maximum_latitude=NE_PACIFIC_ENVELOPE["latitude"][1],
        output_filename=glorys_static_nc.name,
        output_directory=str(GLORYS_DIR),
        coordinates_selection_method="outside",
    )
else:
    print(f"  cached: {glorys_static_nc.name}")

# %% [markdown]
# ## Step 7 — source log

# %%
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


checksums = {
    p.name: sha256(p)
    for p in sorted(RAW_DIR.glob("*.csv"))
    if p.name != "package_manifest.csv"
}

sources = {
    "biologging_archive": {
        "name": "A biologging database of juvenile white sharks from the "
                "Northeast Pacific, 2001-2020",
        "doi": DATASET_DOI,
        "url": f"https://doi.org/{DATASET_DOI}",
        "repository": "ATN DAC / Research Workspace (DataONE member node)",
        "license": "CC-BY-4.0",
        "resource_map": resource_map,
        "checksums_sha256": checksums,
        "tags": {
            shark: {
                "pat_zip": f"{pat_dep}.zip",
                "spot_zip": (f"{spot_dep}.zip" if spot_dep else None),
                "has_referee": has_referee,
            }
            for shark, (pat_dep, spot_dep, has_referee) in TAGS.items()
        },
    },
    "reference_field": {
        "name": "GLORYS12V1 global ocean physics reanalysis",
        "product": "GLOBAL_MULTIYEAR_PHY_001_030",
        "thetao_dataset_id": GLORYS_THETAO,
        "static_dataset_id": GLORYS_STATIC,
        "service": "Copernicus Marine Service",
        "ne_pacific_envelope": NE_PACIFIC_ENVELOPE,
        "per_tag_boxes": tag_boxes,
        "per_tag_download_status": download_status,
    },
    "accessed_on": "2026-06-04",
}
with open(RAW_DIR / "sources.json", "w") as fh:
    json.dump(sources, fh, indent=2, default=list)

print(f"Logged source provenance to {RAW_DIR / 'sources.json'}")
