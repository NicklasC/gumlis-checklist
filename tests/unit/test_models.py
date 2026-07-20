import unittest

from pydantic import ValidationError

from src.models.checklist import Checklist, ChecklistItem, ChecklistsData, CommonGroup


class ChecklistItemModelTests(unittest.TestCase):
    def test_defaults_to_unchecked(self):
        self.assertFalse(ChecklistItem(id="1", title="Test").is_checked)

    def test_default_category_is_other(self):
        self.assertEqual(ChecklistItem(id="1", title="Test").category, "Övrigt")

    def test_created_at_is_generated(self):
        self.assertTrue(ChecklistItem(id="1", title="Test").created_at.endswith("Z"))

    def test_completed_at_defaults_to_none(self):
        self.assertIsNone(ChecklistItem(id="1", title="Test").completed_at)

    def test_id_is_required(self):
        with self.assertRaises(ValidationError):
            ChecklistItem(title="Test")

    def test_title_is_required(self):
        with self.assertRaises(ValidationError):
            ChecklistItem(id="1")

    def test_swedish_text_round_trips_through_json(self):
        value = ChecklistItem(id="1", title="Mjölk & räkor", category="Att göra")
        restored = ChecklistItem.model_validate_json(value.model_dump_json())
        self.assertEqual(restored.title, value.title)


class ChecklistModelTests(unittest.TestCase):
    def test_items_are_not_shared_between_instances(self):
        first = Checklist(id="a", title="A")
        second = Checklist(id="b", title="B")
        first.items.append(ChecklistItem(id="1", title="Test"))
        self.assertEqual(second.items, [])

    def test_default_category_order_is_created(self):
        self.assertIn("Att göra", Checklist(id="a", title="A").category_order)

    def test_template_defaults_to_false(self):
        self.assertFalse(Checklist(id="a", title="A").is_template)

    def test_last_cleaned_date_defaults_to_none(self):
        self.assertIsNone(Checklist(id="a", title="A").last_cleaned_date)


class AggregateModelTests(unittest.TestCase):
    def test_common_group_items_are_not_shared(self):
        first = CommonGroup(id="a", name="A")
        second = CommonGroup(id="b", name="B")
        first.items.append("Test")
        self.assertEqual(second.items, [])

    def test_checklists_data_defaults_to_empty_lists(self):
        value = ChecklistsData()
        self.assertEqual(value.checklists, [])
        self.assertEqual(value.common_groups, [])
