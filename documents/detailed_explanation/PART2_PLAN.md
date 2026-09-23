# Part 2 Plan: Building Footprint Segmentation

Decision log and roadmap for Part 2 of the UNLV (Dr. Sohn) technical assessment. **Deadline: 2026-09-25** (today: 2026-09-22, ~3 days left, shared with finishing Part 1 report polish).

**Target level: "Tier 2"**, same standard as Part 1: a leakage-safe, well-justified pipeline with honest quantitative + qualitative evaluation, not just a model that runs.

---

## 1. What the task demands

**Input:** Inria Aerial Image Labeling dataset, already downloaded and extracted locally at
`AerialImageDataset/{train,test}` (confirmed below; no further download needed).

**Deliverables (shared with Part 1):**
1. Executable Jupyter notebook, data partitioning, model training, evaluation metric computation, predicted-mask visualization.
2. Research memo (.pdf), reasoning behind spatial partitioning, model/loss choices, quantitative test results, visual error analysis.

**Assessment question, restated as requirements:**
- Design and code **your own train/eval split**, explicitly demonstrating no spatial leakage (no overlapping neighboring patches, no geographic leakage across cities).
- Select and justify a **segmentation architecture**.
- Formulate a **loss function** suited for binary masks, accounting for **class imbalance** and **edge/boundary precision**.
- Choose **evaluation metrics beyond pixel accuracy**.
- Present **quantitative results** on the evaluation set.
- Present a **qualitative visual comparison** (image | ground truth | prediction), showing both successes and failures.

---

## 2. Dataset findings and decisions (verified locally)

| Finding | Detail | Decision |
|---|---|---|
| Already downloaded | Full dataset extracted at `AerialImageDataset/` (26 GB); redundant archives (`NEW2-AerialImageDataset.zip`, `aerialimagelabeling.7z.00{1..5}`, ~36 GB) still present. | Work from the extracted folder. Can delete the archives later to reclaim space, **not done automatically**, flagged for the user to confirm. |
| Structure | `train/images/` (180 tiles), `train/gt/` (180 masks), `test/images/` (180 tiles, **no masks**, confirmed against the official project page: test-set ground truth is not publicly released). | Test set is unusable for supervised training/evaluation. **We split the 180 labeled train tiles ourselves** into our own train/val/test. |
| Cities | Train: austin, chicago, kitsap, tyrol-w, vienna (36 tiles each). Test (unlabeled): bellingham, bloomington, innsbruck, sfo, tyrol-e, entirely different cities, confirming the dataset's own design tests cross-city generalization. | Our own split should do the same in miniature (see §4). |
| Image specs | Verified: images are `(5000, 5000, 3)` uint8 RGB; masks are `(5000, 5000)` uint8 with values **exactly `{0, 255}`**, matches the assessment brief precisely. | No unexpected value cleanup needed; threshold mask at `>0` (or `==255`) to get a boolean building/background map. |
| Class imbalance | Sampled 10 tiles across all 5 cities: building coverage ranges **0.2% (kitsap) to 40.3% (vienna)**, mean ≈ 13.5%. | Confirms the assessment's explicit call-out: plain pixel accuracy would be trivially ~86-95% by predicting all-background on sparse tiles. Loss and metrics must account for this (§6, §7). |
| Per-city heterogeneity | Kitsap (suburban/rural, sparse) vs. Vienna (dense urban) vs. Austin/Chicago (mixed) vs. Tyrol-w (alpine, low density) are visibly different regimes. | Any split must keep all 5 cities represented in train **and** eval, so the model is not evaluated only on regimes unlike its training data, done via a per-city-proportional split (§4). A **separate leave-one-city-out run** directly probes geographic-leakage / cross-city generalization, since the assessment specifically names this failure mode. |
| Compute | Local RTX 4060 Laptop GPU, 8.2 GB VRAM (verified via `torch.cuda`), 24 CPU cores, 31 GB RAM, 507 GB free disk. | Sufficient for patch-based training (§5) with mixed precision; full 5000×5000 tiles cannot be trained on directly (memory), hence patching. |

---

## 3. Scope decision: representative subset

Given the ~3-day window (shared with Part 1 wrap-up) and that a full 180-tile run buys little additional insight for a much longer training/iteration cycle, we use a **representative subset: 8 tiles per city × 5 cities = 40 of the 180 labeled train tiles**, chosen by fixed index (e.g. tile IDs 1–8 per city) for reproducibility. This is disclosed explicitly in the report as a compute/time-driven scope decision, not hidden.

*(If time permits after the core pipeline is validated, this can be scaled up to more tiles per city, the pipeline itself does not hard-code the count.)*

---

## 4. Data partitioning (the core leakage-safety requirement)

### 4.1 Patch extraction, avoids overlap leakage by construction
- Each 5000×5000 tile is cut into a **non-overlapping 9×9 grid of 512×512 patches** (covering the top-left 4608×4608 region; the outer ~392 px border is discarded, not padded, to keep every patch a real, full 512×512 crop).
- **Non-overlapping** means no two patches from the same tile share a single pixel, the classic "overlapping neighboring patches" leakage mode named in the assessment cannot occur, by construction, regardless of how tiles are later assigned to splits.
- 40 tiles × 81 patches/tile = **3,240 patches** total before splitting.

### 4.2 Primary split, tile-disjoint, per-city-proportional
- Split at the **whole-tile level, never the patch level**: all 81 patches from a given tile go to exactly one of train/val/test. This prevents the second leakage mode named in the assessment, two nearly-identical neighboring patches (one on each side of a tile split) landing in different sets.
- Per city (8 tiles): **6 train / 1 val / 1 test** tiles, fixed by index → **30 train / 5 val / 5 test tiles** → **2,430 / 405 / 405 patches**.
- Keeping every city represented in every split (rather than splitting whole cities into train vs. test) isolates the effect of *within-city* generalization to unseen tiles, which is the primary, realistic deployment scenario (predicting on a new tile in a city you have training data for).

### 4.3 Secondary split, leave-one-city-out (explicit geographic-leakage probe)
- Using the same 40 tiles: train on all tiles from **4 cities** (32 tiles, 2,592 patches), evaluate on the **held-out 5th city's** 8 tiles (648 patches). Repeated for at least one held-out city (kitsap, chosen for being the most visually distinct/sparse regime, the hardest generalization test) as a documented, secondary robustness check, not the headline result.
- This directly answers the assessment's "geographic leakage across cities" prompt: it quantifies how much performance *drops* when the model has never seen the target city, vs. the primary split's in-distribution-city number.

### 4.4 Assertions to encode in the notebook
- No tile ID appears in more than one of {train, val, test} within a split.
- No two patches share pixel coordinates from the same tile (true by construction of the non-overlapping grid, assert patch offsets are on the 512-pixel grid with no duplicates).
- Every city appears in every split of the primary partition (assert set of cities per split == all 5).

---

## 5. Model architecture

**U-Net** (Ronneberger et al.) with a **ResNet34 encoder pretrained on ImageNet**, via `segmentation_models_pytorch`.

**Justification:**
- U-Net's encoder-decoder + skip connections preserve the fine spatial detail (roof edges, small structures) that a plain encoder-classifier would lose, directly relevant to the "edge boundary precision" requirement.
- A pretrained ResNet encoder gives useful low/mid-level visual features (edges, textures) from ImageNet transfer learning despite the domain gap (aerial vs. natural images), speeding convergence given our reduced (40-tile) data budget.
- ResNet34 (not a deeper backbone) is a deliberate compute/time trade-off given the 8 GB VRAM budget and 3-day window, enough capacity for this task's regularity of appearance (rooftops, roads) without pushing training time far out.

**Output:** single-channel logit map, `sigmoid` + threshold (0.5 default, revisited via a precision/recall curve in evaluation) → binary building mask.

---

## 6. Loss function

**Combined BCE + Dice loss** (`0.5 * BCEWithLogits + 0.5 * DiceLoss`):
- **Dice** directly optimizes overlap and is inherently robust to the class imbalance found in §2 (a trivial all-background prediction scores Dice ≈ 0, unlike accuracy).
- **BCE** provides a smooth, well-behaved per-pixel gradient early in training when Dice's gradient is weak (near-empty predictions).
- A **boundary-aware term is added as a documented extension** if time permits (e.g., a weighted BCE that up-weights pixels within a small morphological dilation band of the ground-truth boundary) to directly target the "edge boundary precision" requirement; if not implemented, this is stated as a limitation and BCE+Dice's boundary behavior is still assessed via Boundary IoU/F1 in evaluation (§7).

---

## 7. Evaluation metrics

- **IoU (Jaccard index)**, primary metric; matches the Inria challenge's own official metric, enabling a sanity comparison against published baselines.
- **Dice / F1**, secondary overlap metric.
- **Precision, Recall**, to characterize the false-positive/false-negative trade-off explicitly (important given imbalance).
- **Boundary IoU / Boundary F1**, computed on a narrow band around the ground-truth boundary (via morphological dilation/erosion), directly addressing the "edge boundary precision" requirement.
- **Pixel accuracy**, reported once, explicitly labeled as **not meaningful alone** given the 13.5% mean building coverage (a trivial all-background classifier would score ~86%).
- **Per-tile and per-city breakdowns** (not just one aggregate number), mirrors Part 1's per-window analysis; expected to reveal the same kind of structural finding (e.g., sparse Kitsap tiles vs. dense Vienna tiles behaving very differently).

---

## 8. Training setup

- **Augmentation** (`albumentations`, applied to training patches only): horizontal/vertical flip, 90° rotations (safe for top-down aerial imagery, no canonical "up"), brightness/contrast/hue jitter (accounts for lighting/sensor differences across cities). No elastic deformation (would distort real building geometry).
- **Normalization:** ImageNet mean/std (matching the pretrained encoder).
- **Mixed precision (AMP)** to fit comfortably in 8 GB VRAM at a reasonable batch size (target: batch 16 at 512×512).
- **Optimizer:** AdamW with a cosine or plateau LR schedule; **early stopping** on validation IoU.
- **Seeds fixed** for reproducibility (`RANDOM_STATE = 42`, consistent with Part 1).
- Model selection (best checkpoint) by **validation IoU**, never by test-set performance, test set touched once, at the end, exactly as in Part 1's forecasting protocol.

---

## 9. Qualitative analysis

- Grids of **[input patch | ground truth | prediction | error map]** (error map: false positive vs. false negative colored separately), for:
  - Best-performing tiles/patches.
  - Worst-performing tiles/patches.
  - At least one patch from each city, so all 5 regimes are visually represented.
- Discussion of **specific, expected failure modes**: shadows misread as gaps/roads, tightly packed rooftops merging into one blob, large industrial/warehouse roofs under- or over-segmented, and the sparse-Kitsap vs. dense-Vienna contrast identified in §2.

---

## 10. Common pitfalls checklist

**Data / leakage**
- [ ] Patches are non-overlapping (grid-aligned, no shared pixels), asserted, not assumed.
- [ ] Split is by whole tile, never by patch, asserted (no tile ID in two splits).
- [ ] Every city represented in every split of the primary partition, asserted.
- [ ] Leave-one-city-out run kept separate from, not blended into, the headline metrics.
- [ ] Mask values `{0,255}` correctly binarized (`==255`, not divided by 255 twice or thresholded wrong).

**Modeling**
- [ ] Loss handles class imbalance (Dice/BCE combo, not plain BCE or plain accuracy-driving loss).
- [ ] Metrics go beyond pixel accuracy (IoU/Dice/Precision/Recall/Boundary-F1 all reported).
- [ ] Pixel accuracy, if shown, is explicitly caveated given ~13.5% mean positive rate.
- [ ] Model selection uses validation IoU, not test-set performance.
- [ ] Predictions thresholded consistently (document the threshold; consider a P/R curve).

**Compute / reproducibility**
- [ ] Seeds fixed; library versions logged (mirrors Part 1 §0).
- [ ] Subset size (40 tiles) and rationale disclosed in the report, not hidden.
- [ ] Notebook runs top to bottom from a fresh kernel within a reasonable time budget.
- [ ] GPU memory usage sanity-checked (no silent OOM/truncated runs).

**Reporting**
- [ ] Both successes and failures shown qualitatively, not just cherry-picked good patches.
- [ ] Per-city / per-tile breakdown included, not just one aggregate metric.
- [ ] Boundary-precision metric explicitly tied back to the loss-function justification.

---

## 11. Notebook / report structure

1. Setup & reproducibility (seeds, versions, device check)
2. Data loading & verification (image/mask specs, class imbalance, per-city stats)
3. Patch extraction (non-overlapping grid) + partitioning (primary + leave-one-city-out) + leakage assertions
4. Model, loss, and training setup
5. Training run(s), primary split, then leave-one-city-out
6. Quantitative evaluation (aggregate + per-tile/per-city breakdown, both splits)
7. Qualitative visual analysis (successes + failures across cities)
8. Summary of findings, limitations

The PDF memo mirrors this order, condensed: methodology (partitioning + model/loss justification), quantitative results table, a few qualitative figures, limitations, targeting a similarly concise length to the Part 1 memo (~4-6 pages).

---

## 12. Decision log

| Date | Decision |
|---|---|
| 2026-09-22 | Dataset already downloaded/extracted locally at `AerialImageDataset/`; no download needed. Confirmed structure (180 train tiles w/ masks, 180 unlabeled test tiles, 5+5 disjoint cities), image specs (5000×5000×3 uint8 RGB / 5000×5000 uint8 {0,255} masks), and class imbalance (13.5% mean building coverage, range 0.2–40.3% across sampled tiles). |
| 2026-09-22 | Scope: representative subset of 40 of 180 labeled train tiles (8/city), for time/compute reasons, disclosed explicitly. |
| 2026-09-22 | Patches: non-overlapping 512×512 grid (9×9/tile, border discarded), leakage-safe by construction. |
| 2026-09-22 | Primary split: tile-disjoint, per-city-proportional (6/1/1 tiles per city). Secondary split: leave-one-city-out (kitsap held out) as an explicit geographic-leakage probe. |
| 2026-09-22 | Architecture: U-Net + ResNet34 (ImageNet-pretrained) via `segmentation_models_pytorch`. Loss: 0.5×BCE + 0.5×Dice, boundary term as a stretch goal. Metrics: IoU (primary), Dice, Precision/Recall, Boundary IoU/F1, pixel accuracy (caveated). |
| 2026-09-22 | Environment: `torch` 2.14.0+cu126 (CUDA confirmed working on RTX 4060 Laptop, 8.2GB VRAM), `segmentation-models-pytorch` 0.5.0, `albumentations` 2.0.8, `opencv-python-headless`, `tifffile`. |
| 2026-09-22 | `DataLoader(num_workers>0)` fails in this environment: Python defaults to the `forkserver` multiprocessing start method, which cannot pickle notebook-defined classes for worker subprocesses. Fixed with `num_workers=0` everywhere; costless here since `PatchDataset` reads from the in-memory `TILES` dict (no disk I/O per item). |
| 2026-09-22 | Primary-split training (U-Net/ResNet34, 30 epochs, batch 16, no early stop triggered): **best val IoU = 0.791, val Dice = 0.883** (epoch 30), 2140s (35.7 min) wall time. `jupyter nbconvert --execute` gives zero visibility into a long-running training cell until the entire notebook finishes (no streamed output), which cost real time diagnosing "is it stuck?" mid-run. For the leave-one-city-out run, training is moved to a standalone script with unbuffered, timestamped logging to a file (tailable live), and the notebook loads the saved checkpoint/history afterward instead of training inline. |

| 2026-09-22 | End-to-end review against the assessment brief found one literal gap: the loss was BCE+Dice, which accounts for class imbalance but not "edge boundary precision" in the loss formulation itself (only in the evaluation metrics). Added a third loss term, BoundaryDice (Dice restricted to a dilation-minus-erosion band around the ground-truth boundary, k=7, about 3px wide on each side), giving `0.4*BCE + 0.4*Dice + 0.2*BoundaryDice`. Validated the term numerically (near-0 on a perfect prediction, near-1 on an empty prediction, finite and non-NaN on an empty-mask edge case, finite gradients) before wiring it into training. Retrained both the primary and leave-one-city-out models with the updated loss. |

*Append new decisions to this table as they are made.*
