"""视频预处理：关键帧、音轨、时序行为。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from preprocessing.audio_preprocessor import AudioPreprocessor
from preprocessing.image_preprocessor import ImagePreprocessor
from preprocessing.schema import KeyFrame, VideoPreprocessResult
from preprocessing.utils import build_cache_file_path, get_preprocess_cache_dir


class VideoPreprocessor:
    def __init__(
        self,
        *,
        image_preprocessor: ImagePreprocessor | None = None,
        audio_preprocessor: AudioPreprocessor | None = None,
    ) -> None:
        self.image_preprocessor = image_preprocessor or ImagePreprocessor()
        self.audio_preprocessor = audio_preprocessor or AudioPreprocessor()

    def preprocess(
        self,
        video_path: str,
        *,
        keyframe_interval_sec: float = 6.0,
        scene_threshold: float = 0.18,
        max_keyframes: int = 24,
    ) -> VideoPreprocessResult:
        p = Path(video_path)
        if not p.exists():
            return VideoPreprocessResult(
                status="skipped",
                source_model="video_preprocessor",
                error_code="VIDEO_FILE_NOT_FOUND",
                error_message=f"video file not found: {video_path}",
                warnings=["VIDEO_FILE_NOT_FOUND"],
            )

        keyframes = self._extract_keyframes(
            video_path,
            keyframe_interval_sec=keyframe_interval_sec,
            scene_threshold=scene_threshold,
            max_keyframes=max_keyframes,
        )
        audio_path = self._extract_audio_track(video_path)
        audio_summary = self.audio_preprocessor.preprocess(audio_path) if audio_path else None
        behavior_sequence = self._build_behavior_sequence(keyframes, audio_summary.transcript if audio_summary else "")
        warnings: list[str] = []
        status = "ok"
        if not keyframes:
            warnings.append("VIDEO_KEYFRAME_EMPTY")
            status = "degraded"
        if not audio_path:
            warnings.append("VIDEO_AUDIO_TRACK_MISSING")
            status = "degraded"
        elif audio_summary is not None and audio_summary.status in {"failed", "skipped"}:
            warnings.append("VIDEO_AUDIO_PREPROCESS_DEGRADED")
            status = "degraded"

        return VideoPreprocessResult(
            keyframes=keyframes,
            audio_summary=audio_summary,
            behavior_sequence=behavior_sequence,
            extracted_audio_path=audio_path,
            status=status,
            source_model="video_preprocessor",
            error_code="",
            error_message="",
            warnings=warnings,
        )

    def _extract_keyframes(
        self,
        video_path: str,
        *,
        keyframe_interval_sec: float,
        scene_threshold: float,
        max_keyframes: int,
    ) -> List[KeyFrame]:
        try:
            import cv2
            import numpy as np
        except ImportError:
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_step = max(int(fps), 1)  # 每秒采样一次用于事件检测
        min_gap_frames = max(int(fps * keyframe_interval_sec), 1)
        frame_id = 0
        keyframes: List[KeyFrame] = []
        out_dir = get_preprocess_cache_dir("video_frames") / f"{Path(video_path).stem}_frames"
        out_dir.mkdir(parents=True, exist_ok=True)
        last_saved_frame = -min_gap_frames
        last_hist = None
        last_ocr_tokens: set[str] = set()

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_id % frame_step != 0:
                frame_id += 1
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [64], [0, 256]).flatten()
            hist = hist / (hist.sum() + 1e-8)
            scene_change = False
            if last_hist is None:
                scene_change = True
            else:
                dist = float(np.abs(hist - last_hist).sum())
                scene_change = dist >= scene_threshold

            time_pos = round(frame_id / fps, 2)
            if len(keyframes) < max_keyframes:
                frame_path = out_dir / f"frame_{frame_id}.jpg"
                cv2.imwrite(str(frame_path), frame)
                image_result = self.image_preprocessor.preprocess(str(frame_path))
                current_tokens = set(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", image_result.ocr_text))
                text_changed = bool(current_tokens.symmetric_difference(last_ocr_tokens))
                time_gap = frame_id - last_saved_frame >= min_gap_frames
                should_keep = scene_change or text_changed or time_gap
                if should_keep:
                    keyframes.append(
                        KeyFrame(
                            time=time_pos,
                            page_type=image_result.page_type,
                            ocr_text=image_result.ocr_text[:300],
                            frame_path=str(frame_path),
                        )
                    )
                    last_saved_frame = frame_id
                    last_ocr_tokens = current_tokens
                else:
                    try:
                        Path(frame_path).unlink(missing_ok=True)
                    except Exception:
                        pass
            last_hist = hist
            frame_id += 1

        cap.release()
        return keyframes

    @staticmethod
    def _extract_audio_track(video_path: str) -> str:
        """依赖 ffmpeg；不可用时返回空字符串。"""
        from shutil import which
        import subprocess

        if which("ffmpeg") is None:
            return ""
        src = Path(video_path)
        dst = build_cache_file_path(video_path, subdir="video_audio", suffix="audio", ext=".wav")
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(dst),
        ]
        try:
            subprocess.run(command, check=False, capture_output=True, text=True)
        except Exception:
            return ""
        return str(dst) if dst.exists() else ""

    @staticmethod
    def _build_behavior_sequence(keyframes: List[KeyFrame], transcript: str) -> List[str]:
        sequence: List[str] = []
        if not keyframes:
            return sequence
        prev_page = ""
        for frame in keyframes:
            if frame.page_type != prev_page:
                sequence.append(f"t={frame.time}s 页面切换为 {frame.page_type}")
                prev_page = frame.page_type
            if any(k in frame.ocr_text for k in ["转账", "验证码", "下载", "安全账户"]):
                sequence.append(f"t={frame.time}s 发现风险页面文案")
        if transcript:
            if "下载" in transcript or "安装" in transcript:
                sequence.append("audio:引导下载/安装")
            if "转账" in transcript or "验证码" in transcript:
                sequence.append("audio:资金或验证码引导")
        # 去重并保持顺序
        deduped: List[str] = []
        seen = set()
        for item in sequence:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped[:20]

