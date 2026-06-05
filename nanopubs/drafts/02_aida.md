# 02 — AIDA Sentence

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

**Form heading:** *"AIDA Sentence — Make structured scientific claims following the AIDA model"*

## Field-by-field draft

### AIDA sentence (textarea, required)

Atomic, Independent, Declarative, Absolute. One empirical finding. Must end with a full stop.

> _If your draft AIDA contains "and" linking two distinct findings, split into two AIDA nanopubs._
>
> **AIDA pre-write checklist (run, all pass):** no numerical values; no method/library names (no pangeo-fish / GLORYS / HEALPix / Brownian / σ); no cryptic identifiers; world-talk not model-talk (states a reproducibility relationship about positions, not "the model finds…"); one empirical finding (no "and" linking two findings); ends with a full stop. The finding is the replication headline (open minimal-config method's positional accuracy vs the Argos referee), worded as geolocation *reproducibility* to stay consistent with the `qualifies` verdict.

```
In juvenile white sharks tracked by archival tags, an open hidden Markov geolocation method that matches tag temperature-at-depth against an ocean reanalysis reproduces the released satellite-tracked positions less accurately than the original proprietary light-based method.
```

### Select related topics/tags (dropdown, optional)

Predefined topic vocabulary — list the labels you intend to pick from the dropdown.

```
This is a fixed predefined vocabulary in the platform UI — pick whichever of these labels actually appear in the dropdown (do not type free text):
- geolocation
- biologging / animal tracking
- reproducibility
- hidden Markov model
- marine ecology
If none match, skip — this field is optional.
```

### Relates to this nanopublication (text input, required)

URI of the nanopub the AIDA derives from.

- For paper-rooted chains: the Quote-with-comment URI (from step 01).
- For question-rooted chains: the PICO or PCC URI (from step 01).

Pull the URI from `nanopubs/PUBLISHED.md`.

```
_pending — paste the step-01 Quote-with-comment URI here after publishing it_
```

### Supported by datasets (repeatable group, optional)

DOIs/URLs of datasets that ground the AIDA claim.

- DOI 1: `https://doi.org/10.24431/rw1k6c3` — the released juvenile white shark biologging archive (the tag records this replication re-geolocates).

### Supported by other publications (repeatable group, optional)

DOIs/URLs of publications that support the AIDA claim — e.g. peer-reviewed methods papers, or the original paper if not already cited via the Quote.

- _(skip — optional. The original paper is already cited via the step-01 Quote; the pangeo-fish method paper is not pinned in this repo, so leave empty rather than guess a DOI.)_

> **Known platform bug (2026-04-26):** if both *Supported by datasets* AND *Supported by other publications* are populated and publishing fails, fall back to publishing this AIDA via Nanodash. The URI namespace becomes `https://w3id.org/np/...` (still valid and citable). Only the datasets field is populated here, so the bug should not trigger.

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 02.
