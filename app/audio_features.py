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
    # Cechy spektralne
    "spectral_centroid_mean",   # "jasność" dźwięku — wyższe = jaśniejszy dźwięk
    "spectral_centroid_std",
    "spectral_bandwidth_mean",  # szerokość pasma
    "spectral_bandwidth_std",
    "spectral_rolloff_mean",    # częstotliwość poniżej której 85% energii
    "spectral_rolloff_std",
    "spectral_flatness_mean",   # jak bardzo szum vs ton
    "spectral_flatness_std",

    # Energia i dynamika
    "rms_mean",                 # średnia energia sygnału
    "rms_std",
    "zero_crossing_rate_mean",  # liczba przejść przez zero (perkusja = dużo)
    "zero_crossing_rate_std",

    # Cechy czasowe
    "onset_strength_mean",      # siła ataku
    "onset_strength_std",
    "tempo",                    # BPM (mniej istotne dla pojedynczych sampli)

    # Chroma — profil harmoniczny (bardziej przydatne dla tonalnych dźwięków)
    "chroma_mean",
    "chroma_std",
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

    # --- Cechy spektralne ---
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features += [spectral_centroids.mean(), spectral_centroids.std()]

    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    features += [spectral_bandwidth.mean(), spectral_bandwidth.std()]

    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    features += [spectral_rolloff.mean(), spectral_rolloff.std()]

    spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
    features += [spectral_flatness.mean(), spectral_flatness.std()]

    # --- Energia i dynamika ---
    rms = librosa.feature.rms(y=y)[0]
    features += [rms.mean(), rms.std()]

    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features += [zcr.mean(), zcr.std()]

    # --- Siła ataku ---
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    features += [onset_env.mean(), onset_env.std()]

    # --- Tempo ---
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    features.append(float(tempo) if np.isscalar(tempo) else float(tempo[0]))

    # --- Chroma ---
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    features += [chroma.mean(), chroma.std()]

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
