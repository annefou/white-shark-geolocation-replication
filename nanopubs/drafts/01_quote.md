# 01 — Quote-with-comment (paper-rooted chains)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> If this is a question-rooted chain, use `01_pico.md` or `01_pcc.md` instead — see `docs/chain-decision-tree.md`.
>
> **After choosing the chain shape, delete the two step-1 alternates you aren't using.** Once you've decided this chain is paper-rooted and keep `01_quote.md`, run:
> ```bash
> rm nanopubs/drafts/01_pico.md nanopubs/drafts/01_pcc.md
> ```

**Form heading:** *"Annotate a paper quotation — Annotating a paper quotation with personal interpretation"*

## Field-by-field draft

### Cited DOI (text input)

Format: starts with `10.` — bare DOI, **NOT** `https://doi.org/...` form.

```
10.1038/s41597-022-01235-3
```

### Quote mode (radio button)

- [x] **Quote whole text (less than 500 characters)**
- [ ] Quote start/end *(use this if the quote exceeds 500 chars)*

### Quoted Text (textarea, required)

Verbatim from the paper PDF in `paper/`. Character-for-character. ≤ 500 chars in whole-text mode.

**Source location:** Abstract block (p. 1), under the "OPEN / Data Descriptor" heading. Verified character-for-character against `paper/osullivan-2022.pdf` (pdftotext extraction). Preceding sentence in the abstract: "…tagging juveniles with animal-borne sensors, also known as biologging." Following sentence: "Whether transmitted or from recovered devices, raw data files from successful deployments (n = 70) were auto-ingested…".

```
Here we report the full data records from 59 pop-up archival (PAT) and 20 smart position and temperature transmitting (SPOT) tags that variously recorded pressure, temperature, and light-level data, and computed depth and geolocations for 63 individuals.
```

Character count: 254 / 500.

> **Alternate candidate** (Background & Summary, p. 2) if you prefer the migration/coverage framing: "Through 2020, the Project deployed 79 electronic tags on 63 juvenile white sharks that have helped document their seasonal migrations and oceanographic preferences, fisheries interactions, nursery locations, ontogenetic shifts, and habitat shifts arising from ocean warming." (274 chars). Less preferred — it is more interpretive and leans on findings from other papers. See `00_paper_summary.md`.

### Comment (textarea, required)

Subtitle: *"Our interpretation or explanation of why this quotation is relevant."*

Why this quote matters and what the replication tests. Connect the paper's claim to the work this repo does. Don't repeat the quote.

> **PROPOSED — user to confirm. This is your interpretation, not a fact from the paper; edit freely before publishing.** Length: 478 / 500 chars.

```
This data descriptor states that geolocations were computed for the released tags. Those positions were derived with Wildlife Computers' proprietary GPE3 model, which cannot be independently recomputed. This replication asks whether the released geolocations are reproducible with a fully open method: a HEALPix hidden Markov model matching tag temperature-at-depth to an ocean reanalysis, judged against the independent Argos satellite fixes rather than against GPE3 itself.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 01.
