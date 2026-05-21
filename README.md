# Personal Task Tracker CLI

![CI](https://github.com/YOUR_USERNAME/task-tracker/actions/workflows/ci.yml/badge.svg)

A command-line task management application built as a Software Engineering
coursework project. The focus is on engineering quality: version control,
testing, CI/CD, design patterns, and refactoring — not just features.

---

## Features

| # | Feature |
|---|---------|
| 1 | Create tasks with title, description, priority, category, due date, and tags |
| 2 | List all tasks with formatted, coloured output |
| 3 | Update any field of an existing task by ID |
| 4 | Delete a task by ID (with undo support) |
| 5 | Full-text keyword search across all text fields |
| 6 | Filter by priority, status, category, and date range |
| 7 | Sort by due date, priority, title, or creation time |
| 8 | Automatic JSON persistence (load on start, save on every mutation) |
| 9 | Export to **JSON** and **CSV** |
| 10 | Statistics: count by status/priority/category, overdue count, completion rate |

---

## Quick Start

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

```bash
git clone https://github.com/PFFantom1290/task-tracker.git
cd task-tracker
pip install -e ".[dev]"
```

### Run

```bash
# Using the installed script
tasks --help

# Or directly
python -m src.main --help
```

---

## Usage

```bash
# Create a task
tasks add "Fix login bug" -p high -c work --due 2025-08-15 --tags backend auth

# Create a recurring task
tasks add "Weekly team standup" --type recurring --interval 7 -p medium -c meetings

# Create a sub-task
tasks add "Write unit tests" --type subtask --parent abc12345

# List all tasks sorted by priority (descending)
tasks list --sort priority --desc

# Filter by priority and status
tasks list --priority high --status todo

# Filter by date range
tasks list --from 2025-01-01 --to 2025-12-31

# Show only overdue tasks
tasks list --overdue

# Show task details
tasks show abc12345

# Update a task
tasks update abc12345 --status in_progress --priority critical

# Delete with confirmation
tasks delete abc12345

# Delete without confirmation (scripts)
tasks delete abc12345 --yes

# Undo last delete or update
tasks undo

# Search
tasks search "login"

# Export
tasks export --format json --output my_tasks.json
tasks export --format csv --output my_tasks.csv

# Export only done tasks
tasks export --format csv --status done --output done_tasks.csv

# Statistics
tasks stats
```

---

## Project Structure

```
task-tracker/
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── .gitignore
├── .github/
│   └── workflows/ci.yml
├── src/
│   ├── main.py
│   ├── models/
│   │   └── task.py              # Task, Priority, Status
│   ├── services/
│   │   ├── task_service.py      # Business logic
│   │   └── export_service.py   # Template Method exporter
│   ├── storage/
│   │   └── json_storage.py     # JSON file adapter
│   ├── patterns/
│   │   ├── factory.py          # Factory Method (Creational)
│   │   ├── strategy.py         # Strategy (Behavioral)
│   │   ├── observer.py         # Observer (Behavioral)
│   │   └── command.py          # Command (Behavioral — undo/redo)
│   └── cli/
│       └── commands.py         # argparse CLI layer
├── tests/
│   ├── test_task.py            # Model unit tests
│   ├── test_task_service.py    # Service unit tests
│   ├── test_export.py          # Export + pattern tests
│   └── test_acceptance.py      # BDD-style acceptance tests
└── docs/
    ├── TEST_PLAN.md
    ├── TDD_EVIDENCE.md
    ├── ESTIMATION.md
    ├── DESIGN_PATTERNS.md
    └── REFACTORING_REPORT.md
```

---

## Running Tests

```bash
# All tests with coverage
pytest

# Verbose output
pytest -v

# Coverage HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Linting

```bash
ruff check src/ tests/
```

---

## Design Patterns Used

| Pattern | Category | Purpose |
|---------|----------|---------|
| Factory Method | Creational | Creates `standard`, `recurring`, and `subtask` task variants |
| Strategy | Behavioral | Interchangeable sort and filter algorithms |
| Observer | Behavioral | Overdue notifications and audit logging |
| Command | Behavioral | Undo/redo for delete and update operations |
| Template Method | Behavioral | Shared export skeleton for JSON and CSV |

See [`docs/DESIGN_PATTERNS.md`](docs/DESIGN_PATTERNS.md) for full documentation.

---

## Engineering Practices

- **Git**: feature branches + Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`)
- **Testing**: 70%+ coverage, black-box + white-box + BDD acceptance tests
- **CI**: GitHub Actions — lint + test on every push and PR
- **TDD**: `FilterByDateRange` developed with Red→Green→Refactor cycle
- **Refactoring**: 3 documented code smells fixed; metrics improved measurably
- See [`docs/`](docs/) for all engineering documentation

---

## Data Storage

Tasks are stored in `tasks.json` in the current working directory.
The file is written atomically (written to a `.tmp` file then renamed)
to prevent data corruption on unexpected exits.
