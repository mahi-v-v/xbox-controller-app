# 🛠️ Developer Documentation

This repository contains the source code for the **Xbox Web Controller**, organized as an open-source monorepo.

## 🏗️ Architecture Overview

The system consists of three main parts:
1.  **The Controller Web App (`webapp/`)**: A frontend built with vanilla HTML/CSS/JS. It handles the virtual analog sticks (using Nipple.js), multi-touch buttons, layout switching, and haptic feedback.
2.  **The Mobile App Wrapper (`android/`)**: An Ionic Capacitor project that takes the `webapp/` and wraps it into a native Android `.apk`.
3.  **The Windows Server (`server/`)**: A Python application using Flask and Socket.IO. It receives websockets from the phone and uses the `vgamepad` library to interface with the Windows `ViGEmBus` driver, injecting genuine Xbox 360 controller inputs.

When built, the Windows Server `.exe` hosts *both* the landing website and the Controller Web App locally, allowing phones to connect to the PC directly without needing internet access.

---

## 📁 Repository Structure

```
Xbox-Controller-App/
│
├── server/          # Python Flask + SocketIO Server code
│   ├── requirements.txt
│   ├── server_cli.py
│   └── server_gui.py
│
├── webapp/          # Controller Web App (HTML/CSS/JS)
│
├── website/         # Landing Page (served locally by the Python Server)
│
├── android/         # Capacitor Android Project
│
├── apk/             # Put the compiled app-debug.apk here before making the .exe
│
├── build_server.ps1 # Build script to create the .exe
├── LICENSE          # MIT open-source license
└── README.md        # User-facing setup and instructions
```

---

## 🚀 Local Development Setup

### Prerequisites
- **Node.js** (for syncing web assets)
- **Python 3.10+** (for running the server)
- **[ViGEmBus Driver](https://github.com/nefarius/ViGEmBus/releases)**
- **Android Studio** (if you want to build the APK)

### 1. Running the Server in Dev Mode
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r server\requirements.txt
```
To run the GUI version:
```bash
python server\server_gui.py
```

### 2. Modifying the Web App
Make your edits inside the `webapp/` folder. When you run the Python server, it will serve these files directly. Refresh your browser to see changes.

---

## 📦 Building for Production

To create a GitHub Release, you need to compile two files: the Android APK and the Windows Server EXE.

### Step 1: Compile the Android APK
The mobile app is wrapped using Ionic Capacitor.
1. Sync any changes you made in `webapp/` over to the Android project:
   ```bash
   npx cap sync android
   ```
2. Build the APK using Gradle:
   ```bash
   # Make sure Android SDK/Java paths are set
   cd android
   ./gradlew.bat assembleDebug
   cd ..
   ```
3. **CRITICAL:** Place the resulting APK into the `apk/` directory at the root of the project so the PC server can bundle it.
   ```bash
   mkdir apk
   Copy-Item "android\app\build\outputs\apk\debug\app-debug.apk" -Destination "apk\app-debug.apk"
   ```

### Step 2: Add the Driver
For a seamless user experience, we bundle the official ViGEmBus installer.
1. Download the latest `ViGEmBus_Setup_...exe` from [GitHub](https://github.com/nefarius/ViGEmBus/releases)
2. Create a `drivers/` folder in your project root and place the `.exe` inside:
   ```bash
   mkdir drivers
   # Drop ViGEmBus installer here
   ```

### Step 3: Compile the Windows Server (.exe)
We use `PyInstaller` to bundle the server, the webapp, the landing website, and the APK into a single portable `.exe` file.

You can automate this using the provided PowerShell script:
```powershell
.\build_server.ps1
```

*(This script installs requirements, creates the `venv` if missing, and runs the PyInstaller command with all the correct `--add-data` flags).*

The final standalone application will be generated at:
`dist\XboxController Server.exe`

---

## 🔐 Security & Threat Model

As a developer, please be aware of the following design choices regarding security:
*   **Unauthenticated Websockets:** The system uses `cors_allowed_origins="*"` and has no authentication token exchange. This is intentionally done to provide a frictionless "scan and play" experience for users. 
*   **Network Exposure:** The server binds to `0.0.0.0`, leaving port 5000 open to horizontal network traffic.
*   **Input Validation:** Socket payloads are parsed inside a `try/except (ValueError, TypeError, AttributeError)` block to prevent malformed data from causing application-level exceptions, defending against basic DoS attempts.
