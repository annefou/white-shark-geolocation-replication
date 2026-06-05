# Paper summary

> This is a working scratchpad for the paper-analysis phase. The output of this file feeds the Quote / AIDA / Claim drafts. It is not itself a nanopub.

**Reference paper:** A biologging database of juvenile white sharks from the northeast Pacific

**DOI:** 10.1038/s41597-022-01235-3

**Authors:** O'Sullivan, J.; Lowe, C. G.; Sosa-Nishizaki, O.; Jorgensen, S. J.; Anderson, J. M.; Farrugia, T. J.; García-Rodríguez, E.; Lyons, K.; McKinzie, M. K.; Oñate-González, E. C.; Weng, K.; White, C. F.; Winkler, C.; Van Houtan, K. S.

**Year:** 2022 (*Scientific Data* 9:142)

**Type:** Data Descriptor (not a hypothesis-testing study).

## Headline claim

Verbatim from the abstract (p. 1, "OPEN / Data Descriptor" abstract block):

> Here we report the full data records from 59 pop-up archival (PAT) and 20 smart position and temperature transmitting (SPOT) tags that variously recorded pressure, temperature, and light-level data, and computed depth and geolocations for 63 individuals.

This is a scope/coverage assertion about the released dataset — the appropriate form of "headline claim" for a data descriptor. The numbers it commits to (59 PAT tags, 20 SPOT tags, 63 individuals, plus computed depth and geolocations) are directly checkable against the released archive, which is what a reproduction tests.

**Alternate candidate** (Background & Summary, p. 2): "Through 2020, the Project deployed 79 electronic tags on 63 juvenile white sharks that have helped document their seasonal migrations and oceanographic preferences, fisheries interactions, nursery locations, ontogenetic shifts, and habitat shifts arising from ocean warming." — More interpretive (lists downstream findings from other papers); less directly reproducible. Not preferred for the Quote step.

## Methodology summary

- **Data sources:** Animal-borne biologging tags on juvenile white sharks (*Carcharodon carcharias*) in the southern California Current / northeast Pacific, Monterey Bay Aquarium Juvenile White Shark Project, 2001–2020. Two platforms: Wildlife Computers SPOT5 (Argos Doppler surface positions, deployed 2006–2009) and PAT pop-up archival tags (models PAT2 2001–2003, PAT4 2004–2005, MK10 2003–2016, MiniPAT 2010–2020), recording wet/dry, light level, pressure, temperature.
- **Geolocation method (the technical core a replication would test):** PAT daily positions from light-level geolocation — dawn/dusk timing vs onboard UTC clock gives longitude; day length vs day-of-year gives latitude. These are then refined by Wildlife Computers' **GPE3**, a proprietary discretized Hidden Markov model that fuses light levels, satellite SST matched to onboard temperature, and known release/pop-up locations. SPOT positions are Argos Doppler-shift fixes with quality classes (Z/B/A/0/1/2/3; errors from <250 m to >10 km). PAT pop-up final location is the first Argos class-1/2/3 fix.
- **Sample sizes:** 79 tags deployed on 63 individuals (64 sharks counted in some figure captions; two ID pairs are the same animal). Of these, 59 PAT and 20 SPOT tags are reported. Successful deployments n = 70 (auto-ingested to ATN DAC); successful transmissions SPOT n = 19, PAT n = 51; recovered archival tags n = 26. 35 of 64 sharks (54.7%) carried multiple tags; PAT on 58 sharks, SPOT on 20, acoustic on 21. Most individuals were neonates/YOY/juveniles (<2.5 m TBL); 33 of 64 (51.6%) female; 50 of 64 (78.1%) deployments <6 months.
- **Headline numerical results a replication can compare against:** the tag/individual counts above (59 PAT, 20 SPOT, 63 individuals, 70 successful deployments); demographic splits (51.6% female, 78.1% <6 months); and the per-deployment geospatial outputs — release lat/lon, PAT/SPOT pop-up lat/lon, and minimum linear travel distance (DIST_KM; two sharks travelled nearly 2,000 km in <200 days). The richest reproducible target is the GPE3 daily geolocation tracks themselves (GPE3-X.csv) and SPOT locations.csv.
- **Statistical model:** none in the descriptor itself beyond a LOWESS smoother on travel-distance-vs-deployment-duration (Fig. 3f). The "model" of interest is GPE3's HMM, which is proprietary and runs on the Wildlife Computers portal.

## Replication design choice

Which of the three FORRT Study Types fits this replication?

- [ ] **Reproduction Study** — direct reproduction: same methodology, same tools.
- [x] **Replication Study** — replication with different methodology or conditions.
- [ ] **Reproduction/Replication Study** — both.

**Decision (user, 2026-06-04, scope corrected): Replication Study (different methodology).** This is a geolocation replication, not a coverage reproduction. There is no meaningful reproduction leg: the paper's geolocation method (GPE3) is proprietary, cannot be recomputed, and its track outputs are already published in the archive. The replication re-derives daily geolocations with an **independent open method** and compares them against the paper's GPE3 tracks, with the Argos SPOT fixes as the accuracy referee.

**Two distinct geolocation methods — do not conflate them:**

- **GPE3 (the paper's method) = light-level + SST, surface-based.** This is the *baseline we compare against*, NOT what we run. Its tracks are already in the archive.
- **pangeo-fish (this replication) = temperature-at-depth + depth time series, matched against a 3-D ocean temperature field.** This is what we build. **The input is the depth + temperature time series — never feed light/SST to pangeo-fish.**

**Replication method (geolocation notebook):**

- **Input subset:** from `JWS_metadata.csv`, select `PAT_RECOVERY == YES` & `DATA_TS == YES` (recovered PAT tags with full time-series). `PAT_DEPLOY_ID` is the per-deployment ZIP filename; read the depth+temperature time-series CSV from inside each `{PAT_DEPLOY_ID}.zip`. **Verify by unzipping ONE recovered-PAT tag first** — confirm the time-series CSV is actually inside; don't assume.
- **Reference field:** GLORYS12V1 `thetao` (Copernicus Marine `GLOBAL_MULTIYEAR_PHY_001_030`), subset per tag's `DATE_START`→`PAT_END` window and a NE-Pacific bounding box, via `copernicusmarine`. GEBCO bathymetry for the state-space land/depth mask.
- **Model:** pangeo-fish HMM with Brownian-motion transition (diffusion σ fit per tag by likelihood); emission likelihood = tag temperature-at-depth vs GLORYS `thetao`. State space on **HEALPix NESTED** (`healpix-geo`, `nest=True` — project convention; do not inherit a lat-lon grid). Endpoints anchored by `LAT_REL`/`LON_REL` (release) and `LAT_END_PAT`/`LON_END_PAT` (pop-up).
- **Validation:** great-circle distance of pangeo-fish daily positions vs the SPOT Argos fixes (referee), reported alongside GPE3-vs-Argos for the same fixes; plus pangeo-fish-vs-GPE3 track agreement and the fitted σ per tag.
- **Outcome verdict space (honest):** `confirm` (comparable-to-GPE3 agreement with Argos) / `partial` (skill correlates with vertical thermal-gradient strength) / `contradicted`. GPE3 is an estimate, not truth — **Argos is the referee; never call GPE3 "ground truth."**

**Caveats to carry into the Study/Outcome drafts:**

- White sharks are regionally endothermic, but the tags record *ambient water* temperature via the external sensor, so temperature-matching against GLORYS is valid — note it explicitly.
- Movement is basin-scale (larger σ) vs pangeo-fish's coastal sea-bass demo.
- GLORYS resolution (~8 km) and tag sensor accuracy (~0.1 °C) bound the achievable error.

**The coverage-count notebook is demoted to a trivial "dataset description" step** (at most), NOT the scientific result. Its Validated/VeryHighConfidence outcome is scientifically vacuous and must NOT be published — it is superseded by the geolocation Outcome.

## Notes for downstream drafts

- This is a **data descriptor**, so the Quote → Claim should be framed as a dataset-scope / coverage assertion, not a hypothesis test. The FORRT Claim type is likely a descriptive/observational claim about dataset composition, not an effect or relationship.
- Two ID pairs (09_11 / 09_11B and 09_09 / 09_09B) are the same individuals — accounts for the 63-vs-64 discrepancy between abstract ("63 individuals") and several figure captions ("64 White Sharks"). Flag this when wording AIDA so the count is unambiguous.
- "59 PAT and 20 SPOT" = 79 tags total, matching "79 electronic tags". But "70 successfully transmitted and/or recovered" is the access-relevant count. Pick one count per AIDA sentence (atomicity) — don't conflate deployed (79) with successful (70).
- Five sharks were held on exhibit (22–198 days) and two penned 6–8 days before release; their early transmissions are not free-ranging. Relevant for any movement/geolocation comparison — exclude or flag.
- GPE3 needs a user-supplied mean swim-speed prior — a deviation point to document in any replication of the geolocation step.
- The descriptor's own GitHub code is visualization-only; do not expect a geolocation pipeline in it.
