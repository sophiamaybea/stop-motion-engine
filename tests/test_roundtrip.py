from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stop_motion_engine.demo import write_synthetic
from stop_motion_engine.cells import detect_cells
from stop_motion_engine.reverse import load_frames


def test_synthetic_cells(tmp_path: Path) -> None:
    dest = write_synthetic(tmp_path / "stills", shots=12, hold=2)
    frames = load_frames(sorted(dest.glob("*.png")))
    cells, energies, _ = detect_cells(frames, fps=12.0)
    assert len(frames) == 24
    assert len(energies) == 23
    assert 10 <= len(cells) <= 13, f"got {len(cells)} cells"


if __name__ == "__main__":
    import tempfile
    test_synthetic_cells(Path(tempfile.mkdtemp()))
    print("ok")
