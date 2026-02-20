# 🎮 Xbox Web Controller

A premium, web-based virtual Xbox controller that transforms your phone into a controller for your PC. Perfect for local multiplayer, remote play, or as a handy backup controller.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![Socket.IO](https://img.shields.io/badge/socket.io-4.x-orange.svg)

## ✨ Features

- **Web-Based**: No app installation required on your phone.
- **PWA Ready**: Add to home screen for a full-screen, immersive experience.
- **Haptic Feedback**: Real-time vibrations and visual response (Ripple effect).
- **Multiplayer Support**: Automatically handles up to 4 concurrent players.
- **Low Latency**: Built with Socket.IO for near-instant response.

## 🚀 Getting Started

### 1. Prerequisites (PC)

This project uses `vgamepad`, which requires the **ViGEmBus** driver.

- **Download ViGEmBus**: [Download here](https://github.com/ViGEm/ViGEmBus/releases) and install the latest `.exe`.
- **Python**: Ensure you have Python 3.7+ installed.

### 2. Installation

Clone the repository and install the dependencies:

```bash
pip install flask flask-socketio vgamepad
```

### 3. Run the Server

Start the application:

```bash
python app.py
```

The terminal will display two URLs:
- `http://localhost:5000` (for testing on your PC)
- `http://192.168.x.x:5000` (**Use this on your phone**)

### 4. Setup on Phone

1. Connect your phone to the same Wi-Fi as your PC.
2. Open the **Network URL** in your phone's browser.
3. For the best experience, select **"Add to Home Screen"** from your browser menu. This will remove the address bar and allow for better touch controls.

## 🛠️ Configuration

The server defaults to port `5000`. You can change this in `app.py` if needed.
The gamepad mapping is pre-configured for standard Xbox controls.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
