"""Golden evals: pin the headline numbers so regressions fail loudly."""
import json
import sys

sys.path.insert(0, ".")
from report import build_report  # noqa: E402


def main():
    r = build_report()
    checks = []

    def chk(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    chk("sample_count_480", r["samples"] == 480, r["samples"])
    chk("parser_mentions_exact", r["parser_accuracy"]["mentions"] == 1.0, r["parser_accuracy"]["mentions"])
    chk("parser_citations_exact", r["parser_accuracy"]["citations"] == 1.0, r["parser_accuracy"]["citations"])
    chk("planted_change_flagged", r["planted_change_w2_to_w3"]["flagged"], r["planted_change_w2_to_w3"])
    chk("planted_change_positive", r["planted_change_w2_to_w3"]["diff"] > 0.05, r["planted_change_w2_to_w3"]["diff"])
    chk("lead_lag_best_is_2", r["lead_lag"]["best_lag"] == 2, r["lead_lag"])
    chk("lead_lag_corr_strong", r["lead_lag"]["correlations"]["2"] > 0.8, r["lead_lag"]["correlations"]["2"])
    chk("ci_brackets_point", r["target_share_ci"]["lo"] <= r["target_share_ci"]["point"] <= r["target_share_ci"]["hi"], r["target_share_ci"])
    chk("target_share_rises", r["weekly"]["8"]["mention_share"]["Helios Home"] > r["weekly"]["1"]["mention_share"]["Helios Home"],
        {"w1": r["weekly"]["1"]["mention_share"]["Helios Home"], "w8": r["weekly"]["8"]["mention_share"]["Helios Home"]})
    chk("intent_classes_present", set(r["by_intent_target_share"]) == {"category", "comparison", "brand"}, r["by_intent_target_share"])
    chk("signups_total_positive", r["signups_total_last_touch"] > 800, r["signups_total_last_touch"])
    chk("attribution_last_touch_only", r["attribution"] == "last_touch_only", r["attribution"])
    out = {"checks": checks, "passed": sum(1 for c in checks if c["ok"]), "total": len(checks),
           "report_headline": {"target_share_ci": r["target_share_ci"],
                               "planted_change": r["planted_change_w2_to_w3"],
                               "lead_lag": r["lead_lag"]}}
    with open("evals/eval_report.json", "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(json.dumps({"passed": out["passed"], "total": out["total"]}))
    for c in checks:
        if not c["ok"]:
            print("FAIL", c["name"], c["detail"])
    return 0 if out["passed"] == out["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
