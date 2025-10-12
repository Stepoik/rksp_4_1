import numpy as np
import torch
from scipy.signal import resample
from torch_ecg.models import ECG_CRNN  # модель для последовательной классификации

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# твои классы. пример: норм, AF, PVC
LABELS = ["Normal", "AF", "PVC"]

def standardize_fs(x: np.ndarray, fs_src: int, fs_tgt: int = 250):
    if fs_src == fs_tgt:
        return x.astype(np.float32), fs_src
    L_tgt = int(round(len(x) * fs_tgt / fs_src))
    x = resample(x, L_tgt).astype(np.float32)
    return x, fs_tgt

def to_windows_1d(x: np.ndarray, fs: int, win_sec: float = 10.0, step_sec: float | None = None):
    if step_sec is None:
        step_sec = win_sec
    w = int(win_sec * fs)
    s = int(step_sec * fs)
    if len(x) < w:
        x = np.pad(x, (0, w - len(x)))
    idxs = range(0, len(x) - w + 1, s)
    wins = np.stack([x[i:i + w] for i in idxs], axis=0)  # (N, w)
    return wins

def normalize(z: np.ndarray):
    mu, sd = float(np.mean(z)), float(np.std(z))
    return (z - mu) / (sd + 1e-6)

def build_model(in_channels=1, classes=LABELS):
    # под 1D-канал
    model = ECG_CRNN(n_leads=in_channels, classes=classes)
    model.to(DEVICE).eval()
    return model

@torch.no_grad()
def infer_ecg_1d(model: torch.nn.Module, x_1d: np.ndarray, fs_src: int,
                 fs_tgt: int = 250, win_sec: float = 10.0):
    # ресэмплинг/окна/нормализация
    x_1d, fs = standardize_fs(x_1d, fs_src, fs_tgt)
    wins = to_windows_1d(x_1d, fs=fs, win_sec=win_sec, step_sec=win_sec)
    wins = np.stack([normalize(w) for w in wins], axis=0)  # (N, L)

    # в тензор B,C,L
    t = torch.from_numpy(wins).float().unsqueeze(1).to(DEVICE)  # (B,1,L)

    # логиты -> вероятности
    logits = model(t)                    # форма зависит от модели, у seq-lab обычно (B, num_classes) для класа
    if logits.ndim > 2:                  # на всякий случай усредним по времени, если seq-label помечает покадрово
        logits = logits.mean(dim=-1)
    probs = torch.sigmoid(logits).cpu().numpy()  # (B, num_classes) для multi-label

    # агрегируем по окнам средним
    mean_probs = probs.mean(axis=0)
    return {LABELS[i]: float(mean_probs[i]) for i in range(len(LABELS))}

DEFAULT_MODEL = build_model(in_channels=1, classes=LABELS)