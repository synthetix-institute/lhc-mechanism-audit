# Can the LHC produce a dangerous black hole?

This repository reconstructs the LHC black-hole safety argument from equations in the scientific literature. The generated article is written for non-specialists: it explains why the question arose, follows the six physical conditions required for danger, defines every displayed variable, shows where the equations come from and compares the result with the independently written CERN Safety Study Group report.

[Read the complete submission packet](paper/lhc_epistack_submission_packet.pdf).
Its first ten pages are a judge-facing explanation; the full fourteen-page
scientific article follows in the same file.

Competition judges can start with the shorter
[judge's guide](paper/lhc_judges_guide.pdf). It follows one source equation
through every intermediate representation and maps the result directly to the
Epistack judging criteria. The [judge route](JUDGES.md) lists the most useful
files and a dependency-free five-minute demo.

The first map in the article shows who wrote, cited and claimed what. The second follows the calculations themselves: production, evaporation, stopping, mass growth, growth time and the compact-star test. Keeping these maps separate makes it possible to distinguish a widely repeated statement from a physically connected derivation.

## Result

A catastrophic outcome requires one consistent derivation through six conditions:

1. a microscopic black hole is produced;
2. it survives Hawking evaporation;
3. it loses enough momentum to remain inside matter;
4. accretion exceeds mass loss;
5. the positive rate integrates to macroscopic growth within the available time;
6. the same mechanism remains compatible with the survival of white dwarfs and neutron stars exposed to cosmic-ray collisions.

The revised extraction recovers equations for every part of this argument. It finds collider-regime equations for production, evaporation, stopping, mass growth and a growth-time calculation. The compact-star condition is supplied by an astrophysical transfer equation. No recovered derivation connects all six conditions under one parameter-consistent set of assumptions. Standard semiclassical objects evaporate; stable or metastable alternatives are constrained by stopping, growth times and compact-star survival.

The independent CERN report follows the same branch order and reaches the same safety conclusion. It was withheld from the equation benchmark. Agreement in physical structure and conclusion provides an external check on the automatically reconstructed argument.

## Evidence

The Hyperion operational archive contains 2.5 million arXiv papers. The public
LHC case build uses two source layers drawn from that larger corpus:

- a broad screen of 500,000 records from the Hyperion arXiv mirror, which retained 492 case-related source records;
- complete source packages for six primary LHC-safety papers, including four papers absent from the screened prefix.

After source overlays, the run contains 496 papers, 708 extracted claims and 729 equation windows. The equation graph retains 728 fingerprinted nodes, 366 source-local transitions and 190 cross-paper structural analogues.

The primary-source regression fixes twelve equations in advance. They cover production cross-sections, parton thresholds, Hawking mass loss, stopping, accretion, competing mass rates, compact-star growth times and astronomical constraints. The current extractor recovers 12 of 12.

## Two graphs

The provenance graph records:

- authorship;
- paper-to-paper citations;
- source-local claims and their claim families.

The mechanism graph records:

- complete equation windows and their source positions;
- operator/substrate fingerprints;
- physical quantities and mechanism roles;
- source-local equation transitions;
- cross-paper structural analogues;
- assignments to the six safety conditions.

These graphs answer different scientific questions. Provenance identifies responsibility and documentary dependence. The mechanism graph tests whether the equations form a physically composable argument.

## Strict equation contracts

`lhc_audit/evidence_contract.py` defines the quantities required by each constructor condition. Formula symbols determine the mechanism role. Source title and local text determine whether the formula is applied to a collider, material or astrophysical regime.

This separation prevents a context sentence from turning a generic formula into evidence. A rapidity cut such as `|y_{gamma gamma}| <= 1`, for example, cannot fill the production condition. A valid production receipt must contain a production threshold or cross-section. A compact-star accretion equation remains a transfer candidate until its density, velocity, capture radius and exposure time are mapped to the collider case.

Branch closure requires:

- a valid equation receipt for every condition;
- compatible output and input quantities between adjacent conditions;
- an equation path in the source graph for each required transition.

## Build the paper from static artifacts

Build the complete competition packet from the committed artifacts:

```bash
bash scripts/build_submission_packet.sh
```

This writes `paper/lhc_epistack_submission_packet.pdf`, with the ten-page core
followed by the fourteen-page article. Set `REBUILD_ARTICLE=1` to regenerate the
article and its figures before assembly.

## Build the full article

The committed static run contains the graph evidence needed to regenerate the constructor, sparse attention, figures, TeX and PDF:

```bash
bash scripts/build_lhc_black_hole_answer.sh
```

The command writes:

- `paper/lhc_black_hole_answer.tex`
- `paper/lhc_black_hole_answer.pdf`
- eight vector PDF figures under `paper/figures/`

## Rebuild the scientific run

With the broad selection and six complete source packages available locally:

```bash
bash scripts/run_full_audit.sh
```

The default pipeline performs nine stages:

1. primary-source equation regression;
2. provenance and equation-window extraction;
3. equation mechanism graph construction;
4. strict physical construction;
5. sparse attention over measured graph edges;
6. provenance-versus-mechanism comparison;
7. joined public knowledge graph construction;
8. source-ordered constructor export;
9. TeX and PDF generation.

Set paths explicitly when the source folders are elsewhere:

```bash
PAPERS_DIR=/path/to/hf_selection/sources \
PRIMARY_SOURCES_DIR=/path/to/full_sources/sources \
KNOWLEDGEPARSER_ROOT=/path/to/KnowledgeParser \
OUT_DIR=/path/to/output \
bash scripts/run_full_audit.sh
```

Set `BUILD_PDF=0` to generate the data artifacts without compiling LaTeX.

## Select and recover source papers

Broad selection:

```bash
python3 -B scripts/select_lhc_literature.py \
  --dataset synthetix-institute/latex-data-pub \
  --out-dir data/hf_lhc_selection_500k \
  --max-docs 500000 \
  --min-score 3 \
  --allow-missing-seeds
```

Fetch the six full primary sources:

```bash
python3 -B scripts/download_arxiv_full_sources.py \
  --out-dir data/arxiv_lhc_full_sources
```

The downloader detects PDF payloads returned by arXiv and extracts their text before equation parsing.

## Tests

```bash
python3 -B -m pytest -q
```

The regression suite checks display-math aliases, long equation systems, citation extraction, strict formula contracts, false production receipts, source-level regime tags, source-local branch closure and edge-based sparse attention.

## Main files

- `lhc_audit/evidence_contract.py`: six typed physical conditions and equation matchers.
- `lhc_audit/physical_constructor.py`: receipt assignment and branch composition.
- `lhc_audit/equation_mechanism.py`: fingerprinted equation graph.
- `lhc_audit/sparse_attention.py`: attention over measured graph transitions.
- `lhc_audit/public_knowledge_graph.py`: joined provenance and mechanism graph.
- `data/lhc_gold_benchmark.json`: twelve prespecified primary-source receipts.
- `scripts/build_lhc_black_hole_answer.py`: vector figures and scientific paper.
- `scripts/run_full_audit.sh`: end-to-end reproducible build.

## Independent reference

J.-P. Blaizot et al., *Study of potentially dangerous events during heavy-ion collisions at the LHC: Report of the LHC Safety Study Group*, CERN-2003-001 (2003): <https://cds.cern.ch/record/613175/files/CERN-2003-001.pdf>
