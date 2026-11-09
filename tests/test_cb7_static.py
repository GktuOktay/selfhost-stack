"""CB-7 (d), (e), (f) static checks for the selfhost-dashboard theme."""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docker  # noqa: E402
import cb7_static_check as cb7  # noqa: E402


def theme_copy(test):
    d = tempfile.mkdtemp(prefix="cb7-")
    test.addCleanup(shutil.rmtree, d, True)
    t = os.path.join(d, "theme")
    shutil.copytree(_docker.THEME, t)
    return t


def put(theme, rel, text="x\n"):
    p = os.path.join(theme, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


class FileSet(unittest.TestCase):  # CB-7 (d)
    def test_real_theme(self):
        self.assertEqual(cb7.check_d(_docker.THEME), [])

    def test_functions_php(self):
        t = theme_copy(self)
        put(t, "functions.php", "<?php\n")
        self.assertTrue(any("functions.php" in e for e in cb7.check_d(t)))

    def test_functions_php_nested(self):
        t = theme_copy(self)
        put(t, "selfhost/functions.php", "<?php\n")
        self.assertTrue(any("functions.php" in e for e in cb7.check_d(t)))

    def test_public_dir(self):
        t = theme_copy(self)
        put(t, "public/a.txt")
        self.assertTrue(any("public" in e for e in cb7.check_d(t)))

    def test_empty_public_dir(self):
        t = theme_copy(self)
        os.makedirs(os.path.join(t, "public"))
        self.assertTrue(any("public" in e for e in cb7.check_d(t)))

    def test_extra_file_not_in_allow(self):
        t = theme_copy(self)
        put(t, "selfhost/data.blade.php")
        self.assertTrue(cb7.check_d(t))

    def test_extra_meta_file(self):
        t = theme_copy(self)
        put(t, "NOTES")
        self.assertTrue(cb7.check_d(t))

    def test_allow_lists_missing_file(self):
        t = theme_copy(self)
        os.remove(os.path.join(t, "selfhost", "cards.blade.php"))
        self.assertTrue(cb7.check_d(t))


class SlashStrings(unittest.TestCase):  # CB-7 (f)
    def check(self, text):
        t = tempfile.mkdtemp(prefix="cb7f-")
        self.addCleanup(shutil.rmtree, t, True)
        os.makedirs(os.path.join(t, "selfhost"))
        with open(os.path.join(t, "selfhost", "x.blade.php"), "w") as f:
            f.write(text)
        return cb7.check_f(t)

    def test_real_theme(self):
        self.assertEqual(cb7.check_f(_docker.THEME), [])

    def test_books_ok(self):
        self.assertEqual(self.check("{{ url('/books') }}\n"), [])

    def test_other_single(self):
        self.assertTrue(self.check("{{ url('/login') }}\n"))

    def test_other_double(self):
        self.assertTrue(self.check('{{ url("/login") }}\n'))

    def test_books_suffix(self):
        self.assertTrue(self.check("{{ url('/books/1') }}\n"))
        self.assertTrue(self.check("{{ url('/books ') }}\n"))

    def test_html_attribute_value(self):
        self.assertTrue(self.check('<a href="/settings">x</a>\n'))

    def test_root_slash(self):
        self.assertTrue(self.check("{{ url('/') }}\n"))

    def test_escaped_quote_does_not_hide(self):
        self.assertTrue(self.check("{{ trim('a\\'', '/etc') }} {{ url('/etc') }}\n"))

    def test_comment_ignored(self):
        self.assertEqual(self.check("{{-- url('/login') --}}\n"), [])

    def test_regex_not_starting_with_slash_ok(self):
        self.assertEqual(self.check("@if(preg_match('#^https?://#i', 'x'))\n@endif\n"), [])

    def test_scheme_relative_url(self):
        self.assertTrue(self.check("{{ url('//evil.example') }}\n"))


class BladeScanStage(unittest.TestCase):  # CB-7 (e)
    def test_scanner_and_negative_fixtures(self):
        self.assertEqual(cb7.check_e(), [])


if __name__ == "__main__":
    unittest.main()
