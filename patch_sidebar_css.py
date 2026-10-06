import sys

with open(r'c:\CineSightApp\web_admin\src\styles\dashboard.css', 'a', encoding='utf-8') as f:
    f.write('''
/* GLOBAL LAYOUT (FIXED SIDEBAR) */
.layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background-color: var(--surface);
  border-right: 1px solid var(--grid-line);
  display: flex;
  flex-direction: column;
  padding: 16px 0;
}

.sidebar-logo {
  font-family: 'Barlow', sans-serif;
  font-size: 24px;
  font-weight: 700;
  padding: 0 20px 24px 20px;
  color: var(--text-main);
  border-bottom: 1px solid var(--grid-line);
  margin-bottom: 16px;
}
.sidebar-logo span {
  color: var(--brand-blue);
}

.nav-item {
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-dim);
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: background-color 0.1s, color 0.1s;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.03);
  color: var(--text-main);
}

.nav-item.active {
  background-color: rgba(47, 114, 244, 0.1);
  color: var(--brand-blue);
  border-right: 3px solid var(--brand-blue);
}

.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
''')
