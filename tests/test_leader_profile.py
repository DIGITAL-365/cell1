"""Leader profile gate: locked fields stay out of the save, marital status starts the list."""

import unittest
from datetime import date

from utils.leader_profile import (
    MARITAL_STATUS_OPTIONS,
    canonical_marital_status,
    collect_leader_profile_update,
    profile_field_gaps,
    profile_missing_labels,
)


def _posted(**overrides):
    data = {
        'address': '12 Main Street',
        'district': 'Colombo',
        'date_of_birth': '1990-05-01',
        'marital_status': 'Rather Not Say',
        'country': '',
        'email': '',
    }
    data.update(overrides)
    return data


class MaritalStatusTests(unittest.TestCase):
    def test_rather_not_say_is_first(self):
        self.assertEqual(MARITAL_STATUS_OPTIONS[0], 'Rather Not Say')

    def test_canonical_ignores_case(self):
        self.assertEqual(canonical_marital_status('married'), 'Married')
        self.assertEqual(canonical_marital_status(''), '')


class MissingProfileTests(unittest.TestCase):
    def test_city_church_complete_row_has_nothing_missing(self):
        self.assertEqual(
            profile_missing_labels({
                'address': '12 Main Street',
                'district': 'Colombo',
                'province': 'Western',
                'date_of_birth': '1990-05-01',
                'marital_status': 'Single',
                'branch_name': 'City Church',
                'country': '',
                'email': '',
            }),
            [],
        )

    def test_miracle_dome_requires_zone_and_sector(self):
        row = {
            'address': '12 Main Street',
            'district': 'Colombo',
            'province': 'Western',
            'date_of_birth': '1990-05-01',
            'marital_status': 'Married',
            'branch_name': 'Miracle Dome',
            'zone_id': None,
            'sector_number': None,
        }
        self.assertEqual(profile_missing_labels(row), ['Zone', 'Sector'])
        row['zone_id'] = 2
        row['sector_number'] = 0
        self.assertEqual(profile_missing_labels(row), [])


class CollectProfileTests(unittest.TestCase):
    def test_save_skips_locked_fields_and_defaults_country(self):
        errors, payload = collect_leader_profile_update(
            _posted(name='Daphnie Thenabadu', phone_number='771256516', cell_category='adult'),
            branch_name='Mount-English',
            today=date(2026, 10, 30),
        )
        self.assertEqual(errors, {})
        self.assertEqual(payload['country'], 'Sri Lanka')
        self.assertEqual(payload['marital_status'], 'Rather Not Say')
        self.assertEqual(payload['province'], 'Western')
        self.assertIsNone(payload['email'])
        for locked in ('name', 'phone_number', 'role_id', 'cell_category', 'branch_id', 'age', 'zone_id', 'sector_number'):
            self.assertNotIn(locked, payload)

    def test_miracle_dome_writes_zone_and_sector(self):
        errors, payload = collect_leader_profile_update(
            _posted(zone_id='3'),
            branch_name='Miracle Dome',
            zones=[{'id': 3, 'sector_number': 1}],
            today=date(2026, 10, 30),
        )
        self.assertEqual(errors, {})
        self.assertEqual(payload['zone_id'], 3)
        self.assertEqual(payload['sector_number'], 1)

    def test_invalid_email_and_empty_marital_are_errors(self):
        errors, payload = collect_leader_profile_update(
            _posted(email='not-an-email', marital_status=''),
            branch_name='City Church',
            today=date(2026, 10, 30),
        )
        self.assertIn('email', errors)
        self.assertIn('marital_status', errors)
        self.assertEqual(payload, {})

    def test_empty_required_fields_are_marked(self):
        gaps = profile_field_gaps(address='', district='', province='', date_of_birth='', marital_status='')
        self.assertIn('address', gaps)
        self.assertIn('marital_status', gaps)
        self.assertNotIn('email', gaps)


if __name__ == '__main__':
    unittest.main()
