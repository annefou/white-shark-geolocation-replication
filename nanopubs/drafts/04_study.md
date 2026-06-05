# 04 — FORRT Replication Study

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> **Verify code first:** read the actual reproduction script in `notebooks/03_analysis.py` before writing the methodology field. See `docs/verify-before-drafting.md`.

## Field-by-field draft

### Short URI suffix for study ID (text input, required)

Slug. Use kebab-case.

```
jws-geolocation-pangeo-fish-replication-study
```

### Label/name of replication study (text input, required)

Human-readable title.

```
Open temperature-at-depth replication of juvenile white shark geolocations using a HEALPix hidden Markov model
```

### Study type (dropdown, required)

- [ ] Reproduction Study — direct reproduction: same methodology, same tools.
- [x] **Replication Study** — replication with different methodology or conditions.
- [ ] Reproduction/Replication Study — both.

> Different methodology: the original geolocations come from the proprietary light-plus-SST GPE3 model; this replication re-derives positions with an independent open temperature-at-depth method. There is no reproduction leg (GPE3 cannot be recomputed). See `00_paper_summary.md` § Replication design choice.

### Search for a FORRT claim (search/select, required)

URI of the Claim published in step 03. Pull from `nanopubs/PUBLISHED.md`.

```
_pending — search for / paste the step-03 FORRT Claim URI here after publishing it_
```

### Describe what part of the claim is reproduced/replicated (textarea, required)

The **scope** of the claim being tested. Which aspect, what's in/out of scope. NOT methodology. NOT results. See `docs/pico-study-outcome-levels.md`.

```
Scope: the daily geolocation product released for the juvenile white sharks in this data descriptor — specifically the computed positions of the recovered pop-up archival (PAT) tags, whose full depth and temperature time-series are available in the archive. In scope: re-deriving those daily positions independently and judging their accuracy against the co-deployed Argos satellite fixes that serve as the referee. Out of scope: the dataset's tag/individual coverage counts (a separate, trivial check, not pursued here); the SPOT-only deployments, which already are direct Argos positions and need no geolocation; the depth records and any downstream ecological inference (migration, habitat) drawn from the tracks in other papers. The released GPE3 tracks are treated as the comparison baseline, not as ground truth.
```

### Describe how the claim is reproduced/replicated (textarea, required)

The **method** in plain prose. Read `notebooks/03_analysis.py` and any config files first. NOT exact numerical results.

```
Input data: the released biologging archive (data DOI https://doi.org/10.24431/rw1k6c3). From the metadata table, the recovered PAT tags carrying a full depth-and-temperature time-series are selected, and each tag's depth/temperature record is read from its per-deployment archive entry.

Reference field: the GLORYS12V1 global ocean physical reanalysis (Copernicus Marine GLOBAL_MULTIYEAR_PHY_001_030), variable thetao (sea-water potential temperature), subset per tag to its deployment time window and a northeast-Pacific bounding box and accessed via the copernicusmarine client.

Geolocation model: the open-source pangeo-fish hidden Markov model. For each timestep an emission likelihood is computed as the agreement between the tag's measured temperature-at-depth profile and the GLORYS thetao field; movement between timesteps is a Brownian-motion transition whose diffusion parameter (a spread in radians on the sphere, bounded by an assumed maximum swim speed) is fitted per tag by maximum likelihood. The state space is a HEALPix grid in NESTED ordering at refinement level 9 (about 6.4 km cells, matched to the GLORYS resolution; project convention is NESTED, never RING). Fitting and decoding use pangeo-fish's low-level EagerEstimator with an EagerBoundsSearch over the diffusion parameter, then the most-probable daily track is decoded. Track endpoints are anchored by the recorded release and pop-up positions.

Validation/referee: for the tags that also carried a SPOT tag, the daily great-circle distance between the re-derived positions and the independent Argos satellite fixes is computed, and the same distance is computed for the released GPE3 track against those same fixes — so the open method and the original method are compared on a common, independent referee. The Argos fixes are the referee; GPE3 is a comparison baseline, not ground truth. Per-tag fitted diffusion and track-vs-GPE3 agreement are also recorded. (Numerical results live in the Replication Outcome, step 05.)
```

### Describe any deviations from original methodology (textarea, optional)

What's different from the original method. Verify against the actual code, don't guess.

```
This is a different-methodology replication, so the whole geolocation engine differs from the original — that difference is the point, not a deviation to apologise for. The deliberate configuration choices and honest exclusions that bound the comparison:

1. Minimal configuration by design. The open method is run with a single emission signal (temperature-at-depth only) and only the release and pop-up endpoints as anchors. It does NOT use the light levels or satellite-SST that the original GPE3 method fuses, nor the acoustic-receiver detections available for many of these sharks, nor multi-variable (temperature-plus-salinity) or bathymetry constraints — all of which pangeo-fish supports. The result is therefore a floor for this bare configuration, not a ceiling for the method.

2. Original method is proprietary and not recomputed. GPE3 (Wildlife Computers, a discretised hidden Markov model fusing light, SST and known endpoints, requiring a user-supplied mean-swim-speed prior) cannot be re-run; its already-released track outputs are used as the comparison baseline.

3. Implementation note. The fit/decode uses pangeo-fish's low-level EagerEstimator + EagerBoundsSearch path rather than the high-level optimize_pdf helper, which trips a pint/xarray incompatibility in the installed version.

4. Two honest exclusions from the analysed tag set. Tag 02_01 (a PAT2 unit) records only internal recorder temperature with no external ambient-water sensor, so the temperature-at-depth emission is invalid and the tag is dropped. Tag 06_10 is dropped because its basin-scale GLORYS reference subset repeatedly failed to download. One further recovered PAT tag has no co-deployed SPOT tag, so it has no Argos referee and contributes only a track-vs-GPE3 comparison, not an accuracy validation.
```

### Search keywords (Wikidata) (multi-select, optional)

Provide labels (not QIDs) — the Wikidata search picks up labels.

- Label 1: `geolocation`
- Label 2: `great white shark` (Carcharodon carcharias)
- Label 3: `biologging`
- Label 4: `hidden Markov model`
- Label 5: `HEALPix`

### Search discipline (Wikidata) (search, optional)

Provide labels.

- Discipline label: `marine biology` (alternatively `movement ecology` if that label resolves in the picker)

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.
