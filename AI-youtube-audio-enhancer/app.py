import os
import re
import time
import logging
import subprocess

import numpy as np
import soundfile as sf
import librosa
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__, static_folder="static", static_url_path="/static")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

for d in ("downloads", "audio", "output"):
    os.makedirs(d, exist_ok=True)

YOUTUBE_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]{11}"
)


def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_RE.match(url.strip()))


def cleanup(*paths: str) -> None:
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
                logger.info("Cleaned up temp file: %s", p)
        except OSError as exc:
            logger.warning("Could not remove %s: %s", p, exc)


def enhance_audio(audio_path: str, enhanced_path: str, sr: int = 44_100) -> None:
    y, sr = librosa.load(audio_path, sr=sr)
    y = y / (np.max(np.abs(y)) + 1e-9)

    S = librosa.stft(y)
    S_mag = np.abs(S)
    S_phase = np.angle(S)

    noise_frames = max(1, int(0.5 * sr / 512))
    noise = np.mean(S_mag[:, :noise_frames], axis=1, keepdims=True)

    S_mag_reduced = np.maximum(S_mag - 4 * noise, 0)
    threshold = np.percentile(S_mag_reduced, 5)
    S_mag_reduced[S_mag_reduced < threshold] = 0

    S_enhanced = S_mag_reduced * np.exp(1j * S_phase)
    y_enhanced = librosa.istft(S_enhanced)

    y_enhanced = y_enhanced / (np.max(np.abs(y_enhanced)) + 1e-9)
    y_enhanced = np.clip(y_enhanced * 1.2, -1.0, 1.0)

    sf.write(enhanced_path, y_enhanced, sr)
    logger.info("Audio enhancement complete → %s", enhanced_path)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "PureWave: YouTube Audio Enhancer"}), 200


@app.route("/", methods=["GET", "POST"])
def home():
    enhanced_ready = False
    error_message = None
    unique_id = None

    if request.method == "POST":
        youtube_url = request.form.get("youtube_url", "").strip()
        unique_id = str(int(time.time()))

        if not youtube_url:
            error_message = "❌ Please enter a YouTube URL."
            return render_template("index.html", enhanced_ready=False, error_message=error_message)

        if not is_valid_youtube_url(youtube_url):
            error_message = "❌ Invalid URL. Please enter a valid YouTube watch link."
            return render_template("index.html", enhanced_ready=False, error_message=error_message)

        video_file = None
        audio_file = None
        enhanced_audio = None

        try:
            logger.info("[%s] Starting download: %s", unique_id, youtube_url)

            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "outtmpl": f"downloads/{unique_id}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_file = ydl.prepare_filename(info)

            logger.info("[%s] Download complete: %s", unique_id, video_file)

            audio_file = f"audio/input_{unique_id}.wav"
            extract_cmd = [
                "ffmpeg", "-y",
                "-i", video_file,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                audio_file,
            ]
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("[%s] FFmpeg extract error:\n%s", unique_id, result.stderr)
                error_message = "❌ Could not extract audio from the video. Please try a different link."
                return render_template("index.html", enhanced_ready=False, error_message=error_message)

            enhanced_audio = f"audio/enhanced_{unique_id}.wav"
            enhance_audio(audio_file, enhanced_audio)

            output_file = f"output/enhanced_{unique_id}.mp4"
            merge_cmd = [
                "ffmpeg", "-y",
                "-i", video_file,
                "-i", enhanced_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_file,
            ]
            result = subprocess.run(merge_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("[%s] FFmpeg merge error:\n%s", unique_id, result.stderr)
                error_message = "❌ Could not merge audio with video. Please try again."
                return render_template("index.html", enhanced_ready=False, error_message=error_message)

            logger.info("[%s] Processing complete → %s", unique_id, output_file)
            enhanced_ready = True

        except Exception as exc:
            logger.exception("[%s] Unexpected error: %s", unique_id, exc)
            error_message = f"❌ An unexpected error occurred. Please try again."

        finally:
            cleanup(video_file, audio_file, enhanced_audio)

        return render_template(
            "index.html",
            enhanced_ready=enhanced_ready,
            error_message=error_message,
            unique_id=unique_id,
        )

    return render_template(
        "index.html",
        enhanced_ready=enhanced_ready,
        error_message=error_message,
        unique_id=unique_id,
    )


@app.route("/download/<unique_id>")
def download(unique_id: str):
    if not re.match(r"^\d+$", unique_id):
        return redirect(url_for("home"))

    output_path = f"output/enhanced_{unique_id}.mp4"
    if not os.path.exists(output_path):
        logger.warning("Download requested for missing file: %s", output_path)
        return redirect(url_for("home"))

    return send_file(
        output_path,
        as_attachment=True,
        download_name="enhanced_video.mp4",
        mimetype="video/mp4",
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
    )