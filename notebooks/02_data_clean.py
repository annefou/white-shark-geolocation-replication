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
# # 02 — Data clean (all recovered-PAT tags)
#
# Turns the raw archive into analysis-ready inputs for the pangeo-fish HMM
# geolocation (notebook 03), **for every recovered-PAT tag**. For each tag we
# build, under per-tag paths:
#
# ```
# data/clean/tags/<tag>/dst.csv             time, pressure, temperature
# data/clean/tags/<tag>/tagging_events.csv  event_name, time, lon, lat
# data/clean/tags/<tag>/metadata.json
# data/clean/gpe3_<tag>.csv                 GPE3 daily baseline track
# data/clean/argos_<tag>.csv                SPOT Argos referee (referee tags only)
# data/clean/reference_model_<tag>.nc       GLORYS reference model (per-tag box)
# ```
#
# The scientific input is each tag's **depth + external-water temperature time
# series** (`out-Archive.csv`). We keep **Depth** as `pressure` and **External
# Temperature** (ambient water) as `temperature` — the external sensor records
# ambient water, so matching against GLORYS `thetao` is valid despite
# white-shark regional endothermy. Internal Temperature (body heat) is discarded.
#
# **Honest skip rule.** One tag (`02_01`, a 2001 PAT2) has **no External
# Temperature sensor** — its archive carries only "Recorder Temp" (internal
# instrument temperature, not ambient water). The temperature-at-depth-vs-GLORYS
# emission is invalid for it, so it is recorded as a skipped tag with that exact
# reason and excluded from the analysis. Nothing is fabricated.

# %%
import json
import zipfile
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# %%
RAW_DIR = Path("../data/raw")
CLEAN_DIR = Path("../data/clean")
TAGS_DIR = CLEAN_DIR / "tags"
TAGS_DIR.mkdir(parents=True, exist_ok=True)
TAG_PKG_DIR = RAW_DIR / "tag_packages"
GLORYS_DIR = RAW_DIR / "glorys"

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

# Resample the DST to this cadence to bound memory while preserving the vertical
# structure the HMM matches against GLORYS depth levels.
DST_RESAMPLE = "10min"

# %%
sharks = pd.read_csv(RAW_DIR / "JWS_metadata.csv", dtype=str, encoding="latin-1")
sharks = sharks.apply(lambda c: c.str.strip() if c.dtype == "object" else c)

# %% [markdown]
# ## Per-tag cleaning helpers

# %%
def clean_dst(pat_dep: str) -> pd.DataFrame | None:
    """Depth + External-Temperature series from a PAT ZIP; None if no ambient
    sensor (e.g. the 2001 PAT2 records only internal 'Recorder Temp')."""
    zf = zipfile.ZipFile(TAG_PKG_DIR / f"{pat_dep}.zip")
    with zf.open("out-Archive.csv") as fh:
        head = pd.read_csv(fh, nrows=1)
    if "External Temperature" not in head.columns:
        return None
    with zf.open("out-Archive.csv") as fh:
        arch = pd.read_csv(
            fh, usecols=["Time", "Depth", "External Temperature"],
            low_memory=False)
    arch["time"] = pd.to_datetime(arch["Time"], format="%H:%M:%S %d-%b-%Y",
                                  errors="coerce")
    dst = (
        arch.dropna(subset=["time", "Depth", "External Temperature"])
        .rename(columns={"Depth": "pressure",
                         "External Temperature": "temperature"})
        .set_index("time")[["pressure", "temperature"]]
        .sort_index()
    )
    dst["pressure"] = dst["pressure"].clip(lower=0.0)
    dst = dst.resample(DST_RESAMPLE).mean().dropna()
    return dst


def tagging_events(shark: str) -> pd.DataFrame:
    row = sharks[sharks["SHARK_ID"] == shark].iloc[0]
    return pd.DataFrame({
        "event_name": ["release", "fish_death"],
        "time": [pd.to_datetime(row["DATE_START"]),
                 pd.to_datetime(row["PAT_END"])],
        "longitude": [float(row["LON_REL"]), float(row["LON_END_PAT"])],
        "latitude": [float(row["LAT_REL"]), float(row["LAT_END_PAT"])],
    })


def clean_gpe3(pat_dep: str) -> pd.DataFrame:
    """Daily most-likely GPE3 positions (glob the `*-GPE3.csv` whose run-number
    suffix varies per tag)."""
    zf = zipfile.ZipFile(TAG_PKG_DIR / f"{pat_dep}.zip")
    name = next(n for n in zf.namelist() if n.endswith("-GPE3.csv"))
    raw = zf.open(name).read().decode("latin-1")
    lines = raw.splitlines()
    hdr = next(i for i, ln in enumerate(lines)
               if (not ln.startswith(";")) and ("Most Likely Latitude" in ln))
    gpe3 = pd.read_csv(StringIO("\n".join(lines[hdr:])))
    gpe3["time"] = pd.to_datetime(gpe3["Date"], errors="coerce")
    gpe3 = (
        gpe3.dropna(subset=["time", "Most Likely Latitude",
                            "Most Likely Longitude"])
        .rename(columns={"Most Likely Latitude": "latitude",
                         "Most Likely Longitude": "longitude"})
        [["time", "latitude", "longitude"]]
        .sort_values("time")
    )
    return (gpe3.set_index("time")[["latitude", "longitude"]]
            .resample("1D").mean().dropna().reset_index())


def clean_argos(spot_dep: str) -> pd.DataFrame:
    """SPOT Argos fixes, classes 1/2/3 only (error < ~1.5 km)."""
    zf = zipfile.ZipFile(TAG_PKG_DIR / f"{spot_dep}.zip")
    loc_name = next(n for n in zf.namelist() if n.endswith("-Locations.csv"))
    with zf.open(loc_name) as fh:
        spot = pd.read_csv(fh)
    spot["time"] = pd.to_datetime(spot["Date"], errors="coerce")
    return (
        spot[spot["Type"] == "Argos"]
        .assign(quality=lambda d: d["Quality"].astype(str))
        .loc[lambda d: d["quality"].isin(["1", "2", "3"])]
        .dropna(subset=["time", "Latitude", "Longitude"])
        .rename(columns={"Latitude": "latitude", "Longitude": "longitude"})
        [["time", "latitude", "longitude", "quality"]]
        .sort_values("time").reset_index(drop=True)
    )


def build_reference_model(shark: str) -> xr.Dataset:
    """Assemble the pangeo-fish reference model from this tag's GLORYS subset."""
    thetao = xr.open_dataset(GLORYS_DIR / f"glorys_thetao_{shark}.nc")
    static = xr.open_dataset(GLORYS_DIR / "glorys_static_nepac.nc")
    static_on = static.interp(latitude=thetao["latitude"],
                              longitude=thetao["longitude"], method="nearest")
    model = (
        thetao.rename({"thetao": "TEMP", "zos": "XE",
                       "latitude": "lat", "longitude": "lon"})
        .assign(H0=static_on["deptho"].rename(
            {"latitude": "lat", "longitude": "lon"})
            if "latitude" in static_on["deptho"].dims else static_on["deptho"])
    )
    if "H0" in model and "latitude" in model["H0"].dims:
        model["H0"] = model["H0"].rename({"latitude": "lat", "longitude": "lon"})
    if "depth" in model["XE"].dims:
        model["XE"] = model["XE"].isel(depth=0, drop=True)
    model = model[["TEMP", "XE", "H0"]]
    model = model.assign(
        dynamic_depth=(model["depth"] + model["XE"]).assign_attrs(
            units="m", positive="down"),
        dynamic_bathymetry=(model["H0"] + model["XE"]).assign_attrs(
            units="m", positive="down"),
    )
    lon2d, lat2d = np.meshgrid(model["lon"].values, model["lat"].values)
    model = model.assign_coords(
        latitude=(("lat", "lon"), lat2d),
        longitude=(("lat", "lon"), lon2d),
    )
    if "units" not in model["TEMP"].attrs:
        model["TEMP"].attrs["units"] = "degC"
    return model


# %% [markdown]
# ## Clean every tag
#
# Each tag is processed independently. Failures (missing sensor, unreadable
# archive) are recorded with their exact reason and the loop continues — a
# partial clean is an honest outcome.

# %%
clean_status = {}
for shark, (pat_dep, spot_dep, has_referee) in TAGS.items():
    print(f"=== {shark} (PAT {pat_dep}, referee={has_referee}) ===")
    status = {"pat_deploy_id": pat_dep, "spot_deploy_id": spot_dep,
              "has_referee": has_referee, "cleaned": False, "reason": None}
    try:
        dst = clean_dst(pat_dep)
        if dst is None:
            status["reason"] = (
                "no External Temperature sensor (PAT2 records only internal "
                "'Recorder Temp'); temperature-at-depth-vs-GLORYS emission "
                "invalid")
            print(f"  SKIP: {status['reason']}")
            clean_status[shark] = status
            continue

        row = sharks[sharks["SHARK_ID"] == shark].iloc[0]
        window_days = (pd.to_datetime(row["PAT_END"])
                       - pd.to_datetime(row["DATE_START"])).days

        tag_root = TAGS_DIR / shark
        tag_root.mkdir(parents=True, exist_ok=True)
        dst_out = dst.copy()
        dst_out.index = dst_out.index.tz_localize("UTC")
        dst_out.to_csv(tag_root / "dst.csv")

        events = tagging_events(shark)
        events_out = events.copy()
        events_out["time"] = pd.to_datetime(
            events_out["time"]).dt.tz_localize("UTC")
        events_out.to_csv(tag_root / "tagging_events.csv", index=False)

        (tag_root / "metadata.json").write_text(json.dumps({
            "tag_name": shark, "shark_id": shark,
            "pat_model": row["PAT_MODEL"], "pat_id": row["PAT_ID"],
            "sex": row["SEX"], "tbl_cm": row["TBL_cm"],
            "release_location": row["LOCATION_REL"],
            "window_days": int(window_days),
            "has_referee": has_referee,
        }, indent=2))

        gpe3 = clean_gpe3(pat_dep)
        gpe3.to_csv(CLEAN_DIR / f"gpe3_{shark}.csv", index=False)

        n_argos = 0
        if has_referee and spot_dep is not None:
            argos = clean_argos(spot_dep)
            argos.to_csv(CLEAN_DIR / f"argos_{shark}.csv", index=False)
            n_argos = len(argos)

        ref_path = CLEAN_DIR / f"reference_model_{shark}.nc"
        if ref_path.exists() and ref_path.stat().st_size > 0:
            model = xr.open_dataset(ref_path)
            print(f"  reusing cached reference model {ref_path.name}")
        else:
            model = build_reference_model(shark)
            model.to_netcdf(ref_path)

        status.update({
            "cleaned": True, "window_days": int(window_days),
            "n_dst": int(len(dst)), "n_gpe3_days": int(len(gpe3)),
            "n_argos_class123": int(n_argos),
            "ref_model_dims": dict(model.sizes),
        })
        print(f"  OK: {len(dst)} DST, {len(gpe3)} GPE3 days, "
              f"{n_argos} Argos fixes, model {dict(model.sizes)}")
    except Exception as e:  # noqa: BLE001
        status["reason"] = f"{type(e).__name__}: {e}"
        print(f"  FAILED: {status['reason']}")
    clean_status[shark] = status

# %% [markdown]
# ## Clean-stage status log

# %%
with open(CLEAN_DIR / "clean_status.json", "w") as fh:
    json.dump(clean_status, fh, indent=2, default=str)

ok = [s for s, v in clean_status.items() if v["cleaned"]]
skipped = [s for s, v in clean_status.items() if not v["cleaned"]]
print(f"\nCleaned OK ({len(ok)}): {ok}")
print(f"Skipped/failed ({len(skipped)}): "
      + ", ".join(f"{s} ({clean_status[s]['reason']})" for s in skipped))
