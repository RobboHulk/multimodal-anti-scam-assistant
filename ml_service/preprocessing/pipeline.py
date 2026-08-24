"""多模态预处理管道编排。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from preprocessing.audio_preprocessor import AudioPreprocessor
from preprocessing.image_preprocessor import ImagePreprocessor
from preprocessing.schema import AudioPreprocessResult, ImagePreprocessResult, TextPreprocessResult, VideoPreprocessResult
from preprocessing.text_preprocessor import TextPreprocessor
from preprocessing.video_preprocessor import VideoPreprocessor


@dataclass
class PreprocessOutput:
    text: TextPreprocessResult
    image: Optional[ImagePreprocessResult] = None
    audio: Optional[AudioPreprocessResult] = None
    video: Optional[VideoPreprocessResult] = None

    def to_metadata(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"text": self.text.to_dict()}
        if self.image is not None:
            data["image"] = self.image.to_dict()
        if self.audio is not None:
            data["audio"] = self.audio.to_dict()
        if self.video is not None:
            data["video"] = self.video.to_dict()
        return data


class MultimodalPreprocessingPipeline:
    def __init__(self) -> None:
        self.text_preprocessor = TextPreprocessor()
        self.audio_preprocessor = AudioPreprocessor()
        self.image_preprocessor = ImagePreprocessor()
        self.video_preprocessor = VideoPreprocessor(
            image_preprocessor=self.image_preprocessor,
            audio_preprocessor=self.audio_preprocessor,
        )

    def run(
        self,
        *,
        query: str,
        image_path: str = "",
        audio_path: str = "",
        video_path: str = "",
    ) -> PreprocessOutput:
        text_result = self.text_preprocessor.preprocess(query)
        image_result = self.image_preprocessor.preprocess(image_path) if image_path else None
        audio_result = self.audio_preprocessor.preprocess(audio_path) if audio_path else None
        video_result = self.video_preprocessor.preprocess(video_path) if video_path else None
        return PreprocessOutput(
            text=text_result,
            image=image_result,
            audio=audio_result,
            video=video_result,
        )

