with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# remove app = FastAPI()
content = content.replace('''app = FastAPI(
    title="CineSight AI Camera API",
    version="2.0.0"
)''', '')

idx = content.find("SHIFTS = [")
content = content[:idx] + '''app = FastAPI(
    title="CineSight AI Camera API",
    version="2.0.0"
)\n\n''' + content[idx:]

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
