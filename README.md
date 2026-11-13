# aeo-visibility-measurement-kit

**AEO** — Answer Engine Optimization: how often a brand shows up inside AI-generated answers, and whether that visibility turns into signups.

Brands are no longer only ranked in search results — they are mentioned, or not mentioned, inside AI answers. Two hiring teams described this exact measurement job in the same week (Cognition's Search & AI Discoverability Lead, 2026-11-10; Klaviyo's Head of Organic Search, SEO & AEO, 2026-11-12): build the framework that measures AI-answer visibility, separates leading from lagging indicators, and ties visibility to revenue without pretending the number is exact.

This kit is that framework, offline and deterministic, on synthetic fixtures only.

## What it does

- **Fixed query set, weighted by intent** — 12 fictional queries in 3 classes (category ×3 weight, comparison ×2, brand ×1), 5 saved answer samples per query per week, 8 weeks = 480 snapshots. Share is reported overall and per intent class.
- **Mention + citation share, with a noise interval** — every share is share of total brand mentions (answer-presence rate is reported alongside), and every headline share carries a **bootstrap confidence interval** — a range built by resampling the snapshots, so sampling noise has a size. A period change is flagged **only when the bootstrap interval for the difference excludes zero**.
- **Parser scored against ground truth** — snapshots are generated fixtures with stored true mentions/citations; the text parser must recover them exactly (it does: 1.0 / 1.0).
- **Lead–lag check** — leading indicator (visibility) vs lagging indicator (last-touch signups from the AI-answer channel): correlations at lags 0–3 weeks, best lag reported. The synthetic data plants a 2-week lag; the check finds it (correlation 0.9992 at lag 2).
- **Planted change, honestly flagged** — Helios Home's mention probability jumps at week 3. Pooled pre (W1–2) vs post (W3–4): diff +0.104, bootstrap CI +0.039 to +0.157, flagged. Stable week pairs (W6 vs W7) are pinned as *not* flagged.

Headline numbers (seed 42): target mention share 0.2928 (95% CI 0.2766–0.3147), W1 share 0.2025 → W8 share 0.3262, signups (last-touch) 1,744 over 8 weeks.

## Honest limits

- Snapshots are generated fixtures, **not live LLM answers** — there is no live querying in this kit. Live answers vary per ask; that variance is exactly why shares carry noise intervals instead of being reported as points.
- **Last-touch attribution only**, on purpose: multi-touch lives in the attribution-pipeline repo. Last-touch also misses influence when someone reads an AI answer and never clicks — measuring that needs a holdout design (see incrementality-holdout-planner), and the report says so.
- Period-over-period change is the only drift view; a full extraction-drift subsystem already lives in web-extraction-drift-kit and is not duplicated here.

## Dev-loop notes (real bugs, fixed in the code — not the tests)

1. The first renderer echoed the query text into the answer. Brand/comparison queries name brands, so the parser "found" brands the answer never recommended — parser accuracy 0.70. Fix: answers never echo the query.
2. A single week is 60 samples: the planted jump's weekly diff (+0.061) sat inside its own noise interval. Fix: flag changes on pooled period windows (pre vs post), which is also how a real measurement team would report it.
3. Signups were planted from an *unweighted* presence series while the report recomputed a *weighted* one — the lead–lag check then found lag 1, not the planted lag 2. Fix: one presence definition, used by both the generator and the check.

## Run it

```bash
python3 cli.py generate   # dataset summary
python3 cli.py report     # markdown report
python3 cli.py check      # CI gate: exit 0 = parser, noise-flag, and lead-lag all hold
python3 demo.py           # full demo incl. live serve round-trip
python3 cli.py serve 8765 # GET /report, POST /report, GET /health on 127.0.0.1
python3 -m unittest discover -s tests   # 14 tests
python3 evals/run_evals.py              # 12 golden evals, eval_report.json
```

Stdlib only. Synthetic data only — five fictional brands, no real company, customer, or personal data.

## Why this exists

Claude cross-check (2026-11-12, both-routes rule; terminal verdict saved with the run): **AGREE-WITH-CUTS** — ranked the only buildable candidate of the day; its cuts are adopted above (no drift subsystem, no multi-touch, no "AI workflows" filler) and its adds are the bootstrap interval, the intent weighting, and the lead–lag check. Two sibling candidates were DISAGREED the same day and not built: an agent-sandbox policy evaluator (duplicate of the guardrails/gateway kits) and an agentic-RAG routing eval (duplicates the RAG evals + cost gate; Claude's router idea is logged as a module backlog item for the existing RAG repo).

MIT License.
