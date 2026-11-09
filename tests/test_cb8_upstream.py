"""CB-8 (spec 0002): upstream compatibility checks, positive on the real theme and negative fixtures."""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _docker  # noqa: E402
import cb8_upstream_check as cb8  # noqa: E402

with open(os.path.join(_docker.THEME, "UPSTREAM"), encoding="utf-8") as _f:
    REAL_UPSTREAM = _f.read()
IMG = _docker.pinned_image()


def theme_copy(test):
    d = tempfile.mkdtemp(prefix="cb8-")
    test.addCleanup(shutil.rmtree, d, True)
    t = os.path.join(d, "theme")
    shutil.copytree(_docker.THEME, t)
    return t


def write(path, data):
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)


def sub_upstream(old, new, count=1):
    assert old in REAL_UPSTREAM, old
    return REAL_UPSTREAM.replace(old, new, count)


class Grammar(unittest.TestCase):
    def errs(self, text):
        up, errors = cb8.parse_upstream(text)
        return errors

    def test_real_upstream_valid(self):
        up, errors = cb8.parse_upstream(REAL_UPSTREAM)
        self.assertEqual(errors, [])
        self.assertEqual(up.image, IMG)
        self.assertEqual(up.view_root, "/app/www/resources/views")
        self.assertEqual(set(up.views), {"home/default.blade.php", "shelves/show.blade.php"})

    def test_unknown_line_type(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "FOO bar\n"))

    def test_lowercase_key(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "view_root=/x\n"))

    def test_two_images(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "BOOKSTACK_IMAGE=x:y@sha256:" + "0" * 64 + "\n"))

    def test_no_image(self):
        text = "\n".join(l for l in REAL_UPSTREAM.splitlines() if not l.startswith("BOOKSTACK_IMAGE="))
        self.assertTrue(self.errs(text))

    def test_no_view_root(self):
        text = "\n".join(l for l in REAL_UPSTREAM.splitlines() if not l.startswith("VIEW_ROOT="))
        self.assertTrue(self.errs(text))

    def test_two_view_roots(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "VIEW_ROOT=/y\n"))

    def test_duplicate_view_path(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "VIEW home/default.blade.php " + "a" * 64 + "\n"))

    def test_duplicate_allow_path(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "ALLOW README\n"))

    def test_bad_sha(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "VIEW x/y.blade.php " + "a" * 63 + "\n"))
        self.assertTrue(self.errs(REAL_UPSTREAM + "VIEW x/y.blade.php " + "A" * 64 + "\n"))
        self.assertTrue(self.errs(REAL_UPSTREAM + "VIEW x/y.blade.php\n"))

    def test_unsafe_paths(self):
        self.assertTrue(self.errs(REAL_UPSTREAM + "ALLOW /etc/passwd\n"))
        self.assertTrue(self.errs(REAL_UPSTREAM + "ALLOW ../x\n"))
        self.assertTrue(self.errs(REAL_UPSTREAM + "ALLOW a/../b\n"))

    def test_no_allow(self):
        text = "\n".join(l for l in REAL_UPSTREAM.splitlines() if not l.startswith("ALLOW "))
        self.assertTrue(self.errs(text))

    def test_view_root_must_be_absolute(self):
        self.assertTrue(self.errs(sub_upstream("VIEW_ROOT=/app/www/resources/views", "VIEW_ROOT=app/www")))

    def test_crlf_rejected(self):
        self.assertTrue(self.errs(REAL_UPSTREAM.replace("\n", "\r\n")))

    def test_empty_file(self):
        self.assertTrue(self.errs(""))

    def test_no_view_lines_is_valid(self):
        text = "\n".join(l for l in REAL_UPSTREAM.splitlines() if not l.startswith("VIEW "))
        up, errors = cb8.parse_upstream(text + "\n")
        self.assertEqual(errors, [])
        self.assertEqual(up.views, {})


class ImageEquality(unittest.TestCase):
    def test_equal(self):
        up, _ = cb8.parse_upstream(REAL_UPSTREAM)
        self.assertEqual(cb8.check_image_equal(up, IMG), [])

    def test_different_tag(self):
        up, _ = cb8.parse_upstream(REAL_UPSTREAM)
        self.assertTrue(cb8.check_image_equal(up, IMG.replace("ls295", "ls296")))

    def test_different_digest_one_char(self):
        up, _ = cb8.parse_upstream(REAL_UPSTREAM)
        self.assertTrue(cb8.check_image_equal(up, IMG[:-1] + ("0" if IMG[-1] != "0" else "1")))

    def test_trailing_space(self):
        up, _ = cb8.parse_upstream(REAL_UPSTREAM)
        self.assertTrue(cb8.check_image_equal(up, IMG + " "))


class AllowAndMapping(unittest.TestCase):
    def setUp(self):
        self.theme = theme_copy(self)
        self.up, _ = cb8.parse_upstream(REAL_UPSTREAM)

    def test_real_theme_file_set_equals_allow(self):
        self.assertEqual(cb8.check_allow_equal(_docker.THEME, self.up), [])

    def test_extra_file(self):
        write(os.path.join(self.theme, "selfhost", "extra.blade.php"), "x")
        self.assertTrue(cb8.check_allow_equal(self.theme, self.up))

    def test_extra_meta_like_file(self):
        write(os.path.join(self.theme, "NOTES"), "x")
        self.assertTrue(cb8.check_allow_equal(self.theme, self.up))

    def test_missing_file(self):
        os.remove(os.path.join(self.theme, "selfhost", "cards.blade.php"))
        self.assertTrue(cb8.check_allow_equal(self.theme, self.up))

    def test_symlink_rejected(self):
        os.symlink("/etc/passwd", os.path.join(self.theme, "link"))
        self.assertTrue(cb8.check_allow_equal(self.theme, self.up))

    def test_mapping_ok_on_real(self):
        self.assertEqual(cb8.check_view_allow_mapping(self.up), [])

    def test_allow_override_without_view(self):
        up, _ = cb8.parse_upstream(sub_upstream("VIEW shelves/show.blade.php c9b32a3fbec368c1f449f4553db73fc1c969bd6f9d7a55b56b05a02386e9ed7a\n", ""))
        self.assertTrue(cb8.check_view_allow_mapping(up))

    def test_view_without_allow(self):
        up, _ = cb8.parse_upstream(sub_upstream("ALLOW shelves/show.blade.php\n", ""))
        self.assertTrue(cb8.check_view_allow_mapping(up))

    def test_partial_deletion_fixture(self):
        # shelves override file and its ALLOW row gone, VIEW row left behind -> (6) breaks
        up, _ = cb8.parse_upstream(sub_upstream("ALLOW shelves/show.blade.php\n", ""))
        os.remove(os.path.join(self.theme, "shelves", "show.blade.php"))
        self.assertTrue(cb8.check_view_allow_mapping(up))

    def test_m2_full_deletion_fixture_passes(self):
        text = "\n".join(l for l in REAL_UPSTREAM.splitlines()
                         if not l.startswith("VIEW ") and "default.blade.php" not in l and "show.blade.php" not in l
                         and "selfhost/" not in l) + "\n"
        up, errors = cb8.parse_upstream(text)
        self.assertEqual(errors, [])
        for rel in ("home/default.blade.php", "shelves/show.blade.php"):
            os.remove(os.path.join(self.theme, rel))
        shutil.rmtree(os.path.join(self.theme, "selfhost"))
        shutil.rmtree(os.path.join(self.theme, "home"))
        shutil.rmtree(os.path.join(self.theme, "shelves"))
        self.assertEqual(cb8.check_allow_equal(self.theme, up), [])
        self.assertEqual(cb8.check_view_allow_mapping(up), [])

    def test_no_view_but_override_allowed_is_not_valid(self):
        text = "\n".join(l for l in REAL_UPSTREAM.splitlines() if not l.startswith("VIEW ")) + "\n"
        up, _ = cb8.parse_upstream(text)
        self.assertTrue(cb8.check_view_allow_mapping(up))


class RawDiff(unittest.TestCase):
    ORIG = b"line one\n    <div>\n  two\n\n@stop\n"

    def test_identical(self):
        self.assertEqual(cb8.check_raw_diff(self.ORIG, self.ORIG), [])

    def test_added_include(self):
        mod = self.ORIG.replace(b"  two\n", b"    @include('selfhost.home')\n  two\n")
        self.assertEqual(cb8.check_raw_diff(self.ORIG, mod), [])

    def test_two_added_includes(self):
        mod = b"@include('selfhost.a-b_c.d')\n" + self.ORIG + b"\t@include('selfhost.z')\n"
        self.assertEqual(cb8.check_raw_diff(self.ORIG, mod), [])

    def test_deleted_line(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG.replace(b"  two\n", b"")))

    def test_modified_line(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG.replace(b"two", b"twO")))

    def test_whitespace_only_change(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG.replace(b"  two", b"   two")))

    def test_added_blank_line(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG.replace(b"  two\n", b"\n  two\n")))

    def test_added_non_include(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG + b"<p>x</p>\n"))

    def test_include_wrong_namespace(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, b"@include('common.view-blocks')\n" + self.ORIG))

    def test_include_uppercase(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, b"@include('selfhost.Home')\n" + self.ORIG))

    def test_include_with_args(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, b"@include('selfhost.home', ['a' => 1])\n" + self.ORIG))

    def test_include_with_trailing_text(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, b"@include('selfhost.home') <script>\n" + self.ORIG))

    def test_include_double_quotes(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, b'@include("selfhost.home")\n' + self.ORIG))

    def test_added_include_and_deleted_line(self):
        mod = self.ORIG.replace(b"  two\n", b"@include('selfhost.home')\n")
        self.assertTrue(cb8.check_raw_diff(self.ORIG, mod))

    def test_carriage_return_added(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG.replace(b"\n", b"\r\n")))

    def test_include_line_with_cr(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, b"@include('selfhost.home')\r\n" + self.ORIG))

    def test_missing_trailing_newline(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG[:-1]))

    def test_extra_trailing_text_after_include(self):
        self.assertTrue(cb8.check_raw_diff(self.ORIG, self.ORIG + b"@include('selfhost.home')"))


class RealImage(unittest.TestCase):
    """Runs against the pinned image through docker (--network none). The image must be local."""

    @classmethod
    def setUpClass(cls):
        cls.up, errors = cb8.parse_upstream(REAL_UPSTREAM)
        assert not errors

    def fetch(self, path, platform=None):
        return _docker.cat_in_image(IMG, self.up.view_root + "/" + path, platform)

    def test_sha256_matches_pinned_image(self):
        self.assertEqual(cb8.check_views(_docker.THEME, self.up, self.fetch), [])

    def test_sha_mismatch_detected(self):
        def bad(path, platform=None):
            return self.fetch(path, platform) + b"x"
        self.assertTrue(cb8.check_views(_docker.THEME, self.up, bad))

    def test_override_edit_detected(self):
        theme = theme_copy(self)
        p = os.path.join(theme, "home", "default.blade.php")
        with open(p, "rb") as fh:
            data = fh.read()
        write(p, data.replace(b"container px-xl", b"container px-l", 1))
        self.assertTrue(cb8.check_views(theme, self.up, self.fetch))

    def test_override_with_extra_script_line_detected(self):
        theme = theme_copy(self)
        p = os.path.join(theme, "shelves", "show.blade.php")
        with open(p, "rb") as fh:
            data = fh.read()
        write(p, data.replace(b"@stop\n", b"<script>1</script>\n@stop\n", 1))
        self.assertTrue(cb8.check_views(theme, self.up, self.fetch))

    def test_override_missing_detected(self):
        theme = theme_copy(self)
        os.remove(os.path.join(theme, "shelves", "show.blade.php"))
        self.assertTrue(cb8.check_views(theme, self.up, self.fetch))

    def test_no_view_lines_skips_2_and_3(self):
        up, _ = cb8.parse_upstream("\n".join(l for l in REAL_UPSTREAM.splitlines() if not l.startswith("VIEW ")) + "\n")
        calls = []
        self.assertEqual(cb8.check_views(_docker.THEME, up, lambda *a: calls.append(a)), [])
        self.assertEqual(calls, [])

    def test_opcache_real_image(self):
        values, texts = cb8.gather_opcache(IMG)
        self.assertEqual(cb8.check_opcache(values, texts), [])
        self.assertEqual(values["opcache.validate_timestamps"], "1")


class Opcache(unittest.TestCase):
    OK = {"opcache.validate_timestamps": "1", "opcache.revalidate_freq": "2"}

    def test_ok(self):
        self.assertEqual(cb8.check_opcache(self.OK, {"/p/www.conf": "; php_admin_value[opcache.validate_timestamps] = 0\n[www]\nuser = abc\n"}), [])

    def test_validate_timestamps_off_effective(self):
        self.assertTrue(cb8.check_opcache({**self.OK, "opcache.validate_timestamps": "0"}, {}))
        self.assertTrue(cb8.check_opcache({**self.OK, "opcache.validate_timestamps": ""}, {}))
        self.assertTrue(cb8.check_opcache({**self.OK, "opcache.validate_timestamps": "Off"}, {}))

    def test_revalidate_freq_too_high(self):
        self.assertTrue(cb8.check_opcache({**self.OK, "opcache.revalidate_freq": "3"}, {}))
        self.assertTrue(cb8.check_opcache({**self.OK, "opcache.revalidate_freq": "abc"}, {}))
        self.assertTrue(cb8.check_opcache({**self.OK, "opcache.revalidate_freq": "-1"}, {}))

    def test_revalidate_freq_low_ok(self):
        self.assertEqual(cb8.check_opcache({**self.OK, "opcache.revalidate_freq": "0"}, {}), [])

    def test_fake_pool_file_validate_timestamps_zero(self):
        pool = "[www]\nphp_admin_value[opcache.validate_timestamps] = 0\n"
        self.assertTrue(cb8.check_opcache(self.OK, {"/etc/php85/php-fpm.d/zz.conf": pool}))

    def test_pool_php_value_variants(self):
        for line in ("php_value[opcache.revalidate_freq] = 60", "php_admin_value[opcache.revalidate_freq]=60",
                     "php_flag[opcache.validate_timestamps] = off", "php_admin_flag[opcache.validate_timestamps]=0",
                     "  php_value[ opcache.validate_timestamps ] = 0"):
            self.assertTrue(cb8.check_opcache(self.OK, {"/p.conf": "[www]\n" + line + "\n"}), line)

    def test_ini_override_file(self):
        self.assertTrue(cb8.check_opcache(self.OK, {"/etc/php85/conf.d/99-x.ini": "opcache.validate_timestamps=0\n"}))
        self.assertTrue(cb8.check_opcache(self.OK, {"/etc/php85/conf.d/99-x.ini": "opcache.revalidate_freq = 60\n"}))

    def test_commented_override_ignored(self):
        self.assertEqual(cb8.check_opcache(self.OK, {"/p.conf": ";php_admin_value[opcache.validate_timestamps] = 0\n# php_value[opcache.revalidate_freq]=9\n"}), [])

    def test_missing_values(self):
        self.assertTrue(cb8.check_opcache({}, {}))


if __name__ == "__main__":
    unittest.main()
