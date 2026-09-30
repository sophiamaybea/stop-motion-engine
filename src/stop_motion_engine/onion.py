"""Onion-skin stills.

A cell is a hold punctuated by a tick. Onion skin is how you see the tick
without interpolating: the previous picture ghosts through the current one.

This module never invents frames. It only composites stills that already exist.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

CYAN = (80, 220, 255)
MAGENTA = (255, 80, 200)
LABEL_BG = (12, 12, 14)
SHEET_BG = (12, 12, 14)


def list_frames(folder: Path) -> list[Path]:
    files = [p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTS]
    return sorted(files, key=lambda p: p.name)


def _font(size: int):
    for name in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def _fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    if img.size == size:
        return img
    return img.resize(size, Image.Resampling.LANCZOS)


def _tint(img: Image.Image, color: tuple[int, int, int], amount: float) -> Image.Image:
    rgb = img.convert("RGB")
    overlay = Image.new("RGB", rgb.size, color)
    return Image.blend(rgb, overlay, amount)


def _composite_ghosts(
    current: Image.Image,
    previous: list[Image.Image],
    alphas: list[float],
    tint_previous: bool = True,
) -> Image.Image:
    w, h = current.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    n = min(len(previous), len(alphas))
    for img, alpha in zip(previous[-n:], alphas[-n:]):
        layer = _fit(img.convert("RGB"), (w, h))
        if tint_previous:
            layer = _tint(layer, CYAN, 0.28)
        rgba = layer.convert("RGBA")
        rgba.putalpha(max(0, min(255, int(255 * alpha))))
        canvas = Image.alpha_composite(canvas, rgba)
    live = _fit(current.convert("RGB"), (w, h)).convert("RGBA")
    canvas = Image.alpha_composite(canvas, live)
    return canvas.convert("RGB")


def write_onion_sheet(
    frames_dir: Path,
    output: Path,
    previous_alpha: float = 0.35,
    columns: int = 6,
    ghosts: int = 1,
    cell_width: int | None = None,
    labels: list[str] | None = None,
) -> Path:
    paths = list_frames(frames_dir)
    if not paths:
        raise FileNotFoundError(f"no images in {frames_dir}")
    images = [Image.open(p).convert("RGB") for p in paths]
    w0, h0 = images[0].size
    if cell_width is not None and cell_width < w0:
        scale = cell_width / w0
        size = (cell_width, max(1, int(h0 * scale)))
        images = [_fit(im, size) for im in images]
    else:
        size = (w0, h0)

    onions: list[Image.Image] = []
    for i, img in enumerate(images):
        if i == 0 or ghosts <= 0:
            onions.append(_fit(img, size))
            continue
        start = max(0, i - ghosts)
        prev = images[start:i]
        n = len(prev)
        alphas = [previous_alpha * ((k + 1) / n) * 0.85 for k in range(n)]
        onions.append(_composite_ghosts(img, prev, alphas))

    if labels:
        labeled = []
        font = _font(max(14, size[1] // 28))
        for i, frame in enumerate(onions):
            canvas = frame.copy()
            draw = ImageDraw.Draw(canvas)
            text = labels[i] if i < len(labels) else str(i)
            pad = 6
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.rectangle((0, 0, tw + pad * 2, th + pad * 2), fill=LABEL_BG)
            draw.text((pad, pad), text, fill=(240, 240, 236), font=font)
            labeled.append(canvas)
        onions = labeled

    rows = (len(onions) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * size[0], rows * size[1]), SHEET_BG)
    for i, frame in enumerate(onions):
        r, c = divmod(i, columns)
        sheet.paste(_fit(frame, size), (c * size[0], r * size[1]))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=88)
    return output


def write_stack_onion(
    frames_dir: Path,
    output: Path,
    max_frames: int | None = None,
    base_alpha: float = 0.18,
) -> Path:
    paths = list_frames(frames_dir)
    if not paths:
        raise FileNotFoundError(f"no images in {frames_dir}")
    if max_frames is not None:
        paths = paths[:max_frames]
    images = [Image.open(p).convert("RGB") for p in paths]
    last = images[-1]
    prev = images[:-1]
    n = max(1, len(prev))
    alphas = [base_alpha + (0.45 - base_alpha) * ((k + 1) / n) for k in range(n)]
    stacked = _composite_ghosts(last, prev, alphas)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    stacked.save(output, quality=90)
    return output


def write_pair_onion(
    source_dir: Path,
    target_dir: Path,
    output: Path,
    columns: int = 7,
    cell_width: int = 240,
    source_alpha: float = 0.40,
    labels: list[str] | None = None,
) -> Path:
    sources = list_frames(source_dir)
    if not sources:
        raise FileNotFoundError(f"no images in {source_dir}")
    targets_by_stem = {}
    target_dir = Path(target_dir)
    if target_dir.exists():
        for p in list_frames(target_dir):
            targets_by_stem[p.stem] = p
            if p.stem.startswith("beat_"):
                targets_by_stem[p.stem[:7]] = p

    cells: list[Image.Image] = []
    font = _font(16)
    size = (cell_width, cell_width)
    for i, src_path in enumerate(sources):
        src = Image.open(src_path).convert("RGB")
        scale = cell_width / src.size[0]
        size = (cell_width, max(1, int(src.size[1] * scale)))
        src = _fit(src, size)
        key = src_path.stem[:7] if src_path.stem.startswith("beat_") else src_path.stem
        tgt_path = targets_by_stem.get(key) or targets_by_stem.get(src_path.stem)
        if tgt_path is None:
            cell = src.copy()
            status = "SOURCE ONLY"
        else:
            tgt = _fit(Image.open(tgt_path).convert("RGB"), size)
            ghost = _tint(src, MAGENTA, 0.35).convert("RGBA")
            ghost.putalpha(int(255 * source_alpha))
            cell = Image.alpha_composite(tgt.convert("RGBA"), ghost).convert("RGB")
            status = "SRC + RECON"
        draw = ImageDraw.Draw(cell)
        text = labels[i] if labels and i < len(labels) else f"{i:02d} {status}"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rectangle((0, 0, tw + 10, th + 10), fill=LABEL_BG)
        draw.text((5, 4), text, fill=(240, 240, 236), font=font)
        cells.append(cell)

    rows = (len(cells) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * size[0], rows * size[1]), SHEET_BG)
    for i, frame in enumerate(cells):
        r, c = divmod(i, columns)
        sheet.paste(frame, (c * size[0], r * size[1]))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=88)
    return output


def write_onion_sequence(
    frames_dir: Path,
    output_dir: Path,
    ghosts: int = 2,
    previous_alpha: float = 0.35,
) -> list[Path]:
    paths = list_frames(frames_dir)
    if not paths:
        raise FileNotFoundError(f"no images in {frames_dir}")
    images = [Image.open(p).convert("RGB") for p in paths]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, img in enumerate(images):
        dest = out_dir / f"{paths[i].stem}_onion.png"
        if i == 0 or ghosts <= 0:
            img.save(dest)
        else:
            prev = images[max(0, i - ghosts) : i]
            n = len(prev)
            alphas = [previous_alpha * ((k + 1) / n) for k in range(n)]
            _composite_ghosts(img, prev, alphas).save(dest)
        written.append(dest)
    return written
