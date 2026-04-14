"""
Testa a seleção de dispositivo de saída do PyAudio.

Uso:
    python test_output_device.py                # lista devices e pede escolha
    python test_output_device.py --list         # só lista
    python test_output_device.py --index 5      # toca no device 5
    python test_output_device.py --name hyperx  # toca no primeiro device cujo nome contém "hyperx" (case-insensitive)
    python test_output_device.py --name hdmi --rate 48000
"""

import argparse
import math
import sys

import numpy as np
import pyaudio


FORMAT = pyaudio.paFloat32
CHANNELS = 1
FRAMES_PER_BUFFER = 1024
RATE_CANDIDATES = (48000, 44100, 16000)


def list_output_devices(pa: pyaudio.PyAudio):
    rows = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info['maxOutputChannels'] <= 0:
            continue
        rows.append((i, info['name'], int(info['maxOutputChannels']), int(info['defaultSampleRate'])))

    print(f'{"idx":>3}  {"ch":>3}  {"rate":>6}  name')
    print('-' * 70)
    for idx, name, ch, rate in rows:
        print(f'{idx:>3}  {ch:>3}  {rate:>6}  {name}')
    return rows


def resolve_device(pa: pyaudio.PyAudio, index: int | None, name: str | None) -> int:
    if index is not None:
        return index

    if name is not None:
        needle = name.lower()
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0 and needle in info['name'].lower():
                return i
        print(f'[erro] nenhum device de saída com "{name}" no nome', file=sys.stderr)
        sys.exit(1)

    raw = input('\ndigite o index do device pra testar: ').strip()
    return int(raw)


def pick_supported_rate(pa: pyaudio.PyAudio, device_index: int, preferred: int | None) -> int:
    candidates = RATE_CANDIDATES if preferred is None else (preferred, *RATE_CANDIDATES)
    for rate in candidates:
        try:
            ok = pa.is_format_supported(
                rate=rate,
                output_device=device_index,
                output_channels=CHANNELS,
                output_format=FORMAT,
            )
            if ok:
                return rate
        except ValueError:
            continue
    raise RuntimeError(f'nenhuma taxa suportada pro device {device_index}')


def make_tone(rate: int, duration_s: float = 1.5, freq: float = 440.0) -> np.ndarray:
    t = np.linspace(0, duration_s, int(rate * duration_s), endpoint=False, dtype=np.float32)
    wave = 0.3 * np.sin(2 * math.pi * freq * t, dtype=np.float32)
    fade = min(int(rate * 0.02), len(wave) // 2)
    if fade:
        wave[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        wave[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return wave.astype(np.float32)


def play_tone_on_device(pa: pyaudio.PyAudio, device_index: int, rate: int):
    info = pa.get_device_info_by_index(device_index)
    print(f'\n[play] device {device_index} — {info["name"]} @ {rate} Hz')

    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=rate,
        frames_per_buffer=FRAMES_PER_BUFFER,
        output=True,
        output_device_index=device_index,
    )
    try:
        stream.write(make_tone(rate).tobytes())
    finally:
        stream.stop_stream()
        stream.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true', help='só lista os devices e sai')
    parser.add_argument('--index', type=int, help='index do device de saída')
    parser.add_argument('--name', type=str, help='substring do nome do device (case-insensitive)')
    parser.add_argument('--rate', type=int, help='taxa desejada (fallback automático se não suportar)')
    args = parser.parse_args()

    pa = pyaudio.PyAudio()
    try:
        list_output_devices(pa)
        if args.list:
            return

        device_index = resolve_device(pa, args.index, args.name)
        rate = pick_supported_rate(pa, device_index, args.rate)
        play_tone_on_device(pa, device_index, rate)
        print('[ok] tom reproduzido sem erros')
    finally:
        pa.terminate()


if __name__ == '__main__':
    main()
