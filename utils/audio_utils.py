import wave
import subprocess
from pathlib import Path

# =========================
# PCM utilities
# =========================


def write_pcm_chunk(file_handle, data: bytes) -> None:
    """
    Writes raw PCM audio chunk to an open file handle.
    """
    file_handle.write(data)


# =========================
# WAV utilities (no ffmpeg)
# =========================


def pcm_to_wav(
    pcm_path: str,
    wav_path: str,
    sample_rate: int = 24000,
    channels: int = 1,
    sample_width: int = 2,
) -> None:
    """
    Converts raw PCM file into a WAV file.

    Assumptions:
    - PCM is signed 16-bit little endian (s16le)
    - Mono audio (default)
    - Sample rate = 24000 Hz (Gemini default)
    """

    pcm_path = Path(pcm_path)
    wav_path = Path(wav_path)

    with open(pcm_path, "rb") as pcm_file:
        pcm_data = pcm_file.read()

    with wave.open(wav_path.as_posix(), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)


def stream_pcm_to_wav_init(wav_path: str, sample_rate: int = 24000):
    """
    Initializes a WAV writer for streaming use.

    Returns:
        wave.Wave_write object (you must close it manually)
    """
    wav_file = wave.open(wav_path, "wb")
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    return wav_file


def write_wav_chunk(wav_file, data: bytes) -> None:
    """
    Writes streaming PCM chunk directly into WAV file.
    """
    wav_file.writeframes(data)


def wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "192k") -> None:
    """Convert a WAV file to MP3 using ffmpeg.

    Parameters
    ----------
    wav_path : str
        Input WAV file path
    mp3_path : str
        Output MP3 file path
    bitrate : str, optional
        MP3 bitrate (e.g. 128k, 192k, 320k), by default '192k'
    """

    wav_path = Path(wav_path)
    mp3_path = Path(mp3_path)

    if not wav_path.exists():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            str(mp3_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
