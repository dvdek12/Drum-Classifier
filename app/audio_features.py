
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path


# Nazwy cech — używane w drzewie i wizualizacji
FEATURE_NAMES = [
    # Cechy spektralne (tylko średnie)
    "spectral_centroid_mean",   # "jasność" dźwięku
    "spectral_bandwidth_mean",  # szerokość pasma
    "spectral_rolloff_mean",    # częstotliwość poniżej której 85% energii
    "spectral_flatness_mean",   # szum vs ton

    # Energia i dynamika
    "rms_mean",                 # średnia energia
    "zero_crossing_rate_mean",  # przejścia przez zero (perkusja = dużo)

    # Siła ataku
    "onset_strength_mean",

    # Nowe cechy
    "attack_time",              # czas narastania do szczytu amplitudy (ms)
    "mfcc_1_mean",              # barwa dźwięku (nisko=kick, wysoko=hi-hat)
    "spectral_contrast_mean",   # kontrast między pikami a dolinami widma
    "tempo_bpm",                # BPM wykryte z sampla
]


def extract_features(audio_path: str, sr: int = 22050, duration: float = None) -> np.ndarray:
   
    # Wczytaj audio
    y, sr = librosa.load(audio_path, sr=sr, duration=duration, mono=True)

    # Normalizacja amplitudy
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))

    features = []

    # --- Cechy spektralne (tylko średnie) ---
    features.append(librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean())
    features.append(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0].mean())
    features.append(librosa.feature.spectral_rolloff(y=y, sr=sr)[0].mean())
    features.append(librosa.feature.spectral_flatness(y=y)[0].mean())

    # --- Energia i dynamika ---
    features.append(librosa.feature.rms(y=y)[0].mean())
    features.append(librosa.feature.zero_crossing_rate(y)[0].mean())

    # --- Siła ataku ---
    features.append(librosa.onset.onset_strength(y=y, sr=sr).mean())

    # --- Czas narastania (attack time) ---
    amplitude_env = np.abs(y)
    peak_idx = np.argmax(amplitude_env)
    attack_time_ms = (peak_idx / sr) * 1000.0
    features.append(attack_time_ms)

    # --- MFCC-1 (ogólna barwa dźwięku) ---
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=1)
    features.append(mfcc[0].mean())

    # --- Kontrast spektralny ---
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    features.append(contrast.mean())

    # --- Tempo (BPM) ---
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    features.append(float(tempo))

    arr = np.array(features, dtype=np.float32)
    # Zamień NaN/inf na 0 (np. tempo_bpm dla bardzo krótkich sampli)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr


def extract_features_batch(file_paths: list[str], labels: list[str] = None):

    X, y_out, errors = [], [], []

    for i, path in enumerate(file_paths):
        try:
            feat = extract_features(path)
            X.append(feat)
            if labels:
                y_out.append(labels[i])
        except Exception as e:
            errors.append({"file": path, "error": str(e)})

    return (
        np.array(X) if X else np.empty((0, len(FEATURE_NAMES))),
        np.array(y_out) if y_out else np.array([]),
        errors,
    )


def get_waveform_data(audio_path: str, max_points: int = 1000) -> dict:

    y, sr = librosa.load(audio_path, sr=22050, mono=True)

    # Downsampling do wizualizacji
    if len(y) > max_points:
        step = len(y) // max_points
        y_vis = y[::step][:max_points]
    else:
        y_vis = y

    duration = len(y) / sr

    return {
        "waveform": y_vis.tolist(),
        "sample_rate": sr,
        "duration_sec": round(duration, 3),
        "n_samples": len(y),
    }


def get_feature_names() -> list[str]:
    return FEATURE_NAMES
