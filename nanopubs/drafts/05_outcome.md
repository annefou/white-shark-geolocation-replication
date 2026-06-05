# 05 — FORRT Replication Outcome

> **Status: filled with real results (2026-06-05), pending user sign-off on the verdict + Phase-5 publishing.** An earlier version recorded a coverage-count *reproduction* outcome (Validated / VeryHighConfidence); that was scientifically vacuous and is **withdrawn** per the 2026-06-04 scope correction. This is a **geolocation Replication Study**. Numbers below were read from `results/summary.csv` + `results/aggregate.json`, produced by the repo notebooks (4 referee tags + 1 PAT-only; 2 honest exclusions).
>
> Two items still need YOUR confirmation before publishing: (1) the **Validation status** — proposed `PartiallySupported`/`qualifies` (rationale in that field); (2) the **Confidence level** — proposed `Moderate`. The Replication Study URI (step 04) is also still blank until that nanopub is published.
>
> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

## Field-by-field draft (geolocation replication)

### Short URI suffix for outcome ID (text input, required)

```
jws-geolocation-pangeo-fish-replication-outcome
```

### Plain-text label for the outcome (text input, required)

```
Replication outcome: pangeo-fish depth-temperature geolocation of juvenile white sharks vs published GPE3 tracks
```

### Search for a FORRT replication study (search/select, required)

URI of the Replication Study published in step 04. Pull from `nanopubs/PUBLISHED.md`.

```
_not yet published — paste the step-04 Replication Study URI here once it exists_
```

### Repository URL (text input, required)

```
https://github.com/annefou/white-shark-geolocation-replication
```

### Completion date (date picker, required)

```
2026-06-05
```

### Validation status (dropdown, required)

Vocabulary (direction of agreement): `Validated` / `PartiallySupported` / `Contradicted` / `Inconclusive` / `NotTested`. Maps to CiTO intention in step 06.

- [ ] Validated → `cito:confirms` — pangeo-fish achieves comparable-to-GPE3 agreement with the Argos referee
- [x] **PartiallySupported → `cito:qualifies`** — *(proposed — confirm before publishing)* the geolocation product is reproducible in principle but an independent open method does NOT match GPE3 accuracy; this **qualifies the reproducibility** of the paper's geolocations, it does not dispute their correctness
- [ ] Contradicted → `cito:disputes` — pangeo-fish positions disagree materially with both Argos and GPE3
- [ ] Inconclusive → `cito:discusses`
- [ ] NotTested → `cito:cites`

> **Verdict rationale (orchestrator recommendation, user to confirm).** Across all four referee tags pangeo-fish is ~3–12× less accurate than GPE3 against the Argos referee (aggregate 276 km vs 54 km). This is NOT `Contradicted`: the paper's GPE3 geolocations are reasonable (54 km median vs Argos) and we are not disputing them. It IS `PartiallySupported`/`qualifies`: an open, transparent depth-temperature method only partially reproduces the published positions, and the gap is mechanistically explained (σ saturation → weak thermal constraint). The referee is the Argos SPOT fix, NOT GPE3.

### Confidence level (dropdown, required)

`VeryHighConfidence` / `HighConfidence` / `Moderate` / `LowConfidence` / `VeryLowConfidence`.

- [ ] VeryHighConfidence
- [ ] HighConfidence
- [x] **Moderate** — *(proposed)* the under-performance is consistent across all 4 referee tags (robust direction), but n is small and from a single region (southern California Current), and 3 of 4 tags hit the σ bound (a configuration limit), so the *magnitude* is method-configuration-dependent.
- [ ] LowConfidence
- [ ] VeryLowConfidence

### Describe the overall conclusion about the original claim (textarea, required)

```
An independent, fully open geolocation method (pangeo-fish: a HEALPix-NESTED hidden Markov model), run here in a deliberately minimal configuration — temperature-at-depth as the only emission signal, matched against the GLORYS12V1 ocean reanalysis, anchored only by the release/pop-up endpoints — does NOT reproduce the accuracy of the paper's proprietary GPE3 (light-plus-SST) geolocations when both are judged against co-deployed Argos SPOT fixes as the referee. (pangeo-fish supports richer multi-signal emissions and known reference-point/acoustic anchoring that this baseline did not use — see limitations; the figure below is a floor for this configuration, not the method's ceiling.) Across four juvenile white sharks carrying both a recovered archival PAT tag and a SPOT tag, the open method's median great-circle error to Argos was 276 km (median of per-tag medians; range 202 to 354 km per tag), versus 54 km for GPE3 (range 30 to 95 km) on the same fixes — roughly three to twelve times larger per tag. The paper's geolocation product is therefore reproducible in principle but not to comparable accuracy with open tooling: the result qualifies the reproducibility of the released geolocations rather than disputing their correctness.
```

### Describe the evidence that supports your conclusion (textarea, required)

```
From results/summary.csv (read directly, not from memory). Tag selection: recovered PAT tags with full time-series (PAT_RECOVERY==YES & DATA_TS==YES). Of 7 candidates, 5 entered the HMM; 2 were excluded honestly — 02_01 (PAT2 records only internal/body-heat temperature, no external ambient sensor, so the emission is invalid) and 06_10 (its basin-scale GLORYS box repeatedly failed to download). Four of the analysed tags have a co-deployed SPOT tag (Argos referee); one (07_01) is PAT-only and compared to GPE3 only.

Referee tags — median great-circle error to Argos (same fixes for both methods):
  tag    n_argos  pangeo-fish vs Argos   GPE3 vs Argos    fitted sigma (rad)
  07_05    68       300.3 km               94.5 km          0.0070  (interior)
  08_01    75       354.5 km               30.4 km          0.0937  (at bound)
  08_02    62       201.8 km               41.3 km          0.0937  (at bound)
  08_09    62       251.1 km               67.0 km          0.0937  (at bound)
  ----------------------------------------------------------------------------
  aggregate (median of per-tag medians): pangeo-fish 275.7 km | GPE3 54.2 km

PAT-only (no referee; NOT an accuracy validation): 07_01 pangeo-fish-vs-GPE3 median offset 169.9 km.

pangeo-fish-vs-GPE3 track-agreement medians on the referee tags: 258.2 / 273.1 / 178.6 / 184.6 km (07_05/08_01/08_02/08_09).

Key diagnostic: the fitted Brownian σ saturated at its upper bound (0.0937 of max 0.0942 rad) for 3 of the 4 referee tags — a signature that the temperature observations were weakly informative, so the model defaulted to maximum diffusion. Only 07_05 fit an interior σ. State space: HEALPix NESTED level 9 (~6.4 km) for every tag (recorded per-tag in summary.csv). Pipeline executed end-to-end via the repo notebooks; numbers verified 2026-06-05.
```

### Describe what limits the conclusions of the study (textarea, optional)

```
Caveats that bound this conclusion:

1. **Validity of temperature-matching.** White sharks are regionally endothermic, but the PAT *external* sensor records ambient water temperature, so matching tag temperature-at-depth against GLORYS thetao is physically valid. (Checked deliberately — not a confound.)

2. **Diagnosed cause of the accuracy gap — weak thermal constraint, not a code error.** For 3 of the 4 referee tags the fitted Brownian σ saturated at its upper bound (≈0.0937 of max 0.0942 rad). σ pinned at the ceiling is diagnostic that the temperature observations carried little positional information, so the posterior defaulted to maximum diffusion. Temperature fields are spatially smooth (many locations share near-identical profiles), giving a flat emission likelihood — the opposite of GPE3's light-based longitude, which is clock-sharp.

3. **Field resolution and habitat bound the achievable skill.** GLORYS12V1 (~8 km, daily-mean) smooths the mesoscale fronts/eddies that carry positional information; the ~0.1 °C tag sensor is *not* the limit, the field is. Movement is basin-scale through the relatively homogeneous offshore California Current, where the vertical thermal gradient — the thing that makes temperature-at-depth informative — is often weak (vs pangeo-fish's coastal sea-bass demo). Leading mechanistic hypothesis: **skill correlates with thermocline strength**.

4. **The referee.** GPE3 is itself an estimate, not truth — only the Argos SPOT fixes serve as the accuracy referee, and only where deployments overlap SPOT coverage (the 3–4 co-deployed tags).

5. **This is a MINIMAL pangeo-fish configuration — a baseline, not the method's ceiling.** The result tests pangeo-fish with a single emission variable (temperature-at-depth), only the two release/pop-up endpoints as anchors, and the GLORYS field — with Argos deliberately held out as the independent referee. pangeo-fish itself supports much more, and none of it was exploited here: (a) **richer multi-signal emissions** — open light-level geolocation (TwGeos/FLightR/SGAT/probGLS), satellite-SST matching (OSTIA/MUR/GHRSST), joint temperature–salinity matching (GLORYS `so`), and bathymetry as a hard exclusion (GEBCO); (b) **known reference-point anchoring along the track, not just endpoints** — including **acoustic-receiver detections** (the MBA project carried acoustic tags on ~21 sharks), which pin position to within ~1 km at known times. So the ≈276 km figure is a floor for this bare configuration, NOT a verdict on pangeo-fish as a method. Caveats on the acoustic route specifically: the detection records are likely **not** in the PAT/SPOT archive used here (they live in a separate acoustic-telemetry network — ATN/OTN / California arrays — and must be joined on shark ID); receivers are dense in the coastal nursery but absent offshore, so acoustics tighten the coastal portions, not the offshore basin-scale excursions where temperature struggles most; and any detection used as an anchor must NOT also be used as a referee (avoid the circularity we avoided with GPE3).

6. **Field/resolution future work.** A natural follow-up that could narrow the gap (a candidate `extends`/`qualifies` chain step): re-run the same HMM with a **finer, eddy-resolving, data-assimilative ocean field** — a regional California Current reanalysis (CCS-ROMS, ~1–4 km, which also covers the older 2001–2009 deployments) or a Destination Earth ocean digital twin for recent-enough tags. Falsifiable prediction: σ comes off its bound and median error drops. Caveats: (i) resolution only helps where thermal structure physically exists but is unresolved, not where the water is genuinely homogeneous; (ii) the field must be high-res AND correctly phased (assimilative) — a sharp-but-misplaced eddy field could add error, so forecast-style twins are not automatically better than GLORYS; (iii) most km-scale products do not reach back to the 2001–2009 windows, so a regional reanalysis may beat a global twin for these specific tags. None of the field improvements remove pangeo-fish's single-signal disadvantage vs GPE3's light+SST+endpoint fusion — which is what caveat 5's multi-signal fusion addresses.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.
