"""Mock-server tests for `./stack export|import penpot` (stacks/penpot/hooks.sh app_export/app_import).

No Docker and no real Penpot: a stdlib HTTP server mimics the RPC commands the hook uses
(login-with-password, get-all-projects, get-teams, get-projects, get-project-files, create-project,
export-binfile (SSE), /assets/by-id, import-binfile (multipart, SSE)). Needs curl and jq on PATH.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL, PASSWORD, TOKEN = "me@example.test", "s3cret-Pass-123", "tok.en-abc_123"
TEAM = "11111111-1111-4111-8111-111111111111"
PROJ = "22222222-2222-4222-8222-222222222222"


class State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.calls = []
        self.blobs = {}
        self.imports = []
        self.projects = [
            {"id": PROJ, "name": "Marka Seti", "teamId": TEAM, "teamName": "Ekibim", "isDefaultTeam": True},
            {"id": "33333333-3333-4333-8333-333333333333", "name": "Drafts", "teamId": TEAM, "teamName": "Ekibim"},
        ]
        self.files = [{"id": "44444444-4444-4444-8444-444444444444", "name": "Ana / Tasarim"},
                      {"id": "55555555-5555-4555-8555-555555555555", "name": "Ikonlar"}]


S = State()


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    def _authed(self):
        return (self.headers.get("Authorization") == "Token " + TOKEN
                or "auth-token=ok" in (self.headers.get("Cookie") or ""))

    def _send(self, code, body=b"", ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, b"ok", "text/html")
        m = re.match(r"^/assets/by-id/([0-9a-f-]{36})$", self.path)
        if m and m.group(1) in S.blobs:
            return self._send(200, S.blobs[m.group(1)], "application/zip")
        self._send(404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        cmd = self.path.rsplit("/", 1)[-1]
        S.calls.append(cmd)
        if cmd == "login-with-password":
            b = json.loads(raw)
            if b.get("email") == EMAIL and b.get("password") == PASSWORD:
                return self._send(200, b"{}", extra={"Set-Cookie": "auth-token=ok; Path=/"})
            return self._send(400, b'{"code":"wrong-credentials"}')
        if not self._authed():
            return self._send(401, b'{"code":"authentication"}')
        if cmd == "get-all-projects":
            return self._send(200, json.dumps(S.projects).encode())
        if cmd == "get-teams":
            return self._send(200, json.dumps([{"id": TEAM, "name": "Ekibim", "isDefault": True}]).encode())
        if cmd == "get-projects":
            return self._send(200, json.dumps([p for p in S.projects if p["teamId"] == json.loads(raw)["teamId"]]).encode())
        if cmd == "get-project-files":
            return self._send(200, json.dumps(S.files).encode())
        if cmd == "create-project":
            b = json.loads(raw)
            p = {"id": str(uuid.uuid4()), "name": b["name"], "teamId": b["teamId"], "teamName": "Ekibim"}
            S.projects.append(p)
            return self._send(200, json.dumps(p).encode())
        if cmd == "export-binfile":
            b = json.loads(raw)
            assert not (b["includeLibraries"] and b["embedAssets"])
            u = str(uuid.uuid4())
            S.blobs[u] = b"PK\x03\x04" + b["fileId"].encode() + (b"-embed" if b["embedAssets"] else b"-libs")
            body = ("event: progress\ndata: {}\n\nevent: end\ndata: \"http://x/assets/by-id/%s\"\n\n" % u).encode()
            return self._send(200, body, "text/event-stream")
        if cmd == "import-binfile":
            fields = {}
            bnd = re.search(r"boundary=(.+)", self.headers["Content-Type"]).group(1).encode()
            for part in raw.split(b"--" + bnd)[1:-1]:
                head, _, val = part.strip(b"\r\n").partition(b"\r\n\r\n")
                nm = re.search(rb'name="([^"]+)"', head).group(1).decode()
                fields[nm] = val
            S.imports.append(fields)
            return self._send(200, b"event: end\ndata: [\"x\"]\n\n", "text/event-stream")
        self._send(404)


class PenpotTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.tmp = tempfile.mkdtemp(prefix="pp-transfer-")
        cls.local = os.path.join(cls.tmp, "local")
        cls.env = {k: v for k, v in os.environ.items() if not k.startswith(("PENPOT_", "STACK_"))}
        cls.env["STACK_LOCAL_DIR"] = cls.local
        r = cls.run_stack("init")
        assert r.returncode == 0, r.stderr
        p = os.path.join(cls.local, ".env")
        txt = open(p).read().replace("PENPOT_PORT=8702", "PENPOT_PORT=%d" % cls.port)
        open(p, "w").write(txt)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        S.reset()

    @classmethod
    def run_stack(cls, *args, extra=None):
        env = dict(cls.env)
        env.update(extra or {})
        return subprocess.run(["/bin/bash", os.path.join(ROOT, "stack")] + list(args), env=env,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)

    def login_env(self):
        return {"PENPOT_EMAIL": EMAIL, "PENPOT_PASSWORD": PASSWORD}

    def export(self, *args, extra=None):
        return self.run_stack("export", "penpot", *args, extra=self.login_env() if extra is None else extra)

    def test_list(self):
        r = self.export("--list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Marka Seti", r.stdout)
        self.assertIn(PROJ, r.stdout)

    def test_no_credentials_is_prereq_error(self):
        r = self.export("--list", extra={})
        self.assertEqual(r.returncode, 2)

    def test_wrong_password(self):
        r = self.export("--list", extra={"PENPOT_EMAIL": EMAIL, "PENPOT_PASSWORD": "nope-nope-nope"})
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("nope-nope-nope", r.stdout + r.stderr)

    def test_unknown_project(self):
        r = self.export("Yok Boyle Proje")
        self.assertEqual(r.returncode, 1)

    def test_export_then_import_roundtrip(self):
        out = os.path.join(self.tmp, "o1")
        r = self.export("Marka Seti", "-o", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn(PASSWORD, r.stdout + r.stderr)
        self.assertEqual(oct(os.stat(out).st_mode & 0o777), "0o700")
        m = json.load(open(os.path.join(out, "manifest.json")))
        self.assertEqual(m["project"]["name"], "Marka Seti")
        self.assertEqual(m["libraries"], "include-libraries")
        self.assertEqual([f["name"] for f in m["files"]], ["Ana / Tasarim", "Ikonlar"])
        for f in m["files"]:
            p = os.path.join(out, f["file"])
            self.assertEqual(oct(os.stat(p).st_mode & 0o777), "0o600")
            self.assertEqual(len(f["sha256"]), 64)
        self.assertTrue(os.path.isfile(out + ".tar"))
        # import from the .tar into a new project name
        r = self.run_stack("import", "penpot", out + ".tar", "--project", "Kopya", extra=self.login_env())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("proje olusturuldu: Kopya", r.stdout)
        self.assertEqual(len(S.imports), 2)
        self.assertEqual(S.imports[0]["name"], b"Ana / Tasarim")
        self.assertEqual(S.imports[0]["version"], b"3")
        self.assertTrue(S.imports[0]["file"].startswith(b"PK"))
        newp = [p for p in S.projects if p["name"] == "Kopya"][0]
        self.assertEqual(S.imports[0]["project-id"].decode(), newp["id"])

    def test_embed_assets_and_default_project_name_with_token(self):
        out = os.path.join(self.tmp, "o2")
        r = self.export("Marka Seti", "-o", out, "--embed-assets", extra={"PENPOT_ACCESS_TOKEN": TOKEN})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.load(open(os.path.join(out, "manifest.json")))["libraries"], "embed-assets")
        r = self.run_stack("import", "penpot", out, extra={"PENPOT_ACCESS_TOKEN": TOKEN})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("proje var", r.stdout)  # "Marka Seti" already exists: files are added
        self.assertNotIn("login-with-password", S.calls)

    def test_default_output_dir_is_under_local_exports(self):
        r = self.export("Marka Seti")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        base = os.path.join(self.local, "exports", "penpot")
        self.assertEqual(oct(os.stat(base).st_mode & 0o777), "0o700")
        self.assertTrue(any(n.endswith(".tar") for n in os.listdir(base)))

    def test_tampered_archive_is_rejected_before_any_request(self):
        out = os.path.join(self.tmp, "o3")
        self.assertEqual(self.export("Marka Seti", "-o", out).returncode, 0)
        m = json.load(open(os.path.join(out, "manifest.json")))
        with open(os.path.join(out, m["files"][1]["file"]), "ab") as f:
            f.write(b"x")
        S.calls.clear()
        r = self.run_stack("import", "penpot", out, extra=self.login_env())
        self.assertEqual(r.returncode, 1)
        self.assertIn("hash uyusmuyor", r.stdout + r.stderr)
        self.assertEqual(S.calls, [])
        self.assertEqual(S.imports, [])

    def test_unsafe_tar_is_rejected(self):
        bad = os.path.join(self.tmp, "bad.tar")
        src = os.path.join(self.tmp, "evil.txt")
        open(src, "w").write("x")
        with tarfile.open(bad, "w") as t:
            t.add(src, arcname="../evil.txt")
        r = self.run_stack("import", "penpot", bad, extra=self.login_env())
        self.assertEqual(r.returncode, 1)
        self.assertEqual(S.calls, [])

    def test_usage_errors(self):
        self.assertEqual(self.run_stack("export", "penpot").returncode, 1)
        self.assertEqual(self.run_stack("export", "plane", "x").returncode, 1)
        self.assertEqual(self.run_stack("import", "penpot").returncode, 1)
        self.assertEqual(self.run_stack("export", "penpot", "--bogus").returncode, 1)


if __name__ == "__main__":
    unittest.main()
