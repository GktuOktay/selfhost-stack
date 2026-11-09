"""Stub-render checks of the selfhost/ partials in the pinned image (logic of CB-2, CB-4, CB-6, CB-10, CB-11).

Not the end-to-end test: BookStack itself is not running here (that needs the stack CLI, blocked on 0001).
Helpers are stubs; Blade compiler, collect() and e() are the image's own.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docker  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
U18 = "adres geçersiz"
U19 = "Bu makinede etkin değil"
U27 = "adres hesaplanamadı"
U22 = "Proje etiketi geçersiz: "
U23 = "Birden fazla proje etiketi var, ilki kullanıldı."
U28 = "Bu rafta görebileceğiniz kitap yok."
TAG = "plane-project"
BOOKS = [(1, "Bir", "2026-01-01 10:00:00"), (2, "Iki", "2026-03-01 10:00:00"), (3, "Uc", "2026-03-01 10:00:00"),
         (4, "Dort", "2025-01-01 10:00:00"), (5, "Bes", "2026-02-01 10:00:00"), (6, "Alti", "2026-04-01 10:00:00"),
         (7, "Yedi", "2025-06-01 10:00:00")]
OKENV = {"SELFHOST_PENPOT_STATE": "ok", "SELFHOST_PENPOT_URL": "http://localhost:8702",
         "SELFHOST_PLANE_STATE": "ok", "SELFHOST_PLANE_URL": "http://localhost:8703"}

SCENARIOS = {
    # cards / home
    "home-admin": {"view": "selfhost.home", "env": OKENV},
    "home-guest": {"view": "selfhost.home", "env": OKENV, "guest": True},
    "cards-default": {"view": "selfhost.cards", "env": OKENV},
    "cards-port": {"view": "selfhost.cards", "env": {**OKENV, "SELFHOST_PENPOT_URL": "http://localhost:8712"}},
    "cards-disabled": {"view": "selfhost.cards", "env": {"SELFHOST_PENPOT_STATE": "disabled", "SELFHOST_PLANE_STATE": "disabled"}},
    "cards-error": {"view": "selfhost.cards", "env": {"SELFHOST_PENPOT_STATE": "error", "SELFHOST_PLANE_STATE": "ok", "SELFHOST_PLANE_URL": "http://localhost:8703"}},
    "cards-unset": {"view": "selfhost.cards", "env": {}},
    "cards-js": {"view": "selfhost.cards", "env": {**OKENV, "SELFHOST_PLANE_URL": "javascript:alert(1)"}},
    "cards-ok-empty-url": {"view": "selfhost.cards", "env": {**OKENV, "SELFHOST_PLANE_URL": ""}},
    "cards-ok-null-url": {"view": "selfhost.cards", "env": {"SELFHOST_PENPOT_STATE": "ok", "SELFHOST_PLANE_STATE": "ok"}},
    "cards-inject": {"view": "selfhost.cards", "env": {**OKENV, "SELFHOST_PLANE_URL": "http://x/\"><script>alert(1)</script>"}},
    "cards-uppercase-scheme": {"view": "selfhost.cards", "env": {**OKENV, "SELFHOST_PLANE_URL": "HTTP://x"}},
    "cards-ftp": {"view": "selfhost.cards", "env": {**OKENV, "SELFHOST_PLANE_URL": "ftp://x"}},
    # shelf (CB-10, CB-11)
    "shelf-no-tags": {"view": "selfhost.shelf", "books": BOOKS},
    "shelf-other-tag": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, "owner", "WEB"]]},
    "shelf-invalid-only": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "<b>x"]]},
    "shelf-spaced": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, " web "]]},
    "shelf-api-then-web": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "API"], [2, TAG, "WEB"]]},
    "shelf-ids-reversed": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[9, TAG, "WEB"], [3, TAG, "API"]]},
    "shelf-invalid-then-web": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "<b>x"], [2, TAG, "WEB"]]},
    "shelf-dotless-i": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "wıb"]]},
    "shelf-capital-name": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, "Plane-Project", "WEB"]]},
    "shelf-capital-then-valid": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, "Plane-Project", "<b>x"], [2, TAG, "WEB"]]},
    "shelf-empty-value": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, ""]]},
    "shelf-13-chars": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "ABCDEFGHIJKLM"]]},
    "shelf-12-chars": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "ABCDEFGHIJKL"]]},
    "shelf-newline-value": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "WEB\nX"]]},
    "shelf-no-books": {"view": "selfhost.shelf", "books": [], "tags": [[1, TAG, "WEB"]]},
    "shelf-xss-name": {"view": "selfhost.shelf", "books": [(1, "<img src=x onerror=1>", "2026-01-01 10:00:00")], "tags": [[1, TAG, "WEB"]]},
    "shelf-guest-sees": {"view": "selfhost.shelf", "books": BOOKS, "tags": [[1, TAG, "WEB"]], "guest": True},
}


class Render(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory(prefix="t3-render-") as d:
            p = os.path.join(d, "scenarios.json")
            with open(p, "w") as f:
                json.dump(SCENARIOS, f)
            r = _docker.run(_docker.pinned_image(), ["/render/render.php", "/theme", "/in/scenarios.json"],
                            mounts=[(os.path.join(HERE, "render"), "/render"), (_docker.THEME, "/theme"), (d, "/in")],
                            entrypoint="php")
        out = r.stdout.decode()
        try:
            cls.out = json.loads(out)
        except ValueError:
            raise RuntimeError("render.php failed: %r %r" % (out[:400], r.stderr.decode(errors="replace")[:400]))

    def test_no_exceptions(self):
        bad = {k: v for k, v in self.out.items() if v.startswith("EXCEPTION")}
        self.assertEqual(bad, {})

    # ---- home and cards
    def test_home_has_marker_and_three_cards(self):
        h = self.out["home-admin"]
        self.assertIn("data-selfhost-dashboard", h)
        for c in ("bookstack", "penpot", "plane"):
            self.assertEqual(h.count(f'data-selfhost-card="{c}"'), 1)
        self.assertNotIn("data-selfhost-plane", h)
        self.assertNotIn("data-selfhost-specs", h)

    def test_home_guest_prints_nothing(self):
        self.assertEqual(self.out["home-guest"].strip(), "")

    def test_card_urls(self):
        h = self.out["cards-default"]
        self.assertIn('href="http://localhost:8701/books"', h)
        self.assertIn('href="http://localhost:8702"', h)
        self.assertIn('href="http://localhost:8703"', h)
        self.assertEqual(h.count('rel="noopener noreferrer"'), 2)
        self.assertIn('href="http://localhost:8712"', self.out["cards-port"])

    def test_cards_disabled_u19(self):
        h = self.out["cards-disabled"]
        self.assertEqual(h.count(U19), 2)
        self.assertEqual(h.count("href="), 1)  # only the BookStack card links

    def test_cards_error_and_unset_u27(self):
        self.assertEqual(self.out["cards-error"].count(U27), 1)
        self.assertEqual(self.out["cards-unset"].count(U27), 2)
        self.assertEqual(self.out["cards-unset"].count("href="), 1)

    def test_cards_invalid_scheme_u18(self):
        for k in ("cards-js", "cards-ok-empty-url", "cards-ftp"):
            h = self.out[k]
            self.assertEqual(h.count(U18), 1, k)
            self.assertNotIn("javascript:", h, k)
            self.assertNotIn("ftp://", h, k)
        self.assertEqual(self.out["cards-ok-null-url"].count(U18), 2)

    def test_cards_uppercase_scheme_is_a_link(self):
        self.assertIn('href="HTTP://x"', self.out["cards-uppercase-scheme"])

    def test_cb4_injection_escaped(self):
        h = self.out["cards-inject"]
        self.assertIn('href="http://x/&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"', h)
        self.assertNotIn("<script>alert(1)", h)
        self.assertEqual(h.count("<script"), 0)

    # ---- shelf
    def test_no_tag_no_marker(self):
        for k in ("shelf-no-tags", "shelf-other-tag", "shelf-capital-name"):
            h = self.out[k].strip()
            self.assertEqual(h, "", k)

    def test_cb11_a_to_g(self):
        o = self.out
        # (b) only an invalid value
        self.assertIn(U22 + "&lt;b&gt;x", o["shelf-invalid-only"])
        self.assertNotIn("data-selfhost-shelf>", o["shelf-invalid-only"])
        self.assertNotIn("data-selfhost-shelf ", o["shelf-invalid-only"])
        self.assertNotIn("<b>x", o["shelf-invalid-only"])
        # (c) padded value
        self.assertIn("Proje: WEB", o["shelf-spaced"])
        # (d) first tag by id decides, U-23 note
        self.assertIn("Proje: API", o["shelf-api-then-web"])
        self.assertEqual(o["shelf-api-then-web"].count(U23), 1)
        self.assertIn("Proje: API", o["shelf-ids-reversed"])  # id 3 (API) precedes id 9 (WEB)
        # (e) invalid first, valid second: U-22 + U-23, no title
        e = o["shelf-invalid-then-web"]
        self.assertIn(U22, e)
        self.assertEqual(e.count(U23), 1)
        self.assertNotIn("Proje: ", e)
        self.assertNotIn("data-selfhost-shelf", e.replace("data-selfhost-shelf-", ""))
        # (f) dotless i
        self.assertIn(U22 + "wıb", o["shelf-dotless-i"])
        self.assertNotIn("Proje: ", o["shelf-dotless-i"])
        # (g) 'Plane-Project' is not a candidate -> nothing; and it does not shadow a real tag
        self.assertEqual(o["shelf-capital-name"].strip(), "")
        self.assertIn("Proje: WEB", o["shelf-capital-then-valid"])
        self.assertNotIn(U23, o["shelf-capital-then-valid"])

    def test_marker_only_for_valid_tag(self):
        marker = "data-selfhost-shelf>"
        for k in ("shelf-spaced", "shelf-api-then-web", "shelf-12-chars", "shelf-guest-sees", "shelf-no-books"):
            self.assertEqual(self.out[k].count(marker), 1, k)
        for k in ("shelf-no-tags", "shelf-invalid-only", "shelf-dotless-i", "shelf-empty-value", "shelf-13-chars",
                  "shelf-newline-value", "shelf-invalid-then-web"):
            self.assertEqual(self.out[k].count(marker), 0, k)
            self.assertNotIn("Proje: ", self.out[k], k)

    def test_value_length_bounds(self):
        self.assertIn("Proje: ABCDEFGHIJKL", self.out["shelf-12-chars"])
        self.assertIn(U22 + "ABCDEFGHIJKLM", self.out["shelf-13-chars"])
        self.assertIn(U22, self.out["shelf-empty-value"])

    def test_cb10_latest_five_by_updated_at_then_id_desc(self):
        h = self.out["shelf-spaced"]
        order = [n for n in ("Alti", "Uc", "Iki", "Bes", "Bir", "Yedi", "Dort") if n in h]
        pos = {n: h.index(n) for n in order}
        self.assertEqual(sorted(pos, key=pos.get), ["Alti", "Uc", "Iki", "Bes", "Bir"])  # tie 03-01: id 3 before id 2
        self.assertNotIn("Yedi", h)
        self.assertNotIn("Dort", h)
        self.assertIn("Son güncellenen kitaplar", h)
        self.assertIn('href="/books/6"', h)

    def test_cb10_no_visible_books_u28(self):
        h = self.out["shelf-no-books"]
        self.assertIn(U28, h)
        self.assertIn("Proje: WEB", h)
        self.assertNotIn(U28, self.out["shelf-spaced"])

    def test_book_names_escaped(self):
        h = self.out["shelf-xss-name"]
        self.assertNotIn("<img", h)
        self.assertIn("&lt;img", h)


if __name__ == "__main__":
    unittest.main()
