"""Which member fields a leader still needs to fill in."""

ALLOWED_MEMBER_CELL_CATEGORIES = frozenset({'youth', 'young adult', 'adult'})


def missing_member_fields(member, zone_required=False):
    """Labels for empty fields the leader should fill.

    Name, phone, and cell category are always checked. Zone is checked only
    when the leader's branch requires it (Miracle Dome). Age, gender, district,
    and church are not included: a blank there is allowed.
    """
    member = member or {}
    missing = []
    if not str(member.get('name') or '').strip():
        missing.append('name')
    if not str(member.get('phone_number') or '').strip():
        missing.append('phone')
    category = str(member.get('cell_category') or '').strip()
    if category not in ALLOWED_MEMBER_CELL_CATEGORIES:
        missing.append('cell category')
    if zone_required and not member.get('zone_id'):
        missing.append('zone')
    return missing


def format_missing_list(missing):
    """'phone', 'phone and zone', or 'phone, cell category, and zone'."""
    labels = [str(item) for item in (missing or []) if item]
    if not labels:
        return ''
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f'{labels[0]} and {labels[1]}'
    return ', '.join(labels[:-1]) + f', and {labels[-1]}'


def apply_missing_member_fields(members, zone_required=False):
    """Set missing_fields and missing_label on each row. Return how many are incomplete."""
    count = 0
    for member in members or []:
        if not isinstance(member, dict):
            continue
        missing = missing_member_fields(member, zone_required=zone_required)
        member['missing_fields'] = missing
        member['missing_label'] = format_missing_list(missing)
        if missing:
            count += 1
    return count
