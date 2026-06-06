# Can an open method reproduce the white shark geolocations of O'Sullivan et al. (2022)?

> A **Replication Study (different methodology)** of [10.1038/s41597-022-01235-3](https://doi.org/10.1038/s41597-022-01235-3) · data archive [10.24431/rw1k6c3](https://doi.org/10.24431/rw1k6c3)

The reference paper released daily geolocations for juvenile white sharks (*Carcharodon carcharias*) computed by **GPE3**, a *proprietary* light-plus-SST hidden Markov model that cannot be re-run from the public data. This study re-derives the positions with a **fully open** method — `pangeo-fish`, a HEALPix-NESTED HMM matching tag *temperature-at-depth* against the GLORYS12V1 ocean reanalysis — and compares both against **Argos SPOT fixes as an independent accuracy referee** (GPE3 is never treated as ground truth).

**Headline result:** in a deliberately *minimal* configuration, the open method is materially less accurate than GPE3 — median **276 km vs 54 km** great-circle error to Argos across four co-deployed tags. The Brownian σ saturates (weak thermal constraint), so the result **qualifies** the *reproducibility* of the released geolocations with open tooling without disputing the paper. This is a baseline with substantial unused headroom (multi-signal fusion, acoustic anchoring, finer assimilative fields).

![Main result: open pangeo-fish vs proprietary GPE3, judged against the Argos referee](figures/main_result.png)

It produces:

- A reproducible computational pipeline (Snakefile + notebooks).
- A FORRT-tagged nanopublication chain on the [Science Live platform](https://platform.sciencelive4all.org), documenting the claim, the replication design, and the outcome with full provenance.
- A Zenodo-archived release (source + container image) with a citable DOI.

## Quick start

```bash
git clone https://github.com/annefou/white-shark-geolocation-replication.git
cd white-shark-geolocation-replication
pixi install
pixi run snakemake --cores 1
```

Or with Docker:

```bash
docker run --rm ghcr.io/annefou/white-shark-geolocation-replication:latest
```

## Structure

- `paper/` — the source paper PDF (drop yours in there).
- `notebooks/` — jupytext `.py` notebooks that drive the pipeline.
- `data/` — downloaded by `notebooks/01_data_download.py`, never committed.
- `nanopubs/` — drafts of the FORRT chain field-by-field, plus the published-URI registry.
- `docs/` — operating manuals (FORRT form fields, chain decision tree, claim-type vocabulary).
- `figures/` — curated figures used in the Jupyter Book.

## Nanopublication chain

The published chain is listed in [`nanopubs/PUBLISHED.md`](nanopubs/PUBLISHED.md). Each step links to its viewer URL on the Science Live platform.

## Citation

If you use this work, please cite both:

- This software: [`CITATION.cff`](CITATION.cff) → DOI [10.5281/zenodo.20569075](https://doi.org/10.5281/zenodo.20569075).
- The original paper: [10.1038/s41597-022-01235-3](https://doi.org/10.1038/s41597-022-01235-3).
