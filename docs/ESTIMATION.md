# ESTIMATION.md — Agile Estimation

## User Stories and Story Points

Estimation used the **Fibonacci scale** (1, 2, 3, 5, 8).

| ID | User Story | Estimated SP | Actual Hours | Notes |
|----|-----------|:---:|:---:|-------|
| US-01 | As a user, I can create a task with title, description, priority, category, and due date | 3 | 2 | Straightforward model + service |
| US-02 | As a user, I can list all tasks with formatted output | 2 | 1.5 | Tabular formatting took extra time |
| US-03 | As a user, I can update any field of an existing task by ID | 3 | 2 | String→enum conversion edge case |
| US-04 | As a user, I can delete a task by ID with confirmation prompt | 2 | 1 | Simple; added undo as bonus |
| US-05 | As a user, I can search tasks by keyword across all text fields | 2 | 1 | Single-pass filter, easy |
| US-06 | As a user, I can filter tasks by priority and date range | 3 | 2.5 | Strategy pattern added scope |
| US-07 | As a user, I can sort tasks by due date and priority | 2 | 1.5 | Strategy pattern reused cleanly |
| US-08 | As a user, tasks are automatically saved and loaded | 2 | 2 | Atomic write (tmp+rename) |
| US-09 | As a user, I can export tasks to JSON and CSV | 3 | 2.5 | Template Method pattern added |
| US-10 | As a user, I can view statistics (count, overdue, completion) | 2 | 1.5 | — |
| US-11 | As a developer, unit test suite with ≥70% coverage | 5 | 5 | Many edge cases to cover |
| US-12 | As a developer, CI pipeline with lint + tests | 3 | 2 | GitHub Actions YAML iteration |
| US-13 | As a developer, Factory Method pattern for task creation | 3 | 2 | Three concrete factories |
| US-14 | As a developer, Strategy pattern for sort/filter | 5 | 4 | Most complex, many variants |
| US-15 | As a developer, Observer pattern for overdue notifications | 3 | 2 | Clean event bus implementation |
| US-16 | As a developer, Command pattern for undo/redo | 5 | 3 | Simpler than estimated |
| US-17 | As a developer, refactoring with before/after metrics | 3 | 3 | radon analysis added time |
| US-18 | As a developer, all documentation written | 3 | 4 | More detailed than planned |

**Total estimated:** 54 SP  
**Total actual:** ~43 hours

---

## Velocity and Reflection

### What went well
- The Strategy pattern estimation (5 SP) was accurate — it was genuinely the most complex piece.
- Storage (US-08) took exactly as long as estimated because the atomic write pattern required research.

### Where estimation was off
- **US-16 (Command pattern)**: Estimated 5 SP but completed in ~3 hours. The pattern structure
  was cleaner than anticipated because `TaskService` already exposed the needed interface.
- **US-18 (documentation)**: Estimated 3 SP but took 4 hours. Good documentation is consistently
  underestimated.

### Lessons Learned
1. When a pattern depends on an existing service interface, reduce the estimate — you're writing
   the adapter, not the underlying logic.
2. Documentation time should be estimated as its own user story, not bundled with implementation.
3. Testing (US-11) was accurately estimated at 5 SP because edge cases are hard to enumerate upfront.
