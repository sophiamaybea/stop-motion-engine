from stop_motion_engine.keyframes import FrameSignal, select_keyframes
from stop_motion_engine.retarget import SkeletonProfile, retarget_named_pose


def test_expression_peak_is_kept():
    signals = [FrameSignal(frame=i, motion=0.1) for i in range(20)]
    signals[9] = FrameSignal(frame=9, motion=0.1, expression_delta=10.0)
    selected, _ = select_keyframes(signals, fps=20)
    assert 9 in selected
    assert selected[0] == 0 and selected[-1] == 19


def test_max_gap_inserts_frames():
    signals = [FrameSignal(frame=i) for i in range(60)]
    selected, _ = select_keyframes(signals, fps=30, max_gap_s=0.5)
    assert max(b - a for a, b in zip(selected, selected[1:])) <= 15


def test_retarget_preserves_direction_changes_length():
    source = {
        "neck": {"x": 0.0, "y": 0.0},
        "right_shoulder": {"x": 1.0, "y": 0.0},
        "right_elbow": {"x": 2.0, "y": 0.0},
        "right_wrist": {"x": 3.0, "y": 0.0},
    }
    profile = SkeletonProfile({
        "neck>right_shoulder": 2.0,
        "right_shoulder>right_elbow": 3.0,
        "right_elbow>right_wrist": 4.0,
    })
    out = retarget_named_pose(source, profile, torso_scale=1.0)
    assert out["right_shoulder"]["x"] == 2.0
    assert out["right_elbow"]["x"] == 5.0
    assert out["right_wrist"]["x"] == 9.0
