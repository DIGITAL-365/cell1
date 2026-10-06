"""Roster cutoff is when the member joined this leader, not created_at alone."""

import unittest
from datetime import date

from utils.attendance_roster import (
    on_roster_for_meeting,
    roster_join_date,
    thursday_of_meeting_week,
)


MEETING = date(2026, 10, 6)  # Tuesday
THURSDAY = '2026-10-08'


class ThursdayOfMeetingWeekTests(unittest.TestCase):
    def test_tuesday_meeting_is_that_weeks_thursday(self):
        self.assertEqual(thursday_of_meeting_week(MEETING), THURSDAY)
        self.assertEqual(thursday_of_meeting_week('2026-10-06'), THURSDAY)
        self.assertEqual(thursday_of_meeting_week('2026-10-06T00:00:00+00:00'), THURSDAY)

    def test_wednesday_and_thursday_stay_on_the_same_week(self):
        self.assertEqual(thursday_of_meeting_week(date(2026, 10, 7)), THURSDAY)
        self.assertEqual(thursday_of_meeting_week(date(2026, 10, 8)), THURSDAY)

    def test_friday_through_monday_use_their_own_week(self):
        self.assertEqual(thursday_of_meeting_week(date(2026, 10, 9)), THURSDAY)
        self.assertEqual(thursday_of_meeting_week(date(2026, 10, 11)), THURSDAY)
        self.assertEqual(thursday_of_meeting_week(date(2026, 10, 12)), '2026-10-15')

    def test_invalid_date_returns_none(self):
        self.assertIsNone(thursday_of_meeting_week(None))
        self.assertIsNone(thursday_of_meeting_week('not-a-date'))


class RosterJoinDateTests(unittest.TestCase):
    def test_prefers_leader_assigned_at(self):
        member = {
            'leader_assigned_at': '2026-10-06T12:00:00+00:00',
            'created_at': '2024-01-01T00:00:00+00:00',
        }
        self.assertEqual(roster_join_date(member), '2026-10-06T12:00:00+00:00')

    def test_falls_back_to_created_at(self):
        self.assertEqual(
            roster_join_date({'leader_assigned_at': None, 'created_at': '2024-01-01'}),
            '2024-01-01',
        )
        self.assertEqual(
            roster_join_date({'leader_assigned_at': '', 'created_at': '2024-01-01'}),
            '2024-01-01',
        )

    def test_missing_member_or_dates(self):
        self.assertIsNone(roster_join_date(None))
        self.assertIsNone(roster_join_date({}))


class OnRosterForMeetingTests(unittest.TestCase):
    def test_missing_join_date_is_included(self):
        self.assertTrue(on_roster_for_meeting({}, MEETING))
        self.assertTrue(on_roster_for_meeting(None, MEETING))

    def test_wednesday_and_thursday_additions_belong_this_week(self):
        self.assertTrue(on_roster_for_meeting({'leader_assigned_at': '2026-10-07'}, MEETING))
        self.assertTrue(on_roster_for_meeting(
            {'leader_assigned_at': '2026-10-08T23:30:00+00:00'},
            MEETING,
        ))

    def test_friday_waits_until_next_tuesday(self):
        self.assertFalse(on_roster_for_meeting({'leader_assigned_at': '2026-10-09'}, MEETING))

    def test_transfer_with_old_created_at_is_not_on_earlier_meetings(self):
        transferred_today = {
            'created_at': '2024-03-01T08:00:00+00:00',
            'leader_assigned_at': '2026-10-06T11:00:00+00:00',
        }
        earlier = date(2026, 9, 29)
        self.assertFalse(on_roster_for_meeting(transferred_today, earlier))
        self.assertTrue(on_roster_for_meeting(transferred_today, MEETING))

    def test_backfill_matches_created_at(self):
        member = {
            'created_at': '2026-09-20T04:00:00+00:00',
            'leader_assigned_at': '2026-09-20T04:00:00+00:00',
        }
        self.assertTrue(on_roster_for_meeting(member, MEETING))
        self.assertFalse(on_roster_for_meeting(member, date(2026, 9, 15)))

    def test_invalid_meeting_date_does_not_drop_the_member(self):
        self.assertTrue(on_roster_for_meeting(
            {'leader_assigned_at': '2026-10-06'},
            'not-a-date',
        ))
