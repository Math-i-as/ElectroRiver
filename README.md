# ⚡ Electro River

Juego educativo de electrónica en pixel art. Aprende a armar circuitos
con pila, resistencias, LEDs, transistores y capacitores.

![Estado](https://img.shields.io/badge/estado-beta-yellow)
![Licencia](https://img.shields.io/badge/licencia-MIT-green)

## 🎮 Cómo jugar

- **Arrastra** los componentes desde el sidebar izquierdo al área de trabajo
- **Suéltalos** en su slot correspondiente (marcado con `[nombre]`)
- Si el circuito es correcto → el LED enciende ✨
- Si está mal → 💥 ¡se quema! Inténtalo de nuevo

### Controles

| Tecla | Acción |
|-------|--------|
| 🖱️ Clic + arrastrar | Mover componentes |
| 🖱️ Rueda del mouse | Scroll en el sidebar |
| `R` | Reiniciar el nivel |
| `M` | Volver al menú |

## 📚 Niveles

1. **El LED** — Pila + resistencia + LED
2. **Transistor NPN** — Control de corriente con transistor
3. **Oscilador Astable** — LED parpadeante con 2 transistores y 2 capacitores

## 🚀 Instalación

### Opción 1: Descargar el .exe (Windows)

Descarga `ElectroRiver.exe` desde [Releases](../../releases) y ejecútalo.
No requiere instalar nada.

### Opción 2: Desde código fuente

```bash
git clone https://github.com/tu-usuario/electro-river.git
cd electro-river
pip install -r requirements.txt
python main.py
```

## 🛠️ Compilar a .exe

```bash
build.bat
```

Genera `dist/ElectroRiver.exe` listo para distribuir.

## 📁 Estructura

```
electro-river/
├── main.py           ← código principal
├── sound.py          ← sonido chiptune procedural
├── assets/           ← sprites PNG
├── build.bat         ← script de compilación
├── requirements.txt  ← dependencias
├── LICENSE           ← licencia MIT
└── README.md         ← este archivo
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

- 🐛 Reporta bugs en [Issues](../../issues)
- 💡 Sugiere niveles nuevos
- 🎨 Mejora los sprites
- 📖 Mejora la documentación

## 📜 Licencia

MIT — libre para usar, modificar y distribuir. Ver [LICENSE](LICENSE).

## 🙏 Créditos

- Motor: [pygame-ce](https://pyga.me/)
- Sonido: numpy + pygame.mixer
- Creado por Math-i-as a HuMAN
