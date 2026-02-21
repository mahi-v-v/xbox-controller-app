// ====== LAYOUT EDITOR ======
// Allows drag-to-move and pinch-to-resize for every controller element.
// Saves custom positions/scales to localStorage.

(function () {
    'use strict';

    const STORAGE_KEY = 'xbox_custom_layout';

    // Elements that can be individually repositioned/resized
    const EDITABLE_SELECTORS = [
        '[data-element-id="ls"]',
        '[data-element-id="rs"]',
        '[data-element-id="dpad"]',
        '[data-element-id="abxy"]',
        '[data-element-id="lt"]',
        '[data-element-id="rt"]',
        '[data-element-id="lb"]',
        '[data-element-id="rb"]',
        '[data-element-id="ls-click"]',
        '[data-element-id="rs-click"]',
        '[data-element-id="view"]',
        '[data-element-id="home"]',
        '[data-element-id="menu"]',
    ];

    let editMode = false;
    let customLayout = {}; // { elementId: { x, y, scale } }
    let editToolbar = null;

    // ── Load saved layout ──
    function loadCustomLayout() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) customLayout = JSON.parse(saved);
        } catch (e) {
            customLayout = {};
        }
    }

    function saveCustomLayout() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(customLayout));
    }

    // ── Apply saved transforms ──
    function applyCustomLayout() {
        EDITABLE_SELECTORS.forEach(sel => {
            const el = document.querySelector(sel);
            if (!el) return;
            const id = el.dataset.elementId;
            const data = customLayout[id];
            if (data) {
                el.style.transform = `translate(${data.x || 0}px, ${data.y || 0}px) scale(${data.scale || 1})`;
                el.classList.add('custom-positioned');
            }
        });
    }

    function clearCustomTransforms() {
        EDITABLE_SELECTORS.forEach(sel => {
            const el = document.querySelector(sel);
            if (!el) return;
            el.style.transform = '';
            el.classList.remove('custom-positioned');
        });
    }

    // ── Create Edit Toolbar ──
    function createToolbar() {
        if (editToolbar) return;

        editToolbar = document.createElement('div');
        editToolbar.id = 'edit-toolbar';
        editToolbar.innerHTML = `
            <span class="edit-toolbar-title">✏️ Edit Mode</span>
            <div class="edit-toolbar-actions">
                <button id="edit-reset-btn" class="edit-action-btn" title="Reset to Default">↩️ Reset</button>
                <button id="edit-done-btn" class="edit-action-btn edit-done" title="Save & Exit">✅ Done</button>
            </div>
        `;
        document.body.appendChild(editToolbar);

        document.getElementById('edit-reset-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            customLayout = {};
            saveCustomLayout();
            clearCustomTransforms();
            if (navigator.vibrate) navigator.vibrate([20, 30, 20]);
        });

        document.getElementById('edit-done-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            exitEditMode();
        });
    }

    // ── Enter / Exit Edit Mode ──
    function enterEditMode() {
        editMode = true;
        window.isEditMode = true;
        document.body.classList.add('editing');
        createToolbar();
        editToolbar.classList.add('visible');

        // Add drag handles to each editable element
        EDITABLE_SELECTORS.forEach(sel => {
            const el = document.querySelector(sel);
            if (!el) return;
            el.classList.add('editable');
            setupDrag(el);
            setupPinchResize(el);
        });

        if (navigator.vibrate) navigator.vibrate(30);
    }

    function exitEditMode() {
        editMode = false;
        window.isEditMode = false;
        document.body.classList.remove('editing');
        if (editToolbar) editToolbar.classList.remove('visible');

        // Remove editable state
        EDITABLE_SELECTORS.forEach(sel => {
            const el = document.querySelector(sel);
            if (!el) return;
            el.classList.remove('editable', 'dragging');
        });

        saveCustomLayout();
        if (navigator.vibrate) navigator.vibrate(15);
    }

    // ── Drag Logic ──
    function setupDrag(el) {
        if (el._dragSetup) return;
        el._dragSetup = true;

        let startX, startY, origX, origY;
        let activeTouchId = null;

        const getPos = () => {
            const id = el.dataset.elementId;
            const data = customLayout[id] || { x: 0, y: 0, scale: 1 };
            return data;
        };

        const setPos = (x, y) => {
            const id = el.dataset.elementId;
            if (!customLayout[id]) customLayout[id] = { x: 0, y: 0, scale: 1 };
            customLayout[id].x = x;
            customLayout[id].y = y;
            const s = customLayout[id].scale || 1;
            el.style.transform = `translate(${x}px, ${y}px) scale(${s})`;
            el.classList.add('custom-positioned');
        };

        el.addEventListener('touchstart', function (e) {
            if (!editMode) return;
            // Only single-finger drag (not pinch)
            if (e.touches.length > 1) return;

            e.preventDefault();
            e.stopPropagation();
            const touch = e.changedTouches[0];
            activeTouchId = touch.identifier;
            startX = touch.clientX;
            startY = touch.clientY;
            const pos = getPos();
            origX = pos.x;
            origY = pos.y;
            el.classList.add('dragging');
        }, { passive: false });

        el.addEventListener('touchmove', function (e) {
            if (!editMode || activeTouchId === null) return;
            // Only process single-finger moves for drag
            if (e.touches.length > 1) return;

            e.preventDefault();
            e.stopPropagation();
            for (const t of e.changedTouches) {
                if (t.identifier === activeTouchId) {
                    const dx = t.clientX - startX;
                    const dy = t.clientY - startY;
                    setPos(origX + dx, origY + dy);
                    break;
                }
            }
        }, { passive: false });

        const endDrag = (e) => {
            if (!editMode) return;
            if (activeTouchId === null) return;
            for (const t of e.changedTouches) {
                if (t.identifier === activeTouchId) {
                    activeTouchId = null;
                    el.classList.remove('dragging');
                    break;
                }
            }
        };

        el.addEventListener('touchend', endDrag, { passive: false });
        el.addEventListener('touchcancel', endDrag, { passive: false });

        // Mouse fallback
        let mouseDown = false;
        el.addEventListener('mousedown', function (e) {
            if (!editMode) return;
            e.preventDefault();
            e.stopPropagation();
            mouseDown = true;
            startX = e.clientX;
            startY = e.clientY;
            const pos = getPos();
            origX = pos.x;
            origY = pos.y;
            el.classList.add('dragging');
        });
        window.addEventListener('mousemove', function (e) {
            if (!editMode || !mouseDown) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            setPos(origX + dx, origY + dy);
        });
        window.addEventListener('mouseup', function () {
            if (mouseDown) {
                mouseDown = false;
                el.classList.remove('dragging');
            }
        });
    }

    // ── Pinch-to-Resize Logic ──
    function setupPinchResize(el) {
        if (el._pinchSetup) return;
        el._pinchSetup = true;

        let initialDist = null;
        let initialScale = 1;

        const getScale = () => {
            const id = el.dataset.elementId;
            const data = customLayout[id];
            return data ? (data.scale || 1) : 1;
        };

        const setScale = (s) => {
            const id = el.dataset.elementId;
            if (!customLayout[id]) customLayout[id] = { x: 0, y: 0, scale: 1 };
            customLayout[id].scale = Math.max(0.4, Math.min(2.5, s));
            const data = customLayout[id];
            el.style.transform = `translate(${data.x || 0}px, ${data.y || 0}px) scale(${data.scale})`;
            el.classList.add('custom-positioned');
        };

        el.addEventListener('touchstart', function (e) {
            if (!editMode) return;
            if (e.touches.length === 2) {
                e.preventDefault();
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                initialDist = Math.sqrt(dx * dx + dy * dy);
                initialScale = getScale();
            }
        }, { passive: false });

        el.addEventListener('touchmove', function (e) {
            if (!editMode || initialDist === null) return;
            if (e.touches.length === 2) {
                e.preventDefault();
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const ratio = dist / initialDist;
                setScale(initialScale * ratio);
            }
        }, { passive: false });

        const endPinch = () => {
            initialDist = null;
        };

        el.addEventListener('touchend', endPinch);
        el.addEventListener('touchcancel', endPinch);
    }

    // ── Edit Mode Toggle via Settings ──
    // Long-press on settings gear opens edit mode
    let settingsLongPress = null;
    const settingsBtn = document.getElementById('settings-btn');

    // Add an explicit edit button in the status bar
    function addEditButton() {
        const statusBar = document.getElementById('status-bar');
        const btn = document.createElement('button');
        btn.id = 'edit-layout-btn';
        btn.className = 'status-icon-btn';
        btn.title = 'Edit Layout';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34a.9959.9959 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
        `;
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (editMode) {
                exitEditMode();
            } else {
                enterEditMode();
            }
        });
        // Insert before settings button
        statusBar.insertBefore(btn, settingsBtn);
    }

    // ── Initialize ──
    loadCustomLayout();
    applyCustomLayout();
    addEditButton();

})();
