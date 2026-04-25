import glob
import re

files = glob.glob('d:\\Project\\Splitwise\\app\\templates\\**\\*.html', recursive=True)
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if '<form ' in content and 'csrf_token' not in content:
        content = re.sub(r'(<form[^>]*>)', r'\1\n        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>', content)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
