#!/usr/bin/env python3
"""Membuat assets/stats.svg dari data GitHub (GraphQL) tanpa layanan pihak ketiga.

Dipanggil oleh workflow .github/workflows/profil.yml memakai GITHUB_TOKEN bawaan.
Opsi lokal:
  python3 scripts/generate_stats.py --placeholder   kartu 'menunggu data' (dipakai sebelum run pertama)
  python3 scripts/generate_stats.py --demo          kartu dengan data contoh untuk cek tampilan
"""
import datetime
import html
import json
import math
import os
import sys
import urllib.request
from xml.dom import minidom

INK, PANEL, EDGE = "#080a10", "#0e1119", "#1f2637"
TEXT, SOFT, DIM = "#e8f0f2", "#b4bfd1", "#8994a8"
CYAN, VIOLET = "#00f0ff", "#a78bfa"
LANG_COLORS = ["#00f0ff", "#a78bfa", "#5b8cff", "#e879f9", "#5df2a6"]
MONO = "ui-monospace,'SF Mono','Cascadia Code',Consolas,Menlo,'DejaVu Sans Mono',monospace"
SERIF = "Georgia,'Times New Roman','Noto Serif','DejaVu Serif',serif"
SANS = "'Segoe UI','Helvetica Neue',Arial,'Noto Sans','DejaVu Sans',sans-serif"
esc = html.escape

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-readme-stats"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"])[:500])
    return payload["data"]["user"]


def parse(user):
    cc = user["contributionsCollection"]
    counts = [d["contributionCount"] for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    current, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:  # hari ini belum ada kontribusi: jangan putus streak
        i -= 1
    while i >= 0 and counts[i] > 0:
        current += 1
        i -= 1
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    langs = {}
    stars = 0
    for repo in user["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return {
        "contrib": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "repos": user["repositories"]["totalCount"],
        "stars": stars,
        "streak": current,
        "longest": longest,
        "active": sum(1 for c in counts if c > 0),
        "langs": [(n, s / total * 100) for n, s in top],
    }


def num(n):
    return f"{n:,}".replace(",", ".")


def render(data):
    W, H = 1000, 320
    placeholder = data is None
    if placeholder:
        data = {"contrib": 0, "commits": 0, "prs": 0, "issues": 0, "repos": 0, "stars": 0,
                "streak": 0, "longest": 0, "active": 0, "langs": []}
    r, cx, cy = 56, 800, 112
    circ = 2 * math.pi * r
    ratio = min(data["streak"] / data["longest"], 1) if data["longest"] else 0
    final_off = circ * (1 - ratio)
    cells = [("Kontribusi 12 bulan", data["contrib"]), ("Commit", data["commits"]), ("Pull request", data["prs"]),
             ("Issue", data["issues"]), ("Repositori publik", data["repos"]), ("Bintang diterima", data["stars"])]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="Statistik GitHub: {data["contrib"]} kontribusi dalam 12 bulan, streak {data["streak"]} hari">',
           '<title>Statistik GitHub</title>', '<defs>',
           f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#10141f"/><stop offset="1" stop-color="{INK}"/></linearGradient>',
           f'<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>',
           f'<clipPath id="bar"><rect x="40" y="246" width="0" height="10" rx="5"><animate attributeName="width" from="0" to="920" dur="1.4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .2 1"/></rect></clipPath>',
           '</defs>',
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="url(#bg)" stroke="{EDGE}"/>']
    for i, (label, value) in enumerate(cells):
        x = 40 + (i % 3) * 190
        y = 88 + (i // 3) * 96
        out.append(f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="44" font-weight="700" fill="{TEXT}">{num(value)}</text>')
        out.append(f'<text x="{x}" y="{y + 28}" font-family="{SANS}" font-size="16" fill="{DIM}">{esc(label)}</text>')
    out.append(f'<line x1="640" y1="40" x2="640" y2="210" stroke="{EDGE}"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{EDGE}" stroke-width="9"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#ring)" stroke-width="9" stroke-linecap="round" '
               f'stroke-dasharray="{circ:.2f}" stroke-dashoffset="{final_off:.2f}" transform="rotate(-90 {cx} {cy})">'
               f'<animate attributeName="stroke-dashoffset" from="{circ:.2f}" to="{final_off:.2f}" dur="1.6s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .2 1"/></circle>')
    out.append(f'<text x="{cx}" y="{cy + 8}" text-anchor="middle" font-family="{SERIF}" font-size="34" font-weight="700" fill="{TEXT}">{num(data["streak"])}</text>')
    out.append(f'<text x="{cx}" y="{cy + 28}" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{DIM}">hari berturut</text>')
    out.append(f'<text x="{cx}" y="204" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{SOFT}">terpanjang {num(data["longest"])} hari, aktif {num(data["active"])} hari</text>')
    if placeholder:
        out.append(f'<text x="40" y="288" font-family="{MONO}" font-size="14" fill="{DIM}">Menunggu data pertama. Buka tab Actions, pilih workflow Profil, lalu klik Run workflow.</text>')
        out.append(f'<rect x="40" y="246" width="920" height="10" rx="5" fill="{EDGE}"/>')
    else:
        out.append(f'<rect x="40" y="246" width="920" height="10" rx="5" fill="{EDGE}"/>')
        x = 40.0
        segs = []
        for idx, (name, pct) in enumerate(data["langs"]):
            w = 920 * pct / sum(p for _, p in data["langs"]) if data["langs"] else 0
            segs.append(f'<rect x="{x:.1f}" y="246" width="{max(w - 2, 1):.1f}" height="10" fill="{LANG_COLORS[idx % 5]}"/>')
            x += w
        out.append('<g clip-path="url(#bar)">' + "".join(segs) + '</g>')
        n = max(len(data["langs"]), 1)
        for idx, (name, pct) in enumerate(data["langs"]):
            lx = 40 + idx * (920 / n)
            out.append(f'<circle cx="{lx + 5:.1f}" cy="284" r="4" fill="{LANG_COLORS[idx % 5]}"/>')
            out.append(f'<text x="{lx + 16:.1f}" y="288" font-family="{MONO}" font-size="15" fill="{SOFT}">{esc(name)} {pct:.0f}%</text>')
    out.append('</svg>\n')
    return "\n".join(out)


def main():
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "stats.svg")
    args = sys.argv[1:]
    if "--placeholder" in args:
        svg = render(None)
    elif "--demo" in args:
        svg = render({"contrib": 1284, "commits": 903, "prs": 41, "issues": 18, "repos": 27, "stars": 112,
                      "streak": 23, "longest": 61, "active": 214,
                      "langs": [("JavaScript", 46.0), ("Python", 24.0), ("TypeScript", 14.0), ("CSS", 10.0), ("HTML", 6.0)]})
    else:
        login = os.environ.get("GH_LOGIN") or os.environ["GITHUB_REPOSITORY_OWNER"]
        svg = render(parse(fetch(login, os.environ["GITHUB_TOKEN"])))
    minidom.parseString(svg.encode("utf-8"))
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("ditulis", os.path.normpath(dest))


if __name__ == "__main__":
    main()
