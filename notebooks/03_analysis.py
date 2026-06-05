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
# # 03 — Analysis: pangeo-fish geolocation across all recovered-PAT tags
#
# This is the scientific result of the **Replication Study**. For every cleaned
# recovered-PAT tag we re-derive the daily geolocation track with an independent
# open method — the **pangeo-fish** hidden Markov model — and compare it against:
#
# - the published **GPE3** baseline (the paper's method: light + SST), and
# - **for the four tags with a co-deployed SPOT tag**, the SPOT **Argos fixes**
#   (the accuracy referee). The three PAT-only tags have no referee, so only the
#   pangeo-fish-vs-GPE3 track agreement is reported for them — and GPE3 is itself
#   an estimate, so that is weaker evidence, **not** an accuracy validation.
#
# **Method (identical to the proven single-tag run).** A Brownian-motion
# transition model on a HEALPix (NESTED) state space; the emission likelihood at
# each timestep is the agreement between the tag's temperature-at-depth profile
# and the GLORYS12V1 `thetao` 3-D field. The diffusion σ (in radians on the
# sphere) is fit per tag by maximum likelihood, driving the low-level
# `EagerEstimator` + `EagerBoundsSearch` directly (the high-level `optimize_pdf`
# helper trips a pint/xarray incompatibility in this version — we keep the proven
# low-level path). Endpoints are anchored by release and pop-up positions.
#
# **Per-tag robustness.** Each tag runs in a `try/except`; a tag that fails
# (GLORYS gap, σ-fit error, HMM non-convergence) is recorded with its exact error
# and the loop continues. A partial run is an honest outcome; a fabricated one is
# not.

# %%
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pint
import xarray as xr

from pangeo_fish.helpers import (
    compute_diff,
    compute_emission_pdf,
    load_tag,
    normalize_pdf,
    regrid_dataset,
    to_healpix,
)
from pangeo_fish.hmm.estimator import EagerEstimator
from pangeo_fish.hmm.optimize import EagerBoundsSearch
from pangeo_fish.hmm.prediction import Gaussian1DHealpix
from tlz.functoolz import curry

warnings.filterwarnings("ignore", category=RuntimeWarning)

# %%
CLEAN_DIR = Path("../data/clean")
RESULTS_DIR = Path("../results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
TAG_ROOT = str((CLEAN_DIR / "tags").resolve())

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

# HEALPix refinement level for the state space. Level 9 ~ 6.4 km cells (near the
# GLORYS 0.083deg ~ 8 km resolution); NESTED ordering is the project default.
# All seven deployments are short windows (41-180 days), so level 9 is feasible
# for every tag. A per-tag override could drop a long/slow tag to level 8 here.
DEFAULT_HEALPIX_LEVEL = 9
HEALPIX_LEVEL_OVERRIDE: dict[str, int] = {}

# Emission-likelihood spread (degC): tag/GLORYS temperature-match uncertainty.
DIFFERENCES_STD = 0.75
INITIAL_STD = 1e-3
RECAPTURE_STD = 1e-3
RELATIVE_DEPTH_THRESHOLD = 0.8
MAX_SPEED = pint.Quantity(5.0, "km/h")
EARTH_RADIUS = pint.Quantity(6371.0, "km")
ADJUSTMENT_FACTOR = 5.0
TRUNCATE = 4.0
TOLERANCE = 1e-3

# Which tags were successfully cleaned in notebook 02.
clean_status = json.loads((CLEAN_DIR / "clean_status.json").read_text())


# %% [markdown]
# ## Great-circle distance helper

# %%
def gc_km(lon1, lat1, lon2, lat2):
    """Great-circle distance (km) via the haversine formula."""
    r = 6371.0088
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    d = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * r * np.arcsin(np.sqrt(d))


def daily_lookup(track: pd.DataFrame) -> pd.DataFrame:
    t = track.copy()
    t["day"] = pd.to_datetime(t["time"]).dt.floor("D")
    return t.groupby("day")[["longitude", "latitude"]].mean()


# %% [markdown]
# ## Per-tag pangeo-fish run
#
# Returns the daily track and the fitted σ. Raises on any pipeline failure so the
# caller can record the error and continue with the next tag.

# %%
def run_pangeo_fish(shark: str, level: int) -> tuple[pd.DataFrame, float, float]:
    tag, tag_log, time_slice = load_tag(tag_root=TAG_ROOT, tag_name=shark)

    reference_model = (
        xr.open_dataset(CLEAN_DIR / f"reference_model_{shark}.nc")
        .chunk({"time": 24, "lat": -1, "lon": -1, "depth": -1})
        .sel(time=time_slice)
    )

    diff, _ = compute_diff(
        reference_model=reference_model, tag_log=tag_log,
        relative_depth_threshold=RELATIVE_DEPTH_THRESHOLD, chunk_time=24)
    diff = diff.compute()

    diff = diff.assign(
        latitude=reference_model["latitude"],
        longitude=reference_model["longitude"],
    ).swap_dims({"lat": "yi", "lon": "xi"}).drop_vars(["lat", "lon"])
    diff = diff.compute()

    regridded, _ = regrid_dataset(ds=diff, refinement_level=level,
                                  dims=["cells"])
    regridded["cell_ids"].attrs.setdefault("grid_name", "healpix")
    regridded["cell_ids"].attrs["level"] = level
    regridded["cell_ids"].attrs["indexing_scheme"] = "nested"

    emission, _ = compute_emission_pdf(
        diff_ds=regridded, events_ds=tag["tagging_events"].ds,
        differences_std=DIFFERENCES_STD, initial_std=INITIAL_STD,
        recapture_std=RECAPTURE_STD, dims=["cells"])
    normalized, _ = normalize_pdf(ds=emission, chunks={"time": 24})
    normalized = normalized.compute()
    normalized["cell_ids"].attrs.setdefault("grid_name", "healpix")
    normalized["cell_ids"].attrs["level"] = level
    normalized["cell_ids"].attrs["indexing_scheme"] = "nested"

    emission_hp = to_healpix(normalized)

    times = emission_hp["time"].values
    dt_h = float(np.median(np.diff(times)) / np.timedelta64(1, "h"))
    max_sigma = (MAX_SPEED.to("km/h").magnitude * dt_h * ADJUSTMENT_FACTOR
                 / EARTH_RADIUS.to("km").magnitude)

    predictor_factory = curry(
        Gaussian1DHealpix,
        cell_ids=emission_hp["cell_ids"].data,
        grid_info=emission_hp.dggs.grid_info,
        truncate=TRUNCATE, weights_threshold=1e-8,
        pad_kwargs={"mode": "constant", "constant_value": 0},
        optimize_convolution=True,
    )
    estimator = EagerEstimator(sigma=None, predictor_factory=predictor_factory)
    optimizer = EagerBoundsSearch(
        estimator, (1e-4, max_sigma),
        optimizer_kwargs={"xtol": TOLERANCE})
    optimized = optimizer.fit(emission_hp)
    sigma = float(optimized.sigma)

    states = optimized.predict_proba(emission_hp)
    states = states.to_dataset() if not hasattr(states, "data_vars") else states
    trajectories = optimized.decode(
        emission_hp, states.fillna(0), mode=["mean", "mode"],
        progress=False, additional_quantities=["speed", "distance"])

    mean_traj = next(t for t in trajectories.trajectories if t.id == "mean")
    pf_df = mean_traj.df.copy().reset_index().rename(columns={"index": "time"})
    if "time" not in pf_df.columns:
        pf_df["time"] = mean_traj.df.index
    if hasattr(mean_traj.df, "geometry"):
        pf_df["longitude"] = mean_traj.df.geometry.x.values
        pf_df["latitude"] = mean_traj.df.geometry.y.values
    pf_track = (
        pf_df[["time", "longitude", "latitude"]]
        .assign(time=lambda d: pd.to_datetime(d["time"]).dt.tz_localize(None))
        .set_index("time").resample("1D").mean().dropna().reset_index()
    )
    return pf_track, sigma, max_sigma


# %% [markdown]
# ## Run every cleaned tag

# %%
records = []
for shark, (pat_dep, spot_dep, has_referee) in TAGS.items():
    print(f"\n=== {shark} (referee={has_referee}) ===")
    # Resumable: an already-computed tag is cached as results/rec_<tag>.json
    # (the HMM is expensive and the run can be interrupted, e.g. laptop sleep).
    # Reuse a prior successful result instead of recomputing; delete the json to
    # force a recompute.
    cache_path = RESULTS_DIR / f"rec_{shark}.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text())
        if cached.get("status") == "ok":
            print(f"  CACHED — reusing prior result "
                  f"(pf-vs-Argos={cached.get('pf_vs_argos_median_km')})")
            records.append(cached)
            continue
    level = HEALPIX_LEVEL_OVERRIDE.get(shark, DEFAULT_HEALPIX_LEVEL)
    rec = {
        "tag": shark, "has_referee": has_referee,
        "healpix_level": level, "status": "pending",
        "deploy_days": clean_status.get(shark, {}).get("window_days"),
        "n_argos_fixes": clean_status.get(shark, {}).get("n_argos_class123"),
        "fitted_sigma_rad": np.nan,
        "pf_vs_argos_median_km": np.nan,
        "gpe3_vs_argos_median_km": np.nan,
        "pf_vs_gpe3_median_km": np.nan,
        "error": None,
    }

    if not clean_status.get(shark, {}).get("cleaned", False):
        rec["status"] = "skipped_clean"
        rec["error"] = clean_status.get(shark, {}).get("reason", "not cleaned")
        print(f"  SKIP (clean stage): {rec['error']}")
        records.append(rec)
        continue

    try:
        pf_track, sigma, max_sigma = run_pangeo_fish(shark, level)
        pf_track.to_csv(RESULTS_DIR / f"pangeo_fish_track_{shark}.csv",
                        index=False)
        rec["fitted_sigma_rad"] = sigma
        print(f"  fitted sigma = {sigma:.5g} rad (max {max_sigma:.4g}); "
              f"{len(pf_track)} daily positions")

        gpe3 = pd.read_csv(CLEAN_DIR / f"gpe3_{shark}.csv", parse_dates=["time"])
        pf_daily = daily_lookup(pf_track)
        gpe3_daily = daily_lookup(gpe3)

        # pangeo-fish vs GPE3 track agreement (computed for every tag).
        common = pf_daily.index.intersection(gpe3_daily.index)
        if len(common):
            pf_gpe3 = gc_km(
                pf_daily.loc[common, "longitude"].values,
                pf_daily.loc[common, "latitude"].values,
                gpe3_daily.loc[common, "longitude"].values,
                gpe3_daily.loc[common, "latitude"].values)
            rec["pf_vs_gpe3_median_km"] = float(np.median(pf_gpe3))

        # Referee comparison (Argos) only for tags with a co-deployed SPOT.
        if has_referee:
            argos = pd.read_csv(CLEAN_DIR / f"argos_{shark}.csv",
                                parse_dates=["time"])
            argos["day"] = argos["time"].dt.floor("D")
            rows = []
            for _, fix in argos.iterrows():
                day = fix["day"]
                r = {"time": fix["time"], "quality": fix["quality"]}
                if day in pf_daily.index:
                    r["pf_err_km"] = gc_km(
                        fix["longitude"], fix["latitude"],
                        pf_daily.loc[day, "longitude"],
                        pf_daily.loc[day, "latitude"])
                if day in gpe3_daily.index:
                    r["gpe3_err_km"] = gc_km(
                        fix["longitude"], fix["latitude"],
                        gpe3_daily.loc[day, "longitude"],
                        gpe3_daily.loc[day, "latitude"])
                rows.append(r)
            errors = pd.DataFrame(rows)
            errors.to_csv(RESULTS_DIR / f"validation_errors_{shark}.csv",
                          index=False)
            if "pf_err_km" in errors:
                rec["pf_vs_argos_median_km"] = float(
                    errors["pf_err_km"].median())
            if "gpe3_err_km" in errors:
                rec["gpe3_vs_argos_median_km"] = float(
                    errors["gpe3_err_km"].median())
            print(f"  pf-vs-Argos median  = "
                  f"{rec['pf_vs_argos_median_km']:.1f} km")
            print(f"  GPE3-vs-Argos median = "
                  f"{rec['gpe3_vs_argos_median_km']:.1f} km")
        print(f"  pf-vs-GPE3 median   = {rec['pf_vs_gpe3_median_km']:.1f} km")
        rec["status"] = "ok"
    except Exception as e:  # noqa: BLE001
        rec["status"] = "failed"
        rec["error"] = f"{type(e).__name__}: {e}"
        print(f"  FAILED: {rec['error']}")

    records.append(rec)
    if rec["status"] == "ok":
        (RESULTS_DIR / f"rec_{shark}.json").write_text(json.dumps(rec))

# %% [markdown]
# ## Aggregate into results/summary.csv
#
# One row per tag; plus a top-level aggregate (median-of-medians across the four
# referee tags) for pangeo-fish-vs-Argos and GPE3-vs-Argos.

# %%
summary = pd.DataFrame(records)[[
    "tag", "deploy_days", "has_referee", "n_argos_fixes", "healpix_level",
    "fitted_sigma_rad", "pf_vs_argos_median_km", "gpe3_vs_argos_median_km",
    "pf_vs_gpe3_median_km", "status", "error",
]]
summary.to_csv(RESULTS_DIR / "summary.csv", index=False)

referee_ok = summary[(summary["has_referee"]) & (summary["status"] == "ok")]
agg = {
    "n_tags_total": int(len(summary)),
    "n_tags_ok": int((summary["status"] == "ok").sum()),
    "n_referee_tags_ok": int(len(referee_ok)),
    "pf_vs_argos_median_of_medians_km": (
        float(referee_ok["pf_vs_argos_median_km"].median())
        if len(referee_ok) else None),
    "gpe3_vs_argos_median_of_medians_km": (
        float(referee_ok["gpe3_vs_argos_median_km"].median())
        if len(referee_ok) else None),
}
with open(RESULTS_DIR / "aggregate.json", "w") as fh:
    json.dump(agg, fh, indent=2)

print("\n========== SUMMARY ==========")
print(summary.to_string(index=False))
print("\n========== AGGREGATE (referee tags) ==========")
print(json.dumps(agg, indent=2))
