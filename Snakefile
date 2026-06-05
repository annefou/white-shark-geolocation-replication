# Snakefile — orchestrates the cross-tag geolocation replication end-to-end.
#
# One rule per pipeline stage; each rule wraps a jupytext notebook so the
# notebook stays the source of truth and the Snakefile just sequences them.
# The notebooks loop internally over all seven recovered-PAT tags, so the rules
# here express the per-tag inputs/outputs as expanded file lists.
#
# Usage:
#   snakemake --cores 1                  # run everything (all 7 tags)
#   snakemake --cores 1 -n               # dry run
#
# Scope: seven recovered-PAT tags. Four have a co-deployed SPOT tag (Argos
# referee): 07_05, 08_01, 08_02, 08_09. Three are PAT-only: 02_01, 06_10, 07_01.
# A tag that fails at the clean or analysis stage is recorded in summary.csv with
# its error and the run continues — the pipeline still completes.

NOTEBOOKS = "notebooks"
DATA = "data"
RESULTS = "results"
FIGURES = "figures"

# shark_id -> (PAT_DEPLOY_ID, SPOT_DEPLOY_ID or None)
TAGS = {
    "07_05": ("07_05-66885", "07_05-77272"),
    "08_01": ("08_01-40561", "08_01-77274"),
    "08_02": ("08_02-55716", "08_02-77273"),
    "08_09": ("08_09-83066", "08_09-83076"),
    "02_01": ("02_01-18616", None),
    "06_10": ("06_10-40564", None),
    "07_01": ("07_01-64272", None),
}

PAT_ZIPS = [f"{DATA}/raw/tag_packages/{pat}.zip" for pat, _ in TAGS.values()]
SPOT_ZIPS = [f"{DATA}/raw/tag_packages/{spot}.zip"
             for _, spot in TAGS.values() if spot]

# Per-tag GLORYS `thetao` subsets (`glorys_thetao_<tag>.nc`) are deliberately NOT
# declared rule outputs: a basin-scale roamer (06_10) can legitimately time out and
# be dropped (best-effort), and a rule whose declared output is never produced would
# fail the whole DAG. Instead the download stage writes `sources.json` as its
# completion sentinel (it records per_tag_download_status), and notebooks 02/03
# handle any missing tag per-tag via try/except. The four Argos-referee headline
# tags always download.


rule all:
    input:
        f"{FIGURES}/main_result.png",
        f"{RESULTS}/summary.csv",


# ---------- 01: Data download ----------
# Self-contained: fetches the biologging archive (DOI 10.24431/rw1k6c3) via the
# DataONE REST API, every tag's PAT + co-deployed SPOT ZIP, and a per-tag
# GLORYS12V1 reference subset via Copernicus Marine. Needs ~/.copernicusmarine
# credentials for the GLORYS step. All downloads are cached.
rule data_download:
    output:
        f"{DATA}/raw/JWS_metadata.csv",
        f"{DATA}/raw/package_manifest.csv",
        f"{DATA}/raw/sources.json",
        f"{DATA}/raw/glorys/glorys_static_nepac.nc",
        *PAT_ZIPS,
        *SPOT_ZIPS,
    log:
        f"{RESULTS}/logs/01_data_download.log",
    shell:
        "mkdir -p {RESULTS}/logs && cd {NOTEBOOKS} && "
        "jupytext --to notebook --execute 01_data_download.py 2>&1 | tee ../{log}"


# ---------- 02: Data clean ----------
# Extracts each tag's depth+temperature series into the pangeo-fish layout, the
# GPE3 baseline, the Argos referee (referee tags only), and a per-tag GLORYS
# reference model. Writes clean_status.json recording which tags were cleaned.
rule data_clean:
    input:
        f"{DATA}/raw/JWS_metadata.csv",
        f"{DATA}/raw/sources.json",
        f"{DATA}/raw/glorys/glorys_static_nepac.nc",
        *PAT_ZIPS,
        *SPOT_ZIPS,
    output:
        f"{DATA}/clean/clean_status.json",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 02_data_clean.py"


# ---------- 03: Analysis (pangeo-fish HMM geolocation, all tags) ----------
# Runs the HMM per tag (try/except per tag), computes pangeo-fish-vs-Argos and
# GPE3-vs-Argos (referee tags) and pangeo-fish-vs-GPE3 (all tags), and aggregates
# into summary.csv + aggregate.json.
rule analysis:
    input:
        f"{DATA}/clean/clean_status.json",
    output:
        f"{RESULTS}/summary.csv",
        f"{RESULTS}/aggregate.json",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 03_analysis.py"


# ---------- 04: Figures ----------
rule figures:
    input:
        f"{RESULTS}/summary.csv",
        f"{RESULTS}/aggregate.json",
    output:
        f"{FIGURES}/main_result.png",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 04_figures.py"
