"""Parsing, share metrics, bootstrap noise intervals, and lead-lag check."""
import math
import random

from generator import BRANDS, DOMAINS, TARGET


def parse_answer(text):
    """Extract mentions (first-appearance order) and citations from answer text."""
    found = []
    for b in BRANDS:
        i = text.find(b)
        if i >= 0:
            found.append((i, b))
    mentions = [b for _, b in sorted(found)]
    cfound = []
    for b in BRANDS:
        i = text.find(DOMAINS[b])
        if i >= 0:
            cfound.append((i, b))
    return mentions, [b for _, b in sorted(cfound)]


def shares(samples, key="mentions"):
    """Weighted share of total brand mentions/citations, plus answer-presence rate."""
    total = {}
    denom = 0.0
    presence_num = {b: 0.0 for b in BRANDS}
    presence_den = 0.0
    parsed = []
    for s in samples:
        m, c = parse_answer(s["text"])
        parsed.append((m, c))
        vals = m if key == "mentions" else c
        for b in vals:
            total[b] = total.get(b, 0.0) + s["weight"]
            denom += s["weight"]
        for b in m:
            presence_num[b] += s["weight"]
        presence_den += s["weight"]
    share = {b: (total.get(b, 0.0) / denom if denom else 0.0) for b in BRANDS}
    presence = {b: (presence_num[b] / presence_den if presence_den else 0.0) for b in BRANDS}
    return share, presence


def shares_by_intent(samples):
    out = {}
    for intent in ("category", "comparison", "brand"):
        sub = [s for s in samples if s["intent"] == intent]
        out[intent] = shares(sub)[0] if sub else {b: 0.0 for b in BRANDS}
    return out


def bootstrap_share_ci(samples, brand=TARGET, reps=200, seed=7):
    """Percentile bootstrap CI for a brand's mention share (share of mentions)."""
    if not samples:
        return (0.0, 0.0, 0.0)
    point = shares(samples)[0][brand]
    rng = random.Random(seed)
    vals = []
    n = len(samples)
    for _ in range(reps):
        resample = [samples[rng.randrange(n)] for _ in range(n)]
        vals.append(shares(resample)[0][brand])
    vals.sort()
    lo = vals[int(0.025 * reps)]
    hi = vals[min(reps - 1, int(0.975 * reps))]
    return (point, lo, hi)


def change_flag(samples_a, samples_b, brand=TARGET, reps=200, seed=7):
    """Flag a change only when the bootstrap CI of the difference excludes 0."""
    if not samples_a or not samples_b:
        return {"diff": 0.0, "lo": 0.0, "hi": 0.0, "flagged": False}
    rng = random.Random(seed)
    diffs = []
    for _ in range(reps):
        ra = [samples_a[rng.randrange(len(samples_a))] for _ in range(len(samples_a))]
        rb = [samples_b[rng.randrange(len(samples_b))] for _ in range(len(samples_b))]
        diffs.append(shares(rb)[0][brand] - shares(ra)[0][brand])
    diffs.sort()
    point = shares(samples_b)[0][brand] - shares(samples_a)[0][brand]
    lo, hi = diffs[int(0.025 * reps)], diffs[min(reps - 1, int(0.975 * reps))]
    return {"diff": round(point, 4), "lo": round(lo, 4), "hi": round(hi, 4),
            "flagged": bool(lo > 0 or hi < 0)}


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def lead_lag(presence_by_week, signups_by_week, max_lag=3):
    """Correlation of visibility vs signups at each lag; best lag wins."""
    weeks = sorted(presence_by_week)
    out = {}
    for lag in range(max_lag + 1):
        xs, ys = [], []
        for w in weeks:
            src = w - lag
            if src in presence_by_week:
                xs.append(presence_by_week[src])
                ys.append(signups_by_week[w])
        out[lag] = round(_pearson(xs, ys), 4) if len(xs) >= 3 else 0.0
    best = max(out, key=lambda k: out[k])
    return {"correlations": {str(k): v for k, v in out.items()}, "best_lag": best}
