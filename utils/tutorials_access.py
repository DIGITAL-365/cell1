"""Filter tutorials by the leader's cell categories — shared by routes and API.

Leaders view only. PDF and video lists live on tutorials.materials
(sinhala | english | tamil). Legacy columns are a one-file fallback
when materials is missing.
"""
import json
import re
from datetime import date, datetime

# Legacy single-resource titles, e.g. "Tutorial PDF (Tamil) — Weekly Meeting - July 14, 2026"
_LEGACY_RESOURCE_TITLE_RE = re.compile(
    r'(?i)^\s*tutorial\s+(pdf|video)\b'
)
# Generic weekly labels we rebuild ourselves (with consistent date formatting)
_GENERIC_WEEKLY_TITLE_RE = re.compile(
    r'(?i)^\s*weekly\s+meeting(\b|[\s\-—–:].*)?$'
)
_PLACEHOLDER_TITLES = frozenset({
    '',
    'tutorial',
    'no tutorial',
    'no tutorial uploaded',
})


def parse_tutorial_meeting_date(meeting_date):
    """Parse tutorials.meeting_date to a date; return None if invalid."""
    if meeting_date is None:
        return None
    try:
        if isinstance(meeting_date, datetime):
            return meeting_date.date()
        if isinstance(meeting_date, date):
            return meeting_date
        if isinstance(meeting_date, str):
            try:
                return datetime.strptime(meeting_date, "%Y-%m-%d").date()
            except ValueError:
                try:
                    return datetime.strptime(meeting_date, "%Y-%m-%dT%H:%M:%S").date()
                except ValueError:
                    return datetime.strptime(meeting_date.split('T')[0], "%Y-%m-%d").date()
    except Exception:
        return None
    return None


def str_url(val):
    if val is None:
        return ''
    return str(val).strip()


def is_legacy_tutorial_resource_title(title):
    """True for old single PDF/video titles that should not be shown as section headings."""
    if title is None:
        return False
    s = str(title).strip()
    if not s:
        return False
    return bool(_LEGACY_RESOURCE_TITLE_RE.match(s))


def usable_custom_tutorial_title(title):
    """
    Return a stripped custom title worth showing, or None.
    Skips placeholders, legacy "Tutorial PDF/Video (...)" names, and generic Weekly Meeting labels.
    """
    if title is None:
        return None
    s = str(title).strip()
    if not s:
        return None
    if s.lower() in _PLACEHOLDER_TITLES:
        return None
    if is_legacy_tutorial_resource_title(s):
        return None
    if _GENERIC_WEEKLY_TITLE_RE.match(s):
        return None
    return s


def format_tutorial_section_heading(meeting_date, *, include_date=True, raw_title=None):
    """
    Clean section heading for tutorial list cards and language-chip panels.

    Prefer a real custom title when present; otherwise "Weekly Meeting"
    (optionally with meeting date). Never surfaces legacy resource titles.
    """
    custom = usable_custom_tutorial_title(raw_title)
    if custom:
        return custom

    pd = meeting_date if isinstance(meeting_date, date) and not isinstance(meeting_date, datetime) else parse_tutorial_meeting_date(meeting_date)
    if include_date and pd:
        return f"Weekly Meeting — {pd.strftime('%B %d, %Y')}"
    return 'Weekly Meeting'


def tutorial_row_raw_title(row):
    """Best raw title field from a tutorials row (does not clean)."""
    if not isinstance(row, dict):
        return None
    return row.get('title') or row.get('tutorial_name')


def sinhala_pdf_url(row):
    if not isinstance(row, dict):
        return ''
    u = str_url(row.get('pdf_url'))
    if not u:
        u = str_url(row.get('pdf_url_1'))
    return u


def sinhala_video_url(row):
    if not isinstance(row, dict):
        return ''
    u = str_url(row.get('video_url_1'))
    if not u:
        u = str_url(row.get('video_url'))
    return u


LANGS = (
    {'key': 'sinhala', 'label': 'Sinhala'},
    {'key': 'english', 'label': 'English'},
    {'key': 'tamil', 'label': 'Tamil'},
)

CELL_CATEGORIES = ('youth', 'young adult', 'adult')
_CELL_CATEGORY_SET = frozenset(CELL_CATEGORIES)

CATEGORY_VIEW_LABELS = {
    'youth': 'View Youth',
    'young adult': 'View Young adult',
    'adult': 'View Adult',
}


def _canonical_category(value):
    text = '' if value is None else str(value).strip()
    if text in _CELL_CATEGORY_SET:
        return text
    low = text.lower()
    if low in _CELL_CATEGORY_SET:
        return low
    return ''


def category_view_label(cell_category):
    cat = (cell_category or '').strip()
    return CATEGORY_VIEW_LABELS.get(cat, f'View {cat}' if cat else 'View')


def normalize_cell_categories(raw):
    """Keep youth | young adult | adult, in that order. Exact strings, including the space."""
    items = []
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        items = list(raw)
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if text.startswith('['):
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                items = parsed
            else:
                items = [part.strip() for part in text.split(',')]
        elif ',' in text:
            items = [part.strip() for part in text.split(',')]
        else:
            items = [text]
    else:
        items = [raw]

    found = set()
    for item in items:
        if item is None:
            continue
        val = str(item).strip()
        if not val:
            continue
        if val in _CELL_CATEGORY_SET:
            found.add(val)
            continue
        low = val.lower()
        if low in _CELL_CATEGORY_SET:
            found.add(low)
    return [cat for cat in CELL_CATEGORIES if cat in found]


def _clean_urls(values, limit=3):
    if not isinstance(values, list):
        return []
    out = []
    for url in values:
        if len(out) >= limit:
            break
        text = str_url(url)
        if text:
            out.append(text)
    return out


def materials_dict(row):
    """Return tutorials.materials when present. None means the column is missing."""
    if not isinstance(row, dict) or 'materials' not in row or row.get('materials') is None:
        return None
    materials = row.get('materials')
    if isinstance(materials, str):
        text = materials.strip()
        if not text:
            return None
        try:
            materials = json.loads(text)
        except Exception:
            return None
    if isinstance(materials, dict):
        return materials
    return None


def _fallback_urls(row, key):
    """At most one PDF and one video when materials is absent."""
    if key == 'sinhala':
        pdf = sinhala_pdf_url(row)
        video = sinhala_video_url(row)
    elif key == 'english':
        pdf = str_url(row.get('pdf_url_2'))
        video = str_url(row.get('video_url_2'))
    else:
        pdf = str_url(row.get('pdf_url_3'))
        video = str_url(row.get('video_url_3'))
    return [pdf] if pdf else [], [video] if video else []


def files_for(row):
    """Languages that have at least one PDF or video. Prefer materials over legacy columns."""
    materials = materials_dict(row)
    use_materials = materials is not None
    blocks = []
    for lang in LANGS:
        if use_materials:
            block = materials.get(lang['key']) or {}
            if not isinstance(block, dict):
                block = {}
            pdfs = _clean_urls(block.get('pdfs'))
            videos = _clean_urls(block.get('videos'))
        else:
            pdfs, videos = _fallback_urls(row, lang['key'])
        if pdfs or videos:
            blocks.append({
                'key': lang['key'],
                'label': lang['label'],
                'pdfs': pdfs,
                'videos': videos,
            })
    return blocks


def _indexed_view_label(language_label, index, *, link=False):
    if link:
        base = f'View {language_label} link'
    else:
        base = f'View {language_label}'
    if index == 0:
        return base
    return f'{base} {index + 1}'


def view_buttons_for(row):
    """One button per filled PDF and video. Empty languages are omitted."""
    result = []
    for lang in files_for(row):
        pdfs = [
            {'url': url, 'label': _indexed_view_label(lang['label'], i)}
            for i, url in enumerate(lang['pdfs'])
        ]
        videos = [
            {'url': url, 'label': _indexed_view_label(lang['label'], i, link=True)}
            for i, url in enumerate(lang['videos'])
        ]
        result.append({
            'key': lang['key'],
            'label': lang['label'],
            'pdfs': pdfs,
            'videos': videos,
        })
    return result


def tutorial_file_urls(row):
    urls = []
    for lang in files_for(row):
        urls.extend(lang['pdfs'])
        urls.extend(lang['videos'])
    return urls


def _user_row(supabase, leader_id):
    """Leader category fields. cell_categories is optional and may not exist yet."""
    if not supabase or not leader_id:
        return None
    try:
        res = (
            supabase.table('users')
            .select('cell_category, cell_categories')
            .eq('id', leader_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"fetch_leader_cell_categories wide select: {e}")
    try:
        res = (
            supabase.table('users')
            .select('cell_category')
            .eq('id', leader_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"fetch_leader_cell_categories: {e}")
        return None


def fetch_leader_cell_categories(supabase, leader_id):
    """Categories this leader may view, in display order. Empty if none are set."""
    row = _user_row(supabase, leader_id)
    if not row:
        return []
    cats = normalize_cell_categories(row.get('cell_categories'))
    if cats:
        return cats
    return normalize_cell_categories(row.get('cell_category'))


def fetch_leader_cell_category(supabase, leader_id):
    """First category only. Kept for callers that still expect one value."""
    cats = fetch_leader_cell_categories(supabase, leader_id)
    return cats[0] if cats else None


def _category_query(query, categories):
    if len(categories) == 1:
        return query.eq('cell_category', categories[0])
    return query.in_('cell_category', list(categories))


def _sort_tutorial_rows(rows):
    def sort_key(row):
        parsed = parse_tutorial_meeting_date(row.get('meeting_date') if isinstance(row, dict) else None)
        return parsed.toordinal() if parsed else 0

    return sorted((r for r in rows if isinstance(r, dict)), key=sort_key, reverse=True)


def query_tutorials_for_categories(supabase, categories, meeting_date=None, meeting_dates=None):
    """Tutorial rows for these categories only, newest meeting_date first."""
    cats = normalize_cell_categories(categories)
    if not supabase or not cats:
        return []
    allowed = set(cats)

    def run(query):
        query = _category_query(query, cats)
        if meeting_date:
            query = query.eq('meeting_date', meeting_date)
        elif meeting_dates:
            query = query.in_('meeting_date', list(meeting_dates))
        res = query.order('meeting_date', desc=True).execute()
        rows = res.data or []
        return [row for row in rows if _canonical_category(row.get('cell_category')) in allowed]

    try:
        query = supabase.table('tutorials').select('*')
        return run(query)
    except Exception as e:
        print(f"query_tutorials_for_categories: {e}")
        if len(cats) == 1:
            return []
        merged = []
        seen = set()
        for cat in cats:
            try:
                query = supabase.table('tutorials').select('*').eq('cell_category', cat)
                if meeting_date:
                    query = query.eq('meeting_date', meeting_date)
                elif meeting_dates:
                    query = query.in_('meeting_date', list(meeting_dates))
                res = query.execute()
            except Exception as inner:
                print(f"query_tutorials_for_categories {cat}: {inner}")
                continue
            for row in res.data or []:
                if _canonical_category(row.get('cell_category')) not in allowed:
                    continue
                key = row.get('id') or (row.get('meeting_date'), row.get('cell_category'))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(row)
        return _sort_tutorial_rows(merged)


def empty_tutorial_access(categories=None):
    cats = normalize_cell_categories(categories or [])
    return {
        'cell_category': cats[0] if cats else None,
        'cell_categories': cats,
        'can_edit': False,
        'data': [],
    }


def fetch_tutorials_for_my_cell(supabase, leader_id):
    """
    Returns cell_category (first), cell_categories, can_edit False, and rows
    for every allowed category, sorted by meeting_date descending.
    """
    cats = fetch_leader_cell_categories(supabase, leader_id)
    result = empty_tutorial_access(cats)
    if not cats:
        return result
    result['data'] = query_tutorials_for_categories(supabase, cats)
    return result


def fetch_tutorials_for_category(supabase, leader_id, cell_category):
    """One of the leader's categories. Other categories return no rows."""
    cats = fetch_leader_cell_categories(supabase, leader_id)
    result = empty_tutorial_access(cats)
    requested = normalize_cell_categories(cell_category)
    if len(requested) != 1 or requested[0] not in cats:
        return result
    result['cell_category'] = requested[0]
    result['data'] = query_tutorials_for_categories(supabase, requested)
    return result


def is_tutorial_placeholder(row):
    if not isinstance(row, dict):
        return True
    title = row.get('title') if row.get('title') is not None else row.get('tutorial_name')
    text = '' if title is None else str(title).strip()
    return text in ('', 'No Tutorial Uploaded')


def build_weekly_tutorial_dashboard_rows(tutorial_rows):
    """
    Template rows: heading plus one block per language that has files.
    Each PDF and video is its own View button. Empty languages are omitted.
    """
    rows = []
    for row in _sort_tutorial_rows(tutorial_rows or []):
        languages = view_buttons_for(row)
        if not languages:
            continue
        pd = parse_tutorial_meeting_date(row.get('meeting_date'))
        date_str = pd.strftime("%B %d, %Y") if pd else None
        heading = format_tutorial_section_heading(
            pd,
            include_date=True,
            raw_title=tutorial_row_raw_title(row),
        )
        cat = _canonical_category(row.get('cell_category'))
        rows.append({
            'heading': heading,
            'date_str': date_str,
            'cell_category': cat,
            'uploaded_at': row.get('uploaded_at'),
            'languages': languages,
        })
    return rows
