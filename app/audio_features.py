"""
Ekstrakcja cech audio z plików .wav / .mp3 / .flac itp.
Używamy librosa do wczytywania i obliczania cech.
Cechy są znormalizowane — gotowe do podania do drzewa decyzyjnego.
"""

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

    # MFCC — pierwsze 5 współczynników (barwa dźwięku)
    *[f"mfcc_{i}_mean" for i in range(1, 6)],
]


def extract_features(audio_path: str, sr: int = 22050, duration: float = None) -> np.ndarray:
    """
    Wczytuje plik audio i zwraca wektor cech.

    Args:
        audio_path: ścieżka do pliku audio
        sr: częstotliwość próbkowania (22050 Hz standard)
        duration: przytnij do N sekund (None = cały plik)

    Returns:
        np.ndarray shape (n_features,) — wektor cech
    """
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

    # --- MFCC (pierwsze 5 współczynników) ---
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=5)
    for i in range(5):
        features.append(mfccs[i].mean())

    return np.array(features, dtype=np.float32)


def extract_features_batch(file_paths: list[str], labels: list[str] = None):
    """
    Ekstraktuje cechy z listy plików.

    Returns:
        X: np.ndarray shape (n_files, n_features)
        y: np.ndarray shape (n_files,) — etykiety (jeśli podane)
        errors: lista błędów
    """
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
    """
    Zwraca dane fali dźwiękowej do wizualizacji na froncie.
    Redukuje liczbę punktów do max_points żeby nie przeciążać przeglądarki.
    """
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
