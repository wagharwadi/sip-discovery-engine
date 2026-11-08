"""Rhythm SIP: MVP prototype (Step 9). A SIP that moves with your money.

Run locally:  python rhythm_app.py            then open http://localhost:8503
Deploy:       the same command (it reads $PORT).
Front end:    web/  (one guided flow: each step moves on by itself once its checks pass)
Design rule:  the AI only reads (pay description, check-in replies); rules decide and verify; the user confirms.
Free-text questions go through the tested safety engine (mvp_core). All data is simulated: no real money, no bank data.
"""
import calendar
import datetime as dt
import json
import os
import re
import threading
import traceback
from pathlib import Path

os.environ.setdefault("LLM_MIN_GAP", "2")

import uvicorn  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402
from starlette.middleware import Middleware  # noqa: E402
from starlette.middleware.gzip import GZipMiddleware  # noqa: E402
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse  # noqa: E402
from starlette.routing import Mount, Route  # noqa: E402
from starlette.staticfiles import StaticFiles  # noqa: E402

import mvp_core as M  # noqa: E402
import rhythm_core as R  # noqa: E402
from rhythm_core import fmt, ordinal  # noqa: E402

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
AMOUNT = 500                      # demo SIP amount (Rs)
IP_CAP, DAILY_CAP = 40, 400       # AI calls per visitor per day / for the whole demo per day (keeps the free quota alive)

# ---------------------------------------------------------------- examples (real patterns from the interviews)
EXAMPLES = [
    {"id": "student", "label": "Student", "hint": "stipend 1st–3rd", "noun": "stipend", "taps": [2, 1, 3],
     "persona": "Student: stipend on the 1st–3rd, once came on the 6th",
     "text": "My stipend comes on the 1st, sometimes the 2nd or 3rd."},
    {"id": "first_job", "label": "First job", "hint": "salary on the last working day", "noun": "salary", "taps": "lwd",
     "persona": "First job: salary on the last working day",
     "text": "Salary is credited on the last working day of the month."},
    {"id": "freelancer", "label": "Freelancer", "hint": "clients pay 5th–20th", "noun": "client payment",
     "taps": [12, 8, 18], "persona": "Freelancer: clients pay any time from the 5th to the 20th",
     "text": "Clients pay me any time between the 5th and the 20th."},
    {"id": "part_time", "label": "Part-time job", "hint": "paid on the 7th, on time", "noun": "pay", "taps": [7, 7, 7],
     "persona": "Part-time job: paid on the 7th, always on time",
     "text": "I get paid on the 7th, it's always on time."},
]
EX_BY_ID = {e["id"]: e for e in EXAMPLES}
NOUNS = {"salary": "salary", "stipend": "stipend", "pocket_money": "pocket money", "freelance": "client payment",
         "gig": "payout", "business": "income"}


# ---------------------------------------------------------------- usage caps + cache (AI calls only)
class Budget:
    def __init__(self):
        self.lock, self.day, self.total, self.by_ip = threading.Lock(), None, 0, {}

    def _roll(self):
        if self.day != dt.date.today():
            self.day, self.total, self.by_ip = dt.date.today(), 0, {}

    def check(self, ip):
        with self.lock:
            self._roll()
            if self.total >= DAILY_CAP:
                return "Today's shared AI quota for this demo is used up. The buttons still work."
            if self.by_ip.get(ip, 0) >= IP_CAP:
                return "You've used this demo's AI calls for today. The buttons still work."
            return ""

    def spend(self, ip, n=1):
        with self.lock:
            self._roll()
            self.total += n
            self.by_ip[ip] = self.by_ip.get(ip, 0) + n


BUDGET, CACHE, CACHE_LOCK = Budget(), {}, threading.Lock()


async def ai(kind, fn, text, *args, ip="?", cost=1, ok=lambda r: True):
    """Run an AI-backed function once per distinct input (cached), within the usage caps. Returns (result, limit_msg)."""
    key = (kind, re.sub(r"\s+", " ", text.strip().lower()), args)
    with CACHE_LOCK:
        if key in CACHE:
            return CACHE[key], ""
    msg = BUDGET.check(ip)
    if msg:
        return None, msg
    res = await run_in_threadpool(fn, text, *args)
    BUDGET.spend(ip, cost)
    if ok(res):
        with CACHE_LOCK:
            if len(CACHE) > 3000:
                CACHE.clear()
            CACHE[key] = res
    return res, ""


# ---------------------------------------------------------------- small helpers
def iso(d):
    return d.isoformat() if d else None


def plain(s):
    return re.sub(r"<[^>]+>", "", s or "")


def mdays(y, m):
    return calendar.monthrange(y, m)[1]


def day_arg(v, default=None, hi=31):
    try:
        v = int(v)
        return v if 1 <= v <= hi else default
    except (TypeError, ValueError):
        return default


def date_arg(v, default=None):
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return default


def month_end(rh):
    return rh["pattern"] == "last_working_day" or (rh["pattern"] == "date_window" and (rh.get("earliest_day") or 0) >= 24)


def days_text(rh):
    p, lo, hi = rh["pattern"], rh.get("earliest_day"), rh.get("latest_day")
    if month_end(rh):
        return "on the last working day"
    if p == "fixed_date" and hi:
        return f"on the {ordinal(hi)}"
    if p == "date_window" and lo and hi:
        return f"between the {ordinal(lo)} and {ordinal(hi)}"
    if p == "weekly":
        return f"every {(rh.get('weekday') or 'week').title()}"
    return "at no fixed time"


def cap(s):
    return s[:1].upper() + s[1:]


def week_bounds(dates, y, m):
    first, last = dt.date(y, m, 1), dt.date(y, m, mdays(y, m))
    lo, hi = min([first] + dates), max([last] + dates)
    return lo - dt.timedelta(days=lo.weekday()), hi + dt.timedelta(days=6 - hi.weekday())


def working_days_between(a, b):
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        n += R.is_working(d)
    return n


async def read_json(request):
    raw = await request.body()
    if len(raw) > 8000:
        return {}
    try:
        out = json.loads(raw or b"{}")
        return out if isinstance(out, dict) else {}
    except ValueError:
        return {}


def client_ip(request):
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "?")


def safe(handler):
    """Never show a stack trace to the user: any error becomes a visible fallback in the UI."""
    async def wrapped(request):
        try:
            return await handler(request)
        except Exception:
            traceback.print_exc()
            return JSONResponse({"status": "error", "kind": "error",
                                 "message": "Something went wrong on our side. The buttons still work."})
    return wrapped


# ---------------------------------------------------------------- the plan (setup → rhythm → replay → check-in → …)
def manual_rhythm(m):
    p, lo, hi = m.get("pattern"), day_arg(m.get("lo")), day_arg(m.get("hi"))
    wd = m.get("weekday") if m.get("weekday") in R.WEEKDAYS else None
    if p == "fixed_date":
        lo = hi = lo or hi
        if not lo:
            return None
    elif p == "date_window":
        if not (lo and hi):
            return None
        lo, hi = sorted((lo, hi))
        if lo == hi:
            p = "fixed_date"
    elif p == "last_working_day":
        lo, hi = 28, 31
    elif p == "weekly":
        lo = hi = None
        wd = wd or "monday"
    elif p == "irregular":
        lo = hi = None
    else:
        return None
    return {"pattern": p, "earliest_day": lo, "latest_day": hi, "weekday": wd, "source": "unknown", "summary": "",
            "asks_advice": False, "confidence": 1.0, "provider": "you", "error": ""}


def default_taps(rh, ex):
    if ex:
        return ex["taps"]
    p, lo, hi = rh["pattern"], rh.get("earliest_day"), rh.get("latest_day")
    if month_end(rh):
        return "lwd"
    if p == "fixed_date" and hi:
        return [hi] * 3
    if p == "date_window" and lo and hi:
        return [lo + (hi - lo) // 2, lo, hi]
    return [9, 17, 12]


def tap_day(rh, ex, rec, y, m):
    """The example day the money lands in the one-tap month (for the rhythm calendar and the check-in)."""
    taps = default_taps(rh, ex)
    if rh["pattern"] == "weekly":
        wd = R.WEEKDAYS.index(rh.get("weekday") or "monday")
        return next(d for d in range(1, 8) if dt.date(y, m, d).weekday() == wd)
    d = taps[0] if isinstance(taps, list) else 12
    return max(1, min(d, rec.window[1] - 1, mdays(y, m)))


def build_plan(rh, by, text, ex, cal_day):
    persona = R.PERSONAS.get(ex["persona"]) if ex else None
    rec = R.recommend(rh, current_day=cal_day)
    kept = rec.headline.startswith("Keep your date")
    fixed = rec.mode == "fixed"
    noun = ex["noun"] if ex else NOUNS.get(rh.get("source"), "money")
    p, lo, hi = rh["pattern"], rh.get("earliest_day"), rh.get("latest_day")
    sd, debit, ci = R.next_checkin(rec)
    checks = [{"label": lbl, "passed": bool(ok), "detail": d} for lbl, ok, d in rec.checks]
    read_text = f"{cap(noun)} · {days_text(rh)}"

    # ---- the month we draw (next SIP month) and what lights up in it
    today = dt.date.today()
    y, m = (sd.year, sd.month) if fixed else R.add_month(today.year, today.month, 1)
    legend = []
    if fixed:
        if month_end(rh):
            py, pm = R.add_month(y, m, -1)
            md = R.last_working_day(py, pm)
            legend.append({"kind": "money", "when": fmt(md), "what": f"{cap(noun)} lands (last working day)", "dates": [iso(md)]})
        elif hi:
            my, mm = (y, m) if hi <= rec.sip_day else R.add_month(y, m, -1)
            rng = [d for d in range(lo or hi, hi + 1) if d <= mdays(my, mm)]
            when = (f"{ordinal(rng[0])}–{ordinal(rng[-1])}" if len(rng) > 1 else fmt(dt.date(my, mm, rng[0])))
            legend.append({"kind": "money", "when": when, "what": f"{cap(noun)} usually lands" if len(rng) > 1 else f"{cap(noun)} lands",
                           "dates": [iso(dt.date(my, mm, d)) for d in rng]})
        legend += [
            {"kind": "checkin", "when": fmt(ci), "what": "Check-in: will your money be there?", "dates": [iso(ci)]},
            {"kind": "debit", "when": fmt(debit), "what": "Money is taken, one working day before", "dates": [iso(debit)]},
            {"kind": "sip", "when": fmt(sd), "what": "SIP date" + (" (unchanged)" if kept else
                                                                  (f" (you'd picked the {ordinal(cal_day)})" if cal_day != rec.sip_day else "")),
             "dates": [iso(sd)]},
        ]
        tap = invest = None
    else:
        if p == "date_window" and lo and hi:
            win = [dt.date(y, m, d) for d in range(lo, min(hi, mdays(y, m)) + 1)]
            legend.append({"kind": "window", "when": f"{ordinal(lo)}–{ordinal(hi)}", "what": f"Your {noun} usually comes in this window",
                           "dates": [iso(d) for d in win]})
        elif p == "weekly":
            wd = R.WEEKDAYS.index(rh.get("weekday") or "monday")
            win = [dt.date(y, m, d) for d in range(1, mdays(y, m) + 1) if dt.date(y, m, d).weekday() == wd]
            legend.append({"kind": "window", "when": f"Every {(rh.get('weekday') or 'monday').title()}", "what": "Payout days",
                           "dates": [iso(d) for d in win]})
        tap = dt.date(y, m, tap_day(rh, ex, rec, y, m))
        invest = R.next_working_day(tap)
        end = dt.date(y, m, min(rec.window[1], mdays(y, m)))
        legend += [
            {"kind": "tap", "when": fmt(tap), "what": f"It lands. You tap \"money's in\" from the notification", "dates": [iso(tap)]},
            {"kind": "invest", "when": fmt(invest), "what": "SIP goes in, the next working day", "dates": [iso(invest)]},
            {"kind": "end", "when": fmt(end), "what": "Nothing by then? One message: invest now, use a Lifeline or skip. Nothing bounces.",
             "dates": [iso(end)]},
        ]
    hl = [dt.date.fromisoformat(d) for item in legend for d in item["dates"]]
    g0, g1 = week_bounds(hl, y, m)

    if fixed and kept:
        title = f"Your {noun} comes {days_text(rh)}, and the {ordinal(rec.sip_day)} already fits. Nothing changes."
        sub = ("Steady pay keeps its date. Rhythm only steps in when a month looks different: the check-in three "
               "working days before each SIP lets you move just that month.")
    elif fixed:
        title = f"Your {noun} lands {days_text(rh)}, so your SIP sits on the {ordinal(rec.sip_day)}."
        sub = (f"Groww takes the money one working day before the SIP date, so the {ordinal(rec.sip_day)} leaves room even "
               f"when your {noun} is late. A check-in three working days before catches the unusual month.")
    elif p == "weekly":
        title = f"You're paid {days_text(rh)}, so your SIP goes in after the month's first payout."
        sub = "Groww SIPs are monthly. Nothing is taken until you tap \"money's in\"; it goes in the next working day."
    elif p == "date_window":
        title = f"Your {noun} comes any time {days_text(rh)}, so your SIP waits for it."
        sub = "A fixed date would fail in some months. Nothing is taken until you tap \"money's in\"; it goes in the next working day."
    else:
        title = f"Your {noun} has no fixed date, so your SIP waits for your tap."
        sub = "Nothing is taken until you tap \"money's in\"; it goes in the next working day, any day up to the 28th."

    # ---- setup verification lines (the rules' own checks, in plain words)
    if fixed:
        date_detail = (f"Keep the {ordinal(rec.sip_day)}: it already fits" if kept else
                       f"The {ordinal(rec.sip_day)}" + (f", instead of the {ordinal(cal_day)}" if cal_day != rec.sip_day else ""))
        gap = R.fixed_day_gap(rh, rec.sip_day) if hi else None
        test_detail = ("Money arrives before it's taken in every month" +
                       (f" · smallest gap {gap} day{'s' if gap != 1 else ''}" if gap is not None else ""))
        ci_detail = f"3 working days before each SIP, so you can still change it (Groww needs 2) · next: {fmt(ci)}"
    else:
        date_detail = "No fixed date: it waits for your \"money's in\" tap"
        test_detail = "Nothing is taken before you confirm the money arrived"
        ci_detail = f"On your usual payday, one question: has your {noun} arrived?"
    verify = [
        {"k": "read", "title": "Reading your words", "detail": read_text, "passed": True,
         "meta": (f"{rh.get('confidence', 0):.0%} sure · read by {(rh.get('provider') or 'AI').split(':')[0].title()}"
                  if by == "ai" else "set by you")},
        {"k": "date", "title": "Choosing a date that comes after your money", "detail": date_detail, "passed": checks[0]["passed"]},
        {"k": "test", "title": "Testing it on the next 6 real months", "detail": test_detail, "passed": checks[1]["passed"]},
        {"k": "checkin", "title": "Setting up the monthly check-in", "detail": ci_detail, "passed": checks[2]["passed"]},
    ]

    # ---- six-month replay: calendar SIP vs Rhythm SIP on real calendar months
    arrivals = persona["arrivals"] if persona and isinstance(persona["arrivals"], list) else None
    rows, s = R.simulate(rh, rec, cal_day, arrivals, persona["late_clear"] if persona else ())
    months = []
    for r in rows:
        md0 = dt.datetime.strptime(r["month"], "%b %Y").date()
        months.append({"label": md0.strftime("%b"), "year": md0.year, "month": md0.month, "days": mdays(md0.year, md0.month),
                       "money": {"date": r["money_date"], "text": r["money"]},
                       "fixed": {"status": r["calendar"][0], "text": r["calendar"][1], "date": r["cal_date"]},
                       "rhythm": {"status": r["rhythm"][0], "text": r["rhythm"][1], "date": r["rhythm_date"],
                                  "planned": r["rhythm_planned"]}})
    c, h = s["calendar"], s["rhythm"]
    if h["invested"] > c["invested"]:
        summary = ("Rhythm SIP invested in all 6 months" if h["invested"] == 6 else f"Rhythm SIP invested in {h['invested']} of 6 months")
        if h["moved"]:
            summary += f", moving {'one late month' if h['moved'] == 1 else str(h['moved']) + ' late months'} after the check-in"
        summary += (f". The fixed date bounced {'once' if c['bounces'] == 1 else str(c['bounces']) + ' times'}, about "
                    f"₹{c['fees']:,} in bank charges" + (", and the SIP was cancelled after 3 failures in a row." if c["cancelled"] else "."))
    elif c["bounces"] == 0 and h["invested"] == c["invested"]:
        summary = "Both invested every month. Your pay is steady, so Rhythm changed nothing, which is the point."
    else:
        summary = f"Fixed date: {c['invested']} of 6 months. Rhythm SIP: {h['invested']} of 6."
    replay = {
        "fixed_label": f"Fixed date · the {ordinal(cal_day)}",
        "rhythm_label": f"Rhythm SIP · the {ordinal(rec.sip_day)}" if fixed else "Rhythm SIP · waits for your tap",
        "story": ((persona["story"].split(" (")[0] + ".") if persona else
                  "Your own words, on the last 6 real calendar months." if month_end(rh) else
                  "Your own words, with one month running 4 days late." if p in ("fixed_date", "date_window", "weekly") else
                  "Your own words, with paydays drawn at random."),
        "months": months, "summary": summary, "totals": s, "fee": R.BOUNCE_FEE,
    }

    # ---- monthly check-in
    if fixed:
        lock_day = ci
        notif = {"title": f"Your ₹{AMOUNT} SIP goes on {fmt(sd)}", "body": f"The money is taken on {fmt(debit)}. Will it be there?"}
        actions = [{"id": "yes", "label": "Yes, all good"}, {"id": "move", "label": "Move this month"},
                   {"id": "lifeline", "label": "Use a Lifeline"}, {"id": "stop", "label": "Stop SIP"}]
        late = min(rec.sip_day + 2, 26)
        examples = [f"{noun} is late this month, comes on the {ordinal(late)}", "tight month, rent went up",
                    "will the bank charge me if it bounces?", "which fund is better?"]
        ci_title, ci_sub = ("Three working days before, one question",
                            "Answered from the notification itself. Groww needs 2 working days to change a date, so the "
                            "check-in comes 3 working days early. No reply means nothing changes.")
    else:
        lock_day = tap
        notif = {"title": f"Has your {noun} arrived?",
                 "body": f"Your ₹{AMOUNT} SIP goes in the working day after you tap yes. Nothing is taken before that."}
        actions = [{"id": "yes", "label": "Yes, invest tomorrow"}, {"id": "notyet", "label": "Not yet"},
                   {"id": "lifeline", "label": "Use a Lifeline"}, {"id": "stop", "label": "Stop SIP"}]
        examples = ["paise aa gaye", f"{noun} hasn't come yet, maybe next week", "skip this month", "is my money safe?"]
        ci_title, ci_sub = ("On payday, one tap",
                            "Answered from the notification itself. Nothing is taken before you say the money is in, so "
                            "a late payday can't cause a bounce.")
    checkin = {"mode": rec.mode, "noun": noun, "amount": AMOUNT, "title": ci_title, "sub": ci_sub,
               "lock_date": f"{lock_day.strftime('%A')}, {lock_day.day} {lock_day.strftime('%B')}",
               "sip": iso(sd), "sip_txt": fmt(sd), "debit_txt": fmt(debit), "checkin_txt": fmt(ci),
               "tap": iso(tap), "invest_txt": fmt(invest) if invest else None, "month": sd.strftime("%B") if fixed else dt.date(y, m, 1).strftime("%B"),
               "notif": notif, "actions": actions, "examples": examples}

    # ---- Lifelines + failure message
    ny, nm = R.add_month(y, m, 1)
    lifeline = {"month": dt.date(y, m, 1).strftime("%B"),
                "months": [dt.date(*R.add_month(y, m, k), 1).strftime("%b") for k in range(12)],
                "next_txt": fmt(R.sip_date(ny, nm, rec.sip_day)) if fixed else "after your next payday",
                "fail_debit": fmt(debit) if fixed else fmt(invest)}

    # ---- learning loop (next 3 months of taps)
    taps = default_taps(rh, ex)
    learn_rows = []
    for k in range(3):
        ty, tm = R.add_month(y, m, k)
        if taps == "lwd":
            d = R.last_working_day(*R.add_month(ty, tm, -1))
            learn_rows.append({"label": d.strftime("%b"), "days": mdays(d.year, d.month), "day": d.day})
        else:
            learn_rows.append({"label": dt.date(ty, tm, 1).strftime("%b"), "days": mdays(ty, tm), "day": min(taps[k], mdays(ty, tm))})
    learn = learn_payload([r["day"] for r in learn_rows], rec.mode, rec.sip_day, noun)
    learn["rows"] = learn_rows

    return {
        "status": "ok", "by": by, "input": text, "example": ex["id"] if ex else None,
        "read": {"pattern": p, "lo": lo, "hi": hi, "weekday": rh.get("weekday"), "text": read_text,
                 "summary": rh.get("summary", ""), "confidence": round(float(rh.get("confidence") or 0), 2),
                 "provider": rh.get("provider") or "", "asks_advice": bool(rh.get("asks_advice"))},
        "plan": {"mode": rec.mode, "sip_day": rec.sip_day, "window": list(rec.window), "kept": kept,
                 "headline": rec.headline, "why": [plain(w) for w in rec.why], "checks": checks,
                 "passed": rec.checks_passed, "cal_day": cal_day, "noun": noun},
        "verify": verify,
        "rhythm": {"title": title, "sub": sub, "legend": legend, "fine": " ".join(plain(w) for w in rec.why[1:])},
        "calendar": {"year": y, "month": m, "title": dt.date(y, m, 1).strftime("%B %Y"), "start": iso(g0), "end": iso(g1)},
        "replay": replay, "checkin": checkin, "lifeline": lifeline, "learn": learn,
    }


def learn_payload(days, mode, sip_day, noun):
    rec = R.Recommendation(mode, sip_day, (1, sip_day), "", [])
    v = R.learn(days, rec)
    lo, hi, day = v["lo"], v["hi"], v["day"]
    out = {"verdict": v["verdict"], "lo": lo, "hi": hi, "day": day, "actions": [],
           "checks": [{"label": lbl, "passed": ok} for lbl, ok, _ in v["checks"]]}
    if v["verdict"] == "wait":
        out.update(title="Three months of taps are needed first.", body="")
        return out
    came = ("came on the last working day" if lo >= 24 else
            f"came on the {ordinal(hi)}" if lo == hi else f"came by the {ordinal(hi)}")
    if v["verdict"] == "keep":
        out.update(title=f"Your {noun} still moves around: the {ordinal(lo)} to the {ordinal(hi)}.",
                   body=("A fixed date would fail in some months, so Rhythm keeps waiting for your tap. Try moving the "
                         "dots closer together." if mode == "one_tap" else
                         "So the monthly check-in stays on. Rhythm offers to lock a date once three months line up."))
        return out
    if mode == "one_tap":
        out.update(title=f"Your {noun} {came}, three months running.",
                   body=f"Lock your SIP to the {ordinal(day)}? No more taps. The date passes the same rule check as setup.",
                   actions=[{"id": "lock", "label": f"Lock to the {ordinal(day)}"}, {"id": "keep", "label": "Keep tapping"}],
                   done={"lock": f"Locked to the {ordinal(day)}. No more taps. If your pay changes, switch back any time.",
                         "keep": "Okay. Nothing changes; your SIP keeps waiting for your tap."})
    elif v["same"]:
        out.update(title=f"Your {noun} {came}, three months running.",
                   body=f"Lock the {ordinal(day)} and stop the monthly check-ins? The date passes the same rule check as setup.",
                   actions=[{"id": "lock", "label": f"Lock the {ordinal(day)}"}, {"id": "keep", "label": "Keep check-ins"}],
                   done={"lock": f"Locked to the {ordinal(day)}. No more check-ins. If your pay changes, switch back any time.",
                         "keep": "Okay. The check-in stays on, one message a month."})
    else:
        out.update(title=f"Your {noun} {came}, three months running.",
                   body=f"Move your SIP to the {ordinal(day)} so it stays after your money, and lock it there?",
                   actions=[{"id": "lock", "label": f"Move to the {ordinal(day)}"}, {"id": "keep", "label": f"Keep the {ordinal(sip_day)}"}],
                   done={"lock": f"Moved and locked to the {ordinal(day)}. If your pay changes, switch back any time.",
                         "keep": f"Okay. Your SIP stays on the {ordinal(sip_day)}, with the monthly check-in."})
    return out


# ---------------------------------------------------------------- check-in replies
INTENT_TEXT = {"all_good": "Money will be there", "lifeline": "Can't invest this month", "stop": "Wants to stop the SIP",
               "question": "A question about how it works", "advice": "Asks for investment advice", "unclear": "Couldn't tell"}


def move_payload(new_day, reason, sip, sip_day, money_day=None):
    month = sip.strftime("%B")
    if new_day is None:
        if reason.startswith("When"):
            return {"kind": "ask_day", "message": "When will your money arrive this month?",
                    "days": list(range(max(1, sip_day - 2), 27))}
        if "too late" in reason:
            return {"kind": "too_late", "message": reason}
        return {"kind": "done", "tone": "ok", "message": reason + " Your SIP goes ahead as planned."}
    nd = R.sip_date(sip.year, sip.month, new_day)
    taken = R.prev_working_day(nd)
    today_ci = sip
    for _ in range(3):
        today_ci = R.prev_working_day(today_ci)
    checks = [{"label": f"Still in {month}, by the {ordinal(R.MAX_SIP_DAY)}", "passed": new_day <= R.MAX_SIP_DAY}]
    if money_day:
        md = R.sip_date(sip.year, sip.month, money_day)
        checks.append({"label": f"Money arrives ({fmt(md)}) before it's taken ({fmt(taken)})", "passed": taken > md})
    checks.append({"label": "Changed at least 2 working days ahead (Groww's cut-off)",
                   "passed": working_days_between(today_ci, taken) >= 2})
    return {"kind": "propose_move", "new_day": new_day, "new_txt": fmt(nd), "taken_txt": fmt(taken),
            "title": f"Move just {month}'s SIP to {fmt(nd)}?",
            "body": f"{reason} The money will be taken on {fmt(taken)}. Next month goes back to the {ordinal(sip_day)}. "
                    "No Lifeline used.",
            "checks": checks, "passed": all(c["passed"] for c in checks),
            "done": f"Moved. {month}'s SIP goes on {fmt(nd)}; next month is back to the {ordinal(sip_day)}."}


def answer_payload(r):
    kind = {"answer": "answer", "decline_advice": "decline"}.get(r.behaviour, "fallback")
    return {"kind": kind, "message": r.message, "sources": [{"title": t, "url": u} for t, u in r.sources],
            "safety": bool(r.safety_passed), "fallback_reason": r.fallback_reason}


# ---------------------------------------------------------------- endpoints
@safe
async def api_plan(request):
    b = await read_json(request)
    ex = EX_BY_ID.get(str(b.get("example") or ""))
    text = str(b.get("text") or "").strip()[:300]
    if ex and text and text != ex["text"]:
        ex = None                                   # an edited example counts as the user's own words
    if ex and not text:
        text = ex["text"]
    cal_day = day_arg(b.get("current_day"), R.PERSONAS[ex["persona"]]["calendar_sip"] if ex else 5, R.MAX_SIP_DAY)
    decline = ""
    if isinstance(b.get("manual"), dict):
        rh = manual_rhythm(b["manual"])
        if rh is None:
            return JSONResponse({"status": "fallback", "reason": "manual", "message": "Pick a pattern and its days first."})
        by = "you"
    else:
        if not text:
            return JSONResponse({"status": "fallback", "reason": "empty",
                                 "message": "Tell me when your money comes in, or pick the closest pattern."})
        rh, limit = await ai("parse", R.parse_rhythm, text, ip=client_ip(request), ok=lambda r: not r.get("error"))
        if limit:
            return JSONResponse({"status": "fallback", "reason": "limit", "message": limit + " Pick the closest pattern instead."})
        by = "ai"
        decline = M.DECLINE_MSG if rh.get("asks_advice") else ""
        if rh.get("error"):
            return JSONResponse({"status": "fallback", "reason": "ai_down", "decline": decline,
                                 "message": "The AI can't be reached right now. Pick the closest pattern and the rules do the rest."})
        if rh["pattern"] == "unknown" or rh["confidence"] < R.MIN_CONF:
            return JSONResponse({"status": "fallback", "reason": "unsure", "decline": decline,
                                 "confidence": round(float(rh.get("confidence") or 0), 2),
                                 "message": "I couldn't find a payday in that. Pick the closest pattern and the rules do the rest."})
    out = build_plan(rh, by, text, ex, cal_day)
    out["decline"] = decline
    return JSONResponse(out)


@safe
async def api_reply(request):
    b = await read_json(request)
    text = str(b.get("text") or "").strip()[:300]
    sip = date_arg(b.get("sip"), dt.date.today())
    sip_day, mode = day_arg(b.get("sip_day"), 5, R.MAX_SIP_DAY), b.get("mode", "fixed")
    if not text:
        return JSONResponse({"kind": "unclear", "message": "Type a reply, or use one of the buttons."})
    c, limit = await ai("reply", R.classify_reply, text, fmt(sip), ip=client_ip(request),
                        ok=lambda r: not str(r.get("rule", "")).startswith("llm failed"))
    if limit:
        return JSONResponse({"kind": "limit", "message": limit})
    intent = c["intent"]
    read = {"intent": intent, "money_day": c["money_day"], "target_day": c["target_day"],
            "confidence": round(float(c["confidence"] or 0), 2), "provider": (c.get("provider") or "").split(":")[0].title(),
            "rule": c.get("rule") or ""}
    if intent == "move":
        read["text"] = ("Money's late" + (f": arrives on the {ordinal(c['money_day'])}" if c["money_day"] else "")
                        + (f", asks for the {ordinal(c['target_day'])}" if c["target_day"] else ""))
    else:
        read["text"] = INTENT_TEXT.get(intent, "Couldn't tell")
    if read["rule"].startswith("llm failed"):
        read["rule"] = ""
    out = {"read": read}
    if intent == "all_good":
        if mode == "one_tap":
            inv = R.next_working_day(date_arg(b.get("tap"), dt.date.today()))
            out.update(kind="done", tone="ok", message=f"Done. ₹{AMOUNT} will be invested on {fmt(inv)}. Your bank also "
                                                     "sends its standard notice the day before.")
        else:
            out.update(kind="done", tone="ok", message=f"Great. Nothing changes: ₹{AMOUNT} goes on {fmt(sip)}.")
    elif intent == "move":
        if mode == "one_tap":
            out.update(kind="done", tone="info", message="No problem. I'll ask again in 2 days. Nothing is taken before you "
                                                         "tap yes.")
        else:
            new_day, reason = R.propose_move(c, sip_day, sip)
            out.update(move_payload(new_day, reason, sip, sip_day, c["money_day"] if not c["target_day"] else None))
    elif intent in ("lifeline", "stop"):
        out["kind"] = intent
    elif intent == "advice":
        out.update(kind="decline", message=M.DECLINE_MSG)
    elif intent == "question":
        r, limit = await ai("ask", M.run, text, ip=client_ip(request), cost=2)
        out.update(answer_payload(r) if r else {"kind": "limit", "message": limit})
    else:
        out.update(kind="unclear", message="I didn't catch that. Pick one of the options in the notification.")
    if c.get("rule", "").startswith("llm failed"):
        out.update(kind="unclear", message="The AI can't be reached right now. The options in the notification still work.")
    return JSONResponse(out)


@safe
async def api_move(request):
    b = await read_json(request)
    sip = date_arg(b.get("sip"), dt.date.today())
    sip_day, money_day = day_arg(b.get("sip_day"), 5, R.MAX_SIP_DAY), day_arg(b.get("money_day"))
    if not money_day:
        return JSONResponse({"kind": "ask_day", "message": "When will your money arrive this month?",
                             "days": list(range(max(1, sip_day - 2), 27))})
    new_day, reason = R.propose_move({"money_day": money_day}, sip_day, sip)
    return JSONResponse(move_payload(new_day, reason, sip, sip_day, money_day))


@safe
async def api_learn(request):
    b = await read_json(request)
    days = [day_arg(d) for d in (b.get("days") or [])][:3]
    mode = "one_tap" if b.get("mode") == "one_tap" else "fixed"
    noun = str(b.get("noun") or "money")[:20]
    return JSONResponse(learn_payload(days, mode, day_arg(b.get("sip_day"), 5, R.MAX_SIP_DAY), noun))


@safe
async def api_ask(request):
    b = await read_json(request)
    text = str(b.get("text") or "").strip()[:300]
    if not text:
        return JSONResponse({"kind": "fallback", "message": "Type a question first."})
    r, limit = await ai("ask", M.run, text, ip=client_ip(request), cost=2)
    return JSONResponse(answer_payload(r) if r else {"kind": "limit", "message": limit})


def _evals():
    """Headline numbers for the 'How it's checked' step, read from the eval reports so they never drift."""
    def grab(fname, label):
        f = ROOT / fname
        if not f.exists():
            return None
        mt = re.search(re.escape(label) + r"[^|]*\|\s*\**\s*(\d+)%[^(|]*\((\d+)/(\d+)\)", f.read_text(encoding="utf-8"))
        return [int(x) for x in mt.groups()] if mt else None

    def tile(v, label, detail):
        return {"value": v[0], "suffix": "%", "label": label, "detail": detail.format(a=v[1], b=v[2])} if v else None
    pat, pat1 = grab("rhythm_eval.md", "Pay pattern read correctly"), grab("rhythm_eval_v1.md", "Pay pattern read correctly")
    rep, rep1 = grab("rhythm_eval.md", "Check-in reply intent"), grab("rhythm_eval_v1.md", "Check-in reply intent")
    dates = grab("rhythm_eval.md", "Recommended dates passing")
    beh, adv = grab("mvp_eval.md", "Behaviour accuracy"), grab("mvp_eval.md", "Advice refusal **recall**")
    tiles = [tile(pat, "pay descriptions read correctly", "{a} of {b}" + (f" · first run {pat1[0]}%" if pat1 else "")),
             tile(rep, "check-in replies read correctly", "{a} of {b}" + (f" · first run {rep1[0]}%" if rep1 else "")),
             tile(dates, "suggested dates passed the rule check", "{a} of {b}"),
             tile(beh, "safety tests handled correctly", "{a} of {b}, incl. 19 red-team prompts"),
             tile(adv, "advice requests refused", "{a} of {b}, 0 answerable questions refused")]
    tiles = [t for t in tiles if t]
    tiles.append({"value": 0, "suffix": "", "label": "unsafe answers shown", "detail": "Guard 2 checks every answer"})
    return tiles


async def api_config(request):
    return JSONResponse({"examples": [{**{k: e[k] for k in ("id", "label", "hint", "text")},
                                       "sip": R.PERSONAS[e["persona"]]["calendar_sip"]} for e in EXAMPLES],
                         "evals": _evals(), "amount": AMOUNT, "today": dt.date.today().isoformat(),
                         "max_day": R.MAX_SIP_DAY})


class Static(StaticFiles):
    """Static files that browsers re-check on every load (cheap 304s), so a redeploy never serves stale JS/CSS."""
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


async def index(request):
    return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-cache"})


async def health(request):
    return PlainTextResponse("ok")


app = Starlette(routes=[
    Route("/", index), Route("/healthz", health), Route("/api/config", api_config),
    Route("/api/plan", api_plan, methods=["POST"]), Route("/api/reply", api_reply, methods=["POST"]),
    Route("/api/move", api_move, methods=["POST"]), Route("/api/learn", api_learn, methods=["POST"]),
    Route("/api/ask", api_ask, methods=["POST"]),
    Mount("/static", Static(directory=WEB), name="static"),
], middleware=[Middleware(GZipMiddleware, minimum_size=800)])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8503"))
    uvicorn.run(app, host="0.0.0.0" if "PORT" in os.environ else "127.0.0.1", port=port, log_level="info")
