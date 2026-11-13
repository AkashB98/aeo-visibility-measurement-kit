"""Deterministic synthetic AEO dataset.

Fictional brands only. No live LLM querying: answer snapshots are
generated fixtures, stored with structured ground truth so the parser
can be scored against truth.
"""
import random

BRANDS = ["Helios Home", "Lumen Living", "Casa Verde", "BrightNest", "Urban Habitat"]
DOMAINS = {
    "Helios Home": "helioshome.example",
    "Lumen Living": "lumenliving.example",
    "Casa Verde": "casaverde.example",
    "BrightNest": "brightnest.example",
    "Urban Habitat": "urbanhabitat.example",
}
TARGET = "Helios Home"
WEEKS = [1, 2, 3, 4, 5, 6, 7, 8]
SAMPLES_PER_QUERY = 5

QUERIES = [
    {"id": "q01", "text": "best smart home starter kit", "intent": "category", "weight": 3.0, "brand": None},
    {"id": "q02", "text": "best home energy monitor", "intent": "category", "weight": 3.0, "brand": None},
    {"id": "q03", "text": "best smart lighting system for apartments", "intent": "category", "weight": 3.0, "brand": None},
    {"id": "q04", "text": "best smart thermostat setup", "intent": "category", "weight": 3.0, "brand": None},
    {"id": "q05", "text": "Helios Home vs Lumen Living", "intent": "comparison", "weight": 2.0, "brand": None},
    {"id": "q06", "text": "Casa Verde vs BrightNest for energy saving", "intent": "comparison", "weight": 2.0, "brand": None},
    {"id": "q07", "text": "which is better for renters, Helios Home or Urban Habitat", "intent": "comparison", "weight": 2.0, "brand": None},
    {"id": "q08", "text": "BrightNest vs Helios Home pricing", "intent": "comparison", "weight": 2.0, "brand": None},
    {"id": "q09", "text": "Helios Home reviews", "intent": "brand", "weight": 1.0, "brand": "Helios Home"},
    {"id": "q10", "text": "Lumen Living reviews", "intent": "brand", "weight": 1.0, "brand": "Lumen Living"},
    {"id": "q11", "text": "Casa Verde pricing", "intent": "brand", "weight": 1.0, "brand": "Casa Verde"},
    {"id": "q12", "text": "BrightNest setup guide", "intent": "brand", "weight": 1.0, "brand": "BrightNest"},
]

# Mention probability per brand, before the planted week-3 Helios jump.
BASE_P = {"Helios Home": 0.30, "Lumen Living": 0.62, "Casa Verde": 0.48, "BrightNest": 0.44, "Urban Habitat": 0.36}
POST_P = {"Helios Home": 0.82, "Lumen Living": 0.44, "Casa Verde": 0.46, "BrightNest": 0.42, "Urban Habitat": 0.34}


def _prob(brand, week, query):
    if query["brand"] is not None:
        return 0.96 if brand == query["brand"] else 0.10
    if query["intent"] == "comparison":
        named = [b for b in BRANDS if b in query["text"]]
        if brand in named:
            return 0.92
        return 0.12
    return (POST_P if week >= 3 else BASE_P)[brand]


def render_answer(query_text, mentions, citations):
    # NOTE: the query text itself is NOT echoed — brand queries name a brand,
    # and echoing it would make parser-vs-truth scoring meaningless.
    parts = ["Here are the options most often recommended for this request."]
    if mentions:
        parts.append("Top picks include " + ", ".join(mentions) + ".")
        for b in mentions:
            parts.append(f"{b} is a common choice for this use case.")
    else:
        parts.append("No single brand stands out in this answer.")
    for b in citations:
        parts.append(f"See {DOMAINS[b]} for details.")
    return " ".join(parts)


def generate(seed=42):
    """Return (samples, signups). Samples carry ground-truth mentions/citations."""
    samples = []
    for wi, week in enumerate(WEEKS):
        for qi, q in enumerate(QUERIES):
            for si in range(SAMPLES_PER_QUERY):
                rng = random.Random(seed * 100000 + wi * 1000 + qi * 100 + si)
                mentions = [b for b in BRANDS if rng.random() < _prob(b, week, q)]
                rng.shuffle(mentions)
                citations = [b for b in mentions if rng.random() < 0.70]
                samples.append({
                    "week": week, "query_id": q["id"], "intent": q["intent"],
                    "weight": q["weight"], "sample": si,
                    "text": render_answer(q["text"], mentions, citations),
                    "truth_mentions": mentions, "truth_citations": citations,
                })
    # Lagging indicator: weekly signups, last-touch attributed to the AI-answer
    # channel, with a PLANTED lag of 2 weeks behind Helios answer-presence.
    # Presence here uses the SAME weighted definition measure.shares() uses,
    # so the lead-lag check reads the series the signups were planted from.
    presence = {}
    for week in WEEKS:
        wk = [s for s in samples if s["week"] == week]
        num = sum(s["weight"] for s in wk if TARGET in s["truth_mentions"])
        presence[week] = num / sum(s["weight"] for s in wk)
    signups = []
    for wi, week in enumerate(WEEKS):
        lagged = presence[week - 2] if week - 2 in presence else 0.30
        rng = random.Random(seed * 777 + wi)
        total = int(round(120 + 180 * lagged + rng.uniform(-2, 2)))
        signups.append({"week": week, "signups": total, "channel": "ai_answer_last_touch"})
    return samples, signups
