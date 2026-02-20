// ====== SOCKET ======
const socket = io();

// ====== STATE ======
const state = {
    ls: { x: 0, y: 0 },
    rs: { x: 0, y: 0 },
    buttons: {},
    lt: 0,
    rt: 0,
};

let sendScheduled = false;
function scheduleEmit() {
    if (sendScheduled) return;
    sendScheduled = true;
    requestAnimationFrame(() => {
        socket.emit('input', state);
        sendScheduled = false;
    });
}

// ====== STATUS ======
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const playerBadge = document.getElementById('player-badge');

socket.on('connect', () => {
    statusDot.classList.add('connected');
    statusText.textContent = 'Connected';
});
socket.on('disconnect', () => {
    statusDot.classList.remove('connected');
    statusText.textContent = 'Disconnected';
    playerBadge.textContent = '';
});
socket.on('player_id', (id) => {
    playerBadge.textContent = `P${id}`;
});

// ====== HAPTIC VIBRATION ======
function vibrate(pattern = 30) {
    if (navigator.vibrate) {
        navigator.vibrate(pattern);
    }
}

function pulseRipple(el, e) {
    const r = document.createElement('span');
    r.className = 'ripple';

    // Position ripple at touch point or center
    if (e && e.changedTouches && e.changedTouches[0]) {
        const rect = el.getBoundingClientRect();
        const x = e.changedTouches[0].clientX - rect.left;
        const y = e.changedTouches[0].clientY - rect.top;
        r.style.left = x + 'px';
        r.style.top = y + 'px';
    } else if (e && e.clientX !== undefined) {
        const rect = el.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        r.style.left = x + 'px';
        r.style.top = y + 'px';
    }

    el.appendChild(r);
    r.addEventListener('animationend', () => r.remove());
}

// Unlock haptics on first touch
let hapticsUnlocked = false;
function unlockHaptics() {
    if (hapticsUnlocked) return;
    vibrate(10);
    hapticsUnlocked = true;
    window.removeEventListener('touchstart', unlockHaptics);
    window.removeEventListener('mousedown', unlockHaptics);
}
window.addEventListener('touchstart', unlockHaptics, { once: true });
window.addEventListener('mousedown', unlockHaptics, { once: true });

// ====== GENERIC BUTTON HANDLER ======
function setupButton(el, stateKey) {
    const onDown = (e) => {
        e.preventDefault();
        if (state.buttons[stateKey]) return;
        state.buttons[stateKey] = true;
        el.classList.add('active');

        // Distinct haptics for system buttons
        if (['home', 'menu', 'view'].includes(stateKey)) {
            vibrate(stateKey === 'home' ? [40, 30, 40] : 45);
        } else {
            vibrate(20);
        }

        pulseRipple(el, e);
        scheduleEmit();
    };
    const onUp = (e) => {
        e.preventDefault();
        if (!state.buttons[stateKey]) return;
        state.buttons[stateKey] = false;
        el.classList.remove('active');
        scheduleEmit();
    };

    el.addEventListener('touchstart', onDown, { passive: false });
    el.addEventListener('touchend', onUp, { passive: false });
    el.addEventListener('touchcancel', onUp, { passive: false });
    // mouse fallback for desktop testing
    el.addEventListener('mousedown', onDown, { passive: false });
    el.addEventListener('mouseup', onUp, { passive: false });
    el.addEventListener('mouseleave', onUp, { passive: false });
}

// Register all face/dpad/sys buttons
['a', 'b', 'x', 'y',
    'dpad-up', 'dpad-down', 'dpad-left', 'dpad-right',
    'lb', 'rb', 'view', 'menu', 'home',
    'ls-click', 'rs-click'].forEach(id => {
        const el = document.getElementById(id);
        if (el) setupButton(el, id);
    });

// ====== ANALOG TRIGGERS (hold = analog fill) ======
function setupTrigger(id, stateKey, fillId) {
    const el = document.getElementById(id);
    const fill = document.getElementById(fillId);

    let interval = null;
    let value = 0;

    const ramp = (target) => {
        clearInterval(interval);
        interval = setInterval(() => {
            value = target === 1
                ? Math.min(1, value + 0.07)
                : Math.max(0, value - 0.07);
            fill.style.height = (value * 100) + '%';
            state[stateKey] = value;
            scheduleEmit();
            if (value === target) clearInterval(interval);
        }, 16);
    };

    const onDown = (e) => {
        e.preventDefault();
        el.classList.add('active');
        vibrate(15);
        pulseRipple(el, e);
        ramp(1);
    };
    const onUp = (e) => {
        e.preventDefault();
        el.classList.remove('active');
        ramp(0);
    };

    el.addEventListener('touchstart', onDown, { passive: false });
    el.addEventListener('touchend', onUp, { passive: false });
    el.addEventListener('touchcancel', onUp, { passive: false });
    el.addEventListener('mousedown', onDown, { passive: false });
    el.addEventListener('mouseup', onUp, { passive: false });
    el.addEventListener('mouseleave', onUp, { passive: false });
}

setupTrigger('lt', 'lt', 'lt-fill');
setupTrigger('rt', 'rt', 'rt-fill');

// ====== JOYSTICK ======
function setupJoystick(wrapperId, stickId, stateKey) {
    const wrapper = document.getElementById(wrapperId);
    const stick = document.getElementById(stickId);
    let activeTouch = null;

    const getCenter = () => {
        const r = wrapper.getBoundingClientRect();
        return { cx: r.left + r.width / 2, cy: r.top + r.height / 2, maxDist: r.width * 0.4 };
    };

    const move = (clientX, clientY) => {
        const { cx, cy, maxDist } = getCenter();
        let dx = clientX - cx;
        let dy = clientY - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > maxDist) {
            dx *= maxDist / dist;
            dy *= maxDist / dist;
        }
        stick.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
        state[stateKey] = { x: dx / maxDist, y: dy / maxDist };
        scheduleEmit();
    };

    const reset = () => {
        stick.style.transform = 'translate(-50%, -50%)';
        state[stateKey] = { x: 0, y: 0 };
        wrapper.classList.remove('active');
        activeTouch = null;
        scheduleEmit();
    };

    wrapper.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (activeTouch !== null) return;
        activeTouch = e.changedTouches[0].identifier;
        wrapper.classList.add('active');
        vibrate(10);
        move(e.changedTouches[0].clientX, e.changedTouches[0].clientY);
    }, { passive: false });

    wrapper.addEventListener('touchmove', (e) => {
        e.preventDefault();
        for (const t of e.changedTouches) {
            if (t.identifier === activeTouch) {
                move(t.clientX, t.clientY);
                break;
            }
        }
    }, { passive: false });

    wrapper.addEventListener('touchend', (e) => {
        e.preventDefault();
        for (const t of e.changedTouches) {
            if (t.identifier === activeTouch) { reset(); break; }
        }
    }, { passive: false });

    wrapper.addEventListener('touchcancel', () => reset(), { passive: false });

    // Mouse fallback
    let mouseDown = false;
    wrapper.addEventListener('mousedown', (e) => {
        mouseDown = true;
        wrapper.classList.add('active');
        move(e.clientX, e.clientY);
    });
    window.addEventListener('mousemove', (e) => {
        if (mouseDown) move(e.clientX, e.clientY);
    });
    window.addEventListener('mouseup', () => {
        if (mouseDown) { mouseDown = false; reset(); }
    });
}

setupJoystick('ls', 'ls-stick', 'ls');
setupJoystick('rs', 'rs-stick', 'rs');

// ====== PREVENT ALL DEFAULT BROWSER GESTURES ======
document.addEventListener('gesturestart', e => e.preventDefault());
document.addEventListener('contextmenu', e => e.preventDefault());
document.addEventListener('touchmove', e => {
    if (e.target.closest('.joystick, .trigger-btn')) return;
    e.preventDefault();
}, { passive: false });