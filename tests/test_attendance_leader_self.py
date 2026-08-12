"""Unit tests for leader-self attendance save validation."""

import os
import unittest
from unittest import mock

from utils.attendance_leader_self import (
    LEADER_ONLY_PRESENT_MESSAGE,
    LEADER_ONLY_PRESENT_WARNING,
    attendance_save_allowed,
    cell_is_operated,
    hard_block_only_leader_present_enabled,
    is_leader_self_member,
    only_leader_present,
    phone_digits,
    phones_match,
    present_count_for_operated_totals,
)


class PhoneMatchTests(unittest.TestCase):
    def test_phone_digits_strips_non_digits(self):
        self.assertEqual(phone_digits('+91 98765-43210'), '919876543210')
        self.assertEqual(phone_digits(None), '')
        self.assertEqual(phone_digits(''), '')

    def test_phones_match_exact(self):
        self.assertTrue(phones_match('9876543210', '9876543210'))

    def test_phones_match_country_code_last9(self):
        self.assertTrue(phones_match('919876543210', '9876543210'))
        self.assertTrue(phones_match('+91 98765 43210', '09876543210'))

    def test_phones_no_match(self):
        self.assertFalse(phones_match('9876543210', '9876543211'))
        self.assertFalse(phones_match('', '9876543210'))
        self.assertFalse(phones_match(None, None))


class LeaderSelfIdentityTests(unittest.TestCase):
    def test_is_leader_flag(self):
        self.assertTrue(
            is_leader_self_member(
                {'is_leader': True, 'name': 'Other', 'phone_number': '111'},
                '999',
                'Leader',
            )
        )

    def test_phone_match_identifies_leader(self):
        self.assertTrue(
            is_leader_self_member(
                {'is_leader': False, 'name': 'Alex', 'phone_number': '919876543210'},
                '9876543210',
                'Different Name',
            )
        )

    def test_name_fallback_when_phones_missing(self):
        self.assertTrue(
            is_leader_self_member(
                {'is_leader': False, 'name': '  Jane Doe ', 'phone_number': None},
                None,
                'jane doe',
            )
        )

    def test_name_not_used_when_phones_differ(self):
        self.assertFalse(
            is_leader_self_member(
                {'is_leader': False, 'name': 'Jane Doe', 'phone_number': '1111111111'},
                '2222222222',
                'Jane Doe',
            )
        )

    def test_regular_member_not_leader(self):
        self.assertFalse(
            is_leader_self_member(
                {'is_leader': False, 'name': 'Guest', 'phone_number': '5555555555'},
                '9876543210',
                'Leader Name',
            )
        )


class AttendanceSaveAllowedTests(unittest.TestCase):
    leader_phone = '9876543210'
    leader_name = 'Cell Leader'

    def _rows(self, *specs):
        """specs: (is_leader_self_or_member_dict, status) or dict with status."""
        out = []
        for spec in specs:
            if isinstance(spec, tuple):
                member, status = spec
                if isinstance(member, bool):
                    row = {
                        'is_leader': member,
                        'name': self.leader_name if member else 'Guest Member',
                        'phone_number': self.leader_phone if member else '5555555555',
                        'status': status,
                    }
                else:
                    row = dict(member)
                    row['status'] = status
                out.append(row)
            else:
                out.append(spec)
        return out

    def test_soft_default_allows_only_leader_present(self):
        rows = self._rows((True, 'present'), (False, 'absent'))
        with mock.patch.dict(os.environ, {'ATTENDANCE_HARD_BLOCK_LEADER_ONLY': ''}, clear=False):
            self.assertTrue(
                attendance_save_allowed(rows, self.leader_phone, self.leader_name)
            )

    def test_hard_flag_blocks_only_leader_present(self):
        rows = self._rows((True, 'present'), (False, 'absent'))
        with mock.patch.dict(os.environ, {'ATTENDANCE_HARD_BLOCK_LEADER_ONLY': '1'}, clear=False):
            self.assertTrue(hard_block_only_leader_present_enabled())
            self.assertFalse(
                attendance_save_allowed(rows, self.leader_phone, self.leader_name)
            )

    def test_leader_absent_guest_present_allowed(self):
        rows = self._rows((True, 'absent'), (False, 'present'))
        self.assertTrue(
            attendance_save_allowed(rows, self.leader_phone, self.leader_name)
        )
        self.assertTrue(cell_is_operated(rows, self.leader_phone, self.leader_name))

    def test_leader_and_guest_present_allowed(self):
        rows = self._rows((True, 'present'), (False, 'present'))
        self.assertTrue(
            attendance_save_allowed(rows, self.leader_phone, self.leader_name)
        )
        self.assertTrue(cell_is_operated(rows, self.leader_phone, self.leader_name))

    def test_everyone_absent_allowed(self):
        rows = self._rows((True, 'absent'), (False, 'absent'))
        self.assertTrue(
            attendance_save_allowed(rows, self.leader_phone, self.leader_name)
        )
        self.assertFalse(cell_is_operated(rows, self.leader_phone, self.leader_name))

    def test_only_leader_present_not_operated(self):
        rows = self._rows((True, 'present'), (False, 'absent'))
        self.assertTrue(only_leader_present(rows, self.leader_phone, self.leader_name))
        self.assertFalse(cell_is_operated(rows, self.leader_phone, self.leader_name))
        self.assertEqual(
            present_count_for_operated_totals(rows, self.leader_phone, self.leader_name),
            0,
        )

    def test_operated_present_count_includes_leader_when_members_present(self):
        rows = self._rows((True, 'present'), (False, 'present'))
        self.assertEqual(
            present_count_for_operated_totals(rows, self.leader_phone, self.leader_name),
            2,
        )

    def test_phone_matched_leader_only_present_not_operated(self):
        rows = [
            {
                'is_leader': False,
                'name': 'Weird Name',
                'phone_number': '919876543210',
                'status': 'present',
            },
            {
                'is_leader': False,
                'name': 'Guest',
                'phone_number': '5555555555',
                'status': 'absent',
            },
        ]
        self.assertTrue(only_leader_present(rows, self.leader_phone, self.leader_name))
        self.assertFalse(cell_is_operated(rows, self.leader_phone, self.leader_name))

    def test_message_constants(self):
        self.assertIn('not count as cell operated', LEADER_ONLY_PRESENT_WARNING)
        self.assertIn('count as operated', LEADER_ONLY_PRESENT_MESSAGE)


if __name__ == '__main__':
    unittest.main()
