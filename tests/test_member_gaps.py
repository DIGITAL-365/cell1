"""Leaders are notified only for member fields they still need to fill."""

import unittest

from utils.member_gaps import (
    apply_missing_member_fields,
    format_missing_list,
    missing_member_fields,
)


def _complete(**overrides):
    row = {
        'name': 'Ann Perera',
        'phone_number': '0771234567',
        'cell_category': 'youth',
        'zone_id': 4,
    }
    row.update(overrides)
    return row


class MissingMemberFieldsTests(unittest.TestCase):
    def test_complete_member_has_nothing_missing(self):
        self.assertEqual(missing_member_fields(_complete(), zone_required=True), [])

    def test_blank_name_phone_and_category(self):
        self.assertEqual(
            missing_member_fields({'name': '  ', 'phone_number': None, 'cell_category': ''}),
            ['name', 'phone', 'cell category'],
        )

    def test_unknown_category_counts_as_empty(self):
        self.assertEqual(
            missing_member_fields(_complete(cell_category='kids')),
            ['cell category'],
        )

    def test_zone_only_when_the_branch_requires_it(self):
        member = _complete(zone_id=None)
        self.assertEqual(missing_member_fields(member, zone_required=False), [])
        self.assertEqual(missing_member_fields(member, zone_required=True), ['zone'])

    def test_optional_blanks_do_not_notify(self):
        member = _complete(age=None, gender=None, district='', province=None, church=False)
        self.assertEqual(missing_member_fields(member), [])


class ApplyMissingMemberFieldsTests(unittest.TestCase):
    def test_counts_and_labels_only_incomplete_rows(self):
        rows = [
            _complete(),
            _complete(name='Kamal', phone_number='', cell_category='adult', zone_id=None),
        ]
        count = apply_missing_member_fields(rows, zone_required=True)
        self.assertEqual(count, 1)
        self.assertEqual(rows[0]['missing_fields'], [])
        self.assertEqual(rows[1]['missing_label'], 'phone and zone')

    def test_format_three_labels(self):
        self.assertEqual(
            format_missing_list(['name', 'phone', 'cell category']),
            'name, phone, and cell category',
        )
