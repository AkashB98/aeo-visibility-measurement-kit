"""Build the full AEO report (JSON dict + markdown) from generated fixtures."""
from generator import BRANDS, TARGET, WEEKS, generate
from measure import bootstrap_share_ci, change_flag, lead_lag, parse_answer, shares, shares_by_intent


def build_report(seed=42):
    samples, signups = generate(seed)
    # Parser accuracy vs stored ground truth is itself an eval headline.
    exact_m = exact_c = 0
    for s in samples:
        m, c = parse_answer(s["text"])
        exact_m += int(m == s["truth_mentions"])
        exact_c += int(c == s["truth_citations"])
    weekly = {}
    presence_by_week, signups_by_week = {}, {}
    for w in WEEKS:
        sub = [s for s in samples if s["week"] == w]
        mshare, presence = shares(sub)
        cshare, _ = shares(sub, key="citations")
        weekly[str(w)] = {"mention_share": {b: round(mshare[b], 4) for b in BRANDS},
                          "citation_share": {b: round(cshare[b], 4) for b in BRANDS},
                          "presence": {b: round(presence[b], 4) for b in BRANDS}}
        presence_by_week[w] = presence[TARGET]
        signups_by_week[w] = next(x["signups"] for x in signups if x["week"] == w)
    # Period-over-period change on POOLED windows (pre W1-2 vs post W3-4):
    # a single week is 60 samples and too noisy to flag honestly.
    w2 = [s for s in samples if s["week"] in (1, 2)]
    w3 = [s for s in samples if s["week"] in (3, 4)]
    ci_all = bootstrap_share_ci(samples)
    report = {
        "target": TARGET,
        "samples": len(samples),
        "parser_accuracy": {"mentions": round(exact_m / len(samples), 4),
                            "citations": round(exact_c / len(samples), 4)},
        "weekly": weekly,
        "by_intent_target_share": {k: round(v[TARGET], 4) for k, v in shares_by_intent(samples).items()},
        "target_share_ci": {"point": round(ci_all[0], 4), "lo": round(ci_all[1], 4), "hi": round(ci_all[2], 4)},
        "planted_change_w2_to_w3": change_flag(w2, w3),
        "lead_lag": lead_lag(presence_by_week, signups_by_week),
        "signups_total_last_touch": sum(signups_by_week.values()),
        "attribution": "last_touch_only",
    }
    return report


def to_markdown(r):
    lines = ["# AEO visibility report (synthetic fixtures)", "",
             f"Target brand: {r['target']} — samples: {r['samples']}",
             f"Parser accuracy vs ground truth: mentions {r['parser_accuracy']['mentions']}, citations {r['parser_accuracy']['citations']}",
             f"Target mention share (all weeks): {r['target_share_ci']['point']} "
             f"(bootstrap 95% CI {r['target_share_ci']['lo']}–{r['target_share_ci']['hi']})",
             f"Planted change pre (W1-2) → post (W3-4), pooled: diff {r['planted_change_w2_to_w3']['diff']}, "
             f"CI {r['planted_change_w2_to_w3']['lo']}–{r['planted_change_w2_to_w3']['hi']}, flagged={r['planted_change_w2_to_w3']['flagged']}",
             f"Lead-lag: best lag {r['lead_lag']['best_lag']} weeks, correlations {r['lead_lag']['correlations']}",
             f"Signups (last-touch, AI-answer channel): {r['signups_total_last_touch']}",
             "", "## Honest limits",
             "- Snapshots are generated fixtures, not live LLM answers. Live answers vary per ask; "
             "that is why every share carries a bootstrap noise interval and changes flag only beyond noise.",
             "- Last-touch attribution misses influence when someone reads an AI answer and never clicks. "
             "Measuring that needs a holdout design (see the incrementality-holdout-planner repo), not last-touch.",
             "- Mention share is share of total brand mentions; answer-presence rate is reported alongside it in the JSON."]
    return "\n".join(lines) + "\n"
