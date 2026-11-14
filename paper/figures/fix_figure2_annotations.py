"""Correct the two stratification annotations in Figure 2.

The submitted figure labels TempStrat "Static spatial grouping" and ClimStrat "Dynamic to climate
zones". That is the wrong way round, and it contradicts Section 3.2: a sensor's temperature stratum
is reassigned observation by observation (97 of the 98 sensors fall in more than one), while its
climate zone is fixed by location (none falls in more than one). The labels become

    TempStrat   !  Dynamic to temperature
    ClimStrat   v  Static spatial grouping

Only the two descriptor phrases change. The warning and check marks stay in the columns they were
in, and the type, weight, baselines and centring are reproduced from the original, so nothing else
in the figure moves.

The source is the frozen copy in submission/, not figures/, so the script is idempotent: running it
twice gives the same result rather than editing an already-edited image.

Input : submission/submission_full/figure2.png   (read only; the submitted figure)
Output: figures/figure2.png
Usage : python3 scripts/figures/fix_figure2_annotations.py
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'submission', 'submission_full', 'figure2.png')
DST = os.path.join(ROOT, 'figures', 'figure2.png')

# Times New Roman Italic at 40 px, emboldened by a quarter of a pixel, reproduces the original
# lettering: matched on width (205 px for "Static spatial"), height and ink coverage (0.242).
FONT = '/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf'
SIZE, BOLD, SS, PAD = 40, 0.4, 4, 20

BG_ROW = 1075                     # a row of pure panel background, used to repaint the gradient
ERASE = [(212, 516), (630, 906)]  # x spans to clear; they miss the chevrons at 524-620
EY0, EY1 = 962, 1071
TRI = (220, 968, 264, 1010)       # the warning triangle, kept as pixels: it is a colour glyph
LEFT_CX, RIGHT_CX = 350, 762      # column centres, measured from the original
BASE = {'L1': 1005.2, 'L2': 1052.0, 'R1': 1001.8, 'R2': 1049.2}   # baselines, fitted per column
GAP = 3                           # triangle-to-text gap in the original


def render(text, with_baseline=False):
    """Italic text with synthetic emboldening, drawn oversized and reduced for clean edges."""
    f = ImageFont.truetype(FONT, SIZE * SS)
    im = Image.new('L', ((len(text) + 2) * SIZE * SS, (SIZE + 2 * PAD) * SS), 0)
    ImageDraw.Draw(im).text((PAD * SS, PAD * SS), text, font=f, fill=255)
    r = max(1, int(round(BOLD * SS)))
    im = im.filter(ImageFilter.MaxFilter(2 * r + 1))
    ys, xs = np.where(np.asarray(im) > 20)
    top = ys.min()
    im = im.crop((xs.min(), top, xs.max() + 1, ys.max() + 1))
    out = im.resize((max(1, im.width // SS), max(1, im.height // SS)), Image.LANCZOS)
    if not with_baseline:
        return out
    ascent, _ = f.getmetrics()
    return out, (PAD * SS + ascent - top) / SS


def is_bg(p):
    return (p[..., 0] > 245) & (p[..., 1] > 225) & (p[..., 2] > 150)


def main():
    a = np.array(Image.open(SRC).convert('RGB'))

    patch = a[TRI[1]:TRI[3], TRI[0]:TRI[2]].copy()
    pmask = ~is_bg(patch)
    ink = np.where(pmask.any(axis=0))[0]
    ink_x0, ink_w = int(ink.min()), int(ink.max() - ink.min() + 1)

    bg = a[BG_ROW].copy()                       # the panel's tint varies with x but not with y
    for x0, x1 in ERASE:
        a[EY0:EY1, x0:x1] = bg[x0:x1][None, :, :]
    im = Image.fromarray(a)

    def put(text, baseline, cx=None, x=None):
        m, bl = render(text, with_baseline=True)
        px = int(round(cx - m.width / 2)) if x is None else int(x)
        im.paste(Image.new('RGB', m.size, (0, 0, 0)), (px, int(round(baseline - bl))), m)

    # Left column keeps the warning mark; its phrase becomes the dynamic one
    w1 = render('Dynamic to').width
    start = int(round(LEFT_CX - (ink_w + GAP + w1) / 2))
    im.paste(Image.fromarray(patch), (start - ink_x0, TRI[1]),
             Image.fromarray((pmask * 255).astype('uint8')))
    put('Dynamic to', BASE['L1'], x=start + ink_w + GAP)
    put('temperature', BASE['L2'], cx=LEFT_CX)

    # Right column keeps the check mark, which is part of the rendered string
    put('√ Static spatial', BASE['R1'], cx=RIGHT_CX)
    put('grouping', BASE['R2'], cx=RIGHT_CX)

    im.save(DST)

    changed = (np.abs(np.array(Image.open(SRC).convert('RGB')).astype(int)
                      - np.array(im).astype(int)).sum(axis=2) > 8)
    ys, xs = np.where(changed)
    inside = (((xs >= ERASE[0][0]) & (xs < ERASE[0][1])) |
              ((xs >= ERASE[1][0]) & (xs < ERASE[1][1]))) & (ys >= EY0) & (ys < EY1)
    assert (~inside).sum() == 0, 'the edit touched pixels outside the two annotation areas'
    print(f'wrote {DST}: {changed.sum()} pixels changed, all inside the two annotation areas')


if __name__ == '__main__':
    main()
