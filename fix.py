import os

with open('tests/test_all.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'assert "youtube" in wa.sites' in line:
        lines[i] = '    assert len(wa.sites) > 0\n'
        lines[i+1] = '''    youtube_found = False\n    for site in wa.sites:\n        if site.get("name", "").lower() == "youtube" or "youtube" in site.get("aliases", []):\n            youtube_found = True\n            assert "youtube.com" in site.get("url", "")\n            break\n    assert youtube_found\n'''

with open('tests/test_all.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
