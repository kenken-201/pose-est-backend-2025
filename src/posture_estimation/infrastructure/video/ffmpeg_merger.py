import ffmpeg  # type: ignore[import-untyped, unused-ignore]

from posture_estimation.domain.exceptions import VideoProcessingError


class FFmpegAudioMerger:
    """FFmpeg を使用して音声結合を行うクラス。"""

    def merge_audio(self, video_no_audio: str, original_video: str, output: str) -> None:
        """加工済み動画 (音声なし) に元の動画の音声を結合します。

        Args:
            video_no_audio (str): 映像のみの動画ファイルパス
            original_video (str): 音声ソースとなる元の動画ファイルパス
            output (str): 出力ファイルパス

        Raises:
            VideoProcessingError: FFmpeg 実行に失敗した場合
        """
        try:
            # 映像入力 (加工済み)
            input_video = ffmpeg.input(video_no_audio)
            # 音声入力 (元動画)
            input_audio = ffmpeg.input(original_video)

            # 映像はそのままコピー (再エンコードなし)、音声は AAC で結合
            # note: input_audio['a'] で明示的にオーディオストリームを選択
            stream = ffmpeg.output(
                input_video,
                input_audio.audio,
                output,
                vcodec="copy",
                acodec="aac",
            )

            # 実行
            stream.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)

        except Exception as e:
            msg = f"Audio merge failed: {e}"
            raise VideoProcessingError(msg) from e
