# 🎮 Xbox Web Controller

Turn your smartphone (Android or iOS) into a complete, responsive PC gamepad over Wi-Fi.

This app allows you to connect your phone locally to your Windows PC. The server translates your phone's touch inputs (buttons, thumbsticks, triggers) into genuine Xbox 360 controller inputs so you can play any PC game!

---

## ✨ Features
- **Zero Install for Phones:** Run instantly in your phone's browser or download the Android APK directly from your PC!
- **Haptic Feedback:** Authentic vibration when pressing buttons.
- **Multiple Layouts:** Switch between Xbox, PlayStation, Nintendo, Southpaw, Racing, and Minimal styles.
- **Standalone Server:** The PC server boasts a clean UI, live connection logs, and a scannable QR code. It bundles everything into one file!

---

## 🚀 Quick Start Guide

### Step 1: Install the Windows Driver
For your PC to detect the virtual controller, you must install the official ViGEmBus driver.
1. Download here: [ViGEmBus Release Page](https://github.com/nefarius/ViGEmBus/releases/latest)
2. Run the installer (`ViGEmBus_Setup_...exe`) and follow the prompts.

### Step 2: Download the Application
Head over to the **Releases** tab on the right side of this GitHub page and download the latest:
*   `XboxController Server.exe`

### Step 3: Run the Server
1. Double-click `XboxController Server.exe` on your PC.
2. Click **Start Server**.
3. A QR code and an IP Address (e.g., `192.168.1.100:5000`) will appear. Keep this window open!

### Step 4: Connect Your Phone (Two Ways)

**Method A: Web Browser (iOS & Android)**
1. Scan the QR code on your PC screen with your phone's camera, or visit the IP address in your mobile browser.
2. You will see a landing page. Tap **Play in Browser (PWA)**.
3. *Tip: For the best full-screen experience, tap your browser's Share/Menu button and select **Add to Home Screen**, then launch the app from your home screen.*

**Method B: Android App**
1. Scan the QR code or visit the IP address in your browser.
2. Tap **Download Android (.apk)**.
3. Install the APK (you may need to allow "Install from Unknown Sources").
4. Open the app, type in the IP address shown on your PC, and connect!

---

## ❓ Troubleshooting

*   **My phone cannot connect to the server (Timeout / Site Cannot Be Reached).**
    *   Ensure both your PC and your phone are connected to the exactly the same Wi-Fi network.
    *   Windows Firewall might be blocking port `5000`. When Windows asks if you want to allow Python/Server through the firewall, click **Allow**. Or temporarily disable your firewall to test.
*   **The server shows "ViGEmBus driver not found".**
    *   You missed Step 1. Please install the ViGEmBus driver linked above.

---

> 👨‍💻 **Are you a Developer?**
> If you want to view the source code, see the architecture, or compile the project yourself, please head over to the [Developer Documentation](docs/DEVELOPER.md).
