# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [1.0.0] — 2025-06-15

### Added
- Week 6: Refactoring report with before/after metrics (radon CC, MI)
- Week 6: Extract Method applied to `cmd_list`, removed duplicate priority ordering

## [0.6.0] — 2025-06-08

### Added
- Week 5: Factory Method pattern for standard, recurring, and subtask variants
- Week 5: Strategy pattern for sorting (4 strategies) and filtering (6 strategies)
- Week 5: Observer pattern — OverdueNotifier and AuditLogger
- Week 5: Command pattern — undo/redo for delete and update

## [0.5.0] — 2025-05-25

### Added
- Week 4: GitHub Actions CI pipeline (lint + test + coverage)
- Week 4: ruff static analysis integration
- Week 4: CI badge added to README

### Fixed
- Week 4: CI failure — missing `pytest-cov` in dev dependencies (subsequently fixed)

## [0.4.0] — 2025-05-18

### Added
- Week 3: TDD cycle for `FilterByDateRange` (red → green → refactor commits)
- Week 3: BDD-style acceptance tests in `tests/test_acceptance.py`
- Week 3: Self-review PR with 3+ substantive review comments

## [0.3.0] — 2025-05-11

### Added
- Week 2: Full test suite — `test_task.py`, `test_task_service.py`, `test_export.py`
- Week 2: 14 black-box + 18 white-box tests, 70%+ line coverage
- Week 2: `docs/TEST_PLAN.md` documenting testing strategy

## [0.2.0] — 2025-05-04

### Added
- All 10 functional requirements implemented (CRUD, search, filter, sort, export, stats)
- `ExportService` with JSON and CSV exporters (Template Method)
- `JsonStorage` with atomic write

## [0.1.0] — 2025-04-27

### Added
- Repository initialised with README, .gitignore, pyproject.toml
- `Task` model with Priority, Status enums
- `TaskService` skeleton with create/list/get/update/delete
- `JsonStorage` — basic load/save
- Feature branch strategy established (`main` + `feature/*`)
