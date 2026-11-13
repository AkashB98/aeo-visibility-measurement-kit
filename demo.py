"""End-to-end demo: report, check gate, and a live serve round-trip."""
import json
import subprocess
import sys
import time
import urllib.request


def run():
    from report import build_report, to_markdown
    r = build_report()
    print(to_markdown(r))
    assert r["parser_accuracy"]["mentions"] == 1.0
    assert r["planted_change_w2_to_w3"]["flagged"] is True
    assert r["lead_lag"]["best_lag"] == 2
    proc = subprocess.Popen([sys.executable, "cli.py", "serve", "8791"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8791/health", timeout=2) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.1)
        with urllib.request.urlopen("http://127.0.0.1:8791/report", timeout=5) as resp:
            served = resp.read().decode()
        assert "AEO visibility report" in served
        req = urllib.request.Request("http://127.0.0.1:8791/report", data=b"{}", method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            posted = json.loads(resp.read().decode())
        assert posted["lead_lag"]["best_lag"] == 2
        print("serve round-trip OK (GET /report, POST /report match local)")
    finally:
        proc.terminate()
    print("demo OK")
    return 0


if __name__ == "__main__":
    sys.exit(run())
