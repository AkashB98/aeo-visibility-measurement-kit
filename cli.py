"""CLI: generate / report / check / demo / serve."""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from generator import generate
from report import build_report, to_markdown


def validate(samples):
    errors = []
    if len(samples) != 480:
        errors.append(f"expected 480 samples, got {len(samples)}")
    for s in samples:
        if s["weight"] <= 0:
            errors.append("non-positive query weight")
            break
        if s["intent"] not in ("category", "comparison", "brand"):
            errors.append(f"bad intent {s['intent']}")
            break
    return errors


def cmd_check():
    samples, _ = generate()
    errors = validate(samples)
    r = build_report()
    if r["parser_accuracy"]["mentions"] != 1.0:
        errors.append("parser does not recover ground-truth mentions exactly")
    if not r["planted_change_w2_to_w3"]["flagged"]:
        errors.append("planted pre->post visibility change was not flagged beyond noise")
    if r["lead_lag"]["best_lag"] != 2:
        errors.append(f"lead-lag check found lag {r['lead_lag']['best_lag']}, planted lag is 2")
    if errors:
        print("FAIL: " + "; ".join(errors))
        return 1
    print("PASS: samples, parser, noise-flagged change, and lead-lag (2 weeks) all hold")
    return 0


def serve(port=8765):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == "/health":
                body, code = b'{"ok": true}', 200
            elif self.path == "/report":
                body, code = to_markdown(build_report()).encode(), 200
            else:
                body, code = b"not found", 404
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/report":
                self.send_response(404); self.end_headers(); return
            length = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(length)
            body = json.dumps(build_report()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    HTTPServer(("127.0.0.1", port), H).serve_forever()


def main(argv):
    if not argv:
        print(__doc__); return 2
    cmd = argv[0]
    if cmd == "generate":
        samples, signups = generate()
        print(json.dumps({"samples": len(samples), "signups_weeks": len(signups)}))
        return 0
    if cmd == "report":
        print(to_markdown(build_report()))
        return 0
    if cmd == "check":
        return cmd_check()
    if cmd == "demo":
        import demo
        return demo.run()
    if cmd == "serve":
        serve(int(argv[1]) if len(argv) > 1 else 8765)
        return 0
    print(f"unknown command {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
