#!/usr/bin/env python3
"""Генерит stats.svg (карточку контрибуций) из живых данных GitHub.
Запускается GitHub Action'ом по расписанию — карточка всегда актуальна,
без кэша сторонних виджетов. Токен берётся из GH_TOKEN (GITHUB_TOKEN в Action)."""
import subprocess, json, datetime, os

USER = "Ryuga-Hideki-L"
START = datetime.date(2024, 10, 25)  # первый вклад
TODAY = datetime.date.today()
MON = ["", "янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def gql(frm, to):
    q = ('{user(login:"%s"){contributionsCollection(from:"%sT00:00:00Z",to:"%sT00:00:00Z")'
         '{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'
         % (USER, frm.isoformat(), to.isoformat()))
    out = subprocess.run(["gh", "api", "graphql", "-f", "query=" + q], capture_output=True, text=True)
    out.check_returncode()
    return json.loads(out.stdout)


days = {}
cur = START
while cur <= TODAY:
    nxt = min(cur.replace(year=cur.year + 1), TODAY + datetime.timedelta(days=1))
    for w in gql(cur, nxt)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for cd in w["contributionDays"]:
            d = datetime.date.fromisoformat(cd["date"])
            if START <= d <= TODAY:
                days[cd["date"]] = cd["contributionCount"]
    cur = nxt

D = datetime.date.fromisoformat
dates = sorted(days)
total = sum(days.values())

longest, run, prev, lrng, ls = 0, 0, None, (dates[0], dates[0]), None
for ds in dates:
    if days[ds] > 0:
        run = run + 1 if prev and (D(ds) - D(prev)).days == 1 else 1
        if run == 1:
            ls = ds
        if run > longest:
            longest, lrng = run, (ls, ds)
    else:
        run, ls = 0, None
    prev = ds

i = len(dates) - 1
if days[dates[i]] == 0:
    i -= 1
cs, cstart = 0, dates[i] if i >= 0 else TODAY.isoformat()
while i >= 0 and days[dates[i]] > 0:
    cs, cstart = cs + 1, dates[i]
    i -= 1


def full(s):
    d = D(s)
    return f"{d.day} {MON[d.month]} {d.year}"


def short(s):
    d = D(s)
    return f"{d.day} {MON[d.month]}"


BG, NUM, LAB, SUB, FIRE, LINE = "#0A0A0A", "#D6DBE3", "#9AA1AD", "#5A606B", "#B69154", "#20242c"
FF = "font-family=\"'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif\""
W, H = 495, 140


def col(cx, num, label, sub, nc=NUM):
    return (f'<text x="{cx:.0f}" y="60" text-anchor="middle" {FF} font-weight="700" font-size="30" fill="{nc}">{num}</text>'
            f'<text x="{cx:.0f}" y="88" text-anchor="middle" {FF} font-weight="600" font-size="13.5" fill="{LAB}">{label}</text>'
            f'<text x="{cx:.0f}" y="107" text-anchor="middle" {FF} font-size="11" fill="{SUB}">{sub}</text>')


svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img">'
       f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>'
       f'<line x1="165" y1="30" x2="165" y2="110" stroke="{LINE}"/><line x1="330" y1="30" x2="330" y2="110" stroke="{LINE}"/>'
       + col(W / 6, total, "Всего вкладов", f"с {full(dates[0])}")
       + col(W / 2, cs, "Текущая серия", f"{short(cstart)} — {short(TODAY.isoformat())}", nc=FIRE)
       + col(5 * W / 6, longest, "Лучшая серия", f"{short(lrng[0])} — {short(lrng[1])}") + '</svg>')

out = os.path.join(os.path.dirname(__file__), "..", "stats.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"stats.svg: total={total} current={cs} longest={longest}")
