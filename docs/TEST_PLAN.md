# TEST_PLAN.md — Personal Task Tracker

## 1. Testing Strategy

The test suite uses both specification-based (black-box) and structure-based
(white-box) techniques to achieve broad coverage of both expected behaviour and
internal code paths.

| Layer | Framework | Location |
|-------|-----------|----------|
| Unit & integration | pytest | `tests/` |
| Coverage reporting | pytest-cov | CI + local |
| Acceptance (BDD-style) | pytest (Given-When-Then comments) | `tests/test_acceptance.py` |

---

## 2. Black-Box Tests (Specification-Based)

These tests are derived **only** from the written requirements.
No knowledge of implementation details is required to write or understand them.

| Test ID | File | Description |
|---------|------|-------------|
| BB-01 | `test_task.py` | Task stores all supplied fields correctly |
| BB-02 | `test_task.py` | Missing optional fields use sensible defaults |
| BB-03 | `test_task.py` | `is_overdue()` returns True for active past-due task |
| BB-04 | `test_task.py` | `is_overdue()` returns False for completed past-due task |
| BB-05 | `test_task.py` | `matches_keyword()` searches title, description, category, tags |
| BB-06 | `test_task_service.py` | `create()` returns correctly populated Task |
| BB-07 | `test_task_service.py` | `list_all()` returns all tasks |
| BB-08 | `test_task_service.py` | `delete()` removes the task |
| BB-09 | `test_task_service.py` | `search()` finds matching tasks by keyword |
| BB-10 | `test_task_service.py` | `statistics()` returns correct aggregate counts |
| BB-11 | `test_export.py` | JSON export produces a valid, parseable file |
| BB-12 | `test_export.py` | CSV export contains correct column headers |
| BB-13 | `test_export.py` | Storage handles missing file gracefully |
| BB-14 | `test_export.py` | StandardTaskFactory creates a basic task |

---

## 3. White-Box Tests (Structure-Based)

These tests are derived from reading the source code to ensure every **branch**
is exercised at least once (**branch coverage** technique).

| Test ID | File | Code Path Covered |
|---------|------|-------------------|
| WB-01 | `test_task.py` | `is_overdue()` — `due_date is None` branch |
| WB-02 | `test_task.py` | `is_overdue()` — `Status.CANCELLED` branch |
| WB-03 | `test_task.py` | `matches_keyword()` — lowercase normalisation |
| WB-04 | `test_task.py` | `to_dict()` / `from_dict()` full round-trip |
| WB-05 | `test_task.py` | `from_dict()` — missing optional key defaults |
| WB-06 | `test_task.py` | `to_dict()` — `due_date=None` serialises to `None` |
| WB-07 | `test_task.py` | `Priority.__lt__` ordering |
| WB-08 | `test_task.py` | `matches_keyword()` — category branch |
| WB-09 | `test_task_service.py` | `update()` — invalid field guard |
| WB-10 | `test_task_service.py` | `get_by_id()` — missing ID guard |
| WB-11 | `test_task_service.py` | `list_all()` — sort + filter chaining |
| WB-12 | `test_task_service.py` | `statistics()` — overdue detection branch |
| WB-13 | `test_task_service.py` | `create()` — `tags=None` → `[]` |
| WB-14 | `test_task_service.py` | `update()` — string-to-enum conversion (priority) |
| WB-15 | `test_task_service.py` | `update()` — string-to-enum conversion (status) |
| WB-16 | `test_task_service.py` | `reload()` — re-reads storage |
| WB-17 | `test_task_service.py` | `search()` — empty store returns [] |
| WB-18 | `test_task_service.py` | `statistics()` — zero-division guard |
| WB-19 | `test_export.py` | `ExportService.export()` — unsupported format raises |
| WB-20 | `test_export.py` | CSV `tags` — pipe-separated serialisation |
| WB-21 | `test_export.py` | `JsonStorage.load()` — corrupt JSON except-branch |
| WB-22 | `test_export.py` | `CompositeFilter` — AND semantics |
| WB-23 | `test_export.py` | `SortByPriority` — ascending ordering |
| WB-24 | `test_export.py` | `FilterByDateRange` — excludes out-of-range tasks |

---

## 4. Acceptance Tests (BDD / ATDD Style)

Written in **Given-When-Then** format to represent full user scenarios:

| Test ID | Scenario |
|---------|----------|
| AT-01 | User creates a high-priority task and it appears in listings |
| AT-02 | User filters by priority to see only critical tasks |
| AT-03 | User marks tasks done and completion rate improves |
| AT-04 | Keyword search returns only the matching task |
| AT-05 | Export to JSON and CSV produces valid output files |
| AT-06 | Update is persisted after service restart |
| AT-07 | Delete removes task from listing |
| AT-08 | Overdue statistics correctly identifies only past-due tasks |

---

## 5. Coverage Target

**Target:** ≥ 70% line coverage of all business logic modules.

Modules measured:
- `src/models/task.py`
- `src/services/task_service.py`
- `src/services/export_service.py`
- `src/storage/json_storage.py`
- `src/patterns/factory.py`
- `src/patterns/strategy.py`
- `src/patterns/observer.py`
- `src/patterns/command.py`

The CLI layer (`src/cli/commands.py`) is excluded from the coverage minimum
because it requires integration testing with subprocess invocation.

### Measurement Command

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

Coverage results are reported in CI via GitHub Actions and stored as an HTML
report in `htmlcov/`.
