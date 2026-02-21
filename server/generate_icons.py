"""
Generates icon-192.png and icon-512.png for the Xbox Controller PWA.
Run once: python generate_icons.py
Requires: pip install Pillow
"""
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'])
    from PIL import Image, ImageDraw, ImageFont

import os, math

def draw_xbox_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background circle – Xbox green
    margin = size * 0.04
    d.ellipse([margin, margin, size - margin, size - margin], fill='#107c10')

    # Inner white circle (lighter highlight)
    inner_m = size * 0.15
    d.ellipse([inner_m, inner_m, size - inner_m, size - inner_m],
              fill=None, outline='rgba(255,255,255,60)', width=max(2, size // 60))

    # Draw four dots like Xbox logo: up(green lighter), down, left, right + center X
    cx, cy = size / 2, size / 2
    r = size * 0.22   # radius of the 4 balls
    ball_r = size * 0.08

    positions = {
        'top':    (cx,          cy - r),
        'bottom': (cx,          cy + r),
        'left':   (cx - r,      cy),
        'right':  (cx + r,      cy),
    }
    colors = {
        'top':    '#ffffff',
        'bottom': '#ffffff',
        'left':   '#ffffff',
        'right':  '#ffffff',
    }
    for key, (px, py) in positions.items():
        d.ellipse([px - ball_r, py - ball_r, px + ball_r, py + ball_r],
                  fill=colors[key])

    # Center X
    lw = max(3, size // 32)
    x0, y0 = cx - size * 0.12, cy - size * 0.12
    x1, y1 = cx + size * 0.12, cy + size * 0.12
    d.line([x0, y0, x1, y1], fill='white', width=lw)
    d.line([x1, y0, x0, y1], fill='white', width=lw)

    return img

out_dir = os.path.join(os.path.dirname(__file__), '..', 'webapp')
for sz in [192, 512]:
    icon = draw_xbox_icon(sz)
    path = os.path.join(out_dir, f'icon-{sz}.png')
    icon.save(path, 'PNG')
    print(f'Saved {path}')

print('Icons generated successfully!')
