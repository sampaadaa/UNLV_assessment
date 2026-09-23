"""Standalone primary-split training script (run out-of-notebook for live, tailable logging).

Mirrors scripts/train_loco.py but for the primary (tile-disjoint, per-city-proportional) split.
Saves the best checkpoint + per-epoch history so the notebook can load results back in without
retraining every time it is re-executed. See PART2_PLAN.md for the design rationale.
"""
import time, random, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import segmentation_models_pytorch as smp
import albumentations as A
from albumentations.pytorch import ToTensorV2

warnings.filterwarnings("ignore")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


RANDOM_STATE = 42
random.seed(RANDOM_STATE); np.random.seed(RANDOM_STATE)
torch.manual_seed(RANDOM_STATE); torch.cuda.manual_seed_all(RANDOM_STATE)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CODE_DIR = Path(__file__).resolve().parent.parent    # code/ (this script lives at code/scripts/)
PROJECT_ROOT = CODE_DIR.parent                        # project root
DATA_ROOT = PROJECT_ROOT / "datasets" / "aerial_imagery"
ARTIFACTS = CODE_DIR / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

TRAIN_CITIES = ["austin", "chicago", "kitsap", "tyrol-w", "vienna"]
SUBSET_IDS = list(range(1, 9))
SELECTED_TILES = [(city, tid) for city in TRAIN_CITIES for tid in SUBSET_IDS]
PATCH, GRID = 512, 9
OFFSETS = list(range(0, GRID * PATCH, PATCH))
TRAIN_IDS, VAL_IDS, TEST_IDS = SUBSET_IDS[:6], SUBSET_IDS[6:7], SUBSET_IDS[7:8]

log(f"device={DEVICE} {torch.cuda.get_device_name(0) if DEVICE.type=='cuda' else ''}")

IMG_DIR, GT_DIR = DATA_ROOT / "train" / "images", DATA_ROOT / "train" / "gt"
t0 = time.time()
TILES = {}
for city, tid in SELECTED_TILES:
    name = f"{city}{tid}"
    img = tifffile.imread(IMG_DIR / f"{name}.tif")
    mask = (tifffile.imread(GT_DIR / f"{name}.tif") == 255).astype(np.uint8)
    TILES[(city, tid)] = {"img": img, "mask": mask}
log(f"preloaded {len(TILES)} tiles in {time.time()-t0:.1f}s")

patch_index = pd.DataFrame([
    {"city": city, "tile_id": tid, "row": row, "col": col}
    for city, tid in SELECTED_TILES for row in OFFSETS for col in OFFSETS
])

def assign_split(tid):
    if tid in TRAIN_IDS: return "train"
    if tid in VAL_IDS: return "val"
    return "test"

patch_index["split"] = patch_index["tile_id"].map(assign_split)
log(f"primary split counts: {patch_index.groupby('split').size().to_dict()}")

IMAGENET_MEAN, IMAGENET_STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
train_tf = A.Compose([
    A.HorizontalFlip(p=0.5), A.VerticalFlip(p=0.5), A.RandomRotate90(p=0.5),
    A.RandomBrightnessContrast(p=0.3), A.HueSaturationValue(p=0.2),
    A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD), ToTensorV2(),
])
eval_tf = A.Compose([A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD), ToTensorV2()])


class PatchDataset(Dataset):
    def __init__(self, index_df, transform):
        self.index = index_df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.index)

    def __getitem__(self, i):
        r = self.index.iloc[i]
        tile = TILES[(r["city"], r["tile_id"])]
        row, col = r["row"], r["col"]
        img = tile["img"][row:row+PATCH, col:col+PATCH]
        mask = tile["mask"][row:row+PATCH, col:col+PATCH]
        out = self.transform(image=img, mask=mask)
        return out["image"], out["mask"].float().unsqueeze(0)


train_ds = PatchDataset(patch_index[patch_index.split == "train"], train_tf)
val_ds = PatchDataset(patch_index[patch_index.split == "val"], eval_tf)
log(f"train={len(train_ds)} val={len(val_ds)}")


def build_model():
    return smp.Unet(encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes=1).to(DEVICE)

dice_loss = smp.losses.DiceLoss(mode="binary", from_logits=True)
bce_loss = nn.BCEWithLogitsLoss()


def _dilate(x, k):
    return torch.nn.functional.max_pool2d(x, kernel_size=k, stride=1, padding=k // 2)


def _erode(x, k):
    return -torch.nn.functional.max_pool2d(-x, kernel_size=k, stride=1, padding=k // 2)


def boundary_dice_loss(logits, target, k=7, eps=1e-6):
    """Dice loss restricted to a band around the ground-truth boundary (dilation minus erosion,
    k=7 gives a ~3px band on each side). Directly targets edge precision, on top of the
    imbalance-robust whole-mask Dice term above."""
    probs = torch.sigmoid(logits)
    band = (_dilate(target, k) - _erode(target, k)).clamp(0, 1)
    inter = (probs * target * band).sum()
    denom = (probs * band).sum() + (target * band).sum()
    return 1 - (2 * inter + eps) / (denom + eps)


def combined_loss(logits, target):
    return 0.4 * bce_loss(logits, target) + 0.4 * dice_loss(logits, target) + 0.2 * boundary_dice_loss(logits, target)

def binarize(logits, threshold=0.5):
    return (torch.sigmoid(logits) > threshold).float()

def confusion_counts(pred, target):
    pred, target = pred.bool(), target.bool()
    return ((pred & target).sum().item(), (pred & ~target).sum().item(),
             (~pred & target).sum().item(), (~pred & ~target).sum().item())

class MetricAccumulator:
    def __init__(self):
        self.tp = self.fp = self.fn = self.tn = 0

    def update(self, pred, target):
        tp, fp, fn, tn = confusion_counts(pred, target)
        self.tp += tp; self.fp += fp; self.fn += fn; self.tn += tn

    def compute(self):
        eps = 1e-7
        iou = self.tp / (self.tp + self.fp + self.fn + eps)
        dice = 2 * self.tp / (2 * self.tp + self.fp + self.fn + eps)
        return {"IoU": iou, "Dice": dice,
                "Precision": self.tp / (self.tp + self.fp + eps),
                "Recall": self.tp / (self.tp + self.fn + eps),
                "PixelAcc": (self.tp + self.tn) / (self.tp + self.fp + self.fn + self.tn + eps)}


def run_training(train_ds, val_ds, epochs=30, batch_size=16, lr=1e-3, patience=6, tag="run"):
    torch.manual_seed(RANDOM_STATE)
    model = build_model()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=0.5, patience=2)
    scaler = torch.amp.GradScaler("cuda", enabled=(DEVICE.type == "cuda"))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=True)

    best_iou, best_state, epochs_no_improve = -1.0, None, 0
    history = []
    t_start = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE, non_blocking=True), yb.to(DEVICE, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=(DEVICE.type == "cuda")):
                logits = model(xb)
                loss = combined_loss(logits, yb)
            scaler.scale(loss).backward()
            scaler.step(opt); scaler.update()
            train_loss += loss.item() * xb.size(0)
        train_loss /= len(train_ds)

        model.eval()
        val_metric = MetricAccumulator()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                with torch.amp.autocast("cuda", enabled=(DEVICE.type == "cuda")):
                    logits = model(xb)
                    loss = combined_loss(logits, yb)
                val_loss += loss.item() * xb.size(0)
                val_metric.update(binarize(logits), yb)
        val_loss /= len(val_ds)
        val_scores = val_metric.compute()
        sched.step(val_scores["IoU"])

        improved = val_scores["IoU"] > best_iou
        if improved:
            best_iou, epochs_no_improve = val_scores["IoU"], 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            epochs_no_improve += 1

        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss, **val_scores})
        log(f"[{tag}] epoch {epoch:2d}/{epochs}  train_loss={train_loss:.4f}  val_loss={val_loss:.4f}  "
            f"val_IoU={val_scores['IoU']:.4f}  val_Dice={val_scores['Dice']:.4f}"
            f"{'  *best*' if improved else ''}")

        if epochs_no_improve >= patience:
            log(f"[{tag}] early stopping at epoch {epoch} (no val_IoU improvement for {patience} epochs)")
            break

    log(f"[{tag}] done in {time.time()-t_start:.0f}s. best val_IoU={best_iou:.4f}")
    model.load_state_dict(best_state)
    return model, pd.DataFrame(history)


if __name__ == "__main__":
    model, history = run_training(train_ds, val_ds, epochs=30, batch_size=16, tag="primary")
    torch.save(model.state_dict(), ARTIFACTS / "primary_model.pt")
    history.to_csv(ARTIFACTS / "primary_history.csv", index=False)
    log(f"saved checkpoint + history to {ARTIFACTS}")
