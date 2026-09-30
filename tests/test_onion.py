from pathlib import Path
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stop_motion_engine.onion import write_onion_sequence, write_onion_sheet, write_stack_onion


def _stills(folder: Path, n: int = 6, size=(80, 120)) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        img = Image.new("RGB", size, (20 + i * 20, 30, 180 - i * 15))
        img.save(folder / f"beat_{i:02d}.png")
    return folder


def test_onion_grid(tmp_path: Path) -> None:
    src = _stills(tmp_path / "beats")
    out = tmp_path / "onion.jpg"
    write_onion_sheet(src, out, columns=3, ghosts=2, cell_width=80, labels=["b0", "b1"])
    assert out.exists()


def test_onion_stack_and_sequence(tmp_path: Path) -> None:
    src = _stills(tmp_path / "beats", n=4)
    assert write_stack_onion(src, tmp_path / "stack.jpg").exists()
    assert len(write_onion_sequence(src, tmp_path / "seq", ghosts=2)) == 4
