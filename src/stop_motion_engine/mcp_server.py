"""MCP façade over the local performance-film engine."""
from __future__ import annotations

import json
from pathlib import Path


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install the MCP extra: pip install -e '.[mcp]'") from exc

    from .adapters import ComfyUIClient, assemble_frames
    from .analysis import analyse_performance
    from .doctor import doctor
    from .project import init_project

    mcp = FastMCP("performance-film")

    @mcp.tool()
    def environment_status() -> str:
        """Check local dependencies and configured rendering backends."""
        return json.dumps(doctor(), indent=2)

    @mcp.tool()
    def create_project(project_dir: str, source: str = "") -> str:
        """Create the canonical editable project layout."""
        return str(init_project(Path(project_dir), source or None))

    @mcp.tool()
    def analyse_video(source: str, project_dir: str, face_model: str = "", pose_json_dir: str = "") -> str:
        """Extract motion, optional facial performance, optional pose data, and adaptive keyframes."""
        result = analyse_performance(
            Path(source), Path(project_dir),
            face_model=Path(face_model) if face_model else None,
            pose_json_dir=Path(pose_json_dir) if pose_json_dir else None,
        )
        return json.dumps({k: str(v) for k, v in result.items()}, indent=2)

    @mcp.tool()
    def assemble_stopmotion(frames_dir: str, output: str, fps: float = 12.0) -> str:
        """Assemble accepted PNGs into a stop-motion MP4."""
        return str(assemble_frames(Path(frames_dir), Path(output), fps=fps))

    @mcp.tool()
    def queue_comfy_workflow(workflow_json: str, base_url: str = "http://127.0.0.1:8188") -> str:
        """Queue an already-resolved local ComfyUI API workflow."""
        workflow = json.loads(Path(workflow_json).read_text())
        prompt_id = ComfyUIClient(base_url).queue_workflow(workflow)
        return json.dumps({"prompt_id": prompt_id})

    return mcp


def run() -> None:
    build_server().run()
