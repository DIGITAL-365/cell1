"""Identify the leader's own cell_members row and validate attendance saves.

Operated = at least one non-leader-self member is Present.

Soft default: only-leader Present may be saved (with a UI warning); it does not
count as operated. Optional hard block via ATTENDANCE_HARD_BLOCK_LEADER_ONLY=1.
"""

import os

LEADER_ONLY_PRESENT_WARNING = (
    'Only you are Present. This will not count as cell operated.'
)

# Kept for optional hard-block mode (feature flag).
LEADER_ONLY_PRESENT_MESSAGE = (
    'At least one cell member (not yourself) must be Present for this '
    'meeting to count as operated, or mark everyone Absent.'
)


def hard_block_only_leader_present_enabled():
    """When true, reject submits where the only Present row(s) are leader-self."""
    return os.getenv('ATTENDANCE_HARD_BLOCK_LEADER_ONLY', '').strip().lower() in (
        '1',
        'true',
        'yes',
        'on',
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


def only_leader_present(rows, leader_phone, leader_name):
    """True when there is at least one Present and every Present is leader-self."""
    present = [r for r in rows if (r or {}).get('status') == 'present']
    if not present:
        return False
    return all(is_leader_self_member(row, leader_phone, leader_name) for row in present)


def cell_is_operated(rows, leader_phone=None, leader_name=None):
    """
    Operated when at least one non-leader-self row is Present.
    If leader_phone/name are omitted, uses is_leader flag only on each row.
    """
    for row in rows or []:
        if (row or {}).get('status') != 'present':
            continue
        if leader_phone is not None or leader_name is not None:
            if not is_leader_self_member(row, leader_phone, leader_name):
                return True
        elif row.get('is_leader') is not True:
            return True
    return False


def attendance_save_allowed(rows, leader_phone, leader_name):
    """
    Soft default: always allow (caller shows warning for only-leader Present).
    Hard mode (flag): BLOCK if the only Present row(s) are leader-self;
    ALLOW if everyone Absent or ≥1 real member Present.
    """
    if not hard_block_only_leader_present_enabled():
        return True
    if not only_leader_present(rows, leader_phone, leader_name):
        return True
    return False


def present_count_for_operated_totals(rows, leader_phone=None, leader_name=None):
    """
    Present count for operated/summary totals:
    - If cell is operated: count all Present (including leader personal attendance).
    - If only leader Present (not operated): count 0 so leader-only does not inflate totals.
    """
    present = [r for r in rows if (r or {}).get('status') == 'present']
    if not present:
        return 0
    if cell_is_operated(rows, leader_phone, leader_name):
        return len(present)
    return 0
