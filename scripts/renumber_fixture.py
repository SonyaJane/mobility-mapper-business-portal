# python .\\scripts\\renumber_fixture.py .\\fixtures\\business_categories.json 1
# python .\\scripts\\renumber_fixture.py .\\fixtures\\accessibility_features.json 1

import json
import sys


def renumber_fixture(file_path, start_pk=1):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Renumber sequentially starting at start_pk
    for idx, entry in enumerate(data, start=start_pk):
        entry['pk'] = idx

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python renumber_fixture.py <fixture_json_path> <start_pk>")
        sys.exit(1)
    fixture_path = sys.argv[1]
    start_pk = int(sys.argv[2])
    renumber_fixture(fixture_path, start_pk)
