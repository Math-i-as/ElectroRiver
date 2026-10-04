# ============================================================
#   ⚡ ELECTRO RIVER — Juego educativo de electrónica
#   Niveles: 1) LED  2) Transistor NPN  3) Oscilador Astable
#   Listo para empaquetar con PyInstaller (.exe)
# ============================================================

import pygame
import sys
import math
import os
import json
import io
import contextlib

# ============================================================
#   RUTAS COMPATIBLES CON .EXE (PyInstaller)
# ============================================================
def ruta_recurso(relativa):
    """
    Devuelve la ruta correcta del recurso, ya sea que se ejecute
    como script (.py) o como ejecutable empaquetado (.exe).
    """
    try:
        base = sys._MEIPASS    # PyInstaller crea esta carpeta temporal
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, relativa)

def ruta_persistente(nombre):
    """
    Devuelve la ruta para guardar archivos persistentes (progress.json)
    al lado del .exe (no dentro de la carpeta temporal).
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(".")
    return os.path.join(base, nombre)

# ============ SONIDO (opcional, con fallback silencioso) ============
try:
    with contextlib.redirect_stderr(io.StringIO()):
        from sound import Chiptune
        chiptune = Chiptune()
except Exception:
    class _Silent:
        def play(self, *a, **k): pass
    chiptune = _Silent()

# ============ INICIALIZACIÓN PYGAME ============
pygame.init()
pygame.font.init()

# ============ CONFIGURACIÓN ============
WIDTH, HEIGHT = 1100, 750
FPS = 60
SCALE = 0.1

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("⚡ Electro River — Juego educativo de electrónica")
clock = pygame.time.Clock()

# ============ COLORES ============
FONDO_APP      = (30, 34, 42)
PANEL_LATERAL  = (40, 44, 52)
PANEL_BORDE    = (60, 66, 78)
AREA_TRABAJO   = (245, 245, 240)
AREA_BORDE     = (200, 200, 195)
GRILLA         = (225, 225, 220)
NEGRO          = (20, 20, 30)
GRIS           = (60, 60, 80)
GRIS_CLARO     = (120, 120, 140)
AMARILLO       = (255, 220, 60)
ROJO           = (230, 60, 60)
BLANCO         = (240, 240, 240)
NARANJA        = (255, 140, 40)
VERDE_OK       = (100, 220, 120)
AZUL_BARRA     = (60, 130, 200)
MORADO         = (170, 100, 220)
CIAN           = (100, 200, 240)
TARJETA_BG     = (50, 55, 68)
TARJETA_HOVER  = (65, 72, 88)
TARJETA_LOCK   = (35, 38, 46)
HUECO_BG       = (35, 38, 46)
HUECO_BORDE    = (55, 58, 68)

# ============ FUENTES ============
font_small = pygame.font.SysFont("consolas", 14, bold=True)
font_med   = pygame.font.SysFont("consolas", 18, bold=True)
font_big   = pygame.font.SysFont("consolas", 22, bold=True)
font_huge  = pygame.font.SysFont("consolas", 34, bold=True)
font_tiny  = pygame.font.SysFont("consolas", 12, bold=True)

# ============ PERSISTENCIA ============
PROGRESS_FILE = ruta_persistente("progress.json")

def cargar_progreso():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"desbloqueados": [1]}

def guardar_progreso(data):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[warn] No se pudo guardar progreso: {e}")

progreso = cargar_progreso()

# ============ DEFINICIÓN DE NIVELES ============
NIVELES = [
    {
        "id": 1,
        "titulo": "El LED",
        "subtitulo": "Pila + R + LED",
        "descripcion": "Enciende un LED sin quemarlo usando una resistencia limitadora.",
        "color": VERDE_OK,
    },
    {
        "id": 2,
        "titulo": "Transistor NPN",
        "subtitulo": "Control de corriente",
        "descripcion": "Usa un transistor como interruptor para controlar el LED(Todo a tierra).",
        "color": MORADO,
    },
    {
        "id": 3,
        "titulo": "Oscilador Astable",
        "subtitulo": "LED parpadeante",
        "descripcion": "Dos transistores y dos capacitores: el LED parpadea solo.",
        "color": CIAN,
    },
]

# ============ LAYOUT ============
SIDEBAR_W    = 280
TOP_BAR_H    = 40
STATUS_BAR_H = 28

CANVAS_X = SIDEBAR_W + 20
CANVAS_Y = TOP_BAR_H + 20
CANVAS_W = WIDTH - SIDEBAR_W - 40
CANVAS_H = HEIGHT - TOP_BAR_H - STATUS_BAR_H - 40
canvas_rect = pygame.Rect(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H)

# ============ SCROLL DEL SIDEBAR ============
PALETA_ITEM_H       = 90
PALETA_PADDING_TOP  = TOP_BAR_H + 50
PALETA_PADDING_BOT  = 20
SCROLLBAR_W         = 12

PALETA_TOTAL_ITEMS  = 0

scroll_y              = 0.0
scroll_vel            = 0.0
scrollbar_dragging    = False
scrollbar_drag_offset = 0
scrollbar_thumb_rect  = None
scrollbar_track_rect  = None

# ============================================================
#   CARGA DE SPRITES
# ============================================================
SPR = {}

def load(name, scale=SCALE):
    path = ruta_recurso(os.path.join("assets", f"{name}.png"))
    img = pygame.image.load(path)
    try:
        img = img.convert_alpha()
    except pygame.error:
        pass
    w, h = img.get_size()
    return pygame.transform.scale(img, (w * scale, h * scale))

def cargar_todos_los_sprites():
    nombres = [
        "pila", "led_off", "led_on", "led_burn",
        "resistencia", "resistencia_1k", "resistencia_47k",
        "slot",
        "transistor_off", "transistor_on", "transistor_burn",
        "capacitor",
    ]

    def color_placeholder(n):
        if "led" in n:          return (230, 60, 60)
        if "pila" in n:         return (70, 130, 220)
        if "resist" in n:       return (200, 180, 120)
        if "transist" in n:     return (100, 60, 100)
        if "capacit" in n:      return (100, 180, 255)
        if "slot" in n:         return (150, 150, 170)
        return (200, 100, 200)

    for n in nombres:
        sprite_final = None
        path = ruta_recurso(os.path.join("assets", f"{n}.png"))

        if os.path.exists(path):
            try:
                sprite_final = load(n)
            except Exception as e:
                print(f"[warn] No se pudo cargar {n}.png: {e}")

        if sprite_final is None:
            print(f"[placeholder] {n}.png no encontrado -> cuadrado de color")
            base = pygame.Surface((16, 16), pygame.SRCALPHA)
            base.fill(color_placeholder(n))
            pygame.draw.rect(base, BLANCO, (0, 0, 16, 16), 1)
            sprite_final = pygame.transform.scale(base, (16 * SCALE, 16 * SCALE))

        SPR[n] = sprite_final

cargar_todos_los_sprites()
print(f"[ok] Sprites cargados: {len(SPR)}")

# ============ ESTADO GLOBAL ============
escena = "MENU"
nivel_actual = None

# ============================================================
#   COMPONENTE
# ============================================================
class Component:
    def __init__(self, name, sprite_key, palette_index, slot_key=None):
        self.name = name
        self.sprite_key = sprite_key
        self.img = SPR[sprite_key]
        self.w, self.h = self.img.get_size()
        self.palette_index = palette_index
        self.palette_x = SIDEBAR_W // 2 - self.w // 2
        self.palette_y = 0
        self.x = self.palette_x
        self.y = 0
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.placed_slot = None
        self.in_palette = True
        self.slot_key = slot_key if slot_key else name
        self.card_rect = pygame.Rect(0, 0, 0, 0)

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, surf):
        if not self.in_palette:
            shadow = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 100))
            surf.blit(shadow, (self.x + 3, self.y + 3))
        surf.blit(self.img, (self.x, self.y))

# ============================================================
#   CONSTRUCCIÓN DE NIVELES
# ============================================================
def construir_nivel(id_nivel):
    comps = []
    slots_local = {}
    SLOT_SIZE = SPR["slot"].get_width()

    if id_nivel == 1:
        SP = 90
        row_y = canvas_rect.centery - SLOT_SIZE // 2 + 30
        total = SLOT_SIZE * 3 + SP * 2
        start = canvas_rect.centerx - total // 2

        slots_local = {
            "pila":        pygame.Rect(start,                          row_y, SLOT_SIZE, SLOT_SIZE),
            "resistencia": pygame.Rect(start + SLOT_SIZE + SP,         row_y, SLOT_SIZE, SLOT_SIZE),
            "led":         pygame.Rect(start + (SLOT_SIZE + SP) * 2,   row_y, SLOT_SIZE, SLOT_SIZE),
        }
        items = [
            ("pila",        "pila",        "pila"),
            ("resistencia", "resistencia", "resistencia"),
            ("led",         "led_off",     "led"),
        ]
        for i, (label, sprite, sk) in enumerate(items):
            comps.append(Component(label, sprite, i, sk))

    elif id_nivel == 2:
        SP = 80
        row1_y = canvas_rect.top + 120
        row2_y = canvas_rect.top + 320

        total1 = SLOT_SIZE * 3 + SP * 2
        start1 = canvas_rect.centerx - total1 // 2

        slots_local = {
            "pila":  pygame.Rect(start1,                          row1_y, SLOT_SIZE, SLOT_SIZE),
            "r_led": pygame.Rect(start1 + SLOT_SIZE + SP,         row1_y, SLOT_SIZE, SLOT_SIZE),
            "led":   pygame.Rect(start1 + (SLOT_SIZE + SP) * 2,   row1_y, SLOT_SIZE, SLOT_SIZE),
        }
        total2 = SLOT_SIZE * 2 + SP
        start2 = canvas_rect.centerx - total2 // 2
        slots_local["transistor"] = pygame.Rect(start2,                  row2_y, SLOT_SIZE, SLOT_SIZE)
        slots_local["r_base"]     = pygame.Rect(start2 + SLOT_SIZE + SP, row2_y, SLOT_SIZE, SLOT_SIZE)

        items = [
            ("pila",       "pila",            "pila"),
            ("R LED 330",  "resistencia",     "r_led"),
            ("R base 1k",  "resistencia_1k",  "r_base"),
            ("LED",        "led_off",         "led"),
            ("transistor", "transistor_off",  "transistor"),
        ]
        for i, (label, sprite, sk) in enumerate(items):
            comps.append(Component(label, sprite, i, sk))

    elif id_nivel == 3:
        SP = 60
        row1_y = canvas_rect.top + 40
        total1 = SLOT_SIZE * 3 + SP * 2
        start1 = canvas_rect.centerx - total1 // 2
        slots_local = {
            "pila": pygame.Rect(start1,                          row1_y, SLOT_SIZE, SLOT_SIZE),
            "r4":   pygame.Rect(start1 + SLOT_SIZE + SP,         row1_y, SLOT_SIZE, SLOT_SIZE),
            "led":  pygame.Rect(start1 + (SLOT_SIZE + SP) * 2,   row1_y, SLOT_SIZE, SLOT_SIZE),
        }

        row2_y = canvas_rect.top + 170
        total2 = SLOT_SIZE * 4 + SP * 3
        start2 = canvas_rect.centerx - total2 // 2
        slots_local["q1"] = pygame.Rect(start2,                            row2_y, SLOT_SIZE, SLOT_SIZE)
        slots_local["c1"] = pygame.Rect(start2 + SLOT_SIZE + SP,           row2_y, SLOT_SIZE, SLOT_SIZE)
        slots_local["c2"] = pygame.Rect(start2 + (SLOT_SIZE + SP) * 2,     row2_y, SLOT_SIZE, SLOT_SIZE)
        slots_local["q2"] = pygame.Rect(start2 + (SLOT_SIZE + SP) * 3,     row2_y, SLOT_SIZE, SLOT_SIZE)

        row3_y = canvas_rect.top + 300
        total3 = SLOT_SIZE * 3 + SP * 2
        start3 = canvas_rect.centerx - total3 // 2
        slots_local["r1"] = pygame.Rect(start3,                          row3_y, SLOT_SIZE, SLOT_SIZE)
        slots_local["r3"] = pygame.Rect(start3 + SLOT_SIZE + SP,         row3_y, SLOT_SIZE, SLOT_SIZE)
        slots_local["r2"] = pygame.Rect(start3 + (SLOT_SIZE + SP) * 2,   row3_y, SLOT_SIZE, SLOT_SIZE)

        items = [
            ("pila",       "pila",            "pila"),
            ("R LED 220",  "resistencia",     "r4"),
            ("R col 330",  "resistencia",     "r3"),
            ("R base 47k", "resistencia_47k", "r1"),
            ("R base 47k", "resistencia_47k", "r2"),
            ("LED",        "led_off",         "led"),
            ("Q1",         "transistor_off",  "q1"),
            ("Q2",         "transistor_off",  "q2"),
            ("C1 10uF",    "capacitor",       "c1"),
            ("C2 10uF",    "capacitor",       "c2"),
        ]
        for i, (label, sprite, sk) in enumerate(items):
            comps.append(Component(label, sprite, i, sk))

    return comps, slots_local

# ============ ESTADO DEL NIVEL ============
componentes = []
slots = {}
state = "PLAY"
failure_reason = ""
feedback = ""
feedback_timer = 0
led_bright = 0.0
led_burning = False
transistor_burning = False
burn_timer = 0
cables_on = False
cable_anim = 0.0

def cargar_nivel(id_nivel):
    global componentes, slots, nivel_actual, state, feedback, failure_reason
    global cables_on, cable_anim, led_bright, led_burning, transistor_burning, burn_timer
    global escena, scroll_y, scroll_vel, scrollbar_dragging
    global PALETA_TOTAL_ITEMS

    nivel_actual = id_nivel
    componentes, slots = construir_nivel(id_nivel)
    PALETA_TOTAL_ITEMS = len(componentes)
    state = "PLAY"
    failure_reason = ""
    feedback = ""
    feedback_timer = 0
    led_bright = 0.0
    led_burning = False
    transistor_burning = False
    burn_timer = 0
    cables_on = False
    cable_anim = 0.0
    scroll_y = 0.0
    scroll_vel = 0.0
    scrollbar_dragging = False
    escena = "PLAY"

def desbloquear_nivel(id_nivel):
    if id_nivel not in progreso["desbloqueados"]:
        progreso["desbloqueados"].append(id_nivel)
        guardar_progreso(progreso)

# ============================================================
#   VALIDACIÓN
# ============================================================
def validar_circuito():
    global state, feedback, failure_reason, led_burning, transistor_burning, cables_on

    def slot_ocupado(key):
        return any(c.slot_key == key and c.placed_slot == key for c in componentes)

    # ---------- NIVEL 1 ----------
    if nivel_actual == 1:
        pila_ok = slot_ocupado("pila")
        res_ok  = slot_ocupado("resistencia")
        led_ok  = slot_ocupado("led")

        if pila_ok and led_ok and not res_ok:
            state = "LOSE"
            failure_reason = "led_burn"
            feedback = "¡El LED se quemó! Faltó la resistencia."
            led_burning = True
            burn_timer = 0
            cables_on = True
            chiptune.play("burn")
            for c in componentes:
                if c.slot_key == "led":
                    c.img = SPR["led_burn"]
            return

        if pila_ok and res_ok and led_ok:
            state = "WIN"
            feedback = "¡Circuito correcto!"
            cables_on = True
            chiptune.play("level_complete")
            desbloquear_nivel(2)
            for c in componentes:
                if c.slot_key == "led":
                    c.img = SPR["led_on"]
            return

        feedback = "Faltan componentes por colocar."
        feedback_timer = 120
        chiptune.play("warn")

    # ---------- NIVEL 2 ----------
    elif nivel_actual == 2:
        pila_ok       = slot_ocupado("pila")
        led_ok        = slot_ocupado("led")
        r_led_ok      = slot_ocupado("r_led")
        r_base_ok     = slot_ocupado("r_base")
        transistor_ok = slot_ocupado("transistor")

        if pila_ok and led_ok and not transistor_ok:
            feedback = "Sin transistor no hay control."
            feedback_timer = 150
            chiptune.play("warn")
            return

        if pila_ok and led_ok and transistor_ok and not r_base_ok:
            state = "LOSE"
            failure_reason = "transistor_burn"
            feedback = "¡El transistor se quemó! Faltó la R de base."
            transistor_burning = True
            burn_timer = 0
            cables_on = True
            chiptune.play("burn")
            for c in componentes:
                if c.slot_key == "transistor":
                    c.img = SPR["transistor_burn"]
            return

        if pila_ok and led_ok and transistor_ok and r_base_ok and not r_led_ok:
            state = "LOSE"
            failure_reason = "led_burn"
            feedback = "¡El LED se quemó! Faltó la R del LED."
            led_burning = True
            burn_timer = 0
            cables_on = True
            chiptune.play("burn")
            for c in componentes:
                if c.slot_key == "led":
                    c.img = SPR["led_burn"]
            return

        if pila_ok and led_ok and r_led_ok and r_base_ok and transistor_ok:
            state = "WIN"
            feedback = "¡Circuito correcto! El transistor controla el LED."
            cables_on = True
            chiptune.play("level_complete")
            desbloquear_nivel(3)
            for c in componentes:
                if c.slot_key == "led":
                    c.img = SPR["led_on"]
                if c.slot_key == "transistor":
                    c.img = SPR["transistor_on"]
            return

        feedback = "Faltan componentes por colocar."
        feedback_timer = 120
        chiptune.play("warn")

    # ---------- NIVEL 3 ----------
    elif nivel_actual == 3:
        pila_ok = slot_ocupado("pila")
        led_ok  = slot_ocupado("led")
        r4_ok   = slot_ocupado("r4")
        q1_ok   = slot_ocupado("q1")
        q2_ok   = slot_ocupado("q2")
        r1_ok   = slot_ocupado("r1")
        r2_ok   = slot_ocupado("r2")
        r3_ok   = slot_ocupado("r3")
        c1_ok   = slot_ocupado("c1")
        c2_ok   = slot_ocupado("c2")

        if q1_ok and q2_ok and (not c1_ok or not c2_ok):
            feedback = "Sin capacitores no hay oscilación."
            feedback_timer = 150
            chiptune.play("warn")
            return

        if pila_ok and q1_ok and q2_ok and c1_ok and c2_ok and (not r1_ok or not r2_ok):
            state = "LOSE"
            failure_reason = "transistor_burn"
            feedback = "¡Los transistores se quemaron! Faltó R de base."
            transistor_burning = True
            burn_timer = 0
            cables_on = True
            chiptune.play("burn")
            for c in componentes:
                if c.slot_key in ("q1", "q2"):
                    c.img = SPR["transistor_burn"]
            return

        if (pila_ok and led_ok and q1_ok and q2_ok and c1_ok and c2_ok
            and r1_ok and r2_ok and r3_ok and not r4_ok):
            state = "LOSE"
            failure_reason = "led_burn"
            feedback = "¡El LED se quemó! Faltó R limitadora."
            led_burning = True
            burn_timer = 0
            cables_on = True
            chiptune.play("burn")
            for c in componentes:
                if c.slot_key == "led":
                    c.img = SPR["led_burn"]
            return

        if (pila_ok and led_ok and r4_ok and q1_ok and q2_ok
            and r1_ok and r2_ok and r3_ok and c1_ok and c2_ok):
            state = "WIN"
            feedback = "¡Circuito oscilando! El LED parpadea solo."
            cables_on = True
            chiptune.play("level_complete")
            desbloquear_nivel(4)
            return

        feedback = "Faltan componentes por colocar."
        feedback_timer = 120
        chiptune.play("warn")

# ============================================================
#   DIBUJO: MENÚ
# ============================================================
def wrap_text(texto, font, ancho_max):
    palabras = texto.split(" ")
    lineas = []
    actual = ""
    for p in palabras:
        prueba = actual + " " + p if actual else p
        if font.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas

def dibujar_menu(surf, t, mouse_pos):
    surf.fill(FONDO_APP)

    pygame.draw.rect(surf, AZUL_BARRA, (0, 0, WIDTH, TOP_BAR_H))
    pygame.draw.rect(surf, (40, 100, 170), (0, TOP_BAR_H - 2, WIDTH, 2))
    titulo = font_big.render("⚡ Electro River", True, BLANCO)
    surf.blit(titulo, (12, TOP_BAR_H // 2 - titulo.get_height() // 2))

    titulo2 = font_huge.render("SELECCIONA UN NIVEL", True, AMARILLO)
    surf.blit(titulo2, (WIDTH // 2 - titulo2.get_width() // 2, 80))

    sub = font_small.render("Completa cada nivel para desbloquear el siguiente",
                            True, (180, 180, 180))
    surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 130))

    card_w = 300
    card_h = 380
    gap = 40
    total_w = card_w * 3 + gap * 2
    start_x = WIDTH // 2 - total_w // 2
    card_y = 190

    for i, nivel in enumerate(NIVELES):
        x = start_x + i * (card_w + gap)
        rect = pygame.Rect(x, card_y, card_w, card_h)

        desbloqueado = nivel["id"] in progreso["desbloqueados"]
        hover = rect.collidepoint(mouse_pos) and desbloqueado

        if not desbloqueado:
            bg = TARJETA_LOCK
        elif hover:
            bg = TARJETA_HOVER
        else:
            bg = TARJETA_BG

        pygame.draw.rect(surf, (15, 18, 24), rect.move(4, 4), border_radius=10)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        borde_col = nivel["color"] if desbloqueado else PANEL_BORDE
        pygame.draw.rect(surf, borde_col, rect, 3, border_radius=10)

        num_col = nivel["color"] if desbloqueado else GRIS
        num_txt = font_huge.render(f"{nivel['id']:02d}", True, num_col)
        surf.blit(num_txt, (rect.centerx - num_txt.get_width() // 2, rect.top + 20))

        col_txt = BLANCO if desbloqueado else GRIS_CLARO
        tit = font_big.render(nivel["titulo"], True, col_txt)
        surf.blit(tit, (rect.centerx - tit.get_width() // 2, rect.top + 90))

        sub2 = font_small.render(nivel["subtitulo"], True, GRIS_CLARO)
        surf.blit(sub2, (rect.centerx - sub2.get_width() // 2, rect.top + 125))

        pygame.draw.line(surf, PANEL_BORDE,
                         (rect.left + 20, rect.top + 160),
                         (rect.right - 20, rect.top + 160), 1)

        desc_col = (200, 200, 200) if desbloqueado else (90, 90, 100)
        y_desc = rect.top + 180
        for linea in wrap_text(nivel["descripcion"], font_small, card_w - 40):
            txt = font_small.render(linea, True, desc_col)
            surf.blit(txt, (rect.left + 20, y_desc))
            y_desc += 20

        if not desbloqueado:
            lock = font_med.render("BLOQUEADO", True, GRIS)
            surf.blit(lock, (rect.centerx - lock.get_width() // 2, rect.bottom - 50))
        else:
            btn_col = nivel["color"] if hover else (100, 100, 110)
            btn = pygame.Rect(rect.left + 30, rect.bottom - 60, rect.w - 60, 40)
            pygame.draw.rect(surf, btn_col, btn, border_radius=6)
            btn_txt = font_med.render("JUGAR", True, NEGRO)
            surf.blit(btn_txt, (btn.centerx - btn_txt.get_width() // 2,
                                btn.centery - btn_txt.get_height() // 2))

    y = HEIGHT - STATUS_BAR_H
    pygame.draw.rect(surf, (25, 28, 35), (0, y, WIDTH, STATUS_BAR_H))
    pygame.draw.rect(surf, PANEL_BORDE, (0, y, WIDTH, 1))
    msg = font_small.render("Electro River — Beta v0.1.0  |  Haz clic en una tarjeta para jugar",
                            True, (180, 180, 180))
    surf.blit(msg, (12, y + STATUS_BAR_H // 2 - msg.get_height() // 2))

# ============================================================
#   DIBUJO: NIVEL
# ============================================================
BOTON_MENU = pygame.Rect(WIDTH - 100, 6, 90, TOP_BAR_H - 12)

def dibujar_barra_superior(surf):
    pygame.draw.rect(surf, AZUL_BARRA, (0, 0, WIDTH, TOP_BAR_H))
    pygame.draw.rect(surf, (40, 100, 170), (0, TOP_BAR_H - 2, WIDTH, 2))
    titulo = font_big.render(f"⚡ Electro River — Nivel {nivel_actual}", True, BLANCO)
    surf.blit(titulo, (12, TOP_BAR_H // 2 - titulo.get_height() // 2))

    pygame.draw.rect(surf, (40, 100, 170), BOTON_MENU, border_radius=4)
    pygame.draw.rect(surf, BLANCO, BOTON_MENU, 1, border_radius=4)
    txt = font_small.render("< MENU", True, BLANCO)
    surf.blit(txt, (BOTON_MENU.centerx - txt.get_width() // 2,
                    BOTON_MENU.centery - txt.get_height() // 2))

def dibujar_sidebar(surf):
    global scroll_y, scrollbar_thumb_rect, scrollbar_track_rect

    panel_rect = pygame.Rect(0, TOP_BAR_H, SIDEBAR_W, HEIGHT - TOP_BAR_H)
    pygame.draw.rect(surf, PANEL_LATERAL, panel_rect)
    pygame.draw.rect(surf, PANEL_BORDE, (SIDEBAR_W - 2, TOP_BAR_H, 2, HEIGHT - TOP_BAR_H))

    txt = font_med.render("COMPONENTES", True, BLANCO)
    surf.blit(txt, (SIDEBAR_W // 2 - txt.get_width() // 2, TOP_BAR_H + 10))
    pygame.draw.line(surf, PANEL_BORDE,
                     (15, TOP_BAR_H + 36), (SIDEBAR_W - 15, TOP_BAR_H + 36), 1)

    lista_top    = PALETA_PADDING_TOP
    lista_bottom = HEIGHT - STATUS_BAR_H - PALETA_PADDING_BOT
    lista_h      = lista_bottom - lista_top

    total_h = PALETA_TOTAL_ITEMS * PALETA_ITEM_H
    max_scroll = max(0, total_h - lista_h)

    scroll_y = max(0, min(scroll_y, max_scroll))

    clip_rect = pygame.Rect(0, lista_top, SIDEBAR_W - SCROLLBAR_W - 4, lista_h)
    clip_surf = surf.subsurface(clip_rect)

    mouse_pos = pygame.mouse.get_pos()
    en_paleta = [c for c in componentes if c.in_palette]
    en_paleta_indices = {c.palette_index for c in en_paleta}

    # Huecos punteados
    for idx in range(PALETA_TOTAL_ITEMS):
        if idx in en_paleta_indices:
            continue
        card_y = PALETA_PADDING_TOP + idx * PALETA_ITEM_H - scroll_y
        if card_y + PALETA_ITEM_H < lista_top or card_y > lista_bottom:
            continue
        local_y = card_y - lista_top
        card = pygame.Rect(8, local_y, SIDEBAR_W - SCROLLBAR_W - 20, PALETA_ITEM_H - 6)

        pygame.draw.rect(clip_surf, HUECO_BG, card, border_radius=8)
        pygame.draw.rect(clip_surf, HUECO_BORDE, card, 1, border_radius=8)
        for dx in (20, card.w - 20):
            for dy in (18, card.h - 18):
                pygame.draw.rect(clip_surf, HUECO_BORDE, (card.x + dx, card.y + dy, 3, 3))

    # Tarjetas con componentes
    for c in en_paleta:
        card_y = PALETA_PADDING_TOP + c.palette_index * PALETA_ITEM_H - scroll_y
        if card_y + PALETA_ITEM_H < lista_top or card_y > lista_bottom:
            continue

        local_y = card_y - lista_top
        card = pygame.Rect(8, local_y, SIDEBAR_W - SCROLLBAR_W - 20, PALETA_ITEM_H - 6)

        hover = card.collidepoint(mouse_pos[0], mouse_pos[1])
        bg = (58, 64, 78) if hover else (48, 52, 62)
        pygame.draw.rect(clip_surf, bg, card, border_radius=8)
        pygame.draw.rect(clip_surf, PANEL_BORDE, card, 1, border_radius=8)

        sx = card.x + 12
        sy = card.y + (card.h - c.h) // 2
        clip_surf.blit(c.img, (sx, sy))

        label = font_small.render(c.name, True, BLANCO)
        clip_surf.blit(label, (sx + c.w + 10,
                               card.y + card.h // 2 - label.get_height() // 2))

        c.card_rect = pygame.Rect(card.x, card.y + lista_top, card.w, card.h)
        c.x = sx
        c.y = sy + lista_top

    if max_scroll > 0:
        track = pygame.Rect(SIDEBAR_W - SCROLLBAR_W - 2, lista_top,
                            SCROLLBAR_W, lista_h)
        pygame.draw.rect(surf, (30, 33, 40), track, border_radius=5)
        pygame.draw.rect(surf, PANEL_BORDE, track, 1, border_radius=5)

        prop_visible = lista_h / total_h
        thumb_h = max(30, int(lista_h * prop_visible))
        thumb_y = lista_top + int((scroll_y / max_scroll) * (lista_h - thumb_h))
        thumb = pygame.Rect(track.x + 2, thumb_y, SCROLLBAR_W - 4, thumb_h)

        thumb_col = (150, 150, 180) if scrollbar_dragging else (105, 110, 135)
        pygame.draw.rect(surf, thumb_col, thumb, border_radius=4)

        scrollbar_thumb_rect = thumb
        scrollbar_track_rect = track
    else:
        scrollbar_thumb_rect = None
        scrollbar_track_rect = None

def dibujar_canvas(surf, t):
    pygame.draw.rect(surf, (15, 18, 24), canvas_rect.move(4, 4), border_radius=6)
    pygame.draw.rect(surf, AREA_TRABAJO, canvas_rect, border_radius=6)
    pygame.draw.rect(surf, AREA_BORDE, canvas_rect, 2, border_radius=6)

    for x in range(canvas_rect.left + 20, canvas_rect.right - 20, 20):
        pygame.draw.line(surf, GRILLA, (x, canvas_rect.top + 10),
                         (x, canvas_rect.bottom - 10), 1)
    for y in range(canvas_rect.top + 20, canvas_rect.bottom - 20, 20):
        pygame.draw.line(surf, GRILLA, (canvas_rect.left + 10, y),
                         (canvas_rect.right - 10, y), 1)

    txt = font_small.render(f"PROTOBOARD - Nivel {nivel_actual}", True, (160, 160, 155))
    surf.blit(txt, (canvas_rect.left + 12, canvas_rect.top + 8))

def dibujar_slots(surf, t):
    slot_img = SPR["slot"]
    for name, rect in slots.items():
        pygame.draw.rect(surf, (230, 230, 225), rect, border_radius=4)
        img = pygame.transform.scale(slot_img, (rect.w, rect.h))
        surf.blit(img, rect.topleft)
        ocupado = any(c.slot_key == name and c.placed_slot == name for c in componentes)
        if not ocupado:
            txt = font_tiny.render(f"[{name}]", True, (150, 150, 145))
            surf.blit(txt, (rect.centerx - txt.get_width() // 2,
                            rect.centery - txt.get_height() // 2))
        else:
            pulso = int(2 + 2 * math.sin(t * 0.005))
            pygame.draw.rect(surf, (100, 200 + pulso * 5, 130), rect, 2, border_radius=4)

def dibujar_cables(surf, t):
    global cable_anim
    if not cables_on:
        return
    cable_anim = min(1.0, cable_anim + 0.05)

    def cable(a, b, prog, color=NARANJA):
        ax, ay = a; bx, by = b
        mx = ax + (bx - ax) * prog
        my = ay + (by - ay) * prog
        pygame.draw.line(surf, NEGRO, a, (mx, my), 8)
        pygame.draw.line(surf, color, a, (mx, my), 4)

    if nivel_actual == 1:
        cable(slots["pila"].center, slots["resistencia"].center, cable_anim)
        cable(slots["resistencia"].center, slots["led"].center, cable_anim)

    elif nivel_actual == 2:
        p_pila  = slots["pila"].center
        p_rled  = slots["r_led"].center
        p_led   = slots["led"].center
        p_trans = slots["transistor"].center
        p_rbase = slots["r_base"].center

        cable(p_pila, p_rled, cable_anim)
        cable(p_rled, p_led, cable_anim)
        cable(p_rbase, p_trans, cable_anim, color=MORADO)

        mid_x = p_trans[0]
        mid_y = p_led[1] + 60
        pygame.draw.line(surf, NEGRO, p_trans, (mid_x, mid_y), 8)
        pygame.draw.line(surf, NARANJA, p_trans, (mid_x, mid_y), 4)
        pygame.draw.line(surf, NEGRO, (mid_x, mid_y), (p_led[0], mid_y), 8)
        pygame.draw.line(surf, NARANJA, (mid_x, mid_y), (p_led[0], mid_y), 4)
        pygame.draw.line(surf, NEGRO, (p_led[0], mid_y), p_led, 8)
        pygame.draw.line(surf, NARANJA, (p_led[0], mid_y), p_led, 4)

    elif nivel_actual == 3:
        cable(slots["pila"].center, slots["r4"].center, cable_anim)
        cable(slots["r4"].center,   slots["led"].center, cable_anim)
        cable(slots["r1"].center, slots["q1"].center, cable_anim, color=MORADO)
        cable(slots["r2"].center, slots["q2"].center, cable_anim, color=MORADO)
        cable(slots["c1"].center, slots["q2"].center, cable_anim, color=CIAN)
        cable(slots["c2"].center, slots["q1"].center, cable_anim, color=CIAN)
        cable(slots["r3"].center, slots["q2"].center, cable_anim)

def dibujar_efectos(surf, t):
    global led_bright, burn_timer

    led_comp = next((c for c in componentes
                     if c.slot_key == "led" and c.placed_slot == "led"), None)

    if nivel_actual == 3 and state == "WIN" and led_comp:
        fase = (t * 0.004) % 1.0
        encendido = fase < 0.5
        led_comp.img = SPR["led_on"] if encendido else SPR["led_off"]

        if encendido:
            r = slots["led"]
            cx, cy = r.centerx, r.centery
            glow = int(12 * abs(math.sin(t * 0.004 * math.pi)))
            for i in range(glow, 0, -3):
                col = (255, 80 + i * 5, 80)
                pygame.draw.circle(surf, col, (cx, cy), 10 + i)

        fase2 = (t * 0.004 + 0.5) % 1.0
        q1_on = fase2 < 0.5
        for c in componentes:
            if c.slot_key == "q1":
                c.img = SPR["transistor_on"] if q1_on else SPR["transistor_off"]
            if c.slot_key == "q2":
                c.img = SPR["transistor_on"] if not q1_on else SPR["transistor_off"]
        return

    if led_comp and state == "WIN":
        r = slots["led"]
        cx, cy = r.centerx, r.centery
        led_bright = min(1.0, led_bright + 0.05)
        glow = int(12 * led_bright)
        for i in range(glow, 0, -3):
            col = (255, 80 + i * 5, 80)
            pygame.draw.circle(surf, col, (cx, cy), 10 + i)

    if led_burning:
        burn_timer += 1
        r = slots["led"]
        cx, cy = r.centerx, r.centery
        chispa = math.sin(burn_timer * 0.5) * 4
        pygame.draw.circle(surf, (255, 100, 0), (int(cx + chispa), int(cy)), 8)
        pygame.draw.circle(surf, (255, 200, 0), (int(cx + chispa), int(cy - 2)), 5)

    if transistor_burning:
        targets = []
        if nivel_actual == 3:
            if "q1" in slots: targets.append(slots["q1"])
            if "q2" in slots: targets.append(slots["q2"])
        elif "transistor" in slots:
            targets.append(slots["transistor"])

        for target in targets:
            cx, cy = target.centerx, target.centery
            for i in range(5):
                offset = (burn_timer * 1.2 + i * 15) % 80
                alpha = max(0, 180 - offset * 2)
                humo = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(humo, (80, 80, 80, alpha), (10, 10), 8)
                surf.blit(humo, (cx - 10 + math.sin(offset * 0.1) * 6,
                                 cy - 20 - offset))

def dibujar_status_bar(surf):
    y = HEIGHT - STATUS_BAR_H
    pygame.draw.rect(surf, (25, 28, 35), (0, y, WIDTH, STATUS_BAR_H))
    pygame.draw.rect(surf, PANEL_BORDE, (0, y, WIDTH, 1))

    if state == "WIN":
        if nivel_actual == 3:
            msg = "Oscilador funcionando! Los capacitores alternan Q1 y Q2"
        elif nivel_actual == 2:
            msg = "Transistor polarizado correctamente!"
        else:
            msg = "Circuito correcto!"
        col = VERDE_OK
    elif state == "LOSE":
        msg = feedback
        col = ROJO
    else:
        msg = "Arrastra los componentes al area de trabajo"
        col = (180, 180, 180)

    txt = font_small.render(msg, True, col)
    surf.blit(txt, (12, y + STATUS_BAR_H // 2 - txt.get_height() // 2))

    hint = font_small.render("Pulsa [R] para reiniciar | [M] volver al menu",
                             True, (140, 140, 140))
    surf.blit(hint, (WIDTH - hint.get_width() - 12,
                     y + STATUS_BAR_H // 2 - hint.get_height() // 2))

# ============================================================
#   LOOP PRINCIPAL
# ============================================================
t = 0
_last_hover_menu = None

while True:
    dt = clock.tick(FPS)
    t += dt
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ---------- MENÚ ----------
        if escena == "MENU":
            if event.type == pygame.MOUSEMOTION:
                card_w, card_h, gap = 300, 380, 40
                total_w = card_w * 3 + gap * 2
                start_x = WIDTH // 2 - total_w // 2
                card_y = 190
                hover_actual = None
                for i, nivel in enumerate(NIVELES):
                    x = start_x + i * (card_w + gap)
                    rect = pygame.Rect(x, card_y, card_w, card_h)
                    if rect.collidepoint(event.pos) and nivel["id"] in progreso["desbloqueados"]:
                        hover_actual = nivel["id"]
                        break
                if hover_actual != _last_hover_menu:
                    _last_hover_menu = hover_actual
                    if hover_actual is not None:
                        chiptune.play("hover")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                card_w, card_h, gap = 300, 380, 40
                total_w = card_w * 3 + gap * 2
                start_x = WIDTH // 2 - total_w // 2
                card_y = 190
                for i, nivel in enumerate(NIVELES):
                    x = start_x + i * (card_w + gap)
                    rect = pygame.Rect(x, card_y, card_w, card_h)
                    if rect.collidepoint(event.pos):
                        if nivel["id"] in progreso["desbloqueados"]:
                            chiptune.play("click")
                            if nivel["id"] in (1, 2, 3):
                                cargar_nivel(nivel["id"])
                        else:
                            chiptune.play("locked")
                        break

        # ---------- PLAY ----------
        elif escena == "PLAY":

            if event.type == pygame.MOUSEWHEEL:
                if mouse_pos[0] < SIDEBAR_W:
                    scroll_vel -= event.y * 15

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if scrollbar_thumb_rect and scrollbar_thumb_rect.collidepoint(event.pos):
                    scrollbar_dragging = True
                    scrollbar_drag_offset = event.pos[1] - scrollbar_thumb_rect.y
                    continue
                elif scrollbar_track_rect and scrollbar_track_rect.collidepoint(event.pos):
                    total_h = PALETA_TOTAL_ITEMS * PALETA_ITEM_H
                    lista_h = scrollbar_track_rect.h
                    max_scroll = max(0, total_h - lista_h)
                    rel = (event.pos[1] - scrollbar_track_rect.y) / lista_h
                    scroll_y = rel * max_scroll
                    scroll_y = max(0, min(scroll_y, max_scroll))
                    scroll_vel = 0
                    continue

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                scrollbar_dragging = False

            if event.type == pygame.MOUSEMOTION and scrollbar_dragging:
                if scrollbar_track_rect and scrollbar_thumb_rect:
                    track = scrollbar_track_rect
                    thumb_h = scrollbar_thumb_rect.h
                    total_h = PALETA_TOTAL_ITEMS * PALETA_ITEM_H
                    max_scroll = max(0, total_h - track.h)
                    rel_y = event.pos[1] - track.y - scrollbar_drag_offset
                    max_thumb_y = track.h - thumb_h
                    if max_thumb_y > 0:
                        prop = max(0, min(1, rel_y / max_thumb_y))
                        scroll_y = prop * max_scroll

            if state == "PLAY":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if BOTON_MENU.collidepoint(event.pos):
                        chiptune.play("click")
                        escena = "MENU"
                        continue
                    for c in reversed(componentes):
                        if c.in_palette:
                            if c.card_rect.collidepoint(event.pos):
                                c.dragging = True
                                c.offset_x = c.x - event.pos[0]
                                c.offset_y = c.y - event.pos[1]
                                c.in_palette = False
                                componentes.remove(c)
                                componentes.append(c)
                                chiptune.play("pickup")
                                break
                        else:
                            if c.rect().collidepoint(event.pos):
                                c.dragging = True
                                c.offset_x = c.x - event.pos[0]
                                c.offset_y = c.y - event.pos[1]
                                componentes.remove(c)
                                componentes.append(c)
                                chiptune.play("pickup")
                                break

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for c in componentes:
                        if c.dragging:
                            c.dragging = False
                            colocado = False
                            for name, rect in slots.items():
                                if rect.colliderect(c.rect()) and c.slot_key == name:
                                    c.x = rect.x + (rect.w - c.w) // 2
                                    c.y = rect.y + (rect.h - c.h) // 2
                                    c.placed_slot = name
                                    colocado = True
                                    chiptune.play("place")
                                    break
                            if not colocado:
                                c.x = c.palette_x
                                c.y = c.palette_y
                                c.in_palette = True
                                c.placed_slot = None
                                chiptune.play("drop")
                            validar_circuito()

                elif event.type == pygame.MOUSEMOTION:
                    for c in componentes:
                        if c.dragging:
                            c.x = event.pos[0] + c.offset_x
                            c.y = event.pos[1] + c.offset_y

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    chiptune.play("reset")
                    cargar_nivel(nivel_actual)
                elif event.key == pygame.K_m:
                    chiptune.play("click")
                    escena = "MENU"

    # Inercia del scroll
    if escena == "PLAY" and not scrollbar_dragging:
        scroll_y += scroll_vel
        scroll_vel *= 0.85
        if abs(scroll_vel) < 0.1:
            scroll_vel = 0
        total_h = PALETA_TOTAL_ITEMS * PALETA_ITEM_H
        lista_top = PALETA_PADDING_TOP
        lista_bottom = HEIGHT - STATUS_BAR_H - PALETA_PADDING_BOT
        lista_h = lista_bottom - lista_top
        max_scroll = max(0, total_h - lista_h)
        scroll_y = max(0, min(scroll_y, max_scroll))

    # ============ RENDER ============
    if escena == "MENU":
        dibujar_menu(screen, t, mouse_pos)
    else:
        screen.fill(FONDO_APP)
        dibujar_canvas(screen, t)
        dibujar_slots(screen, t)
        dibujar_cables(screen, t)
        dibujar_efectos(screen, t)
        for c in componentes:
            if not c.in_palette:
                c.draw(screen)
        dibujar_sidebar(screen)
        dibujar_barra_superior(screen)
        dibujar_status_bar(screen)

    pygame.display.flip()