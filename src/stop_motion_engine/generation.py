from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
from pathlib import Path
import urllib.request
from typing import Any

from PIL import Image, ImageDraw

from .lab_models import IdentityLock


@dataclass
class GenerationResult:
    ok: bool
    path: str | None
    adapter: str
    message: str


class FrameGenerator(ABC):
    @abstractmethod
    def generate(self, frame_spec: dict[str, Any], identity: IdentityLock, output_path: Path) -> GenerationResult:
        raise NotImplementedError


class MockFrameGenerator(FrameGenerator):
    """Diagnostic only. Never pretends to be identity retargeting."""
    def generate(self, frame_spec: dict[str, Any], identity: IdentityLock, output_path: Path) -> GenerationResult:
        source = Path(frame_spec["source_frame"])
        img = Image.open(source).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size
        draw.rectangle((0, max(0, h-82), w, h), fill=(0, 0, 0))
        draw.multiline_text(
            (12, h-72),
            "MOCK GENERATOR — STRUCTURAL TEST ONLY\nNo identity retargeting performed",
            fill="white", spacing=4,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        return GenerationResult(True, str(output_path), "mock", "Structural placeholder generated; this is not an identity-retargeted result.")


class ComfyFrameGenerator(FrameGenerator):
    """Queue a pre-authored ComfyUI workflow through /prompt."""
    def __init__(self, base_url: str | None = None, workflow_path: str | None = None):
        self.base_url = (base_url or os.getenv("COMFYUI_URL") or "http://127.0.0.1:8188").rstrip("/")
        self.workflow_path = workflow_path or os.getenv("COMFY_WORKFLOW_JSON")

    def available(self) -> bool:
        return bool(self.workflow_path and Path(self.workflow_path).exists())

    def generate(self, frame_spec: dict[str, Any], identity: IdentityLock, output_path: Path) -> GenerationResult:
        if not self.available():
            return GenerationResult(False, None, "comfy", "COMFY_WORKFLOW_JSON is missing or unreadable.")
        raw = Path(self.workflow_path).read_text()
        tokens = {
            "__SOURCE_FRAME__": frame_spec["source_frame"],
            "__IDENTITY_FACE__": identity.face_reference or "",
            "__IDENTITY_BODY__": identity.body_reference or "",
            "__OUTPUT_PATH__": str(output_path),
            "__FRAME_SPEC_JSON__": json.dumps(frame_spec),
        }
        for key, value in tokens.items():
            raw = raw.replace(key, value)
        workflow = json.loads(raw)
        body = json.dumps({"prompt": workflow, "client_id": "stop-motion-lab"}).encode()
        req = urllib.request.Request(self.base_url + "/prompt", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode())
            return GenerationResult(True, None, "comfy", f"Queued ComfyUI prompt {payload.get('prompt_id')}; output collection remains workflow-specific.")
        except Exception as exc:
            return GenerationResult(False, None, "comfy", f"ComfyUI request failed: {exc}")


class RemoteFrameGenerator(FrameGenerator):
    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint or os.getenv("REMOTE_GENERATOR_URL")

    def generate(self, frame_spec: dict[str, Any], identity: IdentityLock, output_path: Path) -> GenerationResult:
        if not self.endpoint:
            return GenerationResult(False, None, "remote", "REMOTE_GENERATOR_URL is not configured.")
        payload = json.dumps({"frame_spec": frame_spec, "identity": identity.to_dict()}).encode()
        req = urllib.request.Request(self.endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                body = response.read()
                ctype = response.headers.get("Content-Type", "")
            if ctype.startswith("image/"):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(body)
                return GenerationResult(True, str(output_path), "remote", "Remote generator returned an image.")
            return GenerationResult(False, None, "remote", "Remote generator did not return image bytes.")
        except Exception as exc:
            return GenerationResult(False, None, "remote", f"Remote generator failed: {exc}")


class LocalFrameGenerator(FrameGenerator):
    def generate(self, frame_spec: dict[str, Any], identity: IdentityLock, output_path: Path) -> GenerationResult:
        return GenerationResult(False, None, "local", "No local diffusion backend is installed. Configure ComfyUI or REMOTE_GENERATOR_URL.")


def get_generator(name: str) -> FrameGenerator:
    key = (name or "mock").lower()
    if key == "comfy":
        return ComfyFrameGenerator()
    if key == "remote":
        return RemoteFrameGenerator()
    if key == "local":
        return LocalFrameGenerator()
    return MockFrameGenerator()
