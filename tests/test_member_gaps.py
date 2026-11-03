"""A member stays on the gate until every required field is filled."""

import unittest

from utils.member_gaps import (
    apply_missing_member_fields,
    canonical_gender,
    form_field_gaps,
    format_missing_list,
    incomplete_members_sorted,
    join_member_name,
    missing_member_fields,
    last_name_valid,
    name_part_valid,
    phone_number_valid,
    selected_member_country,
    split_member_name,
)


def _complete(**overrides):
    row = {
        'name': 'Philip Perera',
        'phone_number': '0771234567',
        'gender': 'Male',
        'branch_id': 2,
        'branch_name': 'City Church',
        'cell_category': 'youth',
        'country': '',
        'district': 'Colombo',
        'province': 'Western',
        'zone_id': None,
        'sector_number': None,
    }
    row.update(overrides)
    return row


class NamePartTests(unittest.TestCase):
    def test_join_lowercases_with_one_space(self):
        self.assertEqual(join_member_name('philip', 'Perera'), 'philip perera')
        self.assertEqual(join_member_name('philip', 'De Silva'), 'philip de silva')

    def test_surname_allows_de_silva_and_rejects_a_short_word(self):
        self.assertTrue(last_name_valid('De Silva'))
        self.assertTrue(last_name_valid('De Jonk'))
        self.assertTrue(last_name_valid('Silva'))
        self.assertFalse(last_name_valid('De'))
        self.assertFalse(last_name_valid('A Silva'))
        self.assertFalse(last_name_valid('De  Silva1'))

    def test_split_on_first_space_keeps_the_rest(self):
        self.assertEqual(split_member_name('Philip John Perera'), ('Philip', 'John Perera'))

    def test_name_part_rejects_short_digits_and_spaces(self):
        self.assertFalse(name_part_valid('Ann'))
        self.assertFalse(name_part_valid('phil1p'))
        self.assertFalse(name_part_valid('john paul'))
        self.assertTrue(name_part_valid('Philip'))

    def test_lowercase_gender_is_canonical(self):
        self.assertEqual(canonical_gender('female'), 'Female')
        self.assertEqual(canonical_gender('MALE'), 'Male')
        self.assertEqual(canonical_gender(''), '')

    def test_nine_digit_phone_is_valid_and_a_short_one_is_not(self):
        self.assertTrue(phone_number_valid('771256516'))
        self.assertTrue(phone_number_valid('0771234567'))
        self.assertFalse(phone_number_valid('12345'))
        self.assertFalse(phone_number_valid(''))

    def test_empty_country_displays_as_sri_lanka(self):
        self.assertEqual(selected_member_country(''), 'Sri Lanka')
        self.assertEqual(selected_member_country(None), 'Sri Lanka')
        self.assertEqual(selected_member_country('India'), 'India')


class MissingMemberFieldsTests(unittest.TestCase):
    def test_complete_city_church_member_has_nothing_missing(self):
        self.assertEqual(missing_member_fields(_complete()), [])

    def test_empty_country_is_not_a_gap(self):
        self.assertEqual(missing_member_fields(_complete(country=None)), [])

    def test_blank_name_lists_both_parts(self):
        self.assertEqual(
            missing_member_fields(_complete(name='')),
            ['First name', 'Last name'],
        )

    def test_short_first_name_is_a_gap_and_a_compound_surname_is_not(self):
        self.assertEqual(
            missing_member_fields(_complete(name='Ann Paul Perera')),
            ['First name'],
        )
        self.assertEqual(
            missing_member_fields(_complete(name='Philip De')),
            ['Last name'],
        )

    def test_single_word_name_is_missing_last_name(self):
        self.assertEqual(
            missing_member_fields(_complete(name='Philip')),
            ['Last name'],
        )

    def test_gender_phone_branch_category_district(self):
        self.assertEqual(
            missing_member_fields(_complete(
                gender='',
                phone_number='  ',
                branch_id=None,
                cell_category='',
                district='not a district',
                province='',
            )),
            ['Gender', 'Phone', 'Branch', 'Cell category', 'District', 'Province'],
        )

    def test_unknown_category_counts_as_empty(self):
        self.assertEqual(
            missing_member_fields(_complete(cell_category='kids')),
            ['Cell category'],
        )

    def test_city_church_empty_zone_is_complete(self):
        self.assertEqual(
            missing_member_fields(_complete(branch_name='City Church', zone_id=None)),
            [],
        )

    def test_miracle_dome_requires_zone_and_sector(self):
        member = _complete(branch_name='Miracle Dome', zone_id=None, sector_number=None)
        self.assertEqual(missing_member_fields(member), ['Zone', 'Sector'])
        member['zone_id'] = 4
        self.assertEqual(missing_member_fields(member), ['Sector'])
        member['sector_number'] = 2
        self.assertEqual(missing_member_fields(member), [])

    def test_miracle_dome_match_ignores_case(self):
        member = _complete(branch_name='  miracle   dome ', zone_id=None, sector_number='')
        self.assertEqual(missing_member_fields(member), ['Zone', 'Sector'])

    def test_lowercase_gender_and_nine_digit_phone_are_complete(self):
        self.assertEqual(
            missing_member_fields(_complete(gender='female', phone_number='771256516')),
            [],
        )

    def test_short_phone_is_a_gap(self):
        self.assertEqual(
            missing_member_fields(_complete(phone_number='12345')),
            ['Phone'],
        )

    def test_sector_zero_counts_as_filled(self):
        member = _complete(branch_name='Miracle Dome', zone_id=4, sector_number=0)
        self.assertEqual(missing_member_fields(member), [])

    def test_form_marks_only_empty_required_fields(self):
        gaps = form_field_gaps(
            first_name='Bernadine',
            last_name='Silva',
            gender='Female',
            phone_number='771256516',
            district='',
            province='',
            branch_name='Mount-English',
            cell_category='adult',
        )
        self.assertEqual(gaps, ['district', 'province'])
        self.assertNotIn('first_name', gaps)

    def test_optional_blanks_do_not_block(self):
        member = _complete(age=None, church=False, potential_leader=False)
        self.assertEqual(missing_member_fields(member), [])

    def test_province_must_match_the_district(self):
        self.assertEqual(
            missing_member_fields(_complete(district='Colombo', province='')),
            ['Province'],
        )


class ApplyMissingMemberFieldsTests(unittest.TestCase):
    def test_counts_labels_and_sorts_incomplete_rows(self):
        rows = [
            _complete(id='b', name='Kamal Perera'),
            _complete(id='a', name='', phone_number='', gender=None),
            _complete(id='c', name='Ann Silva', branch_name='Miracle Dome', zone_id=None, sector_number=None),
        ]
        count = apply_missing_member_fields(rows)
        self.assertEqual(count, 2)
        self.assertEqual(rows[0]['missing_fields'], [])
        self.assertEqual(rows[1]['missing_label'], 'First name, Last name, Gender, Phone')
        ordered = incomplete_members_sorted(rows)
        self.assertEqual([row['id'] for row in ordered], ['a', 'c'])

    def test_format_three_labels(self):
        self.assertEqual(
            format_missing_list(['Phone', 'Gender', 'District']),
            'Phone, Gender, District',
        )
