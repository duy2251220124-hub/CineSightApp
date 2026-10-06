import sys

with open(r'C:\CineSightApp\tools\make_qr.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = "import sys\nif sys.stdout.encoding != 'utf-8':\n    sys.stdout.reconfigure(encoding='utf-8')\n" + content

with open(r'C:\CineSightApp\tools\make_qr.py', 'w', encoding='utf-8') as f:
    f.write(content)
