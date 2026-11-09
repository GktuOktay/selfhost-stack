"""CB-7 (e): two-stage Blade/PHP scanner, positive controls and one negative fixture per rule."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "blade_scan"))
import _docker  # noqa: E402
import blade_scan  # noqa: E402

FIX = os.path.join(blade_scan.HERE, "fixtures")

REQUIRED_RULES = blade_scan.REQUIRED_RULES


def rules_of(entries):
    return {e["rule"] for e in entries}


class BladeScan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = blade_scan.scan()

    def _group(self, sub):
        return {k: v for k, v in self.res.items() if f"/fixtures/{sub}/" in k}

    def test_theme_partials_exist_and_clean(self):
        partials = {k: v for k, v in self.res.items() if k.startswith("/theme/selfhost/")}
        names = {os.path.basename(k) for k in partials}
        for want in ("home.blade.php", "cards.blade.php", "shelf.blade.php"):
            self.assertIn(want, names, f"missing partial {want}")
        for k, v in partials.items():
            self.assertEqual(v, [], f"{k} violates rules: {v}")

    def test_no_phase2a_partials(self):
        self.assertFalse(os.path.exists(os.path.join(_docker.THEME, "selfhost", "data.blade.php")))

    def test_positive_fixtures_clean(self):
        pos = self._group("pos")
        self.assertGreaterEqual(len(pos), 8)
        for k, v in pos.items():
            self.assertEqual(v, [], f"positive control {k} flagged: {v}")

    def test_negative_fixtures_caught_by_named_rule(self):
        groups = {}
        for sub in ("neg", "stage2"):
            groups.update(self._group(sub))
        self.assertGreaterEqual(len(groups), 200)
        failures = []
        for k, v in groups.items():
            expected = os.path.basename(k).split("--", 1)[0]
            if expected not in rules_of(v):
                failures.append(f"{os.path.basename(k)}: expected {expected}, got {sorted(rules_of(v))}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_every_rule_has_a_negative_fixture(self):
        have = {os.path.basename(k).split("--", 1)[0]
                for sub in ("neg", "stage2") for k in self._group(sub)}
        self.assertEqual([r for r in REQUIRED_RULES if r not in have], [])

    def test_stage2_fixtures_are_stage2(self):
        for k, v in self._group("stage2").items():
            self.assertTrue(v, f"{k} not flagged")
            self.assertTrue(all(e["stage"] == 2 for e in v), f"{k}: {v}")


if __name__ == "__main__":
    unittest.main()
