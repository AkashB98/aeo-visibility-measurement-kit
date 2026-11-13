# AEO visibility report (synthetic fixtures)

Target brand: Helios Home — samples: 480
Parser accuracy vs ground truth: mentions 1.0, citations 1.0
Target mention share (all weeks): 0.2928 (bootstrap 95% CI 0.2766–0.3147)
Planted change pre (W1-2) → post (W3-4), pooled: diff 0.104, CI 0.0392–0.1571, flagged=True
Lead-lag: best lag 2 weeks, correlations {'0': 0.7386, '1': 0.8829, '2': 0.9992, '3': 0.7142}
Signups (last-touch, AI-answer channel): 1744

## Honest limits
- Snapshots are generated fixtures, not live LLM answers. Live answers vary per ask; that is why every share carries a bootstrap noise interval and changes flag only beyond noise.
- Last-touch attribution misses influence when someone reads an AI answer and never clicks. Measuring that needs a holdout design (see the incrementality-holdout-planner repo), not last-touch.
- Mention share is share of total brand mentions; answer-presence rate is reported alongside it in the JSON.

