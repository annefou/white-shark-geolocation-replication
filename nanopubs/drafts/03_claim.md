# 03 — FORRT Claim

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

**Form heading:** *"FORRT Claim — Declare an original claim according to FORRT, linking it to an AIDA sentence with a specific FORRT type."*

## Field-by-field draft

### Short URI suffix as claim ID (text input, required)

Slug becomes part of the nanopub URI. Use kebab-case.

```
open-geolocation-reproduces-white-shark-positions
```

### Label of the claim (text input, required)

A descriptive title (not a sentence). Used for searches/discovery.

```
Open temperature-at-depth geolocation reproduces juvenile white shark positions less accurately than the original light-based method
```

### Search for an AIDA sentence (search/select, required)

URI of the AIDA published in step 02. Pull from `nanopubs/PUBLISHED.md`.

> _If the AIDA was published via Nanodash (`w3id.org/np/...` namespace), the platform's search may not find it — paste the URI manually._

```
_pending — search for / paste the step-02 AIDA URI here after publishing it_
```

### Type of FORRT claim (dropdown, required)

Pick one. See `docs/claim-type-vocabulary.md` for the seven options and how to choose.

- [ ] computational performance
- [ ] scalability
- [ ] data quality
- [ ] data governance
- [ ] descriptive pattern
- [x] **model performance**
- [ ] statistical significance

> **Justification (model performance).** The claim is about the *positional accuracy of a geolocation model* evaluated against reference fixes — an evaluation-metric claim (great-circle error to the Argos referee), which is exactly what `model performance` covers (`docs/claim-type-vocabulary.md` § option 6: "accuracy, … evaluation metrics"). It is NOT `descriptive pattern`: no empirical relationship between variables in the world is being asserted (the AIDA is about a method reproducing positions, not about, e.g., temperature correlating with movement). It is NOT `data quality`: the claim is not about preserving fidelity through a preprocessing/transformation step. It is NOT `statistical significance`: there is no significance test as the claim. The model here (the HMM) is the instrument being evaluated, so its accuracy-vs-referee is a model-performance claim.

### Source URI (text input, optional)

Full URL form: `https://doi.org/...` (NOT bare DOI).

```
https://doi.org/10.1038/s41597-022-01235-3
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 03.
