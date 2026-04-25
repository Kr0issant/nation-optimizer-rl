"""Department defaults from the v1 specification."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Department:
    name: str
    baseline: float
    full_name: str


DEFAULT_DEPARTMENTS = (
    Department("Social", 60.0, "Social/Municipal"),
    Department("Agriculture", 70.0, "Agriculture"),
    Department("Health", 90.0, "Health"),
    Department("Education", 80.0, "Education/R&D"),
    Department("Defense", 100.0, "Defense"),
    Department("Commerce", 75.0, "Commerce"),
)

DEFAULT_DEPARTMENT_NAMES = tuple(department.name for department in DEFAULT_DEPARTMENTS)
BASELINES_BY_DEPARTMENT = {
    department.name: department.baseline for department in DEFAULT_DEPARTMENTS
}
