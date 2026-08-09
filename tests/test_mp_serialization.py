import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("probe_materials_project", ROOT / "scripts" / "probe_materials_project.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeMPID(str):
    def __new__(cls, internal, public):
        value = super().__new__(cls, internal)
        value.public = public
        return value

    def __str__(self):
        return self.public


class FakeOrigin:
    def __init__(self):
        self.task_id = FakeMPID("aaainternal", "mp-200")

    def model_dump(self, mode="json"):
        return {"name": "structure", "task_id": "aaainternal"}


class FakeDocument:
    def __init__(self):
        self.material_id = FakeMPID("aaa-material", "mp-100")
        self.origins = [FakeOrigin()]

    def model_dump(self, mode="json"):
        return {"material_id": "aaa-material", "origins": [{"task_id": "aaainternal"}]}


class MPSerializationTests(unittest.TestCase):
    def test_public_identity_overrides_internal_string_value(self):
        row = MODULE.serialize_summary_document(FakeDocument())
        self.assertEqual(row["material_id"], "mp-100")
        self.assertEqual(row["origins"][0]["task_id"], "mp-200")


if __name__ == "__main__":
    unittest.main()

