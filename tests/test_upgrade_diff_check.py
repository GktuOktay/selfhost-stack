"""M-1 (a): tests/upgrade_diff_check.sh against throw-away git repositories (no network, no docker)."""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "upgrade_diff_check.sh")
D1 = "a" * 64
D2 = "b" * 64
OLD = "lscr.io/linuxserver/bookstack:v26.09.2-ls295@sha256:" + D1
NEW = "lscr.io/linuxserver/bookstack:v26.09.3-ls296@sha256:" + D2
VERSIONS = "# pins\nBOOKSTACK_IMAGE=%s\nBOOKSTACK_DB_IMAGE=lscr.io/linuxserver/mariadb:11.8.9-r0-ls239@sha256:" + "c" * 64 + "\n"
UPSTREAM = "# up\nBOOKSTACK_IMAGE=%s\nVIEW_ROOT=/app/www/resources/views\nVIEW home/default.blade.php " + "d" * 64 + "\nALLOW README\n"
VF = "stacks/bookstack/versions.env"
UF = "stacks/bookstack/theme/selfhost-dashboard/UPSTREAM"


def git(cwd, *args, check=True):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, capture_output=True, text=True, check=check)


class Repo:
    def __init__(self, test):
        self.dir = tempfile.mkdtemp(prefix="udc-")
        test.addCleanup(shutil.rmtree, self.dir, True)
        git(self.dir, "init", "-q", "-b", "main")
        self.write(VF, VERSIONS % OLD)
        self.write(UF, UPSTREAM % OLD)
        self.write("README.md", "hello\n")
        with open(SCRIPT) as fh:
            self.write("tests/upgrade_diff_check.sh", fh.read())
        os.chmod(os.path.join(self.dir, "tests/upgrade_diff_check.sh"), 0o755)
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "base")

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)

    def read(self, rel):
        with open(os.path.join(self.dir, rel)) as f:
            return f.read()

    def branch(self, name):
        git(self.dir, "checkout", "-q", "-b", name, "main")

    def commit(self, msg="change"):
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", msg)

    def bump(self, vnew=NEW, unew=None):
        self.write(VF, self.read(VF).replace(OLD, vnew))
        self.write(UF, self.read(UF).replace(OLD, unew if unew is not None else vnew))

    def check(self, head, base="main", script=None):
        """Run the base branch's copy of the script (as CI does) unless `script` is given."""
        if script is None:
            p = git(self.dir, "show", f"{base}:tests/upgrade_diff_check.sh")
            script = os.path.join(self.dir, "..", os.path.basename(self.dir) + "-base-script.sh")
            with open(script, "w") as f:
                f.write(p.stdout)
            os.chmod(script, 0o755)
            self.addclean = script
        return subprocess.run(["sh", script, base, head], cwd=self.dir, capture_output=True, text=True)


class UpgradeDiffCheck(unittest.TestCase):
    def setUp(self):
        self.r = Repo(self)
        self.addCleanup(lambda: [os.path.exists(p) and os.remove(p) for p in
                                 [os.path.join(self.r.dir, "..", os.path.basename(self.r.dir) + "-base-script.sh")]])

    def ok(self, head="bump"):
        p = self.r.check(head)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def bad(self, head="bump", code=1):
        p = self.r.check(head)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p

    def test_clean_bump_passes(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.commit()
        self.ok()

    def test_clean_bump_in_two_commits_passes(self):
        self.r.branch("bump")
        self.r.write(VF, self.r.read(VF).replace(OLD, NEW))
        self.r.commit("one")
        self.r.write(UF, self.r.read(UF).replace(OLD, NEW))
        self.r.commit("two")
        self.ok()

    def test_base_moved_on_uses_merge_base(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.commit()
        git(self.r.dir, "checkout", "-q", "main")
        self.r.write("README.md", "hello again\n")
        self.r.commit("other work on base")
        self.ok()

    def test_empty_diff_fails(self):
        self.r.branch("bump")
        self.bad()

    def test_only_versions_env_fails(self):
        self.r.branch("bump")
        self.r.write(VF, self.r.read(VF).replace(OLD, NEW))
        self.r.commit()
        self.bad()

    def test_only_upstream_fails(self):
        self.r.branch("bump")
        self.r.write(UF, self.r.read(UF).replace(OLD, NEW))
        self.r.commit()
        self.bad()

    def test_third_file_fails(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.write("README.md", "changed\n")
        self.r.commit()
        self.bad()

    def test_new_file_fails(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.write("stacks/bookstack/theme/selfhost-dashboard/selfhost/data.blade.php", "x\n")
        self.r.commit()
        self.bad()

    def test_values_differ_by_one_char_fails(self):
        self.r.branch("bump")
        self.r.bump(unew=NEW[:-1] + "c")
        self.r.commit()
        self.bad()

    def test_trailing_space_in_upstream_value_fails(self):
        self.r.branch("bump")
        self.r.bump(unew=NEW + " ")
        self.r.commit()
        self.bad()

    def test_carriage_return_fails(self):
        self.r.branch("bump")
        self.r.bump(unew=NEW + "\r")
        self.r.commit()
        self.bad()

    def test_no_digest_fails(self):
        self.r.branch("bump")
        v = "lscr.io/linuxserver/bookstack:v26.09.3-ls296"
        self.r.bump(vnew=v)
        self.r.commit()
        self.bad()

    def test_short_digest_fails(self):
        self.r.branch("bump")
        v = "lscr.io/linuxserver/bookstack:v26.09.3-ls296@sha256:" + "b" * 63
        self.r.bump(vnew=v)
        self.r.commit()
        self.bad()

    def test_floating_tag_fails(self):
        self.r.branch("bump")
        v = "lscr.io/linuxserver/bookstack:latest@sha256:" + D2
        self.r.bump(vnew=v)
        self.r.commit()
        self.bad()

    def test_digest_only_no_tag_fails(self):
        self.r.branch("bump")
        v = "lscr.io/linuxserver/bookstack@sha256:" + D2
        self.r.bump(vnew=v)
        self.r.commit()
        self.bad()

    def test_db_image_bumped_too_fails(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.write(VF, self.r.read(VF).replace("mariadb:11.8.9-r0-ls239", "mariadb:11.8.10-r0-ls240"))
        self.r.commit()
        self.bad()

    def test_other_line_in_upstream_changed_fails(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.write(UF, self.r.read(UF).replace("d" * 64, "e" * 64))
        self.r.commit()
        self.bad()

    def test_added_line_instead_of_replaced_fails(self):
        self.r.branch("bump")
        self.r.write(VF, self.r.read(VF) + "BOOKSTACK_IMAGE=%s\n" % NEW)
        self.r.write(UF, self.r.read(UF).replace(OLD, NEW))
        self.r.commit()
        self.bad()

    def test_wrong_key_changed_in_versions_env_fails(self):
        self.r.branch("bump")
        self.r.write(VF, self.r.read(VF).replace("BOOKSTACK_DB_IMAGE=lscr.io/linuxserver/mariadb:11.8.9-r0-ls239@sha256:" + "c" * 64,
                                                 "BOOKSTACK_DB_IMAGE=" + NEW))
        self.r.write(UF, self.r.read(UF).replace(OLD, NEW))
        self.r.commit()
        self.bad()

    def test_mode_change_fails(self):
        self.r.branch("bump")
        self.r.bump()
        os.chmod(os.path.join(self.r.dir, VF), 0o755)
        self.r.commit()
        self.bad()

    def test_rename_fails(self):
        self.r.branch("bump")
        self.r.bump()
        git(self.r.dir, "mv", VF, "stacks/bookstack/versions2.env")
        self.r.commit()
        self.bad()

    def test_deleted_file_fails(self):
        self.r.branch("bump")
        os.remove(os.path.join(self.r.dir, VF))
        self.r.write(UF, self.r.read(UF).replace(OLD, NEW))
        self.r.commit()
        self.bad()

    def test_symlink_fails(self):
        self.r.branch("bump")
        self.r.bump()
        os.remove(os.path.join(self.r.dir, VF))
        os.symlink("/etc/hostname", os.path.join(self.r.dir, VF))
        self.r.commit()
        self.bad()

    def test_working_tree_changes_do_not_matter(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.commit()
        self.r.write(VF, "garbage\n")  # uncommitted: the script must read git objects, not the tree
        self.ok()

    def test_head_copy_of_script_is_refused(self):
        self.r.branch("bump")
        self.r.bump()
        # the PR edits the checker (here: drops the file-count rule) and a CI that ran the head copy
        # would trust it; the guard compares the running script with the base branch's version
        tweaked = self.r.read("tests/upgrade_diff_check.sh").replace("[ \"$got\" = \"$want\" ] ||", "true ||")
        self.assertNotEqual(tweaked, self.r.read("tests/upgrade_diff_check.sh"))
        self.r.write("tests/upgrade_diff_check.sh", tweaked)
        self.r.write("README.md", "also changed\n")
        self.r.commit()
        p = self.r.check("bump", script=os.path.join(self.r.dir, "tests/upgrade_diff_check.sh"))
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_head_changing_script_fails_even_with_base_copy(self):
        self.r.branch("bump")
        self.r.bump()
        self.r.write("tests/upgrade_diff_check.sh", "#!/bin/sh\nexit 0\n")
        self.r.commit()
        self.bad()

    def test_usage_error(self):
        p = subprocess.run(["sh", SCRIPT], cwd=self.r.dir, capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_unknown_ref(self):
        self.r.branch("bump")
        p = subprocess.run(["sh", SCRIPT, "main", "nonexistent"], cwd=self.r.dir, capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
