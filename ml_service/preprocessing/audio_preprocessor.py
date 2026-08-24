"""音频预处理：标准化、VAD、ASR、反诈特征。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from preprocessing.asr_client import BaseASRClient, create_asr_client
from preprocessing.schema import ASRSegment, AudioFeatures, AudioPreprocessResult
from preprocessing.utils import build_cache_file_path, keyword_hits, split_sentences
from speech_detector.service import detect_audio_file

RISK_KEYWORDS = [
    "转账",
    "验证码",
    "安全账户",
    "屏幕共享",
    "下载",
    "链接",
    "银行卡",
    "密码",
]


class AudioPreprocessor:
    def __init__(self, *, asr_client: BaseASRClient | None = None, target_sr: int = 16000) -> None:
        self.asr_client = asr_client or create_asr_client()
        self.target_sr = target_sr

    def preprocess(self, audio_path: str) -> AudioPreprocessResult:
        p = Path(audio_path)
        if not p.exists():
            return AudioPreprocessResult(
                normalized_audio_path=audio_path,
                status="skipped",
                source_model="audio_preprocessor",
                error_code="AUDIO_FILE_NOT_FOUND",
                error_message=f"audio file not found: {audio_path}",
                warnings=["AUDIO_FILE_NOT_FOUND"],
            )

        normalized_audio_path = self._normalize_audio(audio_path)
        vad_windows = self._run_vad(normalized_audio_path)
        asr_result = self.asr_client.transcribe_detailed(normalized_audio_path)
        transcript = str(asr_result.get("text", "")).strip()
        segments = self._build_asr_segments(
            transcript=transcript,
            raw_segments=asr_result.get("segments", []),
            vad_windows=vad_windows,
        )
        audio_features, detect_warning = self._extract_audio_features(normalized_audio_path, segments)
        asr_status = str(asr_result.get("status", "ok") or "ok")
        warnings = list(asr_result.get("warnings", []))
        if detect_warning:
            warnings.append(detect_warning)
        status = "ok"
        if asr_status in {"failed", "skipped"}:
            status = "degraded"
        if not transcript and not segments:
            status = "degraded"

        return AudioPreprocessResult(
            asr_segments=segments,
            audio_features=audio_features,
            transcript=transcript,
            normalized_audio_path=normalized_audio_path,
            status=status,
            source_model=str(asr_result.get("source_model", "funasr_local")),
            error_code=str(asr_result.get("error_code", "")),
            error_message=str(asr_result.get("error_message", "")),
            warnings=warnings,
        )

    def _normalize_audio(self, audio_path: str) -> str:
        """优先做采样率/声道标准化；缺依赖时回退原文件。"""
        try:
            import torchaudio
            import torch
        except ImportError:
            return audio_path

        src = Path(audio_path)
        dst = build_cache_file_path(audio_path, subdir="audio", suffix="norm", ext=".wav")
        try:
            wav, sr = torchaudio.load(str(src))
            if wav.shape[0] > 1:
                wav = wav.mean(dim=0, keepdim=True)
            if sr != self.target_sr:
                wav = torchaudio.functional.resample(wav, sr, self.target_sr)
            wav = self._volume_normalize(wav)
            torchaudio.save(str(dst), wav.cpu(), self.target_sr)
            return str(dst)
        except Exception:
            return audio_path

    @staticmethod
    def _volume_normalize(wav):
        peak = wav.abs().max()
        if float(peak) <= 0:
            return wav
        return wav / peak

    def _build_asr_segments(
        self,
        *,
        transcript: str,
        raw_segments: Any,
        vad_windows: list[tuple[float, float]],
    ) -> List[ASRSegment]:
        if isinstance(raw_segments, list):
            normalized = self._from_asr_segments(raw_segments)
            if normalized:
                return normalized

        sents = split_sentences(transcript)
        if not sents and transcript.strip():
            sents = [transcript.strip()]
        if not sents:
            return []

        # 没有真实 ASR 时间戳时，使用 VAD 窗口作为优先切分依据。
        segments: List[ASRSegment] = []
        if vad_windows:
            for idx, sent in enumerate(sents):
                start, end = vad_windows[min(idx, len(vad_windows) - 1)]
                segments.append(
                    ASRSegment(
                        start=round(start, 2),
                        end=round(end, 2),
                        speaker="unknown",
                        text=sent,
                        risk_patterns=keyword_hits(sent, RISK_KEYWORDS),
                        is_estimated=True,
                    )
                )
            return segments

        for idx, sent in enumerate(sents):
            start = round(idx * 3.0, 2)
            end = round((idx + 1) * 3.0, 2)
            segments.append(
                ASRSegment(
                    start=start,
                    end=end,
                    speaker="unknown",
                    text=sent,
                    risk_patterns=keyword_hits(sent, RISK_KEYWORDS),
                    is_estimated=True,
                )
            )
        return segments

    @staticmethod
    def _from_asr_segments(raw_segments: list[Any]) -> List[ASRSegment]:
        converted: List[ASRSegment] = []
        for idx, raw in enumerate(raw_segments):
            if not isinstance(raw, dict):
                continue
            text = str(raw.get("text", "")).strip()
            if not text:
                continue
            start = float(raw.get("start", 0.0))
            end = float(raw.get("end", start + 3.0))
            speaker = str(raw.get("speaker", "unknown")) or "unknown"
            has_native_ts = "start" in raw and ("end" in raw or "end_time" in raw)
            converted.append(
                ASRSegment(
                    start=start,
                    end=end,
                    speaker=speaker,
                    text=text,
                    risk_patterns=keyword_hits(text, RISK_KEYWORDS),
                    is_estimated=not has_native_ts,
                )
            )
        return converted

    def _run_vad(self, audio_path: str) -> list[tuple[float, float]]:
        """
        真实 VAD 优先：webrtcvad 可用时使用；否则回退到能量阈值 VAD。
        返回值为 (start_sec, end_sec) 语音窗口。
        """
        try:
            return self._run_webrtcvad(audio_path)
        except Exception:
            return self._run_energy_vad(audio_path)

    @staticmethod
    def _run_webrtcvad(audio_path: str) -> list[tuple[float, float]]:
        import wave
        import webrtcvad

        vad = webrtcvad.Vad(2)
        windows: list[tuple[float, float]] = []
        with wave.open(audio_path, "rb") as wf:
            sample_rate = wf.getframerate()
            if sample_rate not in {8000, 16000, 32000, 48000}:
                return []
            frame_ms = 30
            bytes_per_frame = int(sample_rate * frame_ms / 1000) * wf.getsampwidth()
            frame_idx = 0
            speech_start: float | None = None
            while True:
                frame = wf.readframes(int(sample_rate * frame_ms / 1000))
                if not frame:
                    break
                if len(frame) < bytes_per_frame:
                    break
                is_speech = vad.is_speech(frame[:bytes_per_frame], sample_rate)
                t0 = frame_idx * frame_ms / 1000.0
                t1 = t0 + frame_ms / 1000.0
                if is_speech and speech_start is None:
                    speech_start = t0
                elif not is_speech and speech_start is not None:
                    if t0 - speech_start >= 0.3:
                        windows.append((speech_start, t0))
                    speech_start = None
                frame_idx += 1
            if speech_start is not None:
                windows.append((speech_start, frame_idx * frame_ms / 1000.0))
        return windows

    @staticmethod
    def _run_energy_vad(audio_path: str) -> list[tuple[float, float]]:
        try:
            import torch
            import torchaudio
        except ImportError:
            return []

        wav, sr = torchaudio.load(audio_path)
        if wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        signal = wav.squeeze(0)
        if signal.numel() == 0:
            return []
        frame_size = max(int(sr * 0.03), 1)
        hop = frame_size
        energies = []
        for i in range(0, signal.numel() - frame_size + 1, hop):
            frame = signal[i : i + frame_size]
            energies.append(float((frame * frame).mean().item()))
        if not energies:
            return []
        threshold = max(sum(energies) / len(energies) * 1.5, 1e-7)
        windows: list[tuple[float, float]] = []
        start: float | None = None
        for idx, energy in enumerate(energies):
            t0 = idx * hop / sr
            t1 = t0 + frame_size / sr
            if energy >= threshold and start is None:
                start = t0
            elif energy < threshold and start is not None:
                if t0 - start >= 0.3:
                    windows.append((start, t0))
                start = None
        if start is not None:
            windows.append((start, len(energies) * hop / sr))
        return windows

    def _extract_audio_features(self, audio_path: str, segments: List[ASRSegment]) -> tuple[AudioFeatures, str]:
        synthetic_score = 0.0
        synthetic_available = False
        warning = ""
        try:
            detection = detect_audio_file(audio_path)
            synthetic_score = float(detection.get("score", 0.0))
            synthetic_available = True
        except Exception:
            synthetic_score = 0.0
            warning = "DEEPFAKE_DETECTOR_NOT_AVAILABLE"

        urgency_words = {"马上", "立刻", "现在", "紧急", "尽快"}
        pressure_hits = sum(1 for seg in segments if any(word in seg.text for word in urgency_words))
        emotion_pressure_score = min(0.2 + pressure_hits * 0.2, 1.0) if segments else 0.0
        speaker_count = len({seg.speaker for seg in segments if seg.speaker}) or 1
        return (
            AudioFeatures(
                speaker_count=speaker_count,
                emotion_pressure_score=round(emotion_pressure_score, 3),
                synthetic_voice_score=round(synthetic_score, 3),
                synthetic_voice_available=synthetic_available,
                prosody={},
            ),
            warning,
        )

