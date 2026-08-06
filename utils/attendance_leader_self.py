"""Identify the leader's own cell_members row and validate attendance saves.

A meeting may be saved when everyone is Absent, or when at least one
non-leader-self member is Present. Saving with only the leader-self Present
is blocked (the cell was not really operated).
"""

LEADER_ONLY_PRESENT_MESSAGE = (
    'At least one cell member (not only yourself) must be Present for this '
    'meeting to count, or mark everyone Absent.'
)


def phone_digits(value):
    """Return digits-only phone string, or empty string."""
    if value is None:
        return ''
    return ''.join(c for c in str(value) if c.isdigit())


def phones_match(a, b):
    """True if phones match exactly (digits) or by last 9 digits (country code)."""
    da, db = phone_digits(a), phone_digits(b)
    if not da or not db:
        return False
    if da == db:
        return True
    return len(da) >= 9 and len(db) >= 9 and da[-9:] == db[-9:]


def is_leader_self_member(member, leader_phone, leader_name):
    """
    Treat a roster member as the leader themselves when:
    1) is_leader is True, OR
    2) phone matches the cell leader (digits-only; last-9 country-code tolerant), OR
    3) phones missing/no match and name matches (case-insensitive, trimmed).
    """
    if not isinstance(member, dict):
        return False
    if member.get('is_leader') is True:
        return True

    m_phone = member.get('phone_number')
    if phones_match(m_phone, leader_phone):
        return True

    # Name fallback only when phones cannot confirm a match
    if phone_digits(m_phone) and phone_digits(leader_phone):
        return False

    m_name = (member.get('name') or '').strip().lower()
    l_name = (leader_name or '').strip().lower()
    return bool(m_name and l_name and m_name == l_name)


def attendance_save_allowed(rows, leader_phone, leader_name):
    """
    rows: iterable of dicts with at least 'status' ('present'|'absent') and
    member identity fields (is_leader / phone_number / name).

    ALLOW if count(Present among NON-leader-self) >= 1
    ALLOW if count(Present) == 0 (everyone Absent)
    BLOCK if the only Present row(s) are leader-self
    """
    present = [r for r in rows if (r or {}).get('status') == 'present']
    if not present:
        return True
    for row in present:
        if not is_leader_self_member(row, leader_phone, leader_name):
            return True
    return False
