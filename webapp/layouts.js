// ====== LAYOUT PRESETS ======
// Each preset can rearrange the layout AND change button labels/colors.

const LAYOUT_PRESETS = ['default', 'ps', 'nintendo', 'southpaw', 'racing', 'minimal'];
const LAYOUT_LABELS = {
    default: '🎮 Xbox',
    ps: '🎮 PlayStation',
    nintendo: '🎮 Nintendo',
    southpaw: '🔄 Southpaw',
    racing: '🏎️ Racing',
    minimal: '⚡ Minimal',
};

// Button label & color overrides per preset
const BUTTON_THEMES = {
    default: {
        a: { label: 'A', cssClass: 'a-btn' },
        b: { label: 'B', cssClass: 'b-btn' },
        x: { label: 'X', cssClass: 'x-btn' },
        y: { label: 'Y', cssClass: 'y-btn' },
        lb: 'LB', rb: 'RB', lt: 'LT', rt: 'RT',
        view: 'View', menu: 'Menu',
    },
    ps: {
        a: { label: '✕', cssClass: 'ps-cross' },
        b: { label: '○', cssClass: 'ps-circle' },
        x: { label: '□', cssClass: 'ps-square' },
        y: { label: '△', cssClass: 'ps-triangle' },
        lb: 'L1', rb: 'R1', lt: 'L2', rt: 'R2',
        view: 'Share', menu: 'Options',
    },
    nintendo: {
        // Nintendo swaps A/B and X/Y positions
        a: { label: 'B', cssClass: 'nin-b' },
        b: { label: 'A', cssClass: 'nin-a' },
        x: { label: 'Y', cssClass: 'nin-y' },
        y: { label: 'X', cssClass: 'nin-x' },
        lb: 'L', rb: 'R', lt: 'ZL', rt: 'ZR',
        view: '-', menu: '+',
    },
};

// Elements that get relabeled
const FACE_BUTTONS = ['a', 'b', 'x', 'y'];
const FACE_CSS_CLASSES = [
    'a-btn', 'b-btn', 'x-btn', 'y-btn',
    'ps-cross', 'ps-circle', 'ps-square', 'ps-triangle',
    'nin-a', 'nin-b', 'nin-x', 'nin-y',
];

let currentPresetIndex = 0;

// Load saved preset
(function loadPreset() {
    const saved = localStorage.getItem('xbox_layout_preset') || 'default';
    const idx = LAYOUT_PRESETS.indexOf(saved);
    currentPresetIndex = idx >= 0 ? idx : 0;
    applyPreset(LAYOUT_PRESETS[currentPresetIndex]);
})();

function applyPreset(presetName) {
    const controller = document.getElementById('controller');

    // Remove all preset layout classes
    LAYOUT_PRESETS.forEach(p => controller.classList.remove(`layout-${p}`));

    // Apply CSS class (default has no class)
    if (presetName !== 'default') {
        controller.classList.add(`layout-${presetName}`);
    }

    // Determine which button theme to use
    // ps/nintendo have their own themes; all others fall back to 'default'
    const themeName = BUTTON_THEMES[presetName] ? presetName : 'default';
    const theme = BUTTON_THEMES[themeName];

    // Apply face button label & color changes
    FACE_BUTTONS.forEach(btnId => {
        const el = document.getElementById(btnId);
        if (!el) return;

        const btnTheme = theme[btnId];

        // Remove all theme-specific CSS classes
        FACE_CSS_CLASSES.forEach(cls => el.classList.remove(cls));

        // Apply new class and label
        el.classList.add(btnTheme.cssClass);
        el.textContent = btnTheme.label;
    });

    // Apply shoulder/trigger/system label changes
    const lbEl = document.getElementById('lb');
    const rbEl = document.getElementById('rb');
    if (lbEl) lbEl.textContent = theme.lb;
    if (rbEl) rbEl.textContent = theme.rb;

    // Triggers — they have a <span> inside for the label
    const ltEl = document.getElementById('lt');
    const rtEl = document.getElementById('rt');
    if (ltEl) {
        const span = ltEl.querySelector('span');
        if (span) span.textContent = theme.lt;
    }
    if (rtEl) {
        const span = rtEl.querySelector('span');
        if (span) span.textContent = theme.rt;
    }

    // System buttons — they have <span> labels
    const viewEl = document.getElementById('view');
    const menuEl = document.getElementById('menu');
    if (viewEl) {
        const span = viewEl.querySelector('span');
        if (span) span.textContent = theme.view;
    }
    if (menuEl) {
        const span = menuEl.querySelector('span');
        if (span) span.textContent = theme.menu;
    }

    localStorage.setItem('xbox_layout_preset', presetName);

    // Update toggle button label
    const toggleLabel = document.getElementById('layout-toggle-label');
    if (toggleLabel) {
        toggleLabel.textContent = LAYOUT_LABELS[presetName];
    }
}

function cyclePreset() {
    currentPresetIndex = (currentPresetIndex + 1) % LAYOUT_PRESETS.length;
    const preset = LAYOUT_PRESETS[currentPresetIndex];
    applyPreset(preset);

    if (navigator.vibrate) navigator.vibrate(15);

    const btn = document.getElementById('layout-toggle-btn');
    if (btn) {
        btn.classList.add('flash');
        setTimeout(() => btn.classList.remove('flash'), 300);
    }
}

// Expose for other scripts
window.applyPreset = applyPreset;
window.cyclePreset = cyclePreset;
window.LAYOUT_PRESETS = LAYOUT_PRESETS;
window.LAYOUT_LABELS = LAYOUT_LABELS;
