"""Leader profile: what the leader may fill, and what stays read-only."""
import re

from utils.member_gaps import (
    CELL_CATEGORY_LABELS,
    is_miracle_dome_branch,
    selected_member_country,
    split_member_name,
)
from utils.sri_lanka_districts import (
    format_dob_for_input,
    normalize_district,
    parse_date_of_birth,
    province_for_district,
)

# Rather Not Say is first so it sits at the top of the dropdown.
MARITAL_STATUS_OPTIONS = (
    'Rather Not Say',
    'Married',
    'Single',
    'Widow',
    'Divorce',
    'Separated',
)

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def canonical_marital_status(value):
    """Return the stored label, or empty when the value is not one of the options."""
    text = str(value or '').strip().lower()
    for option in MARITAL_STATUS_OPTIONS:
        if option.lower() == text:
            return option
    return ''


def sector_for_zone(zone_id, zones):
    """Sector number copied from the selected zone. Sector 0 is valid."""
    for zone in zones or []:
        if str(zone.get('id')) != str(zone_id):
            continue
        sector = zone.get('sector_number')
        if sector is None or str(sector).strip() == '':
            return None
        try:
            return int(sector)
        except (TypeError, ValueError):
            return None
    return None


def profile_missing_labels(row):
    """Labels still empty on this leader. Country defaults to Sri Lanka and is not listed.

    Name, phone, role, cell category, and branch are shown and are not listed,
    because the leader cannot change them here. Email is optional.
    Zone and Sector are listed only when this leader's branch is Miracle Dome.
    """
    row = row or {}
    missing = []
    if not str(row.get('address') or '').strip():
        missing.append('Address')
    district = normalize_district(row.get('district'))
    province = str(row.get('province') or '').strip()
    expected = province_for_district(district) if district else None
    if not district:
        missing.append('District')
    if not expected or province != expected:
        missing.append('Province')
    if not format_dob_for_input(row.get('date_of_birth')):
        missing.append('Date of birth')
    if not canonical_marital_status(row.get('marital_status')):
        missing.append('Marital status')
    if is_miracle_dome_branch(row.get('branch_name')):
        if not row.get('zone_id'):
            missing.append('Zone')
        sector = row.get('sector_number')
        if sector is None or str(sector).strip() == '':
            missing.append('Sector')
    return missing


def profile_field_gaps(
    *,
    address='',
    district='',
    province='',
    date_of_birth='',
    marital_status='',
    email='',
    zone_required=False,
    zone_id=None,
    sector_number=None,
):
    """Input ids that should show a red border. Filled valid values are omitted."""
    gaps = []
    if not str(address or '').strip():
        gaps.append('address')
    if not normalize_district(district):
        gaps.append('district')
    if not str(province or '').strip():
        gaps.append('province')
    if not format_dob_for_input(date_of_birth):
        gaps.append('date_of_birth')
    if not canonical_marital_status(marital_status):
        gaps.append('marital_status')
    if str(email or '').strip() and not _EMAIL_RE.fullmatch(str(email).strip()):
        gaps.append('email')
    if zone_required:
        if zone_id in (None, ''):
            gaps.append('zone_id')
        if sector_number is None or str(sector_number).strip() == '':
            gaps.append('sector_number')
    return gaps


def leader_name_parts(name):
    """Display split of the stored name. This does not rewrite the stored value."""
    return split_member_name(name)


def leader_category_label(category):
    key = str(category or '').strip().lower()
    return CELL_CATEGORY_LABELS.get(key, str(category or '').strip())


def collect_leader_profile_update(posted, *, branch_name='', zones=None, today=None):
    """Validate the fields a leader may save.

    Returns (errors, payload). The payload never includes name, phone, role,
    cell category, branch, or age. Zone and sector are included only for
    Miracle Dome.
    """
    posted = posted or {}
    errors = {}
    address = str(posted.get('address') or '').strip()
    if not address:
        errors['address'] = 'Address is required.'

    district = normalize_district(posted.get('district'))
    province = province_for_district(district) if district else None
    if not district:
        errors['district'] = 'Pick a district from the list.'

    dob_raw = posted.get('date_of_birth')
    parsed_dob = None
    if not str(dob_raw or '').strip():
        errors['date_of_birth'] = 'Date of birth is required.'
    else:
        try:
            parsed_dob = parse_date_of_birth(dob_raw, today=today)
        except ValueError as exc:
            errors['date_of_birth'] = str(exc)
        if parsed_dob is None and 'date_of_birth' not in errors:
            errors['date_of_birth'] = 'Date of birth is required.'

    marital = canonical_marital_status(posted.get('marital_status'))
    if not marital:
        errors['marital_status'] = 'Marital status is required.'

    email = str(posted.get('email') or '').strip()
    if email and not _EMAIL_RE.fullmatch(email):
        errors['email'] = 'Enter a valid email, or leave it empty.'

    zone_required = is_miracle_dome_branch(branch_name)
    zone_id = None
    sector_number = None
    if zone_required:
        raw_zone = str(posted.get('zone_id') or '').strip()
        if not raw_zone:
            errors['zone_id'] = 'Zone is required for Miracle Dome branch.'
        else:
            try:
                zone_id = int(raw_zone)
            except (TypeError, ValueError):
                errors['zone_id'] = 'Zone is required for Miracle Dome branch.'
        if zone_id is not None and 'zone_id' not in errors:
            sector_number = sector_for_zone(zone_id, zones)
            if sector_number is None:
                errors['sector_number'] = 'Sector is required for Miracle Dome branch.'

    if errors:
        return errors, {}

    payload = {
        'address': address,
        'district': district,
        'province': province,
        'date_of_birth': parsed_dob.isoformat(),
        'marital_status': marital,
        'country': selected_member_country(posted.get('country')),
        'email': email or None,
    }
    if zone_required:
        payload['zone_id'] = zone_id
        payload['sector_number'] = sector_number
    return {}, payload
