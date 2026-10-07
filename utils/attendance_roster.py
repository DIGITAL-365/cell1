"""Attendance roster: who belonged to this leader by the meeting week's Thursday."""

from datetime import date, datetime, timedelta, timezone


def roster_join_date(member):
    """When this person was assigned to the current leader.

    leader_assigned_at if it is set, otherwise created_at. created_at is the
    first time the row was created and does not change on transfer.
    """
    if not member:
        return None
    return member.get('leader_assigned_at') or member.get('created_at') or None


def thursday_of_meeting_week(meeting_date):
    """Thursday (YYYY-MM-DD) of the ISO week that contains the meeting date.

    Meetings are Tuesday. Wednesday and Thursday additions still belong on
    that week. Compare this string to the first 10 characters of the join date.
    """
    if meeting_date is None:
        return None
    if isinstance(meeting_date, datetime):
        d = meeting_date.date()
    elif isinstance(meeting_date, date):
        d = meeting_date
    else:
        raw = str(meeting_date).strip()
        if len(raw) < 10:
            return None
        try:
            d = datetime.strptime(raw[:10], '%Y-%m-%d').date()
        except ValueError:
            return None
    monday = d - timedelta(days=d.weekday())
    thursday = monday + timedelta(days=3)
    return thursday.isoformat()


def on_roster_for_meeting(member, meeting_date):
    """True if this member should be listed for meeting_date.

    Include when the join date is missing, or its calendar date (first 10
    characters) is on or before Thursday of that meeting's week.
    """
    join = roster_join_date(member)
    if not join:
        return True
    cutoff = thursday_of_meeting_week(meeting_date)
    if not cutoff:
        return True
    return str(join)[:10] <= cutoff


def utc_now_iso():
    """UTC timestamp written when a member is assigned to a leader."""
    return datetime.now(timezone.utc).isoformat()
