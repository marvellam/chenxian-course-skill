"""Font loading and framed-heading metrics shared by both export paths."""
from pathlib import Path
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
HEADING_FONT = 'SourceHanSerifCN-Bold-2.otf'
HEADING_SIZE = 52
HEADING_LEADING = 52
HEADING_OFFSET = 11.5


def load_font(name, size):
    candidates = [ROOT / 'fonts' / name,
                  Path.home() / 'AppData/Local/Microsoft/Windows/Fonts' / name]
    for path in candidates:
        if path.is_file():
            # The bundled Source Han Sans collections store Simplified Chinese
            # at face 2. The default face 0 uses different regional glyphs.
            return ImageFont.truetype(str(path), size,
                                      index=2 if path.suffix.lower() == '.ttc' else 0)
    raise FileNotFoundError(
        f"Font '{name}' not found in package fonts/ or system fonts. "
        "Install fonts from the fonts/ directory."
    )


def line_baseline(font, top, leading):
    ascent, descent = font.getmetrics()
    return top + (leading - ascent - descent) / 2 + ascent
