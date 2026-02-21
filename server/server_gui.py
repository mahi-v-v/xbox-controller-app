"""
Xbox Web Controller — Server GUI
A Tkinter-based GUI that wraps the Flask+SocketIO gamepad server.
Displays status, live logs, QR code, and Start/Stop controls.
"""

import sys, os, io, threading, socket as sock, logging, queue, time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ── Fix for PyInstaller bundled paths ─────────────────────────────────────────
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller extracts to _MEIPASS. Data folders are at the root.
        clean_path = relative_path.replace('../', '').replace('..\\', '')
        return os.path.join(sys._MEIPASS, clean_path)
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

# ── Logging redirect to GUI ──────────────────────────────────────────────────
log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))

# ── Check ViGEmBus ────────────────────────────────────────────────────────────
def check_vigembus():
    """Return True if ViGEmBus driver is installed."""
    try:
        import vgamepad as vg
        gp = vg.VX360Gamepad()
        del gp
        return True
    except Exception:
        return False

# ── QR Code generation ───────────────────────────────────────────────────────
def generate_qr_image(url, size=160):
    """Generate a QR code as a Tkinter-compatible PhotoImage."""
    try:
        import qrcode
        from PIL import Image, ImageTk
        qr = qrcode.QRCode(version=1, box_size=4, border=2,
                           error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#52b043", back_color="#1a1a2e")
        img = img.resize((size, size), Image.NEAREST)
        return ImageTk.PhotoImage(img)
    except ImportError:
        return None

# ── Get local IP ──────────────────────────────────────────────────────────────
def get_local_ip():
    try:
        s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return sock.gethostbyname(sock.gethostname())
        except Exception:
            return "127.0.0.1"

# ── Server Thread ─────────────────────────────────────────────────────────────
class ServerThread(threading.Thread):
    def __init__(self, host, port, log_callback):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.log = log_callback
        self.socketio = None
        self.running = False

    def run(self):
        self.running = True
        try:
            # Import server components
            from flask import Flask, send_from_directory, request as flask_request
            from flask_socketio import SocketIO, emit
            import vgamepad as vg

            public_dir = resource_path('../webapp')
            website_dir = resource_path('../website')
            apk_dir = resource_path('../apk')
            app = Flask(__name__)

            # Suppress Flask/Werkzeug default logging
            wlog = logging.getLogger('werkzeug')
            wlog.setLevel(logging.ERROR)

            socketio = SocketIO(app, cors_allowed_origins="*",
                                async_mode='threading', manage_session=False)
            self.socketio = socketio

            # Gamepad pool
            MAX_PLAYERS = 4
            gamepads = {}
            player_ids = {}
            _player_slots = list(range(1, MAX_PLAYERS + 1))

            BUTTON_MAP = {
                'a':          vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                'b':          vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                'x':          vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                'y':          vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                'lb':         vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                'rb':         vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                'view':       vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                'menu':       vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                'home':       vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
                'dpad-up':    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                'dpad-down':  vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                'dpad-left':  vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                'dpad-right': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                'ls-click':   vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                'rs-click':   vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            }

            @app.route('/')
            def website_index():
                return send_from_directory(website_dir, 'index.html')
                
            @app.route('/<path:filename>')
            def website_assets(filename):
                return send_from_directory(website_dir, filename)

            @app.route('/play')
            @app.route('/play/')
            def controller_index():
                return send_from_directory(public_dir, 'index.html')
                
            @app.route('/play/<path:filename>')
            def controller_assets(filename):
                return send_from_directory(public_dir, filename)

            @app.route('/play/sw.js')
            def service_worker():
                response = send_from_directory(public_dir, 'sw.js')
                response.headers['Service-Worker-Allowed'] = '/play/'
                response.headers['Cache-Control'] = 'no-cache'
                return response
                
            @app.route('/download/apk')
            def download_apk():
                return send_from_directory(apk_dir, 'app-debug.apk', as_attachment=True, download_name='XboxController.apk')

            @socketio.on('connect')
            def on_connect():
                sid = flask_request.sid
                if len(gamepads) >= MAX_PLAYERS:
                    emit('error', 'Server full – max 4 players')
                    return
                slot = _player_slots.pop(0)
                gp = vg.VX360Gamepad()
                gamepads[sid] = gp
                player_ids[sid] = slot
                gp.update()
                emit('player_id', slot)
                self.log(f"[+] Player {slot} connected")

            @socketio.on('disconnect')
            def on_disconnect():
                sid = flask_request.sid
                if sid in gamepads:
                    try:
                        gp = gamepads.pop(sid)
                        gp.reset()
                        gp.update()
                    except Exception:
                        pass
                    slot = player_ids.pop(sid, None)
                    if slot:
                        _player_slots.insert(0, slot)
                        _player_slots.sort()
                    self.log(f"[-] Player {slot} disconnected")

            @socketio.on('input')
            def handle_input(data):
                gp = gamepads.get(flask_request.sid)
                if not gp:
                    return
                ls = data.get('ls', {})
                rs = data.get('rs', {})
                gp.left_joystick_float(
                    x_value_float=float(ls.get('x', 0)),
                    y_value_float=-float(ls.get('y', 0))
                )
                gp.right_joystick_float(
                    x_value_float=float(rs.get('x', 0)),
                    y_value_float=-float(rs.get('y', 0))
                )
                gp.left_trigger_float(value_float=float(data.get('lt', 0)))
                gp.right_trigger_float(value_float=float(data.get('rt', 0)))
                buttons = data.get('buttons', {})
                for btn_id, pressed in buttons.items():
                    if btn_id in BUTTON_MAP:
                        if pressed:
                            gp.press_button(button=BUTTON_MAP[btn_id])
                        else:
                            gp.release_button(button=BUTTON_MAP[btn_id])
                gp.update()

            self.log(f"Server started on http://{self.host}:{self.port}")
            socketio.run(app, host='0.0.0.0', port=self.port,
                         debug=False, use_reloader=False, log_output=False, allow_unsafe_werkzeug=True)
        except Exception as e:
            self.log(f"[ERROR] {e}")
            self.running = False

# ── Main GUI ──────────────────────────────────────────────────────────────────

class ControllerServerApp:
    BG          = "#0f0f1e"
    BG_CARD     = "#1a1a2e"
    BG_INPUT    = "#12122a"
    GREEN       = "#52b043"
    GREEN_DIM   = "#2d6b26"
    RED         = "#e53935"
    TEXT        = "#e0e0e0"
    TEXT_DIM    = "#7a7a9a"
    FONT        = ("Segoe UI", 10)
    FONT_BOLD   = ("Segoe UI", 10, "bold")
    FONT_TITLE  = ("Segoe UI", 16, "bold")
    FONT_MONO   = ("Cascadia Code", 9)
    FONT_BIG    = ("Segoe UI", 22, "bold")

    def __init__(self, root):
        self.root = root
        self.root.title("Xbox Controller Server")
        self.root.configure(bg=self.BG)
        self.root.geometry("680x520")
        self.root.minsize(600, 450)
        self.root.resizable(True, True)

        self.server_thread = None
        self.local_ip = get_local_ip()
        self.port = 5000
        self.qr_image = None

        self._build_ui()
        self._check_vigembus()
        self._poll_logs()

    def _build_ui(self):
        # ── Top bar ──
        top = tk.Frame(self.root, bg=self.BG)
        top.pack(fill=tk.X, padx=16, pady=(16, 8))

        tk.Label(top, text="🎮", font=("Segoe UI", 20), bg=self.BG,
                 fg=self.GREEN).pack(side=tk.LEFT)
        tk.Label(top, text="  Xbox Controller Server", font=self.FONT_TITLE,
                 bg=self.BG, fg=self.TEXT).pack(side=tk.LEFT)

        self.status_dot = tk.Label(top, text="●", font=("Segoe UI", 14),
                                   bg=self.BG, fg=self.RED)
        self.status_dot.pack(side=tk.RIGHT, padx=(0, 4))
        self.status_label = tk.Label(top, text="Stopped", font=self.FONT_BOLD,
                                     bg=self.BG, fg=self.RED)
        self.status_label.pack(side=tk.RIGHT)

        # ── Content area ──
        content = tk.Frame(self.root, bg=self.BG)
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(1, weight=1)

        # ── Left: QR + Connection Info card ──
        left_card = tk.Frame(content, bg=self.BG_CARD, relief=tk.FLAT,
                             highlightbackground="#2a2a4a", highlightthickness=1)
        left_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 8), pady=0)

        tk.Label(left_card, text="CONNECTION", font=("Segoe UI", 8, "bold"),
                 bg=self.BG_CARD, fg=self.TEXT_DIM,
                 anchor="w").pack(fill=tk.X, padx=12, pady=(12, 4))

        # QR code area
        self.qr_label = tk.Label(left_card, bg=self.BG_CARD, text="QR Code\nwill appear\nwhen running",
                                  fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.qr_label.pack(padx=12, pady=8)

        # IP display
        ip_frame = tk.Frame(left_card, bg=self.BG_CARD)
        ip_frame.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(ip_frame, text="IP Address", font=("Segoe UI", 8),
                 bg=self.BG_CARD, fg=self.TEXT_DIM, anchor="w").pack(fill=tk.X)
        self.ip_label = tk.Label(ip_frame, text=self.local_ip,
                                  font=self.FONT_BIG, bg=self.BG_CARD,
                                  fg=self.GREEN, anchor="w")
        self.ip_label.pack(fill=tk.X)

        # Port
        port_frame = tk.Frame(left_card, bg=self.BG_CARD)
        port_frame.pack(fill=tk.X, padx=12, pady=(0, 4))

        tk.Label(port_frame, text="Port", font=("Segoe UI", 8),
                 bg=self.BG_CARD, fg=self.TEXT_DIM, anchor="w").pack(fill=tk.X)

        self.port_var = tk.StringVar(value="5000")
        self.port_entry = tk.Entry(port_frame, textvariable=self.port_var,
                                    font=self.FONT_BOLD, bg=self.BG_INPUT,
                                    fg=self.TEXT, insertbackground=self.TEXT,
                                    relief=tk.FLAT, bd=0, width=8,
                                    highlightbackground="#2a2a4a",
                                    highlightthickness=1)
        self.port_entry.pack(fill=tk.X, pady=2)

        # Copy URL button
        self.copy_btn = tk.Button(left_card, text="📋 Copy URL",
                                   font=self.FONT_BOLD, bg="#2a2a4a",
                                   fg=self.TEXT, activebackground="#3a3a5a",
                                   activeforeground=self.TEXT, relief=tk.FLAT,
                                   cursor="hand2", command=self._copy_url)
        self.copy_btn.pack(fill=tk.X, padx=12, pady=(8, 4))

        # ViGEmBus status
        self.vigem_label = tk.Label(left_card, text="", font=("Segoe UI", 8),
                                     bg=self.BG_CARD, fg=self.TEXT_DIM,
                                     wraplength=160, justify="left")
        self.vigem_label.pack(fill=tk.X, padx=12, pady=(8, 12))

        # ── Right: Log area ──
        log_header = tk.Frame(content, bg=self.BG)
        log_header.grid(row=0, column=1, sticky="ew", pady=(0, 4))

        tk.Label(log_header, text="LIVE LOG", font=("Segoe UI", 8, "bold"),
                 bg=self.BG, fg=self.TEXT_DIM, anchor="w").pack(side=tk.LEFT)

        self.clear_btn = tk.Button(log_header, text="Clear", font=("Segoe UI", 8),
                                    bg=self.BG, fg=self.TEXT_DIM,
                                    activebackground=self.BG_CARD,
                                    activeforeground=self.TEXT, relief=tk.FLAT,
                                    cursor="hand2", command=self._clear_logs)
        self.clear_btn.pack(side=tk.RIGHT)

        self.log_area = scrolledtext.ScrolledText(
            content, font=self.FONT_MONO, bg=self.BG_CARD, fg=self.TEXT,
            insertbackground=self.TEXT, relief=tk.FLAT, bd=0,
            highlightbackground="#2a2a4a", highlightthickness=1,
            wrap=tk.WORD, state=tk.DISABLED, cursor="arrow"
        )
        self.log_area.grid(row=1, column=1, sticky="nsew")

        # Configure log colors
        self.log_area.tag_configure("connect",    foreground=self.GREEN)
        self.log_area.tag_configure("disconnect", foreground="#ffa726")
        self.log_area.tag_configure("error",      foreground=self.RED)
        self.log_area.tag_configure("info",       foreground=self.TEXT_DIM)
        self.log_area.tag_configure("timestamp",  foreground="#5a5a7a")

        # ── Bottom bar ──
        bottom = tk.Frame(self.root, bg=self.BG)
        bottom.pack(fill=tk.X, padx=16, pady=(8, 16))

        self.start_btn = tk.Button(
            bottom, text="▶  Start Server", font=self.FONT_BOLD,
            bg=self.GREEN, fg="white", activebackground=self.GREEN_DIM,
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            padx=24, pady=8, command=self._toggle_server
        )
        self.start_btn.pack(side=tk.LEFT)

        self.player_label = tk.Label(bottom, text="Players: 0 / 4",
                                      font=self.FONT, bg=self.BG,
                                      fg=self.TEXT_DIM)
        self.player_label.pack(side=tk.RIGHT)

    def _check_vigembus(self):
        """Check if ViGEmBus driver is installed."""
        def check():
            ok = check_vigembus()
            self.root.after(0, lambda: self._update_vigem_status(ok))
        threading.Thread(target=check, daemon=True).start()

    def _update_vigem_status(self, installed):
        if installed:
            self.vigem_label.config(text="✅ ViGEmBus driver detected",
                                     fg=self.GREEN)
            if hasattr(self, 'install_driver_btn') and self.install_driver_btn.winfo_exists():
                self.install_driver_btn.destroy()
        else:
            self.vigem_label.config(
                text="⚠️ ViGEmBus driver not found!",
                fg="#ffa726"
            )
            
            if not hasattr(self, 'install_driver_btn') or not self.install_driver_btn.winfo_exists():
                self.install_driver_btn = tk.Button(self.vigem_label.master, text="🔧 Install Driver",
                                                    font=self.FONT_BOLD, bg="#2a2a4a",
                                                    fg=self.TEXT, activebackground="#3a3a5a",
                                                    activeforeground=self.TEXT, relief=tk.FLAT,
                                                    cursor="hand2", command=self._install_driver)
                self.install_driver_btn.pack(fill=tk.X, padx=12, pady=(0, 12))
            
            self._log_message("[WARNING] ViGEmBus driver not installed. Click 'Install Driver'.")

    def _install_driver(self):
        import glob
        drivers_dir = resource_path('../drivers')
        installers = glob.glob(os.path.join(drivers_dir, '*.exe')) + glob.glob(os.path.join(drivers_dir, '*.msi'))
        if installers:
            installer_path = installers[0]
            self._log_message(f"[INFO] Launching {os.path.basename(installer_path)}...")
            try:
                os.startfile(installer_path)
                self._log_message("[INFO] After installing, please restart this server.")
            except Exception as e:
                self._log_message(f"[ERROR] Failed to run installer: {e}")
        else:
            self._log_message("[ERROR] Driver installer not found in the bundled 'drivers' folder.")

    def _toggle_server(self):
        if self.server_thread and self.server_thread.running:
            self._log_message("Server stop requires restarting the app.")
            return
        else:
            self._start_server()

    def _start_server(self):
        try:
            self.port = int(self.port_var.get())
        except ValueError:
            self._log_message("[ERROR] Invalid port number")
            return

        self.local_ip = get_local_ip()
        self.ip_label.config(text=self.local_ip)

        # Update UI state
        self.status_dot.config(fg=self.GREEN)
        self.status_label.config(text="Running", fg=self.GREEN)
        self.start_btn.config(text="●  Server Running", bg="#2a2a4a",
                               state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)

        # Generate QR code
        url = f"http://{self.local_ip}:{self.port}"
        qr_img = generate_qr_image(url)
        if qr_img:
            self.qr_image = qr_img  # Keep reference
            self.qr_label.config(image=qr_img, text="")
        else:
            self.qr_label.config(text=f"Scan:\n{url}", fg=self.GREEN)

        # Start server thread
        self.server_thread = ServerThread(
            self.local_ip, self.port, self._log_message
        )
        self.server_thread.start()

    def _log_message(self, msg):
        """Thread-safe log message."""
        log_queue.put(msg)

    def _poll_logs(self):
        """Poll the log queue and display messages."""
        player_count = 0
        while not log_queue.empty():
            msg = log_queue.get_nowait()
            self.log_area.config(state=tk.NORMAL)

            # Timestamp
            ts = time.strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{ts}] ", "timestamp")

            # Color-coded messages
            if "[+]" in msg:
                self.log_area.insert(tk.END, msg + "\n", "connect")
                player_count += 1
            elif "[-]" in msg:
                self.log_area.insert(tk.END, msg + "\n", "disconnect")
                player_count = max(0, player_count - 1)
            elif "[ERROR]" in msg or "[WARNING]" in msg:
                self.log_area.insert(tk.END, msg + "\n", "error")
            else:
                self.log_area.insert(tk.END, msg + "\n", "info")

            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)

        self.root.after(150, self._poll_logs)

    def _copy_url(self):
        url = f"http://{self.local_ip}:{self.port_var.get()}"
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.copy_btn.config(text="✅ Copied!")
        self.root.after(1500, lambda: self.copy_btn.config(text="📋 Copy URL"))

    def _clear_logs(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state=tk.DISABLED)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()

    # Try to set DPI awareness for sharp text on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = ControllerServerApp(root)
    root.mainloop()
