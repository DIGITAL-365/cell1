"""Which member fields a leader still needs to fill in before the app opens."""
import re

from utils.sri_lanka_districts import normalize_district, province_for_district

ALLOWED_MEMBER_CELL_CATEGORIES = frozenset({'youth', 'young adult', 'adult'})
ALLOWED_GENDERS = frozenset({'Male', 'Female', 'Other'})
DEFAULT_MEMBER_COUNTRY = 'Sri Lanka'
CELL_CATEGORY_LABELS = {
    'youth': 'Youth',
    'young adult': 'Young Adult',
    'adult': 'Adult',
}
# First name: more than 3 letters, no spaces. Surname may contain words such as "De Silva".
_NAME_PART_RE = re.compile(r'^[A-Za-z]{4,49}$')
_LAST_NAME_RE = re.compile(r'^(?:[A-Za-z]{2,})(?: [A-Za-z]{2,})*$')


def is_miracle_dome_branch(branch_name):
    """True when this branch name is Miracle Dome, ignoring case and extra spaces."""
    if not branch_name:
        return False
    normalized = re.sub(r'\s+', ' ', str(branch_name).strip().lower())
    return normalized == 'miracle dome'


def split_member_name(name):
    """First word is the first name. Everything after the first space is the last name."""
    text = str(name or '').strip()
    if not text:
        return '', ''
    parts = text.split(' ', 1)
    first = parts[0].strip()
    last = parts[1].strip() if len(parts) > 1 else ''
    return first, last


def _collapse_spaces(value):
    return re.sub(r'\s+', ' ', str(value or '').strip())


def join_member_name(first, last):
    """One lowercase name. The surname may contain a single space between words."""
    first_part = _collapse_spaces(first).lower()
    last_part = _collapse_spaces(last).lower()
    return f'{first_part} {last_part}'


def name_part_valid(value):
    """First name: letters only, longer than 3 characters, no digits and no spaces."""
    return bool(_NAME_PART_RE.fullmatch(str(value or '').strip()))


def last_name_valid(value):
    """Surname: each word at least 2 letters, more than 3 letters in total, one space between words."""
    text = _collapse_spaces(value)
    if not _LAST_NAME_RE.fullmatch(text):
        return False
    letters = text.replace(' ', '')
    return 4 <= len(letters) <= 49


def canonical_gender(value):
    """Male, Female, or Other. Stored values such as 'female' still count."""
    return {'male': 'Male', 'female': 'Female', 'other': 'Other'}.get(
        str(value or '').strip().lower(),
        '',
    )


def phone_digits(value):
    """Digits only, so a stored number can be shown and saved without spaces."""
    return re.sub(r'\D', '', str(value or ''))


def phone_number_valid(value):
    """9-15 digits. Sri Lanka numbers are often stored as 9 digits, without a leading 0."""
    return bool(re.fullmatch(r'\d{9,15}', phone_digits(value)))


def member_country_options(stored=None):
    """Sri Lanka is always in the list. Keep a different stored country so it stays selected."""
    options = [DEFAULT_MEMBER_COUNTRY]
    value = str(stored or '').strip()
    if value and value not in options:
        options.append(value)
    return options


def selected_member_country(stored=None):
    """Empty country displays as Sri Lanka. A stored country stays selected."""
    value = str(stored or '').strip()
    return value or DEFAULT_MEMBER_COUNTRY


def missing_member_fields(member):
    """Labels for empty required fields on this member.

    Country is not listed when it is empty: the form defaults the dropdown to
    Sri Lanka. Age, church, and potential leader are not listed. Zone and
    Sector are listed only when this member's branch is Miracle Dome.
    Address and date of birth are leader-profile fields and are not checked.
    """
    member = member or {}
    missing = []
    first, last = split_member_name(member.get('name'))
    if not name_part_valid(first):
        missing.append('First name')
    if not last_name_valid(last):
        missing.append('Last name')
    if not canonical_gender(member.get('gender')):
        missing.append('Gender')
    if not phone_number_valid(member.get('phone_number')):
        missing.append('Phone')
    if member.get('branch_id') in (None, ''):
        missing.append('Branch')
    category = str(member.get('cell_category') or '').strip().lower()
    if category not in ALLOWED_MEMBER_CELL_CATEGORIES:
        missing.append('Cell category')
    district = str(member.get('district') or '').strip()
    province = str(member.get('province') or '').strip()
    canonical = normalize_district(district)
    expected_province = province_for_district(canonical) if canonical else None
    if not canonical:
        missing.append('District')
    if not expected_province or province != expected_province:
        missing.append('Province')
    if is_miracle_dome_branch(member.get('branch_name')):
        if not member.get('zone_id'):
            missing.append('Zone')
        sector = member.get('sector_number')
        if sector is None or str(sector).strip() == '':
            missing.append('Sector')
    return missing


def form_field_gaps(
    first_name='',
    last_name='',
    gender='',
    phone_number='',
    district='',
    province='',
    branch_name='',
    cell_category='',
    zone_required=False,
    zone_id=None,
    sector_number=None,
):
    """Input ids that should show a red border. Filled valid values are omitted.

    Country and age are never included. Country defaults to Sri Lanka, and age
    is optional.
    """
    gaps = []
    if not name_part_valid(first_name):
        gaps.append('first_name')
    if not last_name_valid(last_name):
        gaps.append('last_name')
    if not canonical_gender(gender):
        gaps.append('gender')
    if not phone_number_valid(phone_number):
        gaps.append('phone_number')
    if not normalize_district(district):
        gaps.append('district')
    if not str(province or '').strip():
        gaps.append('province')
    if not str(branch_name or '').strip():
        gaps.append('branch_name')
    if str(cell_category or '').strip().lower() not in ALLOWED_MEMBER_CELL_CATEGORIES:
        gaps.append('cell_category')
    if zone_required:
        if zone_id in (None, ''):
            gaps.append('zone_id')
        if sector_number is None or str(sector_number).strip() == '':
            gaps.append('sector_number')
    return gaps


def format_missing_list(missing):
    """Comma-separated labels, for example 'Phone, Gender, District'."""
    labels = [str(item) for item in (missing or []) if item]
    return ', '.join(labels)


def apply_missing_member_fields(members):
    """Set missing_fields and missing_label on each row. Return how many are incomplete.

    Each row needs branch_name already resolved from that member's branch_id.
    """
    count = 0
    for member in members or []:
        if not isinstance(member, dict):
            continue
        missing = missing_member_fields(member)
        member['missing_fields'] = missing
        member['missing_label'] = format_missing_list(missing)
        if missing:
            count += 1
    return count


def incomplete_members_sorted(members):
    """Incomplete rows only, sorted by stored name. Blank names come first."""
    rows = []
    for member in members or []:
        if not isinstance(member, dict):
            continue
        if member.get('missing_fields'):
            rows.append(member)
    rows.sort(key=lambda member: (str(member.get('name') or '').strip().lower(), str(member.get('id') or '')))
    return rows
