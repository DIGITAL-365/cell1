"""Canonical Sri Lanka districts for cell leader profile. Spellings must match the portal."""
from datetime import date, datetime

DISTRICT_TO_PROVINCE = {
    'Colombo': 'Western',
    'Gampaha': 'Western',
    'Kalutara': 'Western',
    'Kandy': 'Central',
    'Matale': 'Central',
    'Nuwara Eliya': 'Central',
    'Galle': 'Southern',
    'Matara': 'Southern',
    'Hambantota': 'Southern',
    'Jaffna': 'Northern',
    'Kilinochchi': 'Northern',
    'Mannar': 'Northern',
    'Vavuniya': 'Northern',
    'Mullaitivu': 'Northern',
    'Batticaloa': 'Eastern',
    'Ampara': 'Eastern',
    'Trincomalee': 'Eastern',
    'Kurunegala': 'North Western',
    'Puttalam': 'North Western',
    'Anuradhapura': 'North Central',
    'Polonnaruwa': 'North Central',
    'Badulla': 'Uva',
    'Monaragala': 'Uva',
    'Ratnapura': 'Sabaragamuwa',
    'Kegalle': 'Sabaragamuwa',
}

DISTRICT_LIST = [
    {'district': district, 'province': province}
    for district, province in DISTRICT_TO_PROVINCE.items()
]


def normalize_district(raw):
    """Return the canonical district name, or None if it is missing/invalid."""
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    if value in DISTRICT_TO_PROVINCE:
        return value
    lowered = value.lower()
    for name in DISTRICT_TO_PROVINCE:
        if name.lower() == lowered:
            return name
    return None


def province_for_district(district):
    canonical = normalize_district(district)
    if not canonical:
        return None
    return DISTRICT_TO_PROVINCE[canonical]


def parse_date_of_birth(raw, today=None):
    """Parse YYYY-MM-DD (or date/datetime). Reject future dates. Return date or None if empty."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        raw = raw.date()
    if isinstance(raw, date):
        parsed = raw
    else:
        value = str(raw).strip()
        if not value:
            return None
        value = value.split('T', 1)[0]
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError('Enter a valid date of birth.') from None
    if today is None:
        today = date.today()
    if parsed > today:
        raise ValueError('Date of birth cannot be in the future.')
    if parsed.year < 1900:
        raise ValueError('Enter a valid date of birth.')
    return parsed


def age_from_dob(dob, today=None):
    """Age in full years. Birthday not yet this year → age − 1."""
    if dob is None:
        return None
    parsed = dob if isinstance(dob, date) else parse_date_of_birth(dob, today=today)
    if parsed is None:
        return None
    if today is None:
        today = date.today()
    age = today.year - parsed.year
    if (today.month, today.day) < (parsed.month, parsed.day):
        age -= 1
    return age


def format_dob_for_input(raw):
    """YYYY-MM-DD for <input type=date>, or empty string."""
    if raw is None:
        return ''
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    value = str(raw).strip()
    if not value:
        return ''
    return value.split('T', 1)[0]


def missing_leader_profile_fields(row):
    """Which of address, district, date of birth are still empty on a users row."""
    row = row or {}
    missing = []
    if not str(row.get('address') or '').strip():
        missing.append('address')
    if not normalize_district(row.get('district')):
        missing.append('district')
    if not format_dob_for_input(row.get('date_of_birth')):
        missing.append('date of birth')
    return missing


def leader_profile_write_payload(*, address=None, district=None, date_of_birth=None, today=None):
    """
    Build a users update dict. Omits blank values so partial saves do not wipe existing data.
    Never includes age. Province is always derived from district.
    """
    payload = {}
    if address is not None:
        addr = str(address).strip()
        if addr:
            payload['address'] = addr
    if district is not None:
        raw = str(district).strip()
        if raw:
            canonical = normalize_district(raw)
            if not canonical:
                raise ValueError('Please select a valid Sri Lanka district.')
            payload['district'] = canonical
            payload['province'] = DISTRICT_TO_PROVINCE[canonical]
    if date_of_birth is not None:
        parsed = parse_date_of_birth(date_of_birth, today=today)
        if parsed is not None:
            payload['date_of_birth'] = parsed.isoformat()
    if 'age' in payload:
        payload.pop('age', None)
    return payload
