# AirCast 🎧

**Stream your Windows system audio over LAN to any device directly through a browser. No apps. No drivers. Pure wireless sound.**

---

## ✨ Features

- **Real-time PC audio streaming** to any phone, tablet, or laptop
- **Browser-based:** Works instantly with WebAudio + WebSockets
- **Zero Installation on Client:** Just open your browser and play
- **WASAPI Loopback:** Captures system audio without needing Stereo Mix or microphones
- **Multi-Client Support:** Stream to multiple devices simultaneously
- **Modern UI:** Clean, responsive, and lightweight
- **Reliable:** Auto-buffering and smooth reconnection

---

## ⚙️ Installation

### Prerequisites

- Python 3.x
- Windows OS (required for WASAPI)

### Setup

```bash
git clone https://github.com/utkarsh-deployes/AirCast.git
cd AirCast
pip install -r requirements.txt
```

---

## ▶️ Usage

### 1. Start the Server

```bash
python aircast-server.py
```

Or use the Windows auto-restart script:

```bash
aircast.bat
```

### 2. Connect from Client Devices

1. Find your local IP address (run `ipconfig` on Windows)
2. Open the browser on any device and go to:
   ```
   http://YOUR-IP:5000
   ```
3. Click **Play Stream** to start listening

---

## 🧠 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | Python (Flask, WebSockets, sounddevice) | Audio capture, hosting, streaming |
| Frontend | HTML, CSS, JavaScript, WebAudio API | Audio playback and UI |

---

## 📂 File Structure

```
AirCast/
├── aircast-client.html     # Browser-based audio player
├── aircast-server.py       # Flask + WebSocket audio streamer
├── aircast.bat             # Auto-restart script
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── LICENSE                 # MIT License
```

---

## 🪟 Windows Setup Tips

- **No Sound?** Enable Stereo Mix or WASAPI Loopback in Recording Devices
- **Firewall Issues?** Allow Python through Windows Firewall on port 5000

---

## 🧾 License

MIT License © 2025 Utkarsh

---

## 🌐 Connect with Me

<a href="https://github.com/utkarsh-deployes" target="_blank">
  <img src="https://img.shields.io/badge/GitHub-121011?style=for-the-badge&logo=github&logoColor=white"/>
</a>
<a href="mailto:utkarsh.cloudops@gmail.com">
  <img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white"/>
</a>

---

## 💬 Contributions Welcome!

Found a bug or have an idea?  
Open an issue or submit a PR — let's make AirCast even better.

---

**Enjoy wireless audio streaming with AirCast!** 🎵