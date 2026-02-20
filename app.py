from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import vgamepad as vg
import socket as sock

app = Flask(__name__, static_folder='public', static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', manage_session=False)

# ── Gamepad pool (one per connected player, max 4) ──────────────────────────
MAX_PLAYERS = 4
gamepads = {}       # sid -> VX360Gamepad
player_ids = {}     # sid -> player number (1-based)
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

# ── Static file routes ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/sw.js')
def service_worker():
    response = send_from_directory('public', 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

# ── Socket events ─────────────────────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    from flask import request
    sid = request.sid
    if len(gamepads) >= MAX_PLAYERS:
        emit('error', 'Server full – max 4 players')
        return

    slot = _player_slots.pop(0)
    gp = vg.VX360Gamepad()
    gamepads[sid] = gp
    player_ids[sid] = slot

    gp.update()  # register with ViGEm
    emit('player_id', slot)
    print(f"[+] Player {slot} connected  (sid={sid[:8]})")

@socketio.on('disconnect')
def on_disconnect():
    from flask import request
    sid = request.sid
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
        print(f"[-] Player {slot} disconnected (sid={sid[:8]})")

@socketio.on('input')
def handle_input(data):
    from flask import request
    gp = gamepads.get(request.sid)
    if not gp:
        return

    # ─ Joysticks ─
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

    # ─ Triggers (analog 0.0 – 1.0) ─
    gp.left_trigger_float(value_float=float(data.get('lt', 0)))
    gp.right_trigger_float(value_float=float(data.get('rt', 0)))

    # ─ Buttons ─
    buttons = data.get('buttons', {})
    for btn_id, pressed in buttons.items():
        if btn_id in BUTTON_MAP:
            if pressed:
                gp.press_button(button=BUTTON_MAP[btn_id])
            else:
                gp.release_button(button=BUTTON_MAP[btn_id])

    gp.update()

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    hostname = sock.gethostname()
    try:
        local_ip = sock.gethostbyname(hostname)
    except Exception:
        local_ip = '127.0.0.1'

    print("=" * 50)
    print("  Xbox Web Controller Server")
    print("=" * 50)
    print(f"  ➜  Local:   http://localhost:5000")
    print(f"  ➜  Network: http://{local_ip}:5000")
    print("  Open the Network URL on your phone!")
    print("=" * 50)

    socketio.run(app, host='0.0.0.0', port=5000, debug=False)