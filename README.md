# Fair Developer Score (FDS) System

A comprehensive framework for measuring programmer effort and build importance in software development projects.

## Overview

The Fair Developer Score (FDS) system provides a quantitative approach to evaluate developer contributions by combining **Effort** and **Importance** metrics:

$$\boxed{\text{FDS}_u = \sum_{b} \text{Effort}_{u,b} \times \text{Importance}_{b}}$$

Where:
- $u$ = developer
- $b$ = build (logical working unit)
- Effort captures *how much* a developer pushed
- Importance captures *how much that push matters*

## Table of Contents

- [Part 1: Programmer Effort](#part-1-programmer-effort)
  - [Build Clustering](#build-clustering)
  - [Effort Formula](#effort-formula)
  - [Effort Components](#effort-components)
- [Part 2: Build Importance](#part-2-build-importance)
  - [Importance Formula](#importance-formula)
  - [Importance Components](#importance-components)
- [Examples](#examples)

---

## Part 1: Programmer Effort

### Build Clustering

**Build = one logical working unit.**

Rationale: A tiny bug-fix ≠ full subsystem refactor → credit must differ.

**Heuristic:** Per author, start a new build when:
```
Δt > 2h ∨ Jaccard(dir_sets) < 0.3
```

### Effort Formula

$$\text{Effort}_{u,b}=\text{Share}_{u,b}\,\big(0.25\,Z^{\text{scale}}+0.15\,Z^{\text{reach}}+0.20\,Z^{\text{central}}+0.20\,Z^{\text{dom}}+0.15\,Z^{\text{novel}}+0.05\,Z^{\text{speed}}\big)$$

### Effort Components

#### 1. Share – Who Owns the Build?

$$\text{Share}_{u,b}=\frac{\operatorname{EC}_{u,b}}{\sum_{v}\operatorname{EC}_{v,b}},\quad \operatorname{EC}:=\text{effective churn}$$


- *Effective churn* = insertions + deletions after noise filtering
- 1.0 ⇒ solo author; 0.25 ⇒ quarter of the work

#### 2. Scale – How Big?

$$\text{Scale} = \log(1 + \text{author churn})$$

Log transform prevents monster commits from dominating.

#### 3. Reach – How Wide?

Directory entropy:

$$H = -\sum_{i} p_i \log_2 p_i, \quad p_i = \frac{c_i}{\sum_j c_j}$$

*Example:* 1,000 lines in one dir → $H = 0$; evenly in three dirs → $H ≈ 1.59$.

#### 4. Centrality – How Core?

1. Build co-change graph $G = (V, E)$
2. PageRank with $\alpha = 0.85$:
   $$\mathbf{p} = \alpha M^{\top}\mathbf{p} + (1-\alpha)\frac{1}{|V|}\mathbf{1}$$
3. Build/developer centrality = mean $p_i$ over touched directories

Edits in hub modules receive higher scores.

#### 5. Dominance – Who Leads?

$$\text{Dom}_{u,b}=0.3\,\mathbf{1}_{\text{first}}+0.3\,\mathbf{1}_{\text{last}}+0.4\,\operatorname{commit\_share}$$

Rewards shepherding a build end-to-end.

#### 6. Novelty – How New?

$$\text{Novelty} = \frac{\text{new-file lines} + \text{key-path lines}}{\text{author churn}}$$

Higher when creating new modules or APIs.

#### 7. Speed – How Fast?

$$\text{Speed} = \exp\left(-\frac{\text{hours since prev commit}}{24}\right)$$

Mild bonus for short feedback loops.

---

## Part 2: Build Importance

### Importance Formula

$$\text{Importance}_b = 
0.30\,Z^{\text{scale}} + 
0.20\,Z^{\text{scope}} + 
0.15\,Z^{\text{central}} + 
0.15\,Z^{\text{complex}} + 
0.10\,Z^{\text{type}} + 
0.10\,Z^{\text{release}}$$

Weights sum to 1 and can be re-tuned per organization.

### Importance Components

#### 1. Scale – How Large?

$$\text{Scale} = \log(1 + \text{total churn}_b)$$

Entire build churn (all authors). Log transform reins in mega-commits.

#### 2. Scope – How Broad?

Weighted blend:

$$0.5\,\text{files} + 0.3\,H_{\text{dir}} + 0.2\,\text{unique dirs}$$

where:

$$H_{\text{dir}} = -\sum_i p_i\log_2 p_i$$

*Example:* 200 files in ten evenly hit dirs ⇒ higher score than 200 files in one dir.

#### 3. Centrality – How Core?

1. Build co-change graph $G = (V, E)$
2. PageRank with $\alpha = 0.85$
3. Mean $p_i$ over **all** dirs in the build

Touching architectural hubs inflates importance.

#### 4. Complexity – How Hard?

$$\text{Complexity} = \sqrt{\text{unique dirs} \cdot \log(1 + \text{total churn})}$$

Large × multi-module edits escalate coordination cost; square-root tames scale.

#### 5. Type Priority – How Urgent?

Classifier on commit messages with coefficients:
- Security: 1.2
- Hot-fix: 1.15
- Feature: 1.10
- Performance: 1.05
- Bug-fix: 1.00
- Refactor: 0.90
- Documentation: 0.60
- Other: 0.80

Higher coefficient ⇒ higher importance.

#### 6. Release Proximity – How Late?

$$\text{Release} = \exp\left(-\frac{\text{days to nearest tag}}{30}\right)$$

Edits landed just before a release receive a large multiplier.

---

## Robust Standardization

For both Effort and Importance metrics:

- Compute median & MAD per **repo × quarter**
- Convert each raw metric to MAD-z, clip to $[-3, 3]$
- Aligns heterogeneous units on an outlier-resistant scale

---

## Examples

### Worked Example: Build #1

#### Effort Calculation

| Metric     |   Raw | MAD-z |
|------------|-------|-------|
| Share      | 1.000 |   —   |
| Scale      |  7.36 | +0.67 |
| Reach      |  1.59 | +0.45 |
| Centrality |  0.16 | -1.89 |
| Dominance  |  1.00 |  0.00 |
| Novelty    |  1.30 | +0.67 |
| Speed      | 0.999 |  0.00 |

$$\text{Effort}_{u,b} \approx 0.47$$

#### Importance Calculation

| Metric        |   Raw | MAD-z |
|---------------|-------|-------|
| Scale         |  7.36 | +1.28 |
| Scope         | 10.08 | +2.06 |
| Centrality    |  0.16 | -0.77 |
| Complexity    |  4.70 | +0.53 |
| Type Priority |  0.80 | -0.58 |
| Release Prox. |  1.00 | -0.53 |

$$\text{Importance}_{1} \approx 0.54$$

#### Final Contribution Score

Combined calculation:

$$\text{Contribution}_{u,b} = 0.47\,(\text{effort}) \times 0.54\,(\text{importance}) \approx 0.26$$

---

## Key Benefits

- **Fairness**: Accounts for both quantity and quality of contributions
- **Context-aware**: Considers project structure and timing
- **Robust**: Uses outlier-resistant standardization
- **Flexible**: Weights can be adjusted per organization
- **Comprehensive**: Captures multiple dimensions of developer impact

## Implementation Notes

This system requires:
- Git repository analysis
- Directory structure mapping
- Commit message classification
- Release tag information
- Co-change graph construction

The metrics provide a foundation for fair developer evaluation, performance reviews, and contribution recognition in software development teams.