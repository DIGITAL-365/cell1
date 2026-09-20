"""Unit tests for canonical districts, age-from-DOB, and users write payload."""

import unittest
from datetime import date

from utils.sri_lanka_districts import (
    DISTRICT_LIST,
    DISTRICT_TO_PROVINCE,
    age_from_dob,
    format_dob_for_input,
    leader_profile_write_payload,
    missing_leader_profile_fields,
    normalize_district,
    parse_date_of_birth,
    province_for_district,
)


class DistrictCatalogTests(unittest.TestCase):
    def test_twenty_five_canonical_districts(self):
        self.assertEqual(len(DISTRICT_TO_PROVINCE), 25)
        self.assertEqual(len(DISTRICT_LIST), 25)
        self.assertEqual(DISTRICT_LIST[0]['district'], 'Colombo')
        self.assertEqual(DISTRICT_LIST[0]['province'], 'Western')

    def test_normalize_and_province(self):
        self.assertEqual(normalize_district('  kandy '), 'Kandy')
        self.assertEqual(province_for_district('Kandy'), 'Central')
        self.assertIsNone(normalize_district('Western'))
        self.assertIsNone(normalize_district(''))


class AgeFromDobTests(unittest.TestCase):
    def test_birthday_already_passed(self):
        self.assertEqual(
            age_from_dob(date(2000, 1, 1), today=date(2026, 9, 20)),
            26,
        )

    def test_birthday_not_yet_this_year(self):
        self.assertEqual(
            age_from_dob(date(2000, 12, 1), today=date(2026, 9, 20)),
            25,
        )

    def test_birthday_today(self):
        self.assertEqual(
            age_from_dob(date(2000, 9, 20), today=date(2026, 9, 20)),
            26,
        )

    def test_empty_dob(self):
        self.assertIsNone(age_from_dob(None, today=date(2026, 9, 20)))


class WritePayloadTests(unittest.TestCase):
    def test_omits_blanks_and_never_writes_age(self):
        payload = leader_profile_write_payload(
            address='  ',
            district='',
            date_of_birth='',
        )
        self.assertEqual(payload, {})

    def test_derives_province_and_rejects_invalid_district(self):
        payload = leader_profile_write_payload(district='Colombo', address='12 Main St')
        self.assertEqual(payload['district'], 'Colombo')
        self.assertEqual(payload['province'], 'Western')
        self.assertEqual(payload['address'], '12 Main St')
        self.assertNotIn('age', payload)
        with self.assertRaises(ValueError):
            leader_profile_write_payload(district='NotADistrict')

    def test_rejects_future_dob(self):
        with self.assertRaises(ValueError):
            parse_date_of_birth('2099-01-01', today=date(2026, 9, 20))

    def test_missing_fields(self):
        self.assertEqual(
            missing_leader_profile_fields({}),
            ['address', 'district', 'date of birth'],
        )
        self.assertEqual(
            missing_leader_profile_fields({
                'address': 'A',
                'district': 'Galle',
                'date_of_birth': '1990-05-01',
            }),
            [],
        )
        self.assertEqual(format_dob_for_input('1990-05-01T00:00:00Z'), '1990-05-01')


if __name__ == '__main__':
    unittest.main()
