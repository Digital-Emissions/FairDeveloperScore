# Fair Developer Score (FDS) — An Explainable Productivity Metric for Git Repos

> A principled, auditable alternative to “commit-count” metrics.
> FDS quantifies a developer’s impact as **Effort × Build Importance**, using only repository data and robust statistics.

---

## Why this project

Large organizations still lean on simplistic signals (commit counts, raw LOC). Those are easy to game and ignore context. FDS separates **how much a developer contributed** from **how much that work mattered** by first grouping commits into **builds** (logical working units) and then scoring each developer–build pair with transparent math.

---

## Core idea

We first **cluster commits into builds** (the smallest unit of value we measure), then score:

```text
Contribution(u, k) = Effort(u, k) × Importance(k)
FDS(u)             = Σ_k Contribution(u, k)
```

Here `u` is a developer and `k` is a build. A tiny bug-fix build is not equivalent to a cross-module refactor build; the math reflects that.

---

## Data inputs (Git-only)

For each commit:

```
hash, author_name, author_email,
commit_ts_utc, insertions, deletions, files_changed,
dirs_touched (top-level), is_merge, msg_subject
```

Optional but useful:

```
file_paths                  # for “new-file” & key-path detection
dt_prev_author_sec          # recency for Speed
```

---

## Pre-processing

**Noise filtering → effective_churn**
Down-weight or drop vendor/generated files, format-only sweeps, pure renames, mass moves.
`effective_churn = (insertions + deletions) × noise_factor`.

**Clustering commits into builds (torque-like)**
Per author, sort by time. Start a new **build** when:

```
Δt > TIME_GAP_HOURS  (default 2h)
OR
Jaccard(dir_set_curr, dir_set_prev) < JACCARD_MIN  (default 0.30)
```

**Directory co-change graph & PageRank**
Nodes = top-level directories; edge weight `w_ij` = co-change frequency.
Compute PageRank with damping `α = 0.85`; store `C(dir)`.

**Robust standardization (MAD-z)**
For every raw feature (except Share), per **repo × quarter**:

```
z = clip( (x − median) / (1.4826 · MAD), −3, +3 )
```

---

## Effort — per developer `u` in build `k`

```text
Effort(u, k)
 = Share(u, k) · (
   0.25 · Z_scale(u, k) + 0.15 · Z_reach(u, k) + 0.20 · Z_central(u, k)
 + 0.20 · Z_dom(u, k)  + 0.15 · Z_novel(u, k)  + 0.05 · Z_speed(u, k)
 )
```

### Dimension settings (Effort)

* **Share**
  `Share(u, k) = author_effective_churn / build_effective_churn`.
  Range `[0,1]`. If denominator is 0, set Share=0.

* **Scale**
  `raw = log(1 + author_churn_in_build)`; then MAD-z.
  `author_churn_in_build = Σ(insertions + deletions) (after noise)`

* **Reach (directory entropy)**
  `p_i = churn_in_dir_i / total_author_churn`;
  `raw = H = − Σ p_i · log2 p_i` (0 if one directory). Then MAD-z.

* **Centrality**
  `raw = mean( C(dir) )` over dirs the author touched in the build
  (recommended: churn-weighted mean). Then MAD-z.

* **Dominance**
  `raw = 0.3·is_first + 0.3·is_last + 0.4·commit_count_share`; cap to `[0,1]`. Then MAD-z.

* **Novelty**
  `raw = (new_file_lines + key_path_lines) / author_churn`; cap to `≤ 2.0`. Then MAD-z.
  *(key_path_lines = lines in files under “hot” dirs or high-centrality nodes)*

* **Speed** *(optional if recency available)*
  `raw = exp( − hours_since_prev_author_commit / τ_speed_h )`, default `τ_speed_h = 24`; then MAD-z.

---

## Build Importance — per build `k`

```text
Importance(k)
 = 0.30 · Z_scale(k) + 0.20 · Z_scope(k) + 0.15 · Z_central(k)
 + 0.15 · Z_complex(k) + 0.10 · Z_type(k) + 0.10 · Z_release(k)
```

### Dimension settings (Importance)

* **Scale**
  `raw = log(1 + total_churn_k)` where `total_churn_k = Σ effective_churn (all authors)`; MAD-z.

* **Scope**
  `raw = 0.5·files_changed + 0.3·H_dir + 0.2·unique_dirs`, then MAD-z.
  `H_dir` is directory entropy computed over the entire build’s churn distribution.

* **Centrality**
  `raw = mean( C(dir) )` over **all** dirs touched in the build (unweighted or churn-weighted); MAD-z.

* **Complexity**
  `raw = sqrt( unique_dirs × log(1 + total_churn_k) )`; MAD-z.
  (Square-root tempers growth while keeping multi-module × large edits higher.)

* **Type Priority**
  Lightweight message classifier → coefficient; then MAD-z.
  Default mapping:

  ```
  security 1.20, hotfix 1.15, feature 1.10, perf 1.05,
  bugfix 1.00, refactor 0.90, doc 0.60, other 0.80
  ```

* **Release Proximity**
  `raw = exp( − days_to_nearest_tag_or_merge / τ_release_d )`, default `τ_release_d = 30`; MAD-z.
  (Distance to nearest annotated tag or merge-to-main used as a release proxy.)

---

## Final scoring

```
Contribution_{u,k} = Effort_{u,k} × Importance_k
FDS(u)             = Σ_k Contribution_{u,k}     # over chosen window (e.g., quarter)
```

Effort captures **who lifted how much**; Importance captures **how heavy the build actually is**. Using the same yardsticks (scale, centrality) at two levels prevents “free rides” on critical builds and “thankless marathons” on peripheral ones.

---

## Output artifacts

* `build_table.csv` — per build: each Importance component (raw & z) and final `importance`.
* `effort_table.csv` — per developer–build: Share, each Effort component (raw & z), and final `effort`.
* `contribution_table.csv` — per developer–build: `contribution = effort × importance`.
* `fds_table.csv` — per developer: aggregated FDS over the configured time window.

---

## Configuration knobs (defaults)

```text
# Clustering
TIME_GAP_HOURS = 2
JACCARD_MIN    = 0.30

# Centrality
ALPHA_PAGERANK = 0.85

# Decays
TAU_SPEED_H    = 24     # hours
TAU_RELEASE_D  = 30     # days

# Robust stats
MAD_CLIP_LOW   = -3
MAD_CLIP_HIGH  =  3
STATS_WINDOW   = "repo×quarter"

# Effort weights
W_SCALE   = 0.25
W_REACH   = 0.15
W_CENTRAL = 0.20
W_DOM     = 0.20
W_NOVEL   = 0.15
W_SPEED   = 0.05

# Importance weights
A_SCALE   = 0.30
A_SCOPE   = 0.20
A_CENTRAL = 0.15
A_COMPLEX = 0.15
A_TYPE    = 0.10
A_RELEASE = 0.10
```

All thresholds/weights are configurable (YAML/JSON/env). Teams can tune them against internal ground truth (e.g., release notes, hot-fix lists).

---

## Implementation checklist

1. **Extract Git** → CSV/Parquet with required fields.
2. **Noise filter** → compute `effective_churn`.
3. **Cluster into builds** per author (`Δt`, directory Jaccard).
4. **Build co-change graph** and compute PageRank `C(dir)`.
5. **Compute raw features** for Effort (per developer–build) and Importance (per build).
6. **MAD-z standardize** each raw feature (per repo × quarter).
7. **Calculate Effort & Importance**, then **Contribution** and **FDS**.
8. **Export CSVs** and wire into your dashboards.

---

## Design principles

Explainable by construction, hard to game (entropy/centrality/dominance/novelty), context-aware (type & release), robust to outliers (MAD-z), Git-only, and extensible (drop-in signals like test deltas or static-analysis metrics).

---

## License & contributions

Choose a license (e.g., Apache-2.0). Contributions are welcome—new message classifiers, better noise rules, UI integrations, and additional evaluation datasets.

# Fair Developer Score (FDS) — An Explainable Productivity Metric for Git Repos

> A principled, auditable alternative to “commit-count” style metrics.
> FDS quantifies a developer’s impact as **Effort × Batch Importance**, using only repository data and robust statistics.

---

## Why this project

Most large orgs still rely on simplistic signals (commit counts, LOC) that reward noise and penalize deep work. FDS fixes that with a transparent framework that separates **how much a developer contributed** from **how much that work mattered**. The model is resistant to gaming, easy to explain, and ships with reproducible math.

---

## Core idea

We first **cluster commits into batches** (logical working units), then score each developer–batch pair.

```text
Contribution(u, b) = Effort(u, b) × Importance(b)
FDS(u)             = Σ_b Contribution(u, b)
```

Why batching? A tiny bug-fix isn’t equivalent to a cross-module refactor; batches let us weight work by the unit of value creation.

---

## Data inputs (Git-only)

Each commit should provide:

```
hash, author_name, author_email,
commit_ts_utc, insertions, deletions, files_changed,
dirs_touched (top-level), is_merge, msg_subject
```

Optional and useful: file_paths; dt_prev_author_sec.

---

## Pre-processing

- **Noise filtering**: down-weight vendor/generated, format-only, rename-only, and other low-value changes → effective_churn.
- **Batching (torque-like)**: per author, start a new batch when `Δt > 2h` or `Jaccard(dir_sets) < 0.3`.
- **Co-change graph**: build a directory graph from historical co-changes; compute PageRank with α = 0.85.
- **Robust standardization**: per repo × quarter, convert raw metrics to **MAD-z** and clip to [-3, 3].

---

## Effort — per developer u in batch b

```text
Effort_{u,b}
 = Share_{u,b} · (
 0.25 Z^{scale}_{u,b} + 0.15 Z^{reach}_{u,b} + 0.20 Z^{central}_{u,b}
+0.20 Z^{dom}_{u,b} + 0.15 Z^{novel}_{u,b} + 0.05 Z^{speed}_{u,b})
```

**Share**
`author_effective_churn / batch_effective_churn`

**Scale**
`log(1 + author_churn_in_b)`

**Reach (directory entropy)**
`H = − Σ p_i log2 p_i`, where `p_i = churn_in_dir_i / total_author_churn`

**Centrality**
Mean PageRank of directories the author touched in the batch (optionally churn-weighted).

**Dominance**
`0.3·is_first + 0.3·is_last + 0.4·commit_count_share`

**Novelty**
`(new_file_lines + key_path_lines) / author_churn` (capped)

**Speed**
`exp( − hours_since_prev_author_commit / 24 )`

All Effort components use MAD-z values before weighting.

---

## Batch Importance — per batch b

```text
Importance_b
 = 0.30 Z^{scale}_b + 0.20 Z^{scope}_b + 0.15 Z^{central}_b
 + 0.15 Z^{complex}_b + 0.10 Z^{type}_b + 0.10 Z^{release}_b
```

**Scale**
`log(1 + total_churn_b)`

**Scope**
`0.5·files_changed + 0.3·H_dir + 0.2·unique_dirs`, where `H_dir` is entropy over the batch’s directory distribution.

**Centrality**
Mean PageRank of all directories touched by the batch.

**Complexity**
`sqrt(unique_dirs × log(1 + total_churn_b))`

**Type Priority**
Classifier on commit messages → coefficients:
`security 1.20, hotfix 1.15, feature 1.10, perf 1.05, bugfix 1.00, refactor 0.90, doc 0.60, other 0.80`.

**Release Proximity**
`exp( − days_to_nearest_tag / 30 )`

All six are MAD-z standardized before weighting.

---

## “Isn’t scale/centrality counted twice?”

No. We measure two subjects on two scales: the developer’s slice (Effort) and the batch as a whole (Importance). This avoids “free rides” (tiny tweaks on critical batches) and “thankless marathons” (huge edits in peripheral code). Both bundles are MAD-z normalized, so their product remains stable.

---

## Worked example (from our Linux-kernel test)

Effort(u,b) ≈ 0.47 using Share, Scale, Reach, Centrality, Dominance, Novelty, Speed.
Importance(b) ≈ 0.54 from Scale, Scope, Centrality, Complexity, Type, Release.
Contribution(u,b) ≈ 0.47 × 0.54 ≈ 0.26.

Numbers, definitions, and equations match the project notes.

---

## Outputs

The evaluation run emits CSVs ready for dashboards:

- `detailed_evaluation.csv` — per developer-batch metrics, Effort, Importance, Contribution
- `developer_summary.csv` — per developer totals (FDS) and distribution stats
- `batch_summary.csv` — per batch Importance and components

These names may vary by run; the schema follows the fields above.

---

## Quick start

1. Export Git data with the required fields.
2. Run the evaluator on a repo window (quarter or rolling 90 days).
3. Inspect the CSVs and plug into your BI tool.

> In our reference code we use `modules/evaluation/run_evaluation.py` to produce the three CSVs listed above.

---

## Configuration knobs

```text
TIME_GAP_HOURS = 2       # batching
JACCARD_MIN    = 0.30    # batching
alpha_pagerank = 0.85    # centrality
tau_speed_h    = 24      # hours
tau_release_d  = 30      # days
MAD_clip       = [-3, 3] # robust z
# Effort weights:   0.25, 0.15, 0.20, 0.20, 0.15, 0.05
# Importance wts:   0.30, 0.20, 0.15, 0.15, 0.10, 0.10
```

Weights and thresholds can be tuned against internal ground truth (release notes, hotfix lists).

---

## Design principles (what makes this repo different)

- **Explainable**: every score decomposes to concrete lines, directories, timestamps.
- **Hard to game**: entropy, centrality, dominance, and novelty reward useful work, not just LOC.
- **Context-aware**: batch importance bakes in business reality (type, release timing).
- **Robust**: MAD-z standardization resists outliers and seasonality.
- **Git-only**: no private telemetry required; easy to adopt across orgs.
- **Extensible**: slots for test deltas, static-analysis metrics, runtime adoption.

---

## Reference

Full derivations, equations, and worked examples live in the project notes PDF.

---

## License & contributions

License: MIT. See the LICENSE file for details.

Issues and PRs are welcome—especially around new type-classifiers, UI integrations, and benchmark datasets.

---

*If you use this in a paper or blog, please credit the project and link back to the repo.*

# Fair Developer Score (FDS) – Overview

Modern, end-to-end framework and web application for analyzing GitHub repositories and computing Fair Developer Scores (FDS) from commit history. It includes:

- Django web app with a responsive dashboard (Bootstrap 5.3)
- TORQUE-based commit clustering to form logical Builds (formerly “Batches”)
- Developer Effort × Build Importance with robust MAD-Z normalization
- CSV artifact persistence per analysis and one-click download
- Local, scriptable analyzer for offline debugging

See `fds_webapp/README.md` for detailed webapp usage and endpoints.

## Quick Start

1. Create a virtual environment and install dependencies:
   ```bash
   cd fds_webapp
   python -m venv .venv
   . .venv/Scripts/activate  # PowerShell: .venv\\Scripts\\Activate.ps1
   pip install -r requirements.txt
   ```
2. Initialize DB and run the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
3. Open `http://127.0.0.1:8000` and start an analysis with:
   - GitHub repository URL (e.g., `https://github.com/facebook/react`)
   - GitHub personal access token (classic) with `repo` or `public_repo` scope
   - Commit limit (start with 300 for testing)

Artifacts are saved to `fds_webapp/fds_results/analysis_<id>_<owner_repo>/`.

## Disclaimers

- The FDS outputs are for research and educational purposes only and must not be used as the sole basis for HR, hiring, promotion, or compensation decisions.
- Metrics can reflect biases in source data (repository history, review practices) and should be interpreted with context by qualified stakeholders.
- No warranty of completeness or fitness for a particular purpose is provided. Use at your own risk.
- Keep GitHub tokens secret and rotate regularly. For production, store tokens securely and use HTTPS.

## License (MIT)

Copyright (c) 2025 FDS Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# Programmer Productivity Measurement

Created: July 11, 2025 5:21 PM
Labels & Language: CI&CD, GitHub, JIRA, Python
Source: https://github.com/prof-antar/devProductivity/tree/main

# Developer Productivity Evaluation

---

## Part 1 — Torque Clustering, Validation, and Future ML Models

> Is Torque Clustering a machine learning model?
> 

**In short:**

- **Torque Clustering itself:** no traditional training or test set is required.
- **For best results:** still need a *validation* set for parameter tuning, which is conceptually similar to testing.

### 1 Torque Clustering itself: no traditional training/test set

Torque Clustering is neither a supervised nor an unsupervised ML model; it is a **heuristic clustering algorithm**.

**What is a heuristic algorithm?**
It is a clearly defined, rule- and experience-based procedure. Given the same input data and parameters, it always produces exactly the same output. It does not *learn* patterns from data; it simply *executes* the rules you give it.

**The rules of Torque Clustering** are defined by three core parameters:

| Parameter | Meaning | Role |
| --- | --- | --- |
| **α (alpha)** | *Time weight* | Sensitivity to the time gap between commits |
| **β (beta)** | *Lines-of-code weight* | Sensitivity to the size of each code change |
| **gap** | *Torque threshold* | When the computed “torque” (time × code change) exceeds this value, a new batch is started |

Because the algorithm’s behavior is fully determined by these three values, there are no trainable weights or internal state. You don’t need a “training set” to teach it how to cluster.

### 2 Parameter tuning & validation: a de-facto “test”

Although no training is involved, not every parameter combination is good. To find the α, β, gap that best fit certain team or project, you tune them with a **validation set**.

The goal is to make the algorithm’s output batches match human developers’ idea of logical work units (e.g., “fix bug X”, “finish small feature Y”). The steps are:

**Step 1 – Build a ground truth**
Select a representative period (say, a week or a sprint) of commits.
Manually group them—using commit messages, Jira/Trello cards, and PR descriptions—into logical batches. This manual grouping is your **validation set**.

**Step 2 – Grid search**
Define parameter ranges, e.g.:

```
alpha: [0.0001, 0.0003, 0.001]
beta : [0.5, 1.0, 1.5]
gap  : [0.2, 0.3, 0.5]
```

Run Torque Clustering on the validation set for every combination.

**Step 3 – Evaluate clustering quality**
Compare machine-produced batches with your ground truth using standard metrics:

- **Adjusted Rand Index (ARI):** –1 to 1 (1 = perfect match, 0 = random).
- **Normalized Mutual Information (NMI):** 0 to 1 (1 = perfect).
- Homogeneity, Completeness, V-measure, etc.

**Step 4 – Pick the best parameters**
Choose the α, β, gap combination that yields the highest ARI or NMI.
Even without a strict `train_test_split`, creating a validation set and tuning parameters is effectively *testing* which rule set works best.

### 3 Future extensions: introduce training/test sets

Our current pipeline is a data-engineering and analysis flow that generates metrics. Once produced, those metrics become **features** for real ML models—at which point you *do* need training and test sets.

**Example use cases**

| Task | Goal | Features | Label | Process |
| --- | --- | --- | --- | --- |
| **Code-risk prediction** | Predict the probability that a batch introduces a bug | TBS (batch size), commits per batch, number of authors, files modified … | Whether the batch caused a hotfix | Split historical data into train/test, train a classifier (logistic regression, random forest), evaluate accuracy |
| **Cycle-time prediction** | Predict how long a Jira issue will take from start to finish | Issue type, priority, initial TBS … | Actual completion time | Train a regression model |
| **Developer-productivity anomaly detection** | Spot developers/teams with abnormal work patterns (may need help or are overworked) | Weekly TBS, Deploy Freq, CTL, … | — | Train an unsupervised model (e.g., Isolation Forest) on “normal” data, detect anomalies on new data |

## Part 2 — From Clustering to Evaluation on Batch Value

> What is the relationship between **Torque Clustering** and **measuring programmers’ productivity**?
> 

The project’s core objective is to **evaluate developer productivity**, and the very first step toward that goal is to **classify work units** (more precisely, to “cluster” them).

These two goals stand in a **“means vs. end”** relationship: clustering is the means, evaluation is the end.

### A Metaphor

> Imagine you’re evaluating the productivity of an automobile factory.
> 
> - **Individual Git commits** are like scattered **screws, parts, and steel plates** on the shop floor.
> - **Torque Clustering** is the factory’s **automated assembly line** that turns those parts into fully assembled **cars**.
> - **Developer-productivity evaluation** is the factory’s final **performance report**, telling you how many cars are built per day, how good they are, and how long each one takes.

**You can’t judge a factory’s efficiency by counting screws.** You must first **define a meaningful production unit**—**the “car”**—before measurement makes sense.

### 1 Why Not Evaluate Individual Commits Directly?

Judging productivity by individual commits is unreliable and misleading because commit granularity is inconsistent:

- One feature may span ten commits.
- A single commit might only fix a typo (`"fix typo"`).
- A commit could be unfinished work (`"WIP"`).
- A commit might even roll code back.

Tracking “commit count” encourages gaming the system. A developer could split one feature into 50 trivial commits, inflating numbers while polluting history. In summary, a single commit is “raw material,” not a “finished product”; evaluating it directly is meaningless.

### 2 The Role of Torque Clustering: Defining the “Finished Product”

Torque Clustering’s **sole purpose** is to intelligently group scattered commits into **meaningful, complete “logical work units”**—*batches*:

- A batch might be **one complete bug fix**.
- A batch might be **delivery of a small feature**.
- A batch might be **a complex refactor**.

Clustering transforms **“nuts and bolts” into “finished cars.”** It yields a **stable, reliable, meaningful object** for evaluation.

### 3 How Do We Evaluate the “Finished Product”?

After clustering, we can measure batches and derive true productivity indicators:

| Question about the car | Metric in our system | What it measures |
| --- | --- | --- |
| **How big/complex is the car?** | **TBS (Torque Batch Size)** | Code volume per batch |
| **How many cars per day?** | **Deploy Frequency** | Number of batches delivered per day |
| **How long does a car take?** | **CTL (Cycle/Lead Time)** | Time from start to finish for a batch |
| **How many cars need rework?** | **CSI (Change Failure Rate / Rework)** | Post-delivery fixes per batch |

Clustering is the prerequisite for meaningful evaluation: first define *what* to evaluate, then compute metrics to judge *how well* we’re doing. The project aims to shift from measuring **activity** (commit count) to measuring **outcomes** (valuable batches delivered).

## Part 3 — Evaluation on Batch Value: Different Batches, Different Value

**Each batch delivers entirely different “contribution” or “value.”** The system does not assume all batches are equal. Instead, it computes a **multi-dimensional profile** for each one:

### Layer 1 — Current Distinction of Batch Contribution

| Metric | Small-bug batch (example) | Heavy-feature batch (example) | Why it distinguishes |
| --- | --- | --- | --- |
| **TBS** | `15` lines | `800` lines | Directly reflects effort & complexity |
| **Commit count** | `1` | `12` | Features need many commits |
| **Files changed** | `2` | `25` | Features touch more modules |
| **Authors** | `1` | `3` | Complex features often collaborative |
| **Linked Jira issue** | `Bug` | `Story`/`Epic` | Issue type shows nature |
| **Jira story points** | `1` | `8` | Story points quantify value |
| **CTL** | `2 h` | `5 days` | Bug fixes quick, features long |

### Layer 2 — Toward Business Value

A 10-line **critical performance fix** may outweigh a 1,000-line **ordinary UI change**. 

To capture deeper value, add **qualitative** and **business-related** data:

1. **Jira/task fields:** issue type, priority, business-value score, customer impact.
2. **Code-quality & risk metrics:** cyclomatic complexity, coverage, defect density.
3. **Product & business KPIs:** DAU/MAU, conversion rate, performance metrics.

## Part 4 — Fair Developer Score (FDS)

### Mapping the **5 FDS Dimensions** to Real-World Data

| # | Dimension | What it captures | Concrete Metrics (min set) | Data Source & Extraction Notes | Formula / Query Sketch |
| --- | --- | --- | --- | --- | --- |
| 1 | **Throughput** | How much valuable work is shipped | • **Deploy Freq** – distinct successful pipeline runs (prod) per week• **% Batches On-Time** – batches merged before sprint end | - Git/CI: `commits`, `tags`, pipeline status- Sprint board: issue → sprint mapping | `sql SELECT COUNT(*)/weeks AS deploy_freq FROM ci_runs WHERE status='success'` |
| 2 | **Quality** | Defects & rework generated | • **Change Failure Rate** – hot-fix PRs ÷ total batches• **Defect Density** – confirmed bugs ÷ KLoC touched | - Issue tracker (`issue_type='Bug'`, `linked_pr`)- SonarQube coverage API + `git diff --stat` | CFR = `hotfix_batches / total_batches` |
| 3 | **Impact** | Business / technical value delivered | • **Story Points Closed** × Priority weight• **Business Value Score** (if present) | - Jira fields: `story_points`, `priority`, `customfield_business_value` | `Σ(sp * pri_weight)` where pri_weight ∈ {1,1.2,1.5,2} |
| 4 | **Efficiency** | Speed of turning work into shippable code | • **Median Cycle Time (CTL)** – PR open→merge• **Review Latency** – first review comment – PR open | - Git PR API timestamps- Review tool events | CTL = `P50(merge_ts - first_commit_ts)` |
| 5 | **Collaboration** | Healthy team interaction | • **Reviews Given/Received** per developer• **Co-authors per Batch** (git trailers) | - Git review database- `git show --pretty='%an %cN'` for co-authors | reviews_given = `COUNT(review_actions WHERE actor=user)` |

> Time window: rolling last 4 sprints (or 30 days) for all metrics before normalization.
> 
> 
> **Granularity**: compute per-developer records, then feed into the Z-score step described earlier.
> 

### **Fair Developer Score (FDS) — Mathematical Specification**
The **Fair Developer Score (FDS)** quantifies a developer’s contribution across batches of work by combining:

```
FDS = ∑ (Effort × Importance)  over all batches
```

---

### Part 1: Effort — How Much the Developer Pushed

```
Effort(u, b) = Share(u, b) × (
    0.25 × Z_scale +
    0.15 × Z_reach +
    0.20 × Z_centrality +
    0.20 × Z_dominance +
    0.15 × Z_novelty +
    0.05 × Z_speed
)
```

| Metric      | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| **Share**   | Author’s proportion of effective churn in the batch                        |
| **Scale**   | log(1 + churn) – penalizes monster commits                                 |
| **Reach**   | Directory entropy – wider directory spread = higher score                  |
| **Centrality** | PageRank over co-change graph – importance of touched modules          |
| **Dominance** | Credit for starting, ending, and leading the batch                       |
| **Novelty** | Ratio of new lines (e.g., new files/APIs) to churn                         |
| **Speed**   | exp(–hours since previous commit / 24) – favors fast iteration             |

All metrics are **MAD-Z normalized** per repo × quarter and clipped to [−3, +3].

---

### Part 2: Importance — How Valuable the Batch Was

```
Importance(b) = 
    0.30 × Z_scale +
    0.20 × Z_scope +
    0.15 × Z_centrality +
    0.15 × Z_complexity +
    0.10 × Z_type +
    0.10 × Z_release_proximity
```

| Metric             | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Scale**          | log(1 + total churn) – entire batch size                                   |
| **Scope**          | Weighted blend: 0.5×files + 0.3×entropy + 0.2×unique dirs                   |
| **Centrality**     | PageRank score of modules touched in the batch                             |
| **Complexity**     | sqrt(unique_dirs) × log(1 + churn) – coordination overhead                 |
| **Type Priority**  | Importance inferred from commit type (see table below)                     |
| **Release Proximity** | exp(–days to nearest tag / 30) – urgency boost near releases           |

**Type Priority Weights:**

| Type         | Weight |
|--------------|--------|
| `security`   | 1.20   |
| `hotfix`     | 1.15   |
| `feature`    | 1.10   |
| `perf`       | 1.05   |
| `bugfix`     | 1.00   |
| `refactor`   | 0.90   |
| `other`      | 0.80   |
| `docs`       | 0.60   |

---

### Worked Example: Batch #1

**Effort Metrics (user-specific)**

| Metric      | Z-score |
|-------------|---------|
| Scale       | +0.67   |
| Reach       | +0.45   |
| Centrality  | –1.89   |
| Dominance   | 0.00    |
| Novelty     | +0.67   |
| Speed       | 0.00    |

 **Effort ≈ 0.47**

**Importance Metrics (batch-wide)**

| Metric          | Z-score |
|------------------|---------|
| Scale            | +1.28   |
| Scope            | +2.06   |
| Centrality       | –0.77   |
| Complexity       | +0.53   |
| Type Priority    | –0.58   |
| Release Proximity| –0.53   |

 **Importance ≈ 0.54**

**Final Contribution for Batch #1:**

```
Contribution = Effort × Importance ≈ 0.47 × 0.54 ≈ 0.26
```

---

### Standardization Notes

All raw metrics are normalized via:

- **MAD-Z transformation** per repo × quarter
- Clipping to [–3, +3] for outlier resistance
- Ensures fair comparison across diverse developers and teams
