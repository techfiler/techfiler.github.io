"""Assembles every part into the Book model."""

from bookgen.model import Book

from . import (part01_foundations, part02_control_plane, part03_workloads,
               part04_scheduling, part05_networking, part06_advanced_networking,
               part07_storage, part08_security, part09_operators, part10_lifecycle,
               part11_observability, part12_troubleshooting, part13_resilience,
               part14_hpc, part15_automation, part16_fleet, part17_leadership)

MODULES = [
    part01_foundations, part02_control_plane, part03_workloads, part04_scheduling,
    part05_networking, part06_advanced_networking, part07_storage, part08_security,
    part09_operators, part10_lifecycle, part11_observability, part12_troubleshooting,
    part13_resilience, part14_hpc, part15_automation, part16_fleet, part17_leadership,
]


def build_book() -> Book:
    parts = []
    for index, module in enumerate(MODULES, start=1):
        part = module.PART
        part.number = index
        parts.append(part)

    book = Book(
        title="The OpenShift Platform Engineer's Interview Book",
        subtitle="250 questions, answered the way a senior engineer actually talks - "
                 "structured from first principles to architecture",
        edition="Edition V5 - restructured, expanded and humanised",
        stack="OpenShift 4.x  ·  Kubernetes  ·  RHCOS  ·  ACM 2.x  ·  Ansible  ·  HPC  ·  HA/DR",
        parts=parts,
    )
    book.number_questions()
    book.validate()
    return book
