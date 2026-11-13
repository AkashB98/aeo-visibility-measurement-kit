import socket
import sys
import unittest

# Hermetic guard: no network in tests (serve tests use localhost via demo only).
_real_connect = socket.socket.connect


class NoNetworkGuard(unittest.TestCase):
    def setUp(self):
        def blocked(sock, addr, _orig=_real_connect):
            if addr and addr[0] not in ("127.0.0.1", "::1"):
                raise AssertionError(f"network access blocked in tests: {addr}")
            return _orig(sock, addr)
        socket.socket.connect = blocked

    def tearDown(self):
        socket.socket.connect = _real_connect


sys.path.insert(0, ".")
from generator import BRANDS, generate  # noqa: E402
from measure import bootstrap_share_ci, change_flag, lead_lag, parse_answer, shares, shares_by_intent  # noqa: E402
from report import build_report  # noqa: E402
from cli import validate  # noqa: E402


class TestGenerator(NoNetworkGuard):
    def test_counts(self):
        samples, signups = generate()
        self.assertEqual(len(samples), 480)
        self.assertEqual(len(signups), 8)

    def test_deterministic(self):
        a, _ = generate()
        b, _ = generate()
        self.assertEqual([s["text"] for s in a], [s["text"] for s in b])

    def test_validate_clean(self):
        samples, _ = generate()
        self.assertEqual(validate(samples), [])


class TestParser(NoNetworkGuard):
    def test_recovers_truth_all_samples(self):
        samples, _ = generate()
        for s in samples:
            m, c = parse_answer(s["text"])
            self.assertEqual(m, s["truth_mentions"])
            self.assertEqual(c, s["truth_citations"])

    def test_order_is_first_appearance(self):
        m, _ = parse_answer("Casa Verde is great. Helios Home too. See casaverde.example and helioshome.example.")
        self.assertEqual(m, ["Casa Verde", "Helios Home"])


class TestMetrics(NoNetworkGuard):
    def test_shares_sum_to_one(self):
        samples, _ = generate()
        share, _ = shares(samples)
        self.assertAlmostEqual(sum(share.values()), 1.0, places=6)
        self.assertEqual(set(share), set(BRANDS))

    def test_planted_jump(self):
        samples, _ = generate()
        w2 = shares([s for s in samples if s["week"] == 2])[0]["Helios Home"]
        w8 = shares([s for s in samples if s["week"] == 8])[0]["Helios Home"]
        self.assertGreater(w8, w2)

    def test_by_intent_keys(self):
        samples, _ = generate()
        out = shares_by_intent(samples)
        self.assertEqual(set(out), {"category", "comparison", "brand"})

    def test_bootstrap_ci_contains_point_and_deterministic(self):
        samples, _ = generate()
        a = bootstrap_share_ci(samples)
        b = bootstrap_share_ci(samples)
        self.assertEqual(a, b)
        self.assertLessEqual(a[1], a[0])
        self.assertGreaterEqual(a[2], a[0])
        self.assertGreater(a[2] - a[1], 0)

    def test_change_flag_on_planted_jump(self):
        samples, _ = generate()
        f = change_flag([s for s in samples if s["week"] in (1, 2)],
                        [s for s in samples if s["week"] in (3, 4)])
        self.assertTrue(f["flagged"])

    def test_change_flag_quiet_on_stable_weeks(self):
        samples, _ = generate()
        f = change_flag([s for s in samples if s["week"] == 6],
                        [s for s in samples if s["week"] == 7])
        self.assertFalse(f["flagged"])


class TestLeadLag(NoNetworkGuard):
    def test_best_lag_is_planted_two(self):
        r = build_report()
        self.assertEqual(r["lead_lag"]["best_lag"], 2)

    def test_lead_lag_unit(self):
        presence = {1: 0.3, 2: 0.3, 3: 0.6, 4: 0.6, 5: 0.6, 6: 0.6}
        signups = {1: 100, 2: 100, 3: 100, 4: 100, 5: 154, 6: 154}
        out = lead_lag(presence, signups)
        self.assertIn("best_lag", out)


class TestReport(NoNetworkGuard):
    def test_report_shape(self):
        r = build_report()
        self.assertEqual(r["attribution"], "last_touch_only")
        self.assertEqual(r["parser_accuracy"]["mentions"], 1.0)
        self.assertGreater(r["signups_total_last_touch"], 0)


if __name__ == "__main__":
    unittest.main()
