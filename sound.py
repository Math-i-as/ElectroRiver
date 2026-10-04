"""
Generador de sonidos chiptune estilo NES/GameBoy.
Genera ondas cuadradas y triangulares por código, sin archivos externos.
"""
import numpy as np
import pygame

SAMPLE_RATE = 22050

def _wave_square(freq, duration, duty=0.5, volume=0.35):
    """Onda cuadrada con duty cycle variable (0..1)."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    wave = np.where((t * freq) % 1.0 < duty, 1.0, -1.0)
    # Envolvente ADSR simple
    env = np.ones(n)
    attack = int(n * 0.01)
    release = int(n * 0.15)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    if release > 0:
        env[-release:] = np.linspace(1, 0, release)
    return (wave * env * volume * 32767).astype(np.int16)

def _wave_triangle(freq, duration, volume=0.35):
    """Onda triangular suave (tipo canal de bajo)."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    wave = 2 * np.abs(2 * ((t * freq) % 1.0) - 1) - 1
    env = np.ones(n)
    attack = int(n * 0.01)
    release = int(n * 0.15)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    if release > 0:
        env[-release:] = np.linspace(1, 0, release)
    return (wave * env * volume * 32767).astype(np.int16)

def _wave_noise(duration, volume=0.3):
    """Ruido blanco (para explosiones/quemaduras)."""
    n = int(SAMPLE_RATE * duration)
    wave = np.random.uniform(-1, 1, n)
    env = np.linspace(1, 0, n) ** 2
    return (wave * env * volume * 32767).astype(np.int16)

def _to_sound(mono):
    """Convierte array int16 mono en pygame.mixer.Sound estéreo."""
    stereo = np.column_stack((mono, mono))
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))

def _secuencia(notas):
    """Concatena notas (freq, dur, tipo) en un solo sonido."""
    trozos = []
    for freq, dur, tipo in notas:
        if tipo == "square":
            trozos.append(_wave_square(freq, dur))
        elif tipo == "triangle":
            trozos.append(_wave_triangle(freq, dur))
        elif tipo == "noise":
            trozos.append(_wave_noise(dur))
        elif tipo == "silence":
            trozos.append(np.zeros(int(SAMPLE_RATE * dur), dtype=np.int16))
    return np.concatenate(trozos)


class Chiptune:
    """Contenedor de todos los sonidos del juego."""
    def __init__(self):
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)

        # ---- Notas en Hz (escala cromática) ----
        N = {
            "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
            "G4": 392.00, "A4": 440.00, "B4": 493.88,
            "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
            "G5": 783.99, "A5": 880.00, "B5": 987.77,
            "C6": 1046.50, "E6": 1318.51, "G6": 1567.98,
        }

        # ---- Sonidos de UI ----
        self.click = _to_sound(_secuencia([
            (N["E5"], 0.04, "square"),
        ]))

        self.hover = _to_sound(_secuencia([
            (N["C5"], 0.02, "square"),
        ]))

        self.pickup = _to_sound(_secuencia([
            (N["G4"], 0.04, "square"),
            (N["C5"], 0.05, "square"),
        ]))

        self.drop = _to_sound(_secuencia([
            (N["C5"], 0.03, "square"),
            (N["G4"], 0.05, "square"),
        ]))

        self.place = _to_sound(_secuencia([
            (N["E5"], 0.04, "square"),
            (N["G5"], 0.04, "square"),
        ]))

        # ---- Sonidos de feedback ----
        # Fallo suave: se intenta poner algo mal pero no rompe nada
        self.warn = _to_sound(_secuencia([
            (N["A4"], 0.08, "triangle"),
            (N["F4"], 0.10, "triangle"),
        ]))

        # Quema de LED / transistor
        self.burn = _to_sound(_secuencia([
            (N["C5"], 0.05, "noise"),
            (N["G4"], 0.08, "noise"),
            (N["C4"], 0.20, "noise"),
        ]))

        # Victoria corta (tipo Mario coin)
        self.win = _to_sound(_secuencia([
            (N["E5"], 0.08, "square"),
            (N["G5"], 0.08, "square"),
            (N["C6"], 0.10, "square"),
            (N["G5"], 0.08, "square"),
            (N["C6"], 0.20, "square"),
        ]))

        # Fanfarria de nivel completado
        self.level_complete = _to_sound(_secuencia([
            (N["C5"], 0.10, "square"),
            (N["E5"], 0.10, "square"),
            (N["G5"], 0.10, "square"),
            (N["C6"], 0.15, "square"),
            (N["G5"], 0.10, "square"),
            (N["C6"], 0.30, "square"),
        ]))

        # Bloqueado
        self.locked = _to_sound(_secuencia([
            (N["E4"], 0.06, "square"),
            (N["C4"], 0.10, "square"),
        ]))

        # Navegación menú
        self.menu_move = _to_sound(_secuencia([
            (N["D5"], 0.03, "square"),
            (N["A4"], 0.04, "square"),
        ]))

        # Reset del nivel
        self.reset = _to_sound(_secuencia([
            (N["C5"], 0.04, "square"),
            (N["G4"], 0.04, "square"),
            (N["E4"], 0.06, "square"),
        ]))

    def play(self, nombre, vol=1.0):
        snd = getattr(self, nombre, None)
        if snd is not None:
            snd.set_volume(vol)
            snd.play()