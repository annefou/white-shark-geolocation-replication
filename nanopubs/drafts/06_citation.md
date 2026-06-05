# 06 — CiTO Citation

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

**Description:** *"Declare citations between papers or other works, using Citation Typing Ontology"*

## Field-by-field draft

### Identifier for the citing creative work (text input, required)

URI of the Outcome published in step 05. Pull from `nanopubs/PUBLISHED.md`.

```
_pending — paste the step-05 FORRT Replication Outcome URI here after publishing it_
```

### List citations (repeatable group, required ≥1)

#### Citation 1 — back to the original paper

##### Citation Type (dropdown)

Choose based on the Outcome's validation status:

- Validated → `confirms`
- PartiallySupported → `qualifies`
- Contradicted → `disputes`

For question-rooted chains where there is no original paper to confirm/dispute, use `usesMethodIn` or `citesAsAuthority` for the methodology paper(s).

> **Note:** `replicates` is NOT in the Science Live dropdown (despite existing in upstream CiTO). When citing a notebook/tutorial that was directly reused, use **`credits`** instead.

```
qualifies
```

> **Justification.** The Outcome's validation status is `PartiallySupported`, which maps to `cito:qualifies` (`docs/forrt-form-fields.md` § Citation with CiTO mapping table). We are NOT disputing the paper: the original GPE3 geolocations are reasonable against the Argos referee. We are qualifying the *reproducibility* of the released geolocations — an open, minimal-configuration method only partially reproduces them. So `qualifies`, not `disputes` (would overclaim disagreement) and not `confirms` (the open method did not match GPE3 accuracy).

##### DOI or other URL of the cited work (text input)

```
https://doi.org/10.1038/s41597-022-01235-3
```

#### Additional citations (optional)

If the Outcome cites methods papers, related replications, or upstream tools, add them here.

- _(skip — optional. The single citation above is the FORRT-chain citation from the Outcome to the original paper. The pangeo-fish method and the GLORYS / archive data DOIs are referenced in the Replication Study's methodology field, not re-cited here, to keep this CiTO node atomic.)_

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 06.

This completes the six-step FORRT chain. Optional next layers:

- **Research Software** (`drafts/07_research_software.md`) — if the repo *produces* a reusable software artefact.
- **Research Synthesis** (`drafts/08_synthesis.md`) — if this chain is one of several testing facets of a shared property.
