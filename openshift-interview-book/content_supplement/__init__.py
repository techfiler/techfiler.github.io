"""Assembles the V6 supplement book — topics beyond OpenShift/Kubernetes."""

from bookgen.model import Book

from . import (part01_linux_admin, part02_shell_scripting, part03_python_sre,
               part04_ansible_advanced, part05_go_platform, part06_container_images,
               part07_bare_metal, part08_hpc_ai)

MODULES = [
    part01_linux_admin, part02_shell_scripting, part03_python_sre,
    part04_ansible_advanced, part05_go_platform, part06_container_images,
    part07_bare_metal, part08_hpc_ai,
]


def build_book() -> Book:
    parts = []
    for index, module in enumerate(MODULES, start=1):
        part = module.PART
        part.number = index
        parts.append(part)

    book = Book(
        title="The Platform Engineer's Supplement Interview Book",
        subtitle="100 questions on Linux, automation, Go, containers, bare metal and HPC — "
                 "the topics senior platform roles ask about beyond OpenShift",
        edition="Edition V6 - supplement to the OpenShift V5 book",
        stack="RHEL 9  ·  Ansible AAP  ·  Python  ·  Go  ·  Podman/Buildah  ·  Satellite  ·  GPU Operator",
        parts=parts,
    )
    book.number_questions()
    book.validate()
    return book
