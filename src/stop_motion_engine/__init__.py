"""Stop Motion Engine — compose discrete frames, reverse-engineer motion cells."""

from .cells import Cell, detect_cells, motion_energy
from .compose import compose_from_frames, write_onion_sheet
from .reverse import reverse_video
from .score import MotionScore, write_score

__version__ = "0.1.0"
__all__ = [
    "Cell",
    "MotionScore",
    "compose_from_frames",
    "detect_cells",
    "motion_energy",
    "reverse_video",
    "write_onion_sheet",
    "write_score",
]
