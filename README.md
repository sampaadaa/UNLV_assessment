# PhD Technical Assessment: Time Series Forecasting & Computer Vision

UNLV, Dept. of Civil and Environmental Engineering and Construction, Dr. Sohn's Research Lab.

## What to read first

**`documents/Technical_Assessment_Report.pdf`** is the main deliverable: a concise report covering both parts
(methodology, key results, regression tables, quantitative metrics, and qualitative visual analysis). This is
what addresses the assessment's own request for a research summary report.

## Project structure

This is exactly what's in this repository; nothing below is hidden or excluded.

```
.
├── README.md                               <- this file
│
├── documents/
│   ├── Technical_Assessment_Report.pdf     <- main report, read this first
│   └── detailed_explanation/               <- fuller reasoning and decision history, not required reading
│       ├── PART1_PLAN.md                   <- Part 1 roadmap and decision log
│       ├── PART2_PLAN.md                   <- Part 2 roadmap and decision log
│       ├── Part1_Detailed_Report.pdf       <- fuller Part 1 report (findings, limitations, diagnostics)
│       └── Part2_Detailed_Report.pdf       <- fuller Part 2 report (same, for segmentation)
│
└── code/
    ├── README.md                           <- setup and reproduction instructions, read this second
    ├── requirements.txt                    <- exact package versions, tested in a fresh environment
    ├── part1_bikeshare.ipynb               <- Part 1 notebook: EDA, regression, forecasting
    ├── part2_segmentation.ipynb            <- Part 2 notebook: data partitioning, evaluation, visualization
    ├── scripts/
    │   ├── train_primary.py                <- standalone training script, primary split (live-logged)
    │   └── train_loco.py                   <- standalone training script, leave-one-city-out split
    └── artifacts/                          <- trained model checkpoints + per-epoch histories, committed
                                                so Part 2 runs immediately with no GPU or retraining needed
```

**Not included here, since they are large and/or not part of the submission:** the two datasets (see
`code/README.md` for where the assessment brief's own download links say to place them) and the scripts that
generate the three PDFs above (kept only for the author's own local use; not needed to read or run anything).

## Why Part 2 has standalone training scripts

Both notebooks are fully executable end to end. Part 2's model training was moved out of the notebook and into
`code/scripts/` for two reasons: `jupyter nbconvert --execute` gives no visibility into a long-running cell until
the entire notebook finishes, and re-running the notebook while building later sections would otherwise redo
30+ minutes of training each time. The scripts save a checkpoint and history file to `code/artifacts/`, which is
committed to this repo, so the notebook loads those directly without needing to retrain. The full training code
(model, loss, data pipeline) is identical between the scripts and the notebook's own cells; only the "run and
save" step happens outside the notebook.

## Reproducing the results

See **`code/README.md`** for the full setup guide: environment setup, `code/requirements.txt` (curated from the
project's actual imports and verified by installing into a brand-new virtual environment and re-running both
notebooks end to end), dataset placement, and how to run. In short: both notebooks execute correctly from their
own folder (`code/`), which is the default working directory in Jupyter and in `jupyter nbconvert --execute`.
