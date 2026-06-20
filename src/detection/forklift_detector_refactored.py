"""
Forklift Overload Detector
Detects forklifts (YOLO truck class) and estimates load stack count.

Severity: CRITICAL
Behavior: forklift_overload

Uses vertical projection peak counting on load-colored pixels in the fork ROI.
Overload threshold is read from validated_rules.json (forklift_overload.threshold).

Validation-only environment variable (disabled by default):
    FORKLIFT_SIMULATE_LOAD=<int>
    When set, overrides load estimation for overload-path testing.
    Must NOT be set during normal production runs or demos.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import cv2
import math
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from src.detection.base_detector import BaseDetector, VisualizationData
from src.core.config_manager import ConfigManager
from src.severity.event_factory import EventFactory


class ForkliftOverloadDetector(BaseDetector):
    """
    Detects forklift overload violations via load stack estimation.

    Forklift proxy: COCO class 7 (truck). Static machinery false positives are
    suppressed with a short motion-history check on bbox center displacement.
    """

    COCO_TRUCK_CLASS = 7
    DEFAULT_OVERLOAD_THRESHOLD = 3

    MIN_CONFIDENCE = 0.45
    MIN_BBOX_AREA = 12000
    MOTION_HISTORY_LEN = 8
    MIN_MOTION_PIXELS = 20

    LOAD_HISTORY_LEN = 5
    OVERLOAD_CONFIRM_FRAMES = 3
    COOLDOWN_SECONDS = 5

    # Load ROI: upper portion of truck bbox where forks/load appear
    LOAD_TOP_RATIO = 0.05
    LOAD_BOTTOM_RATIO = 0.58
    LOAD_WIDTH_MARGIN = 0.12

    # Orange standardized blocks / facility totes (HSV)
    LOWER_LOAD = np.array([5, 90, 90])
    UPPER_LOAD = np.array([28, 255, 255])

    MIN_LOAD_PIXEL_RATIO = 0.04
    MIN_ROW_WIDTH_RATIO = 0.22
    MIN_BAND_HEIGHT_RATIO = 0.08
    MERGE_GAP_RATIO = 0.07

    def __init__(self, config_manager: ConfigManager):
        super().__init__("Forklift Overload Detector")
        self.config = config_manager
        self.rule = self.config.get_rule("forklift_overload")
        self.overload_threshold = self._resolve_threshold()
        self.last_violation_time = 0.0
        self._position_history: List[Tuple[int, int]] = []
        self._load_history: List[int] = []
        self._overload_streak = 0
        self._current_viz = VisualizationData()
        self._last_forklift_detected = False
        self._last_estimated_load = 0
        self._simulate_load_count: Optional[int] = self._read_simulate_env()

    @staticmethod
    def _read_simulate_env() -> Optional[int]:
        """
        Read optional validation override from FORKLIFT_SIMULATE_LOAD.

        Returns None when unset (default) so normal detection is unaffected.
        Only used to test overload event generation without modifying footage.
        """
        raw = os.environ.get("FORKLIFT_SIMULATE_LOAD")
        if raw is None or raw.strip() == "":
            return None
        try:
            return max(0, int(raw))
        except ValueError:
            return None

    def _resolve_threshold(self) -> int:
        if self.rule and self.rule.threshold is not None:
            return int(self.rule.threshold)
        return self.DEFAULT_OVERLOAD_THRESHOLD

    @staticmethod
    def evaluate_overload_decision(
        estimated_count: int,
        threshold: int,
        consecutive_over_frames: int,
        confirm_frames: int = OVERLOAD_CONFIRM_FRAMES,
    ) -> bool:
        """
        Deterministic overload decision used by detect() and validation tests.

        Returns True when estimated load meets/exceeds threshold for enough
        consecutive frames.
        """
        if estimated_count < threshold:
            return False
        return consecutive_over_frames >= confirm_frames

    @staticmethod
    def estimate_load_stack_count(
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        lower_hsv: np.ndarray = LOWER_LOAD,
        upper_hsv: np.ndarray = UPPER_LOAD,
        load_top_ratio: float = LOAD_TOP_RATIO,
        load_bottom_ratio: float = LOAD_BOTTOM_RATIO,
        load_width_margin: float = LOAD_WIDTH_MARGIN,
        min_load_pixel_ratio: float = MIN_LOAD_PIXEL_RATIO,
        min_row_width_ratio: float = MIN_ROW_WIDTH_RATIO,
        min_band_height_ratio: float = MIN_BAND_HEIGHT_RATIO,
        merge_gap_ratio: float = MERGE_GAP_RATIO,
    ) -> int:
        """
        Estimate vertical stack count via row-projection band counting.

        Active horizontal bands in the load ROI are merged when separated by small
        gaps; each surviving band approximates one stacked load unit on the forks.
        """
        if frame is None or frame.size == 0:
            return 0

        h = y2 - y1
        w = x2 - x1
        if h <= 0 or w <= 0:
            return 0

        load_y1 = y1 + int(h * load_top_ratio)
        load_y2 = y1 + int(h * load_bottom_ratio)
        load_x1 = x1 + int(w * load_width_margin)
        load_x2 = x2 - int(w * load_width_margin)

        load_y1 = max(0, min(load_y1, frame.shape[0] - 1))
        load_y2 = max(load_y1 + 1, min(load_y2, frame.shape[0]))
        load_x1 = max(0, min(load_x1, frame.shape[1] - 1))
        load_x2 = max(load_x1 + 1, min(load_x2, frame.shape[1]))

        roi = frame[load_y1:load_y2, load_x1:load_x2]
        if roi.size == 0:
            return 0

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        total_pixels = mask.size
        if total_pixels == 0:
            return 0

        load_ratio = cv2.countNonZero(mask) / total_pixels
        if load_ratio < min_load_pixel_ratio:
            return 0

        row_sums = np.sum(mask > 0, axis=1)
        roi_height = mask.shape[0]
        roi_width = mask.shape[1]
        if roi_height == 0 or roi_width == 0:
            return 0

        min_row_pixels = max(5, int(roi_width * min_row_width_ratio))
        min_band_height = max(8, int(roi_height * min_band_height_ratio))
        merge_gap = max(8, int(roi_height * merge_gap_ratio))

        active = row_sums >= min_row_pixels
        bands: List[Tuple[int, int]] = []
        i = 0
        while i < len(active):
            if not active[i]:
                i += 1
                continue
            start = i
            while i < len(active) and active[i]:
                i += 1
            end = i
            if end - start >= min_band_height:
                bands.append((start, end))

        merged: List[List[int]] = []
        for start, end in bands:
            if not merged or start - merged[-1][1] > merge_gap:
                merged.append([start, end])
            else:
                merged[-1][1] = end

        if not merged:
            return 1 if load_ratio >= min_load_pixel_ratio else 0

        return len(merged)

    def _select_forklift_box(self, yolo_detections: List[Any]) -> Optional[Tuple[int, int, int, int, float]]:
        best = None
        best_score = -1.0

        for box in yolo_detections:
            if int(box.cls[0]) != self.COCO_TRUCK_CLASS:
                continue
            conf = float(box.conf[0])
            if conf < self.MIN_CONFIDENCE:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = max(0, x2 - x1) * max(0, y2 - y1)
            if area < self.MIN_BBOX_AREA:
                continue

            score = conf * area
            if score > best_score:
                best_score = score
                best = (x1, y1, x2, y2, conf)

        return best

    def _update_motion_history(self, cx: int, cy: int) -> bool:
        self._position_history.append((cx, cy))
        if len(self._position_history) > self.MOTION_HISTORY_LEN:
            self._position_history.pop(0)

        if len(self._position_history) < 3:
            return False

        first = self._position_history[0]
        last = self._position_history[-1]
        distance = math.hypot(last[0] - first[0], last[1] - first[1])
        return distance >= self.MIN_MOTION_PIXELS

    def _stable_load_estimate(self, raw_count: int) -> int:
        self._load_history.append(raw_count)
        if len(self._load_history) > self.LOAD_HISTORY_LEN:
            self._load_history.pop(0)
        if not self._load_history:
            return raw_count
        return int(round(float(np.median(self._load_history))))

    def detect(
        self,
        frame: np.ndarray,
        yolo_detections: List[Any],
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        self._current_viz = VisualizationData()
        self._last_forklift_detected = False
        self._last_estimated_load = 0

        forklift = self._select_forklift_box(yolo_detections)
        if forklift is None:
            self._overload_streak = 0
            return events

        x1, y1, x2, y2, conf = forklift
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        if not self._update_motion_history(cx, cy):
            return events

        self._last_forklift_detected = True

        if self._simulate_load_count is not None:
            raw_count = self._simulate_load_count
        else:
            raw_count = self.estimate_load_stack_count(frame, x1, y1, x2, y2)

        stable_count = self._stable_load_estimate(raw_count)
        self._last_estimated_load = stable_count

        is_overload = stable_count >= self.overload_threshold
        if is_overload:
            self._overload_streak += 1
        else:
            self._overload_streak = 0

        if is_overload:
            color = (0, 0, 255)
            status = f"OVERLOAD {stable_count}/{self.overload_threshold - 1}"
        else:
            color = (0, 255, 255)
            status = f"LOAD {stable_count}/{self.overload_threshold - 1} OK"

        self._current_viz.bounding_boxes.append((x1, y1, x2, y2, color))
        self._current_viz.circles.append((cx, cy, 6, color))
        self._current_viz.labels.append((x1, max(y1 - 10, 20), status, color))
        self._current_viz.labels.append(
            (x1, max(y1 - 35, 5), f"FORKLIFT {conf:.2f}", color)
        )

        current_time = time.time()
        should_alert = self.evaluate_overload_decision(
            stable_count,
            self.overload_threshold,
            self._overload_streak,
        )

        if should_alert:
            if (current_time - self.last_violation_time) > self.COOLDOWN_SECONDS:
                self.last_violation_time = current_time
                description = (
                    self.rule.observable_indicator
                    if self.rule
                    else "Forklift carrying overload"
                )
                description = (
                    f"{description} (estimated {stable_count} blocks, "
                    f"threshold {self.overload_threshold})"
                )
                policy_ref = self.rule.policy_reference if self.rule else "6.3.2"
                event = EventFactory.create_forklift_overload(
                    event_description=description,
                    zone="Forklift-Zone",
                    policy_override=policy_ref,
                )
                events.append(event)

        return events

    def get_visualization_data(self) -> VisualizationData:
        return self._current_viz

    @property
    def last_forklift_detected(self) -> bool:
        return self._last_forklift_detected

    @property
    def last_estimated_load(self) -> int:
        return self._last_estimated_load


def _run_validation_tests() -> None:
    print("\n=== Forklift Overload Detector Validation ===")

    threshold = ForkliftOverloadDetector.DEFAULT_OVERLOAD_THRESHOLD
    config = ConfigManager("outputs")
    detector = ForkliftOverloadDetector(config)
    threshold = detector.overload_threshold
    print(f"Policy threshold: {threshold} (from validated_rules.json)")

    cases = [
        (2, 0, False),
        (2, 3, False),
        (3, 2, False),
        (3, 3, True),
        (4, 3, True),
    ]
    for count, streak, expected in cases:
        result = ForkliftOverloadDetector.evaluate_overload_decision(
            count, threshold, streak
        )
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] count={count}, streak={streak} -> overload={result}")

    print(
        "  Overload path test: set FORKLIFT_SIMULATE_LOAD=3 and run 7_tr3.mp4 "
        "to validate CRITICAL event generation end-to-end."
    )

    event = EventFactory.create_forklift_overload(
        event_description="Test forklift overload",
        clip_id="validation.mp4",
        zone="Forklift-Zone",
        policy_override="6.3.2",
    )
    valid, msg = EventFactory.validate_event(event)
    print(f"  Event validation: {msg}")
    print(f"  Severity: {event['severity']}, Escalation: {event['escalation_action']}")


if __name__ == "__main__":
    _run_validation_tests()
    config = ConfigManager("outputs")
    detector = ForkliftOverloadDetector(config)
    print(f"\n✅ Initialized: {detector.name}")
    print(f"   Overload threshold: {detector.overload_threshold}")
    print(f"   Rule: {detector.rule.name if detector.rule else 'Not found'}")
