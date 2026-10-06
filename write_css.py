import sys

content = '''@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  --bg-dark: #070B14;
  --surface: #161D2D;
  --grid-line: #2A3446;
  --text-main: #E2E8F0;
  --text-dim: #94A3B8;
  --alert-red: #FF414D;
  --alert-red-bg: rgba(255, 65, 77, 0.1);
  --alert-amber: #FFA000;
  --alert-amber-bg: rgba(255, 160, 0, 0.1);
  --brand-blue: #2F72F4;
}

body {
  margin: 0;
  background-color: var(--bg-dark);
  color: var(--text-main);
  font-family: 'Barlow', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* CONTAINER & HEADER */
.soc-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 16px;
  box-sizing: border-box;
  gap: 16px;
}

.soc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--grid-line);
  padding-bottom: 12px;
}

.soc-brand {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}

.soc-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-indicator.online { background-color: #14C692; }
.status-indicator.offline { background-color: var(--alert-red); }

.soc-clock {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
}

/* PANELS */
.soc-controls-row {
  display: flex;
  gap: 16px;
  height: 80px;
}

.soc-panel {
  background-color: var(--surface);
  border: 1px solid var(--grid-line);
  display: flex;
  flex-direction: column;
}

.soc-stats {
  flex: 2;
}

.soc-manual {
  flex: 1;
}

.soc-feed {
  flex: 1;
  overflow: hidden; /* Contains the scrollable table */
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  padding: 8px 12px;
  border-bottom: 1px solid var(--grid-line);
  background-color: rgba(255, 255, 255, 0.02);
}

/* STATS BAR */
.stats-bar {
  display: flex;
  align-items: center;
  flex: 1;
  padding: 0 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  border-right: 1px solid var(--grid-line);
  padding-right: 16px;
  margin-right: 16px;
}
.stat-item:last-child {
  border-right: none;
  margin-right: 0;
  padding-right: 0;
}

.stat-label {
  font-size: 13px;
  color: var(--text-dim);
}

.stat-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
}
.alert-red { color: var(--alert-red); }
.alert-amber { color: var(--alert-amber); }

/* MANUAL FORM */
.manual-form {
  display: flex;
  align-items: center;
  flex: 1;
  padding: 0 12px;
  gap: 8px;
}

.soc-input {
  background-color: var(--bg-dark);
  border: 1px solid var(--grid-line);
  color: var(--text-main);
  padding: 6px 8px;
  font-family: 'Barlow', sans-serif;
  font-size: 13px;
  outline: none;
}
.soc-input:focus-visible {
  border-color: var(--brand-blue);
}

.file-input {
  flex: 1;
  font-size: 12px;
}

.soc-btn {
  background-color: transparent;
  border: 1px solid var(--grid-line);
  color: var(--text-main);
  padding: 6px 12px;
  font-family: 'Barlow', sans-serif;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.1s, border-color 0.1s;
}
.soc-btn:focus-visible {
  outline: 2px solid var(--brand-blue);
  outline-offset: 2px;
}

.soc-btn.primary {
  background-color: var(--brand-blue);
  border-color: var(--brand-blue);
}
.soc-btn.primary:hover:not(:disabled) {
  background-color: #1e5abf;
}
.soc-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* TABLE */
.table-wrapper {
  flex: 1;
  overflow-y: auto;
}

.soc-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.soc-table th {
  position: sticky;
  top: 0;
  background-color: var(--surface);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-dim);
  padding: 8px 12px;
  border-bottom: 1px solid var(--grid-line);
  z-index: 10;
}

.soc-table td {
  padding: 10px 12px;
  font-size: 14px;
  border-bottom: 1px solid var(--grid-line);
}

.soc-table .mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}
.soc-table .font-bold {
  font-weight: 700;
}

.align-right {
  text-align: right;
}

.empty-state {
  text-align: center;
  padding: 32px !important;
  color: var(--text-dim);
}

/* ROWS & ALERTS */
.row-critical {
  background-color: var(--alert-red-bg);
}
.row-critical td {
  border-bottom-color: rgba(255, 65, 77, 0.2);
}
.row-warning {
  background-color: var(--alert-amber-bg);
}
.row-warning td {
  border-bottom-color: rgba(255, 160, 0, 0.2);
}

.issue-cell {
  font-weight: 600;
}
.row-critical .issue-cell { color: var(--alert-red); }
.row-warning .issue-cell { color: var(--alert-amber); }

.issue-icon {
  display: inline-block;
  margin-right: 4px;
}

.action-btn {
  background-color: rgba(255, 255, 255, 0.05);
}
.action-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: var(--text-dim);
}

/* ANIMATION */
@keyframes flash-bg {
  0% { background-color: var(--text-main); }
  100% { background-color: transparent; }
}

@media (prefers-reduced-motion: no-preference) {
  .new-alert-flash {
    animation: flash-bg 1s ease-out;
  }
}
'''

with open(r'c:\CineSightApp\web_admin\src\styles\dashboard.css', 'w', encoding='utf-8') as f:
    f.write(content)
