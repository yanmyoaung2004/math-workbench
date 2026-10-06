# Research evidence — Clean + Hexagonal in Python (gathered 2026-10-06, subagent)

Synthesis in `../decisions/0001-clean-hexagonal.md`. Canonical sources below.

## Layering

- Hexagonal: app communicates over ports; adapters convert outside; inside never
  leaks outside. Source: https://alistair.cockburn.us/hexagonal-architecture/
- Clean: Entities (innermost) → Use Cases → Interface Adapters → Frameworks/Drivers;
  dependencies point inwards only (DIP at boundaries); cross-boundary data = simple
  structs/DTOs, never Entities/DB rows. Source:
  https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Cosmic Python mapping adopted: `domain/` + `service_layer/`(→ our `application/`)
  + `adapters/` + `entrypoints/`; ports = ABCs (`AbstractRepository` pattern);
  adapters = `SqlAlchemyRepository`/`FakeRepository`; Flask app = thin entrypoint.
  Sources: https://www.cosmicpython.com/book/chapter_04_service_layer.html ·
  https://www.cosmicpython.com/book/chapter_02_repository.html
- Domain: Entities (identity equality) vs Value Objects (immutable, value equality)
  vs Domain Services (stateless fns). Source:
  https://www.cosmicpython.com/book/chapter_01_domain_model.html
- Validation placement: syntax at edge (entrypoint schema), semantics in service
  layer, pragmatics as domain exceptions; don't be defensive inside domain.
  Source: https://www.cosmicpython.com/book/appendix_validation.html

## Keeping SymPy out of domain

- Dependency inversion: ORM imports domain, never reverse — same for SymPy.
- Service signatures use primitives/DTOs; all domain construction inside.
  Source: https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear.html

## Packaging + tests

- `src/` layout (`src/workbench_math/`), editable install for dev. Source:
  https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- Canonical tree: `src/<pkg>/domain|service_layer|adapters|entrypoints`,
  `tests/unit|integration|e2e`, `conftest.py`, `pytest.ini`. Sources:
  https://www.cosmicpython.com/book/appendix_project_structure.html
- Pyramid: many unit (fakes), few integration (real DB/engine), minimal e2e
  (happy + unhappy path); 1 e2e per feature; bulk edge cases at service layer.
- Property testing: Hypothesis `@given` + strategies, pytest-integrated. Source:
  https://hypothesis.readthedocs.io/en/latest/quickstart.html

## Value objects + errors

- `@dataclass(frozen=True)` → immutable, field-wise `__eq__`, hashable; `eq+frozen`
  gives `__hash__`. Source: https://docs.python.org/3/library/dataclasses.html
- Errors as typed exceptions per layer (`domain.exceptions`), user exceptions
  derive from `Exception`, names end in `Error`; service maps to transport codes.
  Sources: https://docs.python.org/3/tutorial/errors.html ·
  https://www.cosmicpython.com/book/appendix_validation.html
