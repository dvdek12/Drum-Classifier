"""
Generator syntetycznych sampli perkusyjnych do testowania.
Tworzy realistyczne (ale syntetyczne) pliki .wav dla:
  kick, snare, hihat, clap, tom

Uruchom: python generate_test_samples.py
"""

import numpy as np
import soundfile as sf
from pathlib import Path

SR = 22050  # Hz
OUTPUT_DIR = Path(__file__).parent / "samples"
OUTPUT_DIR.mkdir(exist_ok=True)


def save(name: str, signal: np.ndarray):
    path = OUTPUT_DIR / f"{name}.wav"
    # Normalizacja
    signal = signal / (np.max(np.abs(signal)) + 1e-8)
    sf.write(str(path), signal.astype(np.float32), SR)
    print(f"  Zapisano: {path}")


def make_kick(duration=0.5, variation=0):
    """Kick drum — niski boom, szybki atak, długi zanik."""
    t = np.linspace(0, duration, int(SR * duration))

    # Podstawowa częstotliwość opada szybko (pitch envelope)
    freq_start = 180 + variation * 20
    freq_end   = 40
    freq = freq_start * np.exp(-t * 15) + freq_end

    # Sygnał sinusoidalny z opadającą częstotliwością
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sine = np.sin(phase)

    # Envelope amplitudy — atak + długi zanik
    env = np.exp(-t * (8 + variation * 2))

    # Dodaj trochę szumu na ataku
    click = np.random.randn(len(t)) * np.exp(-t * 60) * 0.3

    return (sine * env + click) * 0.9


def make_snare(duration=0.3, variation=0):
    """Snare drum — srednia częstotliwość + szum (charakterystyczny "crack")."""
    t = np.linspace(0, duration, int(SR * duration))

    # Ciało snare — średnie tony
    freq = 200 + variation * 30
    body = np.sin(2 * np.pi * freq * t) * np.exp(-t * 20)

    # Druty snare — biały szum z filtrem
    noise = np.random.randn(len(t))
    # Prosty filtr pasmowy przez różnicowanie
    noise_filtered = np.diff(noise, prepend=noise[0]) * 0.5

    env_noise = np.exp(-t * (12 + variation * 3))

    # Atak
    attack = np.exp(-t * 80) * 0.5

    return (body * 0.4 + noise_filtered * env_noise * 0.7 + attack) * 0.85


def make_hihat_closed(duration=0.08, variation=0):
    """Zamknięty hi-hat — krótki, ostry, głównie szum wysokich częstotliwości."""
    t = np.linspace(0, duration, int(SR * duration))

    # Szum wysokich częstotliwości
    noise = np.random.randn(len(t))

    # Prosty high-pass przez różnicowanie wielokrotne
    hp = noise
    for _ in range(3 + variation):
        hp = np.diff(hp, prepend=hp[0])

    env = np.exp(-t * (50 + variation * 10))

    # Metaliczny dźwięk — kilka sinusoidalnych składowych w wysokich częstotliwościach
    metal = (
        np.sin(2 * np.pi * 6000 * t) * 0.1 +
        np.sin(2 * np.pi * 9000 * t) * 0.08 +
        np.sin(2 * np.pi * 12000 * t) * 0.05
    )

    return (hp * env * 0.6 + metal * env * 0.4) * 0.8


def make_hihat_open(duration=0.4, variation=0):
    """Otwarty hi-hat — jak zamknięty ale dłuższy zanik."""
    t = np.linspace(0, duration, int(SR * duration))

    noise = np.random.randn(len(t))
    hp = noise
    for _ in range(3):
        hp = np.diff(hp, prepend=hp[0])

    env = np.exp(-t * (8 + variation * 2))

    metal = (
        np.sin(2 * np.pi * 6000 * t) * 0.12 +
        np.sin(2 * np.pi * 9500 * t) * 0.08
    )

    return (hp * env * 0.6 + metal * env * 0.4) * 0.8


def make_clap(duration=0.25, variation=0):
    """Clap — wielokrotne szybkie uderzenia, charakterystyczny "plask"."""
    t = np.linspace(0, duration, int(SR * duration))

    # Kilka szybkich burst szumu (symuluje wiele dłoni)
    n_bursts = 3 + variation
    signal = np.zeros(len(t))

    for i in range(n_bursts):
        offset = int(SR * i * 0.008)  # 8ms odstęp między uderzeniami
        burst = np.random.randn(len(t))
        burst_env = np.exp(-np.maximum(t - i * 0.008, 0) * 40)
        signal += burst * burst_env * 0.4

    # Środkowe częstotliwości
    mid = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 25) * 0.3

    return (signal + mid) * 0.85


def make_tom(duration=0.4, variation=0):
    """Tom — między kickiem a snare, średnie-niskie tony."""
    t = np.linspace(0, duration, int(SR * duration))

    freq_start = 120 + variation * 40
    freq_end   = 80 + variation * 20
    freq = freq_start * np.exp(-t * 8) + freq_end

    phase = 2 * np.pi * np.cumsum(freq) / SR
    sine = np.sin(phase)

    # Mniej szumu niż snare, więcej ciała
    env = np.exp(-t * (10 + variation * 2))
    noise = np.random.randn(len(t)) * np.exp(-t * 25) * 0.15

    return (sine * env * 0.85 + noise) * 0.9


# ------------------------------------------------------------------ #
#  Generowanie sampli                                                  #
# ------------------------------------------------------------------ #

print("Generowanie syntetycznych sampli perkusyjnych...\n")

generators = {
    "kick":  make_kick,
    "snare": make_snare,
    "hihat": make_hihat_closed,
    "clap":  make_clap,
    "tom":   make_tom,
}

N_VARIATIONS = 6  # ile wariantów każdego sampla

for label, gen_fn in generators.items():
    print(f"[{label}]")
    for i in range(N_VARIATIONS):
        name = f"{label}_{i+1:02d}"
        signal = gen_fn(variation=i % 3)
        # Dodaj trochę losowego szumu dla różnorodności
        signal += np.random.randn(len(signal)) * 0.005
        save(name, signal)

print(f"\nGotowe! Wygenerowano {len(generators) * N_VARIATIONS} sampli w {OUTPUT_DIR}")
print("\nEtykiety klas do wgrania w aplikacji:")
for label in generators:
    print(f"  {label}_*.wav  →  label: '{label}'")
