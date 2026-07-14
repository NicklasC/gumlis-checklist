import json
import os
import shutil
import tempfile
import unittest

from src.repositories.json_repo import JsonChecklistRepository


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="gumli-tests-")
        self.db_path = os.path.join(self.temp_dir, "checklists.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def repository(self):
        return JsonChecklistRepository(db_path=self.db_path)

    def write_data(self, data):
        with open(self.db_path, "w", encoding="utf-8") as handle:
            handle.write(data.model_dump_json(indent=2))

    def write_json(self, value):
        with open(self.db_path, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
