# 🎵 PureWave: YouTube Audio Enhancer

> A Python/Flask web application that downloads any YouTube video and returns it with **crystal-clear audio** using **STFT-based spectral noise reduction**.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat&logo=flask)
![Librosa](https://img.shields.io/badge/Librosa-0.10-green?style=flat)
![FFmpeg](https://img.shields.io/badge/FFmpeg-6.x-orange?style=flat&logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat)

---

## ✨ Features

- 🔗 **Paste any YouTube URL** — yt-dlp handles download automatically
- 🧠 **Noise Reduction** — Short-Time Fourier Transform (STFT) spectral subtraction removes background hiss and noise
- 🔊 **Audio Normalization & Boost** — Standardizes levels and applies a 1.2× clarity boost
- 🎬 **Lossless Video Merge** — FFmpeg copies the original video stream and replaces only the audio track (zero re-encoding quality loss)
- 📥 **One-click Download** — Get the final enhanced MP4 directly from the browser
- 🏥 **`/health` endpoint** — Production-ready health check for deployment platforms (Heroku, Railway, Render)
- 🧹 **Automatic cleanup** — Temporary audio/video files are deleted after processing

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | Flask (Python) |
| Audio DSP | Librosa, NumPy, SoundFile |
| Video Processing | FFmpeg |
| YouTube Download | yt-dlp |
| Production Server | Gunicorn |
| Frontend | HTML5, CSS3, JavaScript |

---

## 🏗️ Architecture

```
User → Browser (HTML/CSS/JS)
         │  POST /  (YouTube URL)
         ▼
      Flask App (app.py)
         │
         ├─ 1. yt-dlp        → downloads/  (raw MP4)
         ├─ 2. FFmpeg         → audio/input_<id>.wav  (raw WAV)
         ├─ 3. Librosa/NumPy  → audio/enhanced_<id>.wav (STFT noise reduction)
         ├─ 4. FFmpeg         → output/enhanced_<id>.mp4 (final video)
         └─ 5. Cleanup temp files
         │
         ▼
      GET /download/<id>  → send_file(enhanced MP4)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- FFmpeg installed and on your system `PATH`

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/PureWave-youtube-enhancer.git
cd PureWave-youtube-enhancer

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
python app.py
```

Open your browser at **http://localhost:5000**

### Running with Gunicorn (Production)

```bash
gunicorn app:app
```

---

## 📁 Project Structure

```
PureWave/
├── app.py              # Flask application (routes, audio pipeline)
├── requirements.txt    # Python dependencies
├── Procfile            # Heroku/Railway deployment config
├── templates/
│   └── index.html      # Frontend UI
├── static/
│   └── style.css       # UI styles
├── downloads/          # Temp: raw downloaded videos
├── audio/              # Temp: extracted & enhanced audio
└── output/             # Final enhanced MP4 files
```

---

## 🔬 How the Audio Processing Works

1. **Load audio** — Librosa loads the extracted WAV at 44,100 Hz
2. **STFT** — Convert time-domain signal to frequency domain (Short-Time Fourier Transform)
3. **Noise floor estimation** — Average the first ~0.5 s of audio as a noise reference
4. **Spectral subtraction** — Subtract 4× the estimated noise from every frequency bin
5. **Soft thresholding** — Zero out remaining low-energy components below the 5th percentile
6. **ISTFT** — Reconstruct the cleaned time-domain signal
7. **Normalize & boost** — Normalize to peak amplitude, apply a 1.2× gain, clip to prevent distortion

---

## 🌐 Deployment

The app is ready to deploy on **Heroku**, **Railway**, or **Render** via the included `Procfile`:

```
web: gunicorn app:app
```

Set environment variables as needed:
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `false` | Enable debug mode |

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

*Built with ❤️ by [Amit Yadav] · Python · Flask · Librosa · FFmpeg*
