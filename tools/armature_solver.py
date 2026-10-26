#!/usr/bin/env python3
"""Viseme → anatomical armature transforms with safety bounds."""
from __future__ import annotations

import math
from typing import Dict, List, Sequence


class ArmatureVisemeSolver:
    def __init__(self) -> None:
        self.min_pupil_spacing_mm = 8.5
        self.max_neck_yaw_rad = math.radians(45.0)
        self.max_jaw_open_mm = 25.0
        self.head_root_xyz = [0.0, 1750.0, 0.0]
        self.left_eye_xyz = [-32.0, 1785.0, 45.0]
        self.right_eye_xyz = [32.0, 1785.0, 45.0]

    def solve_viseme_mechanics(self, phoneme_type: str, intensity: float = 1.0) -> Dict[str, float]:
        """Map viseme token (A/E/O/U or ah/ee/oo/oh) to jaw / mouth / pucker."""
        key = (phoneme_type or "A").upper()
        # Normalize phoneme labels from SongForge MEG
        alias = {"AH": "A", "EE": "E", "EH": "E", "OH": "O", "OO": "U", "U": "U"}
        key = alias.get(key, key if key in ("A", "E", "O", "U") else "A")
        intensity = max(0.0, min(1.0, float(intensity)))

        jaw_open = 0.0
        mouth_width_scale = 1.0
        lip_pucker = 0.0

        if key == "A":
            jaw_open = self.max_jaw_open_mm * 0.85 * intensity
            mouth_width_scale = 1.1
        elif key == "E":
            jaw_open = self.max_jaw_open_mm * 0.3 * intensity
            mouth_width_scale = 1.25
        elif key == "O":
            jaw_open = self.max_jaw_open_mm * 0.6 * intensity
            mouth_width_scale = 0.75
            lip_pucker = 0.8 * intensity
        elif key == "U":
            jaw_open = self.max_jaw_open_mm * 0.4 * intensity
            mouth_width_scale = 0.65
            lip_pucker = 0.95 * intensity

        return {
            "viseme": key,
            "jaw_translation_y_mm": round(-jaw_open, 4),
            "mouth_scale_x": round(mouth_width_scale, 4),
            "lip_pucker_z_factor": round(lip_pucker, 4),
        }

    def evaluate_pupil_safety_clearance(
        self,
        left_eye_offset: Sequence[float],
        right_eye_offset: Sequence[float],
    ) -> float:
        current_left = [
            self.left_eye_xyz[0] + left_eye_offset[0],
            self.left_eye_xyz[1] + left_eye_offset[1],
            self.left_eye_xyz[2] + left_eye_offset[2],
        ]
        current_right = [
            self.right_eye_xyz[0] + right_eye_offset[0],
            self.right_eye_xyz[1] + right_eye_offset[1],
            self.right_eye_xyz[2] + right_eye_offset[2],
        ]
        distance = math.sqrt(
            (current_right[0] - current_left[0]) ** 2
            + (current_right[1] - current_left[1]) ** 2
            + (current_right[2] - current_left[2]) ** 2
        )
        if distance < self.min_pupil_spacing_mm:
            raise ValueError(
                f"Armature Safety Violation: pupil spacing {distance:.4f}mm "
                f"< min {self.min_pupil_spacing_mm}mm"
            )
        return round(distance, 4)

    def solve_meg_event(self, event: dict) -> Dict:
        """Accept SECTION or PHONEME events from SongForge MEG v1/v2."""
        et = event.get("type") or event.get("event_type") or ""
        if et == "PHONEME":
            viseme = event.get("viseme") or event.get("phoneme") or "A"
            mech = self.solve_viseme_mechanics(str(viseme), intensity=0.9)
            return {
                "kind": "phoneme",
                "tick": event.get("tick"),
                "sample": event.get("sample"),
                "word": event.get("word"),
                "role": event.get("role"),
                "transforms": mech,
            }
        if "SECTION" in et or et == "VOCAL_REGION":
            layout = []
            vm = event.get("viseme_map")
            if isinstance(vm, dict) and "layout" in vm:
                layout = list(vm["layout"])
            return {
                "kind": "section",
                "name": event.get("name"),
                "role": event.get("role") or event.get("vocal_role"),
                "start_sample": event.get("start_sample"),
                "end_sample": event.get("end_sample"),
                "layout": layout,
                "transforms": [self.solve_viseme_mechanics(v) for v in layout],
            }
        return {"kind": "other", "raw_type": et}
