# Reproducing this submission

## 1. Requirements

- Python 3.11+ (tested on 3.14)
- Optional but recommended: an NVIDIA GPU with CUDA support and 8GB+ VRAM, for Part 2. Without one, Part 2's
  notebook still runs (it loads the already-trained checkpoints in `artifacts/`, it does not retrain by default),
  but retraining from scratch would be very slow on CPU.

## 2. Set up the environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

# PyTorch needs its own CUDA wheel index, not plain PyPI. If you don't have an NVIDIA GPU,
# drop --index-url entirely and pip will install the CPU-only build instead.
pip install torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cu126

pip install -r requirements.txt
```

`requirements.txt` was generated from the exact packages this project imports (not a full environment dump), and
has been verified by installing into a brand-new virtual environment and re-running both notebooks end to end
with zero errors.

## 3. Get the two datasets

Both are named in the assessment brief. Place them here, relative to this `code/` folder:

```
../datasets/bikeshare/hour.csv
../datasets/aerial_imagery/train/images/*.tif
../datasets/aerial_imagery/train/gt/*.tif
```

- **Part 1:** [UCI Bike Sharing dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset). Only
  `hour.csv` is used.
- **Part 2:** [Inria Aerial Image Labeling dataset](https://project.inria.fr/aerialimagelabeling/). Only the
  `train/` folder is needed (the notebook never touches the official `test/` folder, since we build our own
  train/val/test split from the labeled data). The full 180-tile `train/` folder must be present, even though
  only 40 of those tiles are actually used for training, because one cell in the notebook verifies the full
  tile count as a sanity check.

## 4. Run

Open `part1_bikeshare.ipynb` and `part2_segmentation.ipynb` in Jupyter and run all cells, or from the command
line:

```bash
jupyter nbconvert --to notebook --execute --inplace part1_bikeshare.ipynb
jupyter nbconvert --to notebook --execute --inplace part2_segmentation.ipynb
```

Both notebooks resolve their data paths relative to their own file location, so run them from inside `code/`
(or open them directly in Jupyter/JupyterLab, which sets the working directory to the notebook's own folder by
default).

**Expected runtime:** Part 1 runs in a few minutes (all models train inline on CPU-friendly data sizes). Part 2
also runs in a few minutes, because it loads the pretrained checkpoints in `artifacts/` rather than retraining.

## 5. Retraining Part 2 from scratch (optional)

Not required to reproduce the reported results, since the checkpoints are already included. If you want to
verify the training process itself:

```bash
cd scripts
python train_primary.py   # ~35 min on an RTX 4060-class GPU
python train_loco.py      # ~30 min
```

These write new checkpoints to `../artifacts/`, which the notebook will pick up automatically on its next run.
Both scripts print live, timestamped progress per epoch rather than staying silent until the end.
