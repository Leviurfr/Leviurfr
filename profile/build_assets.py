#!/usr/bin/env python3
"""Generator aset SVG animasi untuk README profil GitHub.

Semua aset berdiri sendiri (tanpa font/gambar eksternal), jadi tetap tampil
di GitHub walau layanan pihak ketiga sedang mati. Jalankan:  python3 build_assets.py
"""
import html
import math
import os
from xml.dom import minidom

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

# Palet: cyan = Fahlevi (pembuat), violet = Echidna (rasa ingin tahu), sisanya netral gelap.
INK = "#080a10"
PANEL = "#0e1119"
EDGE = "#1f2637"
TEXT = "#e8f0f2"
SOFT = "#b4bfd1"
DIM = "#8994a8"
CYAN = "#00f0ff"
VIOLET = "#a78bfa"
ROSE = "#ff5d7d"
MINT = "#5df2a6"

MONO = "ui-monospace,'SF Mono','Cascadia Code',Consolas,Menlo,'DejaVu Sans Mono',monospace"
SERIF = "Georgia,'Times New Roman','Noto Serif','DejaVu Serif',serif"
SANS = "'Segoe UI','Helvetica Neue',Arial,'Noto Sans','DejaVu Sans',sans-serif"
JP = "'Yu Gothic','Hiragino Sans','Noto Sans CJK JP','Noto Sans JP',sans-serif"

esc = html.escape


def f(x):
    s = ("%.5f" % x).rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def fv(v):
    return f(v) if isinstance(v, (int, float)) else str(v)


def _prep(points, total):
    pts = sorted(points, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    out, prev = [], None
    for t, v in pts:
        if prev is not None and t <= prev:
            t = prev + 0.001
        out.append((t, v))
        prev = t
    if out[-1][0] >= total:
        raise ValueError("event melewati total durasi: %r" % (out[-1],))
    out.append((total, out[-1][1]))
    return out


def kf(points, total):
    """Nilai + keyTimes untuk animasi (linear atau discrete, tergantung calcMode pemanggil)."""
    out = _prep(points, total)
    vals = ";".join(fv(v) for _, v in out)
    kts = ";".join(f(t / total) for t, _ in out)
    return vals, kts


def anim(attr, points, total, calc="linear", extra=""):
    vals, kts = kf(points, total)
    cm = ' calcMode="discrete"' if calc == "discrete" else ""
    return (f'<animate attributeName="{attr}" dur="{f(total)}s" repeatCount="indefinite"{cm} '
            f'values="{vals}" keyTimes="{kts}" {extra}/>')


def window(intervals, total):
    """Titik-titik discrete opacity 0/1 untuk daftar interval (mulai, selesai)."""
    pts = [(0, 0)]
    for a, b in intervals:
        if a <= 0:
            pts = [(0, 1)]
        else:
            pts.append((a, 1))
        if b < total:
            pts.append((b, 0))
    return pts


class Doc:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self._n = [], [], 0

    def nid(self, p="i"):
        self._n += 1
        return f"{p}{self._n}"

    def render(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{esc(self.title)}">\n'
                f'<title>{esc(self.title)}</title>\n<defs>\n' + "\n".join(self.defs) +
                '\n</defs>\n' + "\n".join(self.body) + '\n</svg>\n')


def write(name, doc):
    svg = doc.render() if isinstance(doc, Doc) else doc
    minidom.parseString(svg.encode("utf-8"))  # pastikan XML valid
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("ditulis", os.path.relpath(path, ROOT), "%.1f KB" % (len(svg.encode()) / 1024))


def typed(doc, text, x, y, fs, fill, t0, cps, t_off, total, weight="400", caret_off=None):
    """Teks mengetik per karakter (discrete) + kursor. Mengembalikan markup, tidak menambahkannya."""
    n = len(text)
    cw = fs * 0.6
    dt = 1.0 / cps
    cid = doc.nid("c")
    ev = [(0, 0)] + [(t0 + k * dt, k * cw) for k in range(1, n + 1)] + [(t_off, 0)]
    doc.defs.append(
        f'<clipPath id="{cid}"><rect x="{f(x)}" y="{f(y - fs)}" width="0" height="{f(fs * 1.5)}">'
        + anim("width", ev, total, "discrete") + '</rect></clipPath>')
    if text.startswith("$ "):
        inner = f'<tspan fill="{CYAN}">$</tspan>{esc(text[1:])}'
    else:
        inner = esc(text)
    txt = (f'<text x="{f(x)}" y="{f(y)}" font-family="{MONO}" font-size="{fs}" font-weight="{weight}" '
           f'fill="{fill}" textLength="{f(n * cw)}" lengthAdjust="spacing" clip-path="url(#{cid})" '
           f'xml:space="preserve">{inner}</text>')
    cev = [(0, x)] + [(t0 + k * dt, x + k * cw) for k in range(1, n + 1)] + [(t_off, x)]
    c_off = caret_off if caret_off is not None else t_off
    caret = (f'<g opacity="0">{anim("opacity", window([(t0, c_off)], total), total, "discrete")}'
             f'<rect x="{f(x)}" y="{f(y - fs * 0.82)}" width="{f(cw * 0.55)}" height="{f(fs * 1.0)}" fill="{fill}">'
             + anim("x", cev, total, "discrete") +
             '<animate attributeName="opacity" values="1;1;0;0" dur="1s" repeatCount="indefinite" calcMode="discrete"/>'
             '</rect></g>')
    return txt, caret


# ---------------------------------------------------------------- kupu-kupu (motif Echidna)
def butterfly_def(i, flap):
    return (f'<g id="bf{i}"><g>'
            f'<animateTransform attributeName="transform" type="scale" values="1 1;0.28 1;1 1" keyTimes="0;.5;1" '
            f'calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1" dur="{flap}s" repeatCount="indefinite"/>'
            '<path d="M0 -2C-3 -16-22 -20-26 -9C-28 -1-14 3 0 -2Z"/>'
            '<path d="M0 -2C3 -16 22 -20 26 -9C28 -1 14 3 0 -2Z"/>'
            '<path d="M0 1C-8 6-19 12-14 20C-9 24-2 12 0 1Z"/>'
            '<path d="M0 1C8 6 19 12 14 20C9 24 2 12 0 1Z"/></g>'
            '<path d="M0 -8L0 14" fill="none" stroke-width="1.6" stroke-linecap="round" stroke="currentColor"/></g>')


def butterfly(i, x0, y0, scale, dur, begin, path, color):
    return (f'<g transform="translate({x0} {y0})"><g opacity="0">'
            f'<animateMotion path="{path}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;.8;.8;0" keyTimes="0;.12;.85;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<g transform="scale({scale})" fill="{color}" color="{color}"><use href="#bf{i}"/></g></g></g>')


# ---------------------------------------------------------------- clock.svg
def build_clock():
    W, H, cx, cy, R = 300, 434, 150, 196, 112
    d = Doc(W, H, "Jam yang berputar mundur, simbol Return by Death")
    ex = cx + 96 * math.sin(math.radians(80))
    ey = cy - 96 * math.cos(math.radians(80))
    d.defs.append(f'''<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1018"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".5"/><stop offset=".5" stop-color="{EDGE}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".5"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".30"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<linearGradient id="trail" gradientUnits="userSpaceOnUse" x1="{cx}" y1="{cy - 96}" x2="{f(ex)}" y2="{f(ey)}"><stop offset="0" stop-color="{CYAN}" stop-opacity=".5"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>''')
    b = d.body
    b.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="170" fill="url(#glow)"><animate attributeName="opacity" values=".55;1;.55" dur="7s" repeatCount="indefinite"/></circle>')
    b.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="-360 {cx} {cy}" dur="80s" repeatCount="indefinite"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{R + 20}" fill="none" stroke="{VIOLET}" stroke-opacity=".55" stroke-width="2" stroke-dasharray="1 9" stroke-linecap="round"/></g>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{R + 2}" fill="none" stroke="{EDGE}" stroke-width="1.5"/>')
    for i in range(60):
        a = math.radians(i * 6)
        major = i % 5 == 0
        r1 = R - (15 if major else 7)
        r2 = R - 3
        b.append(f'<line x1="{f(cx + r1 * math.sin(a))}" y1="{f(cy - r1 * math.cos(a))}" x2="{f(cx + r2 * math.sin(a))}" y2="{f(cy - r2 * math.cos(a))}" '
                 f'stroke="{TEXT if major else DIM}" stroke-opacity="{.85 if major else .45}" stroke-width="{2 if major else 1}" stroke-linecap="round"/>')
    b.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="50s" repeatCount="indefinite"/>'
             f'<circle cx="{cx}" cy="{cy}" r="74" fill="none" stroke="{CYAN}" stroke-opacity=".28" stroke-width="1.5" stroke-dasharray="34 12 6 12"/></g>')
    # jarum menit berputar mundur, jejaknya tertinggal di sisi searah jarum jam
    b.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="-360 {cx} {cy}" dur="9s" repeatCount="indefinite"/>'
             f'<path d="M{cx} {cy}L{cx} {cy - 96}A96 96 0 0 1 {f(ex)} {f(ey)}Z" fill="url(#trail)"/>'
             f'<line x1="{cx}" y1="{cy + 16}" x2="{cx}" y2="{cy - 98}" stroke="{CYAN}" stroke-width="2.5" stroke-linecap="round"/></g>')
    b.append(f'<g><animateTransform attributeName="transform" type="rotate" from="40 {cx} {cy}" to="-320 {cx} {cy}" dur="54s" repeatCount="indefinite"/>'
             f'<line x1="{cx}" y1="{cy + 10}" x2="{cx}" y2="{cy - 60}" stroke="{TEXT}" stroke-width="4.5" stroke-linecap="round"/></g>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{CYAN}"/><circle cx="{cx}" cy="{cy}" r="2.4" fill="{INK}"/>')
    b.append(f'<text x="{cx}" y="366" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{DIM}" letter-spacing=".4">kembali ke checkpoint terakhir</text>')
    for k in range(3):
        b.append(f'<circle cx="{cx - 12 + k * 12}" cy="388" r="2.2" fill="{CYAN}" opacity=".25"><animate attributeName="opacity" values=".25;1;.25" dur="1.5s" begin="{k * 0.25}s" repeatCount="indefinite"/></circle>')
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="url(#edge)"/>')
    write("clock.svg", d)


# ---------------------------------------------------------------- hero.svg
def build_hero():
    W, H, T = 1000, 300, 15.0
    d = Doc(W, H, "Muhammad Fahlevi, Front-End Developer")
    d.defs.append(f'''<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1018"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/><stop offset=".5" stop-color="{EDGE}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".55"/></linearGradient>
<radialGradient id="gc"><stop offset="0" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
<radialGradient id="gv"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".22"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".85" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".65"/></linearGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>''')
    for i, fl in enumerate([0.85, 1.0, 0.7, 0.92]):
        d.defs.append(butterfly_def(i, fl))
    b = d.body
    b.append('<g clip-path="url(#card)">')
    b.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    grid = "".join(f'<line x1="{x}" y1="-40" x2="{x}" y2="{H + 40}"/>' for x in range(-40, W + 41, 40))
    grid += "".join(f'<line x1="-40" y1="{y}" x2="{W + 40}" y2="{y}"/>' for y in range(-40, H + 41, 40))
    b.append(f'<g stroke="#ffffff" stroke-opacity=".035"><animateTransform attributeName="transform" type="translate" from="0 0" to="40 40" dur="12s" repeatCount="indefinite"/>{grid}</g>')
    b.append(f'<circle cx="170" cy="160" r="300" fill="url(#gc)"><animate attributeName="opacity" values=".6;1;.6" dur="9s" repeatCount="indefinite"/></circle>')
    b.append(f'<circle cx="860" cy="90" r="280" fill="url(#gv)"><animate attributeName="opacity" values="1;.6;1" dur="9s" repeatCount="indefinite"/></circle>')
    specs = [
        (0, 700, 296, 1.0, 15, -2, "M0 0C60 -50 -30 -100 30 -160S80 -250 40 -310", VIOLET),
        (1, 812, 300, 0.75, 19, -9, "M0 0C-50 -60 40 -120 -20 -190S30 -260 10 -330", CYAN),
        (2, 890, 298, 1.2, 17, -5, "M0 0C40 -40 -50 -110 10 -170S-30 -240 20 -320", VIOLET),
        (3, 950, 300, 0.6, 13, -11, "M0 0C-30 -50 30 -110 -10 -180S20 -250 0 -320", TEXT),
    ]
    for s in specs:
        b.append(butterfly(*s))
    b.append(f'<text x="56" y="84" font-family="{JP}" font-size="19" fill="{VIOLET}" letter-spacing="7">ムハンマド・ファレビ</text>')
    nx, ny = 56, 176
    name = (f'font-family="{SERIF}" font-size="70" font-weight="700" textLength="670" lengthAdjust="spacing"')
    b.append(f'<text x="{nx}" y="{ny}" {name} fill="{TEXT}">Muhammad Fahlevi</text>')
    for col, dx in ((CYAN, -6), (VIOLET, 6)):
        ev_o = [(0, 0), (14.45, .8), (14.55, 0), (14.65, .8), (14.72, 0)]
        ev_x = [(0, nx), (14.45, nx + dx), (14.55, nx), (14.65, nx + dx * 1.7), (14.72, nx)]
        b.append(f'<text x="{nx}" y="{ny}" {name} fill="{col}" opacity="0">{anim("opacity", ev_o, T, "discrete")}{anim("x", ev_x, T, "discrete")}Muhammad Fahlevi</text>')
    b.append(f'<rect x="56" y="216" width="3" height="28" rx="1.5" fill="{CYAN}"/>')
    roles = ["Front-End Developer", "Open Source Enthusiast", "Gagal, belajar, ulangi", "Witch of Greed", "Problem Solver"]
    slot = T / len(roles)
    for i, r in enumerate(roles):
        s = i * slot
        op = [(0, 0), (s, 0), (s + .5, 1), (s + slot - .5, 1), (s + slot - .0001 if i < len(roles) - 1 else T - .001, 0)]
        op = [(t, v) for t, v in op]
        ty = [(0, "0 9"), (s, "0 9"), (s + .5, "0 0"), (s + slot - .5, "0 0"), (min(s + slot, T - .001), "0 -9")]
        b.append(f'<g opacity="0">{anim("opacity", op, T)}'
                 f'<animateTransform attributeName="transform" type="translate" dur="{f(T)}s" repeatCount="indefinite" values="{kf(ty, T)[0]}" keyTimes="{kf(ty, T)[1]}"/>'
                 f'<text x="76" y="242" font-family="{MONO}" font-size="26" fill="{CYAN}">{esc(r)}</text></g>')
    b.append(f'<text x="56" y="280" font-family="{JP}" font-size="12" fill="{DIM}" letter-spacing="3">死に戻り</text>')
    b.append(f'<rect x="-140" y="0" width="140" height="{H}" fill="url(#scan)">'
             + anim("x", [(0, -140), (14.3, -140), (14.95, W + 20)], T) + '</rect>')
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="url(#edge)"/>')
    write("hero.svg", d)


# ---------------------------------------------------------------- dialogue.svg
def build_dialogue():
    W, H, slot = 1000, 196, 6.4
    lines = [
        ("Echidna", "Aku penasaran. Apa yang sebenarnya kamu kejar?"),
        ("Fahlevi", "Antarmuka yang terasa hidup. Satu animasi, satu detail."),
        ("Echidna", "Dan ketika kodenya rusak?"),
        ("Fahlevi", "Aku kembali ke checkpoint terakhir, lalu mencoba lagi."),
        ("Echidna", "Kamu tidak takut gagal?"),
        ("Fahlevi", "Gagal itu murah. Berhenti belajar yang mahal."),
    ]
    T = slot * len(lines)
    d = Doc(W, H, "Dialog Echidna dan Fahlevi tentang cara Fahlevi bekerja")
    d.defs.append(f'''<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1018"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<radialGradient id="gv"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".22"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
<radialGradient id="gc"><stop offset="0" stop-color="{CYAN}" stop-opacity=".18"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>''')
    b = d.body
    b.append('<g clip-path="url(#card)">')
    b.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    ev = {"Echidna": [], "Fahlevi": []}
    colors = []
    done = []
    plates = []
    texts = []
    for i, (who, line) in enumerate(lines):
        a, z = i * slot + 0.2, (i + 1) * slot - 0.3
        ev[who].append((a, z))
        col = VIOLET if who == "Echidna" else CYAN
        colors.append((a, col))
        t0 = i * slot + 0.6
        cps = 22
        t_done = t0 + len(line) / cps
        done.append((t_done + .2, z))
        txt, car = typed(d, line, 44, 126, 25, TEXT, t0, cps, z, T)
        texts.append(txt + car)
        plates.append(f'<g opacity="0">{anim("opacity", window([(a, z)], T), T, "discrete")}'
                      f'<rect x="44" y="28" width="128" height="34" rx="8" fill="{col}" fill-opacity=".13" stroke="{col}" stroke-opacity=".7"/>'
                      f'<text x="108" y="51" text-anchor="middle" font-family="{SERIF}" font-size="19" font-style="italic" font-weight="700" fill="{col}">{who}</text></g>')
    b.append(f'<circle cx="0" cy="98" r="330" fill="url(#gv)" opacity="0">{anim("opacity", window(ev["Echidna"], T), T, "discrete")}</circle>')
    b.append(f'<circle cx="0" cy="98" r="330" fill="url(#gc)" opacity="0">{anim("opacity", window(ev["Fahlevi"], T), T, "discrete")}</circle>')
    cev = [(0, colors[0][1])] + colors
    cev = sorted({t: c for t, c in cev}.items())
    b.append(f'<rect x="0" y="0" width="6" height="{H}" fill="{VIOLET}">{anim("fill", cev, T, "discrete")}</rect>')
    b.extend(plates)
    b.extend(texts)
    b.append(f'<g opacity="0">{anim("opacity", window(done, T), T, "discrete")}<g>'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;0 4;0 0" dur=".9s" repeatCount="indefinite"/>'
             f'<path d="M934 158h20l-10 12z" fill="{SOFT}" fill-opacity=".8"/></g></g>')
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{EDGE}"/>')
    write("dialogue.svg", d)


# ---------------------------------------------------------------- terminal.svg
def build_terminal():
    W, H, T = 1000, 372, 16.0
    d = Doc(W, H, "Terminal: build gagal, kembali ke checkpoint, lalu berhasil")
    d.defs.append(f'''<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1018"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{ROSE}" stop-opacity="0"/><stop offset=".85" stop-color="{ROSE}" stop-opacity=".16"/><stop offset="1" stop-color="{ROSE}" stop-opacity=".6"/></linearGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>''')
    b = d.body
    b.append('<g clip-path="url(#card)">')
    b.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    b.append(f'<line x1="0" y1="52" x2="{W}" y2="52" stroke="{EDGE}"/>')
    b.append(f'<circle cx="28" cy="27" r="4" fill="{MINT}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>')
    b.append(f'<text x="44" y="32" font-family="{MONO}" font-size="15" fill="{DIM}">return-by-death.sh</text>')
    n_loops = 8
    for k in range(n_loops):
        ev = [(0, 0), (k * T, 1), ((k + 1) * T, 0)] if k else [(0, 1), (T, 0)]
        ev = [(t, v) for t, v in ev if t < T * n_loops]
        b.append(f'<text x="972" y="32" text-anchor="end" font-family="{MONO}" font-size="15" fill="{VIOLET}" opacity="0">'
                 + anim("opacity", ev, T * n_loops, "discrete") + f'loop {k + 1:03d}</text>')
    y0, step, fs = 102, 34, 21
    end = 13.6
    rows = [
        ("$ npm run build", TEXT, 0.5, True),
        ("error: Cannot read properties of undefined (reading 'motion')", ROSE, 1.7, False),
        ("state hilang. dunia diulang dari titik terakhir.", DIM, 2.4, False),
        ("$ git reset --hard HEAD~1", TEXT, 4.0, True),
        ("HEAD is now at 4e1f9a2 checkpoint: build hijau", SOFT, 5.4, False),
        ("$ npm run build", TEXT, 6.2, True),
        ("compiled successfully in 1.2s", MINT, 7.2, False),
        ("loop selesai. coba lagi, kali ini lebih pintar.", VIOLET, 8.3, False),
    ]
    for i, (text, col, t0, is_cmd) in enumerate(rows):
        y = y0 + i * step
        hist = i <= 2  # tiga baris pertama meredup setelah 'kematian'
        if is_cmd:
            txt, car = typed(d, text, 28, y, fs, col, t0, 24, end, T, caret_off=t0 + len(text) / 24 + 0.7)
            inner = txt + car
            if hist:
                inner = (f'<g opacity="1">{anim("opacity", [(0, 1), (3.1, .35), (end, .35)], T)}{inner}</g>')
            b.append(inner)
        else:
            pts = window([(t0, end)], T)
            g = f'<g opacity="0">{anim("opacity", pts, T, "discrete")}'
            inner = (f'<text x="28" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{col}" xml:space="preserve">{esc(text)}</text>')
            if hist:
                inner = (f'<g opacity="1">{anim("opacity", [(0, 1), (3.1, .35), (end, .35)], T)}{inner}</g>')
            b.append(g + inner + '</g>')
    b.append(f'<rect width="{W}" height="{H}" fill="{ROSE}" opacity="0">' + anim("opacity", [(0, 0), (2.95, 0), (3.05, .2), (3.75, 0)], T) + '</rect>')
    b.append(f'<rect x="-140" y="0" width="140" height="{H}" fill="url(#scan)">' + anim("x", [(0, -140), (2.95, -140), (3.6, W + 20)], T) + '</rect>')
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{EDGE}"/>')
    write("terminal.svg", d)


# ---------------------------------------------------------------- header-*.svg
def build_header(slug, title, delay):
    W, H, fs = 1000, 60, 30
    tw = len(title) * fs * 0.54
    d = Doc(W, H, title)
    lx = 44 + tw + 24
    d.defs.append(f'''<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".6" stop-color="{CYAN}" stop-opacity=".9"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>
<linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="#10141f"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>
<clipPath id="ln"><rect x="{f(lx)}" y="25" width="{f(W - 24 - lx)}" height="10"/></clipPath>''')
    b = d.body
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="url(#bg)" stroke="{EDGE}"/>')
    b.append(f'<rect x="18" y="16" width="4" height="28" rx="2" fill="{CYAN}"/>')
    b.append(f'<text x="36" y="40" font-family="{SERIF}" font-size="{fs}" font-weight="700" fill="{TEXT}" textLength="{f(tw)}" lengthAdjust="spacing">{esc(title)}</text>')
    b.append(f'<rect x="{f(lx)}" y="29.5" width="{f(W - 24 - lx)}" height="1" fill="{EDGE}"/>')
    b.append(f'<g clip-path="url(#ln)"><rect x="{f(lx - 160)}" y="28.75" width="160" height="2.5" fill="url(#sw)">'
             f'<animate attributeName="x" values="{f(lx - 160)};{W - 24}" dur="9s" begin="{delay}s" repeatCount="indefinite"/></rect></g>')
    write(f"h-{slug}.svg", d)


# ---------------------------------------------------------------- stack.svg
def build_stack():
    W = 1000
    rows = [
        (["Bahasa dan framework", "JavaScript", "Python", "React", "Next.js", "Node.js"], CYAN, TEXT, 34, -1),
        (["Tools dan platform", "Git", "GitHub", "Linux (Arch)", "Docker", "AWS"], EDGE, TEXT, 28, 1),
        (["Sedang dipelajari", "Rust", "CyberSecurity"], VIOLET, VIOLET, 24, -1),
    ]
    labels = {"Bahasa dan framework", "Tools dan platform", "Sedang dipelajari"}
    ph, gap, fs = 42, 14, 17
    pad = 18
    H = len(rows) * (ph + 12) - 12 + pad * 2
    d = Doc(W, H, "Stack: JavaScript, Python, React, Next.js, Node.js, Git, GitHub, Linux, Docker, AWS. Sedang dipelajari: Rust dan CyberSecurity")
    d.defs.append(f'''<linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="#10141f"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>
<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".07" stop-color="#fff" stop-opacity="1"/><stop offset=".93" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>''')
    d.body.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="url(#bg)" stroke="{EDGE}"/>')
    d.body.append('<g mask="url(#m)">')
    for r, (tokens, border, tcol, speed, direction) in enumerate(rows):
        y = pad + r * (ph + 12)
        ws = [len(t) * fs * 0.6 + (8 if t in labels else 40) for t in tokens]
        unit = sum(ws) + gap * len(tokens)
        period = unit * math.ceil(W / unit)
        copies = math.ceil((W + period) / unit) + 1
        pills, x = [], 0
        for _ in range(copies):
            for t, w in zip(tokens, ws):
                tl = f'textLength="{f(len(t) * fs * 0.6)}" lengthAdjust="spacing"'
                if t in labels:
                    pills.append(f'<text x="{f(x + w / 2)}" y="{ph / 2 + 5}" text-anchor="middle" font-family="{MONO}" font-size="{fs - 2}" fill="{DIM}" {tl}>{esc(t)}</text>')
                else:
                    is_v = border == VIOLET
                    fillc = VIOLET if is_v else "#141a2a"
                    fop = ' fill-opacity=".08"' if is_v else ""
                    bord = border if border != EDGE else "#2a3348"
                    bop = .7 if border != EDGE else 1
                    pills.append(f'<rect x="{f(x)}" y="0" width="{f(w)}" height="{ph}" rx="{ph // 2}" fill="{fillc}"{fop} stroke="{bord}" stroke-opacity="{bop}"/>'
                                 f'<text x="{f(x + w / 2)}" y="{ph / 2 + 5}" text-anchor="middle" font-family="{MONO}" font-size="{fs}" fill="{tcol}" {tl}>{esc(t)}</text>')
                x += w + gap
        frm, to = (0, -period) if direction < 0 else (-period, 0)
        d.body.append(f'<g transform="translate(0 {y})"><g><animateTransform attributeName="transform" type="translate" from="{f(frm)} 0" to="{f(to)} 0" dur="{f(period / speed)}s" repeatCount="indefinite"/>' + "".join(pills) + '</g></g>')
    d.body.append('</g>')
    write("stack.svg", d)


# ---------------------------------------------------------------- card-*.svg
def build_card(n, title, desc, tags, delay):
    W, H = 1000, 176
    d = Doc(W, H, f"{title}: {' '.join(desc)}")
    d.defs.append(f'''<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#10141f"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<linearGradient id="sw" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>''')
    b = d.body
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="url(#bg)" stroke="{EDGE}"/>')
    b.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="15" fill="none" stroke="url(#sw)" stroke-width="2" stroke-linecap="round" pathLength="100" stroke-dasharray="10 90">'
             f'<animate attributeName="stroke-dashoffset" from="0" to="-100" dur="9s" begin="{delay}s" repeatCount="indefinite"/></rect>')
    b.append(f'<text x="40" y="68" font-family="{SERIF}" font-size="36" font-weight="700" fill="{TEXT}">{esc(title)}</text>')
    b.append(f'<line x1="440" y1="34" x2="440" y2="{H - 34}" stroke="{EDGE}"/>')
    for i, line in enumerate(desc):
        b.append(f'<text x="474" y="{68 + i * 34}" font-family="{SANS}" font-size="23" fill="{SOFT}">{esc(line)}</text>')
    x = 40
    for t in tags:
        w = len(t) * 10.2 + 30
        b.append(f'<rect x="{f(x)}" y="106" width="{f(w)}" height="36" rx="18" fill="#141a2a" stroke="#2a3348"/>'
                 f'<text x="{f(x + w / 2)}" y="130" text-anchor="middle" font-family="{MONO}" font-size="17" fill="{SOFT}">{esc(t)}</text>')
        x += w + 10
    write(f"card-{n}.svg", d)


# ---------------------------------------------------------------- footer.svg
def build_footer():
    W, H = 1000, 120
    d = Doc(W, H, "Created by Return by Death. 2026 Grey A")
    d.defs.append(f'''<linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="#10141f"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>
<linearGradient id="wv" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>''')
    b = d.body
    b.append('<g clip-path="url(#card)">')
    b.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    for i, (amp, per, base, op, dur, sw) in enumerate([(12, 500, 40, .7, 16, 1.6), (9, 400, 50, .4, 22, 1.3), (16, 625, 58, .25, 30, 1.2)]):
        pts = [(x, base + amp * math.sin(2 * math.pi * x / per + i)) for x in range(0, int(per * 3) + 1, 10)]
        path = "M" + "L".join(f"{x} {f(y)}" for x, y in pts)
        b.append(f'<g opacity="{op}"><g><animateTransform attributeName="transform" type="translate" from="0 0" to="-{per} 0" dur="{dur}s" repeatCount="indefinite"/>'
                 f'<path d="{path}" fill="none" stroke="url(#wv)" stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="none"/></g></g>')
    b.append(f'<text x="500" y="98" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{SOFT}" letter-spacing=".5">Created by "Return by Death". © 2026 Grey A</text>')
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{EDGE}"/>')
    write("footer.svg", d)


if __name__ == "__main__":
    build_clock()
    build_hero()
    build_dialogue()
    build_terminal()
    build_stack()
    build_footer()
    for i, (slug, title) in enumerate([("tentang", "Tentang"), ("stack", "Stack"), ("proyek", "Proyek"),
                                       ("statistik", "Statistik"), ("kontribusi", "Kontribusi"), ("loop", "Return by Death")]):
        build_header(slug, title, delay=-i * 1.7)
    build_card(1, "Return-by-Death", ["Bug tracker cerdas berbasis AI.", "Menganalisis error log dan memberi", "saran perbaikan secara real-time."], ["Python", "FastAPI", "AI"], 0)
    build_card(2, "Witch's Cult", ["Platform komunitas open-source:", "forum, live chat, dan reputasi", "berbasis aktivitas GitHub."], ["React", "WebSocket", "PostgreSQL"], -2.3)
    build_card(3, "Greed Authority", ["CLI produktivitas untuk developer:", "scaffold, auto-commit, dan", "deploy otomatis."], ["Node.js", "CLI", "Docker"], -4.6)
