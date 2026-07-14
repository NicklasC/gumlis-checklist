import subprocess
import unittest
from pathlib import Path

from tests.support.paths import DEPLOY_REPOSITORY, PROJECT_ROOT


class DeployScriptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (PROJECT_ROOT / "deploy.py").read_text(encoding="utf-8")

    def test_builds_src_main(self):
        self.assertIn("publish src/main.py", self.script)

    def test_uses_expected_base_url(self):
        self.assertIn("--base-url /gumlis-checklist/", self.script)

    def test_includes_assets(self):
        self.assertIn("--assets assets", self.script)

    def test_targets_github_pages_repository(self):
        self.assertIn('"nicklasc.github.io", "gumlis-checklist"', self.script)

    def test_restores_manifest_after_build(self):
        self.assertIn('"manifest.json"', self.script)

    def test_restores_service_worker_after_build(self):
        self.assertIn('"flutter_service_worker.js"', self.script)

    def test_restores_index_after_build(self):
        self.assertIn('"index.html"', self.script)

    def test_checks_deploy_repository_status(self):
        self.assertIn('run_command("git status"', self.script)


@unittest.skipUnless((DEPLOY_REPOSITORY / ".git").is_dir(), "Deploy repository is not available")
class TwoRepositoryTests(unittest.TestCase):
    def remote_url(self, repository: Path):
        completed = subprocess.run(
            ["git", "-C", str(repository), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def test_source_repository_has_git_metadata(self):
        self.assertTrue((PROJECT_ROOT / ".git").is_dir())

    def test_deploy_repository_has_git_metadata(self):
        self.assertTrue((DEPLOY_REPOSITORY / ".git").is_dir())

    def test_source_and_deploy_are_distinct_repositories(self):
        self.assertNotEqual((PROJECT_ROOT / ".git").resolve(), (DEPLOY_REPOSITORY / ".git").resolve())

    def test_deploy_origin_is_github_pages_repository(self):
        self.assertIn("nicklasc.github.io", self.remote_url(DEPLOY_REPOSITORY))
