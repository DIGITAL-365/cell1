"""Tutorial materials: language lists, view labels, and leader categories."""

import unittest

from utils.tutorials_access import (
    build_weekly_tutorial_dashboard_rows,
    category_view_label,
    files_for,
    normalize_cell_categories,
    view_buttons_for,
)


class MaterialsFilesTests(unittest.TestCase):
    def test_lists_each_filled_pdf_and_video_and_skips_empty_languages(self):
        row = {
            'materials': {
                'sinhala': {
                    'pdfs': ['https://s.example/a.pdf', 'https://s.example/b.pdf', '  '],
                    'videos': ['https://s.example/v'],
                },
                'english': {
                    'pdfs': ['https://e.example/a.pdf'],
                    'videos': [],
                },
                'tamil': {'pdfs': [], 'videos': []},
            },
            'pdf_url_2': 'https://should-not-use.example/old.pdf',
            'video_url_2': 'https://should-not-use.example/old',
        }
        blocks = files_for(row)
        self.assertEqual([b['label'] for b in blocks], ['Sinhala', 'English'])
        self.assertEqual(blocks[0]['pdfs'], [
            'https://s.example/a.pdf',
            'https://s.example/b.pdf',
        ])
        self.assertEqual(blocks[0]['videos'], ['https://s.example/v'])
        self.assertEqual(blocks[1]['pdfs'], ['https://e.example/a.pdf'])
        self.assertEqual(blocks[1]['videos'], [])

    def test_view_button_labels_use_index_for_the_second_file(self):
        row = {
            'materials': {
                'sinhala': {
                    'pdfs': ['https://s.example/a.pdf', 'https://s.example/b.pdf'],
                    'videos': ['https://s.example/v1', 'https://s.example/v2'],
                },
                'english': {'pdfs': ['https://e.example/a.pdf'], 'videos': []},
                'tamil': {'pdfs': [], 'videos': []},
            }
        }
        buttons = view_buttons_for(row)
        sinhala = buttons[0]
        self.assertEqual(
            [item['label'] for item in sinhala['pdfs']],
            ['View Sinhala', 'View Sinhala 2'],
        )
        self.assertEqual(
            [item['label'] for item in sinhala['videos']],
            ['View Sinhala link', 'View Sinhala link 2'],
        )
        self.assertEqual(buttons[1]['pdfs'][0]['label'], 'View English')

    def test_caps_each_list_at_three(self):
        row = {
            'materials': {
                'english': {
                    'pdfs': ['https://e/1', 'https://e/2', 'https://e/3', 'https://e/4'],
                    'videos': [],
                }
            }
        }
        english = files_for(row)[0]
        self.assertEqual(len(english['pdfs']), 3)
        labels = [item['label'] for item in view_buttons_for(row)[0]['pdfs']]
        self.assertEqual(labels, ['View English', 'View English 2', 'View English 3'])

    def test_missing_materials_falls_back_to_one_file_per_language(self):
        row = {
            'pdf_url': 'https://s.example/a.pdf',
            'video_url_1': 'https://s.example/v',
            'pdf_url_2': 'https://e.example/a.pdf',
            'video_url_3': 'https://t.example/v',
        }
        blocks = files_for(row)
        self.assertEqual([b['key'] for b in blocks], ['sinhala', 'english', 'tamil'])
        self.assertEqual(blocks[1]['pdfs'], ['https://e.example/a.pdf'])
        self.assertEqual(blocks[1]['videos'], [])
        self.assertEqual(blocks[2]['videos'], ['https://t.example/v'])

    def test_empty_materials_object_does_not_use_legacy_columns(self):
        row = {
            'materials': {'sinhala': {'pdfs': [], 'videos': []}},
            'pdf_url': 'https://s.example/a.pdf',
        }
        self.assertEqual(files_for(row), [])
        self.assertEqual(build_weekly_tutorial_dashboard_rows([row]), [])

    def test_materials_json_string_is_read(self):
        row = {
            'materials': '{"tamil": {"pdfs": ["https://t.example/a.pdf"], "videos": []}}'
        }
        blocks = files_for(row)
        self.assertEqual(blocks[0]['key'], 'tamil')
        self.assertEqual(view_buttons_for(row)[0]['pdfs'][0]['label'], 'View Tamil')


class CategoryNormalizationTests(unittest.TestCase):
    def test_keeps_young_adult_space_and_display_order(self):
        self.assertEqual(
            normalize_cell_categories(['adult', 'young adult', 'youth', 'other']),
            ['youth', 'young adult', 'adult'],
        )
        self.assertEqual(normalize_cell_categories('young adult'), ['young adult'])
        self.assertEqual(
            normalize_cell_categories('["youth", "adult"]'),
            ['youth', 'adult'],
        )
        self.assertEqual(category_view_label('young adult'), 'View Young adult')
        self.assertEqual(category_view_label('youth'), 'View Youth')
        self.assertEqual(category_view_label('adult'), 'View Adult')

    def test_dashboard_rows_keep_category_and_sort_newest_first(self):
        rows = build_weekly_tutorial_dashboard_rows([
            {
                'meeting_date': '2026-09-01',
                'cell_category': 'youth',
                'materials': {'english': {'pdfs': ['https://e/old.pdf'], 'videos': []}},
            },
            {
                'meeting_date': '2026-09-29',
                'cell_category': 'Adult',
                'title': 'Tutorial - 2026-09-29',
                'materials': {'sinhala': {'pdfs': ['https://s/new.pdf'], 'videos': []}},
            },
        ])
        self.assertEqual([row['cell_category'] for row in rows], ['adult', 'youth'])
        self.assertEqual(rows[0]['languages'][0]['pdfs'][0]['label'], 'View Sinhala')
