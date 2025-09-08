#!/usr/bin/env -S uv run --with flask --with requests
from flask import Flask, request, render_template
import requests
import re
from urllib.parse import quote, urlparse
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

CATEGORY_IDS = {
        "ff": "116",
        "fm": "22",
        "mm": "23",
        }

# Pre-encode parameter names
INCLUDE_ARG = quote('work_search[category_ids][]')
EXCLUDE_ARG = quote('exclude_work_search[category_ids][]')

def get_work_count(task_params):
    base_url, include_categories, exclude_categories = task_params

    url_parts = []
    for cat_id in include_categories:
        url_parts.append(f"{INCLUDE_ARG}={cat_id}")
    for cat_id in exclude_categories:
        url_parts.append(f"{EXCLUDE_ARG}={cat_id}")

    query_string = "&".join(url_parts)

    if '?' in base_url:
        final_url = f"{base_url}&{query_string}"
    else:
        final_url = f"{base_url}?{query_string}"

    try:
        response = requests.get(final_url, timeout=15)
        response.raise_for_status()
        match = re.search(r'([0-9,]+)\s+Works?', response.text)
        if match:
            count_str = match.group(1).replace(',', '')
            return int(count_str)
        return 0
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {final_url}: {e}")
        return 0

def calculate_ratios(ff, fm, mm):
    return {
            'ff_fm': f"{ff / fm:.2f}" if fm > 0 else "N/A",
            'fm_mm': f"{fm / mm:.2f}" if mm > 0 else "N/A",
            'ff_mm': f"{ff / mm:.2f}" if mm > 0 else "N/A",
            'ff_fmmm': f"{ff / (fm + mm):.2f}" if (fm + mm) > 0 else "N/A",
            'fffm_mm': f"{(ff + fm) / mm:.2f}" if mm > 0 else "N/A",
            }

class Stats:
    def __init__(self, ff=0, fm=0, mm=0):
        self.ff = ff
        self.fm = fm
        self.mm = mm
        ratios = calculate_ratios(ff, fm, mm)
        self.ff_fm = ratios['ff_fm']
        self.fm_mm = ratios['fm_mm']
        self.ff_mm = ratios['ff_mm']
        self.ff_fmmm = ratios['ff_fmmm']
        self.fffm_mm = ratios['fffm_mm']

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    fandom_input = ''

    if request.method == 'POST':
        fandom_input = request.form.get('fandom_input', '').strip()

        if fandom_input.startswith(('http://', 'https://')):
            base_url = fandom_input.rstrip('?&')
        else:
            base_url = f"https://archiveofourown.org/tags/{quote(fandom_input.replace('/', '*s*'))}/works"

        tasks = [
                (base_url, [CATEGORY_IDS['ff']], []),
                (base_url, [CATEGORY_IDS['fm']], []),
                (base_url, [CATEGORY_IDS['mm']], []),
                (base_url, [CATEGORY_IDS['ff']], [CATEGORY_IDS['fm'], CATEGORY_IDS['mm']]),
                (base_url, [CATEGORY_IDS['fm']], [CATEGORY_IDS['ff'], CATEGORY_IDS['mm']]),
                (base_url, [CATEGORY_IDS['mm']], [CATEGORY_IDS['ff'], CATEGORY_IDS['fm']]),
                ]

        with ThreadPoolExecutor(max_workers=6) as executor:
            counts = list(executor.map(get_work_count, tasks))

            ff_inc, fm_inc, mm_inc, ff_exc, fm_exc, mm_exc = counts

            results = [
                    {"name": "Inclusive", "stats": Stats(ff_inc, fm_inc, mm_inc)},
                    {"name": "Exclusive", "stats": Stats(ff_exc, fm_exc, mm_exc)}
                    ]

    return render_template('base.html', results=results, fandom_input=fandom_input)

if __name__ == '__main__':
    app.run(debug=True)
