"""Module titles, intros, and which infographics each part embeds."""

from __future__ import annotations

from typing import Dict, List, TypedDict


class ModuleMeta(TypedDict):
    title: str
    subtitle: str
    intro: str
    infographics: List[str]


MODULE_META: Dict[str, ModuleMeta] = {
    "Linux": {
        "title": "Linux",
        "subtitle": "The operating layer every container and node still is",
        "intro": (
            "Most cloud outages still bottom out in Linux: disks fill, inodes exhaust, file descriptors "
            "leak, permissions block a deploy, or load average rises because I/O is stuck. This module "
            "builds the floor you need before Docker, Kubernetes, and cloud provider abstractions make "
            "sense. Speak in mechanisms and commands, not slogans."
        ),
        "infographics": ["linux_mindmap", "linux_troubleshoot_flow"],
    },
    "Networking": {
        "title": "Networking",
        "subtitle": "Name the hop, then prove it",
        "intro": (
            "Networking interviews reward candidates who can walk a packet or a DNS lookup without "
            "skipping floors. Learn to separate addressing, routing, translation, filtering, load "
            "balancing, and application TLS - then show the command that confirms each claim."
        ),
        "infographics": ["network_mindmap", "packet_path_flow"],
    },
    "Docker": {
        "title": "Docker",
        "subtitle": "Images, isolation, and production container hygiene",
        "intro": (
            "Docker is where many engineers first meet namespaces, cgroups, layered filesystems, and "
            "registries. Senior answers go past 'build and run' into digests, least privilege, health "
            "semantics, and why a fat image slows every incident response."
        ),
        "infographics": ["docker_mindmap", "image_to_runtime_flow"],
    },
    "Kubernetes": {
        "title": "Kubernetes",
        "subtitle": "Desired state, controllers, and evidence under pressure",
        "intro": (
            "Kubernetes questions are really about control loops: who owns the object, what condition "
            "tells the truth, and what is the smallest safe change. This is the largest module because "
            "platform interviews live here - workloads, scheduling, networking, storage, security, and "
            "control-plane survival."
        ),
        "infographics": ["kubernetes_mindmap", "kubectl_apply_flow", "workload_chooser"],
    },
    "AWS": {
        "title": "AWS",
        "subtitle": "Identity, network boundaries, and managed failure domains",
        "intro": (
            "AWS interviews test whether you design with account boundaries, IAM evaluation, VPC paths, "
            "and clear ownership between compute, data, and operations services. Managed does not mean "
            "you stop proving restores, limits, and blast radius."
        ),
        "infographics": ["aws_mindmap", "aws_request_path"],
    },
    "Terraform": {
        "title": "Terraform",
        "subtitle": "Plan, state, modules, and safe change",
        "intro": (
            "Terraform answers should sound like change management: remote state, locking, plan review, "
            "module contracts, and recovery from partial apply. HCL fluency without state safety is how "
            "candidates lose senior rounds."
        ),
        "infographics": ["terraform_mindmap", "terraform_workflow_flow"],
    },
    "Python": {
        "title": "Python",
        "subtitle": "Automation glue that fails loudly and tests cleanly",
        "intro": (
            "Platform teams use Python to glue APIs, parse inventories, and ship internal tools. The "
            "interview bar is readable functions, explicit errors, packaging, and concurrency choices "
            "you can defend."
        ),
        "infographics": ["python_mindmap"],
    },
    "Apache Airflow and DAGs": {
        "title": "Apache Airflow and DAGs",
        "subtitle": "Schedulers, sensors, executors, and data-interval truth",
        "intro": (
            "Airflow interviews move quickly from DAG syntax to idempotency, catchup behaviour, executor "
            "capacity, and how you backfill without corrupting downstream tables. Treat the metadata "
            "database and queue time as first-class production concerns."
        ),
        "infographics": ["airflow_mindmap", "airflow_task_lifecycle"],
    },
    "CI/CD and Git": {
        "title": "CI/CD and Git",
        "subtitle": "History, gates, identity, and deploy strategies",
        "intro": (
            "Delivery interviews score you on whether change is reviewable, artefacts are provenance-rich, "
            "secrets are short-lived, and rollouts shrink blast radius. Pipelines are production systems - "
            "flakes and shared credentials count against you."
        ),
        "infographics": ["cicd_mindmap", "delivery_flow"],
    },
    "Monitoring and Observability": {
        "title": "Monitoring and Observability",
        "subtitle": "Signals, SLOs, and questions you can ask of a system",
        "intro": (
            "Anyone can show a CPU graph. Strong candidates choose the signal that answers the question, "
            "design alerts for symptoms, keep cardinality affordable, and connect telemetry to error "
            "budgets and customer journeys."
        ),
        "infographics": ["observability_mindmap", "signal_chooser"],
    },
    "DevSecOps and Security": {
        "title": "DevSecOps and Security",
        "subtitle": "Controls with owners, gates, and evidence",
        "intro": (
            "Security rounds punish theatre. Name the control, where it runs, who owns failures, how it "
            "blocks a pipeline or runtime, and how you respond when a CVE lands at 17:00 on a Friday."
        ),
        "infographics": ["security_mindmap", "security_layers"],
    },
    "Production Troubleshooting Scenarios": {
        "title": "Production Troubleshooting Scenarios",
        "subtitle": "Impact first, then evidence, then the smallest safe fix",
        "intro": (
            "These scenarios are where interviews feel real. Use a fixed loop: impact and scope, evidence "
            "from the owning layer, one hypothesis, mitigation with limited blast radius, validation on "
            "the customer symptom, and prevention that survives the next week."
        ),
        "infographics": ["evidence_first_loop", "scenario_mindmap"],
    },
}


def meta_for(module_title: str) -> ModuleMeta:
    if module_title in MODULE_META:
        return MODULE_META[module_title]
    return {
        "title": module_title,
        "subtitle": "Core interview themes",
        "intro": f"This module covers practical interview themes for {module_title}.",
        "infographics": [],
    }
