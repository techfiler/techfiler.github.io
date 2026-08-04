"""Turn parsed Markdown records into the six-layer interview Question model."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .model import FOUNDATION, INTERMEDIATE, SENIOR, Question
from .parse import RawModule, RawQuestion

LEVEL_MAP = {
    "Beginner": FOUNDATION,
    "Foundation": FOUNDATION,
    "Intermediate": INTERMEDIATE,
    "Senior": SENIOR,
    "Architect": "Architect",
}

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"])")

# Topic-keyed analogies. Keys are lowercase substrings matched against the topic.
ANALOGIES: List[Tuple[str, str]] = [
    ("filesystem and inodes",
     "Think of a library card catalogue: the card (inode) holds the book's location and metadata, "
     "while the shelf label (directory entry) is only the name pointing at that card."),
    ("users, groups, and permissions",
     "It is a building badge system: your identity opens some doors, your group opens shared rooms, "
     "and execute on a directory is the right to walk the corridor, not to run a program."),
    ("processes, signals, and file descriptors",
     "A process is a running shift with a clipboard of open resources; signals are taps on the shoulder "
     "asking it to reload, finish, or leave immediately."),
    ("systemd",
     "systemd is the shift supervisor: it knows who must start before whom, restarts failed workers, "
     "and journald is the shared logbook for every unit."),
    ("cpu, memory, and load",
     "CPU usage is how hard the engines are spinning; load average is how long the queue of work is - "
     "including jobs stuck waiting for disk."),
    ("storage, mounts, lvm",
     "LVM is a flexible filing cabinet: physical disks are drawers you can re-slice without moving the "
     "labels on the outside."),
    ("linux network troubleshooting",
     "Packet path debugging is like tracking a parcel: check the sender, each hop, the firewall stamp, "
     "and whether the recipient was actually listening."),
    ("shell automation",
     "Cron and systemd timers are alarm clocks for scripts - useful until two clocks fire the same job "
     "or the job silently fails with no alert."),
    ("namespaces, cgroups",
     "Namespaces decide what a process can see; cgroups decide what it can spend. Together they make "
     "containers possible without a separate kernel."),
    ("osi and tcp/ip",
     "OSI is the teaching diagram of seven floors; TCP/IP is the building people actually work in. "
     "Use OSI to name the floor where the failure lives."),
    ("subnetting",
     "CIDR is how you draw rooms on a floor plan: the prefix length decides how many desks fit and "
     "which doors connect to which corridors."),
    ("dns resolution",
     "DNS is the phone book with sticky notes: recursive resolvers cache answers, so a wrong sticky "
     "note can outlive the truth on the authoritative page."),
    ("tcp and udp",
     "TCP is a tracked courier with receipts; UDP is a megaphone. Choose receipts when order and "
     "loss matter, megaphones when latency wins."),
    ("http, https, and tls",
     "HTTPS is a sealed envelope with a verified wax seal: TLS protects the contents and proves you "
     "are talking to the right desk."),
    ("routing and nat",
     "NAT is the front desk that rewrites apartment numbers so the outside world only dials one "
     "building number."),
    ("firewalls, security groups",
     "Security groups are sticky notes on a host saying who may knock; network ACLs are corridor "
     "rules that apply to everyone on that floor."),
    ("load balancers",
     "A load balancer is a restaurant host: it seats customers at healthy tables and stops sending "
     "people to a kitchen that just closed."),
    ("mtu, fragmentation",
     "MTU is the maximum suitcase size on a conveyor. If one hop is smaller and ICMP is blocked, "
     "large bags vanish without an explanation."),
    ("end-to-end packet",
     "Trace a packet like a missing shipment: confirm DNS, routing, firewall, listener, and "
     "application response before blaming the furthest component."),
    ("images, containers, and layers",
     "An image is a sealed recipe of stacked layers; a container is one cooked meal from that recipe "
     "with a thin writable plate on top."),
    ("dockerfile",
     "A Dockerfile is the kitchen prep list: each instruction adds a layer, and a fat build context "
     "is like wheeling the entire warehouse into the kitchen."),
    ("container lifecycle",
     "Treat a container like a short-lived worker: inspect status and logs first, then restart - "
     "killing evidence is how you lose the root cause."),
    ("docker networking",
     "Published ports are the reception desk mapping building doors to room numbers inside the "
     "container network."),
    ("volumes, bind mounts",
     "A volume is a lockable storage locker the platform manages; a bind mount is taping a host "
     "folder onto the container wall."),
    ("docker compose",
     "Compose is the cast list for a local play: services, networks, and volumes declared together "
     "so the whole scene starts in one cue."),
    ("multi-stage builds",
     "Multi-stage builds are cooking in a messy kitchen then plating only the finished dish - "
     "compilers stay behind, runtime image stays lean."),
    ("registries, tags, and digests",
     "A tag is a sticky label that can move; a digest is the fingerprint that never lies about "
     "which bits you pulled."),
    ("resource limits and cgroups",
     "Limits are the circuit breakers on a shared power strip: without them one greedy appliance "
     "browns out the whole rack."),
    ("container security",
     "Least privilege is giving the waiter a tray key, not the master key to the building."),
    ("health checks and restart",
     "A health check is asking 'can you take orders?' not merely 'are you standing?' - restart "
     "policies only help if readiness is honest."),
    ("image optimization",
     "Image bloat is luggage fees: every unused package slows every pull, every scan, and every "
     "incident where you need a fresh node."),
    ("cluster architecture and control plane",
     "The control plane is air-traffic control: API server takes clearances, etcd remembers the "
     "flight plan, controllers keep reality matching the plan."),
    ("pods and multi-container",
     "A Pod is a taxi: every passenger shares the ride, the address, and the fate of the trip."),
    ("deployments and replicasets",
     "A Deployment is the shift roster; the ReplicaSet is today's on-duty list that actually keeps "
     "the headcount."),
    ("statefulsets",
     "StatefulSets are numbered lockers: sticky names, sticky disks, ordered open and close."),
    ("daemonsets",
     "A DaemonSet is the fire extinguisher rule: one on every floor that matches the label."),
    ("jobs and cronjobs",
     "A Job is a one-off work order; a CronJob is the recurring calendar invite that creates those "
     "work orders."),
    ("services and cluster dns",
     "A Service is the stable desk number; Endpoints are whoever is currently sitting there and "
     "ready to answer."),
    ("ingress and gateway",
     "Ingress is the building directory and front door TLS desk that routes visitors to the right "
     "Service."),
    ("configmaps and secrets",
     "ConfigMaps are pinned notices on the board; Secrets are the locked drawer - still readable "
     "to anyone with room access unless you add stronger controls."),
    ("liveness, readiness, and startup",
     "Liveness asks 'should we restart you?'; readiness asks 'should we send customers?'; "
     "startup asks 'are you still booting?'"),
    ("requests, limits, qos",
     "Requests reserve a seat on the node; limits cap how much you can binge; QoS decides who "
     "gets pushed off first when memory is gone."),
    ("scheduling, affinity, taints",
     "The scheduler is seating chart logic: filters remove impossible chairs, scores pick the "
     "best remaining one."),
    ("autoscaling",
     "HPA adds waiters when queues grow; cluster autoscaling adds dining rooms when no chairs "
     "remain."),
    ("rbac and service accounts",
     "RBAC is the badge printer for API verbs: who may get, list, patch, or delete which objects."),
    ("networkpolicy",
     "NetworkPolicy is the default-deny guest list for east-west traffic between Pods."),
    ("persistentvolumes, pvcs",
     "A PVC is the request for a locker; the StorageClass is which locker company builds it; the "
     "PV is the locker you actually got."),
    ("cni, csi, and cri",
     "CRI runs containers, CNI wires their network, CSI attaches their disks - three plugs, three "
     "failure domains."),
    ("admission control",
     "Admission webhooks are the door guards that mutate or reject objects before etcd ever sees "
     "them."),
    ("etcd, backups",
     "etcd is the cluster's notarised ledger; without tested restores, a backup is only a comforting "
     "file."),
    ("cluster observability",
     "Observability is the instrument panel: metrics show rate, logs show detail, events show what "
     "the platform decided."),
    ("iam users, roles",
     "IAM is the policy engine at the door: users are people, roles are costumes you assume, and "
     "evaluation order decides the final yes or no."),
    ("ec2, launch templates",
     "Launch templates are cookie cutters for VMs; Auto Scaling is the oven that bakes more when "
     "demand rises."),
    ("vpcs, subnets, routes",
     "A VPC is a private campus: subnets are buildings, route tables are road signs, NAT is the "
     "guarded exit to the public internet."),
    ("security groups and network acls",
     "Security groups stick to instances; NACLs stick to subnets. Confusing them is how you open "
     "or close the wrong door."),
    ("application and network load balancers",
     "ALB reads the HTTP menu; NLB forwards packets at high speed without tasting the content."),
    ("route 53 and cloudfront",
     "Route 53 is the global phone book; CloudFront is the local newsstand caching popular pages "
     "near the reader."),
    ("amazon s3",
     "S3 is a vast labelled warehouse: durability is the building, versioning is the revision "
     "history, lifecycle rules are the cleaners."),
    ("rds and aurora",
     "RDS is a managed database appliance; Aurora pushes the storage layer into a distributed "
     "service so compute can fail without losing the shelves."),
    ("dynamodb",
     "DynamoDB is a partitioned filing system: your partition key chooses the drawer, and hot "
     "drawers become the bottleneck."),
    ("lambda and api gateway",
     "Lambda is a function that wakes when called; API Gateway is the reception that validates, "
     "routes, and meters those calls."),
    ("sqs, sns, and eventbridge",
     "SQS is a queue of tickets, SNS is a loudspeaker fan-out, EventBridge is the smart router "
     "that matches event patterns."),
    ("ecs and fargate",
     "ECS schedules containers on a cluster; Fargate rents you the capacity so you do not manage "
     "the EC2 chairs."),
    ("amazon eks",
     "EKS is Kubernetes with the control plane as a managed service - you still own node health, "
     "addons, and workload design."),
    ("cloudwatch, cloudtrail",
     "CloudWatch is how the system feels; CloudTrail is who touched the control plane; Config is "
     "whether the furniture still matches policy."),
    ("kms, secrets manager",
     "KMS is the key vault; Secrets Manager and SSM Parameter Store are the labelled envelopes "
     "those keys seal."),
    ("organizations, accounts",
     "Organisations are the company chart of AWS accounts; SCPs are the guardrails that even "
     "account admins cannot climb over."),
    ("well-architected",
     "Well-Architected is a design review checklist: reliability, security, cost, performance, "
     "and operations scored as trade-offs, not slogans."),
    ("terraform workflow",
     "Terraform is a rehearsal then a performance: plan shows the script, apply changes the stage, "
     "state remembers what was built."),
    ("variables, locals, outputs",
     "Variables are inputs, locals are calculated props, outputs are the labels you hand to the "
     "next team."),
    ("references, dependencies",
     "References weave a dependency graph; data sources read existing scenery without claiming to "
     "own it."),
    ("state, backends, and locking",
     "State is the inventory clipboard; remote backends plus locks stop two people rewriting the "
     "clipboard at once."),
    ("modules and reusable",
     "Modules are prefabricated rooms: same blueprint, different addresses, fewer copy-paste "
     "fires."),
    ("count, for_each",
     "count is a numbered photocopy; for_each is a labelled set - labels survive reordering, "
     "numbers do not."),
    ("lifecycle meta-arguments",
     "Lifecycle rules are sticky notes on a resource: create before destroy, ignore noisy attrs, "
     "or replace when a force-new field changes."),
    ("import, moved, and removed",
     "Import adopts an orphan, moved renames without rebuild, removed forgets without destroying "
     "the real object."),
    ("workspaces and environment",
     "Workspaces are parallel clipboards - handy for demos, risky as your only isolation between "
     "prod and everything else."),
    ("drift, planning, partial apply",
     "Drift is when reality walked away from the script; partial apply is leaving the stage half "
     "painted - recover with plan, not panic."),
    ("validation, testing, and policy",
     "Validation catches bad inputs early; policy as code is the referee that blocks unsafe plans "
     "before apply."),
    ("terraform ci/cd",
     "CI for Terraform is plan-on-PR and apply-on-merge with identity that is temporary, auditable, "
     "and least-privileged."),
    ("types, control flow",
     "Python truthiness and types are the grammar of automation scripts - silent coercions are how "
     "alerts become no-ops."),
    ("functions, scope",
     "Functions are named tools on a belt; default mutable arguments are the classic trap that "
     "shares one list across calls."),
    ("collections, comprehensions",
     "Comprehensions are concise assembly lines - beautiful until they hide a nested quadratic "
     "cost."),
    ("classes, dataclasses",
     "Dataclasses are labelled boxes for related fields; composition beats deep inheritance when "
     "systems change weekly."),
    ("exceptions and context managers",
     "Context managers are 'borrow and return' blocks - files, locks, and sessions close even when "
     "exceptions fire."),
    ("files, json, http",
     "Most DevOps Python is glue: read config, call an API, write an artefact, exit non-zero on "
     "failure."),
    ("logging, cli design",
     "Logs are the black box; a good CLI fails loudly with codes humans and pipelines can trust."),
    ("testing, packaging",
     "Virtualenvs freeze the workshop; tests are the smoke alarms that should burn in CI before "
     "prod."),
    ("concurrency, asyncio",
     "Threads share memory and surprises; asyncio shares an event loop - pick the model that matches "
     "your waits, not your habits."),
    ("airflow architecture",
     "Airflow is an orchestra conductor: the DAG is the score, workers play the notes, the "
     "metadata DB remembers what already played."),
    ("tasks, operators, taskflow",
     "Operators are instruments; TaskFlow is writing the score in Python functions instead of only "
     "YAML-shaped objects."),
    ("scheduling, data intervals",
     "Airflow schedules data intervals, not 'when the cron fired' - catchup is the backlog of "
     "intervals still owed."),
    ("xcom, params, variables",
     "XCom is passing sticky notes between tasks; Connections are the address book; Variables are "
     "global sticky settings."),
    ("retries, trigger rules, sensors",
     "Sensors wait for the world; deferrable sensors wait without hugging a worker thread all "
     "afternoon."),
    ("executors and worker scaling",
     "The executor chooses whether tasks run locally, on Celery workers, or as Kubernetes pods - "
     "capacity planning follows that choice."),
    ("pools, concurrency",
     "Pools are limited parking spots for contended systems like warehouses and APIs."),
    ("production deployment, security",
     "Production Airflow is identity, secrets, isolation, and upgrade rehearsal - not only DAG "
     "syntax."),
    ("monitoring, troubleshooting, backfills",
     "Backfills rewrite history carefully; monitor queue time, task duration, and DAG import errors "
     "before users notice."),
    ("git commits, branches",
     "Git history is the flight recorder of change: commits should explain why, branches isolate "
     "risk, rebase rewrites local story carefully."),
    ("pipeline stages, jobs",
     "A pipeline is an assembly line with quality gates - stages order the work, jobs are the "
     "stations."),
    ("jenkins",
     "Jenkins is a programmable factory horn: declarative pipelines declare the happy path, shared "
     "libraries stop copy-paste drift."),
    ("gitlab ci",
     "GitLab CI is pipelines-as-YAML beside the code, with runners as the machines that actually "
     "build."),
    ("artifacts, caches, packages",
     "Caches speed rebuilds; artefacts prove what you built; registries store the runnable truth."),
    ("secrets, oidc",
     "OIDC short-lived cloud roles beat long-lived keys taped into CI variables."),
    ("testing, quality gates",
     "Quality gates are locked doors: tests, scans, and policy checks that must open before promote."),
    ("deployment strategies",
     "Blue/green and canaries are seatbelt strategies - they trade speed for a smaller blast radius."),
    ("pipeline reliability",
     "Flaky pipelines train teams to ignore red builds - treat flakes as production defects."),
    ("metrics, logs, traces",
     "Metrics show the shape of pain, logs show the story, traces show the path - you need all three "
     "for modern systems."),
    ("prometheus data model",
     "Prometheus stores time series as labelled gauges of truth; cardinality is how those labels "
     "can bankrupt memory."),
    ("promql",
     "PromQL is the question language for metrics - rate, increase, and histograms answer different "
     "human questions."),
    ("alerting and alertmanager",
     "Alerting should wake a human for symptoms that matter; Alertmanager routes, groups, and silences "
     "so pages stay actionable."),
    ("grafana",
     "Dashboards are shared maps - build them for decisions, not for decorating screens."),
    ("opentelemetry",
     "OpenTelemetry is the USB-C of telemetry: one instrumentation model, many backends."),
    ("slis, slos, slas",
     "SLIs measure, SLOs target, SLAs promise - error budgets tell you when to ship versus stabilise."),
    ("golden signals, red, and use",
     "Golden signals and RED/USE are checklists that stop you from staring at the wrong graph."),
    ("cardinality, retention",
     "Observability cost is mostly cardinality and retention - design labels like you design indexes."),
    ("least privilege, identity",
     "Zero Trust assumes breach: authenticate, authorise narrowly, and never confuse presence on the "
     "network with permission."),
    ("secrets management, encryption",
     "Secrets belong in a vault with rotation, not in git history forever."),
    ("sast",
     "SAST is reading the blueprint for cracked beams before the building is occupied."),
    ("dast",
     "DAST knocks on the running building's doors like an attacker would."),
    ("sca, sboms",
     "SCA and SBOMs are the ingredient labels for software - you cannot patch what you cannot name."),
    ("container image and runtime security",
     "Scan the image, drop capabilities, run as non-root, and still watch runtime behaviour."),
    ("kubernetes security controls",
     "K8s security is layered: RBAC, admission, NetworkPolicy, securityContext, and supply chain."),
    ("software supply-chain",
     "Sign what you ship, verify what you run, and treat the pipeline as part of the attack surface."),
    ("vulnerability and incident",
     "Vuln management is triage with deadlines; incidents need evidence, containment, and learning."),
]


MODULE_DEFAULT_ANALOGY = {
    "Linux": "Picture the machine as a workshop: files, users, processes, and networks are tools on "
             "labelled shelves - the interview is whether you can find the right shelf under pressure.",
    "Networking": "Networking failures are lost deliveries: name the hop, prove it with a packet or "
                  "lookup, then change the smallest thing that restores the path.",
    "Docker": "Docker packages a process with its filesystem and limits - interview answers that stay "
              "at 'containers are lightweight VMs' usually stall on the follow-up.",
    "Kubernetes": "Kubernetes is a control loop factory: you declare desired state, controllers chase "
                  "it forever, and evidence lives in conditions, events, and the owning object.",
    "AWS": "AWS questions reward account boundaries, identity, blast radius, and which managed service "
           "owns the failure domain you just named.",
    "Terraform": "Terraform is desired state for cloud objects with a memory called state - seniors "
                 "talk about blast radius, state safety, and plan review, not only HCL syntax.",
    "Python": "In DevOps interviews, Python is reliable glue: clear interfaces, explicit failures, "
              "tests, and automation that other humans can run at 3 a.m.",
    "Apache Airflow and DAGs": "Airflow schedules data work as a graph - the mature answer covers "
                               "retries, idempotency, observability, and executor capacity.",
    "CI/CD and Git": "CI/CD is change control at machine speed: prove the artefact, prove the identity, "
                     "prove the rollback before you brag about frequency.",
    "Monitoring and Observability": "Monitoring tells you something is wrong; observability lets you ask "
                                    "why without SSH folklore - metrics, logs, and traces cooperate.",
    "DevSecOps and Security": "Security answers that only say 'we scan' lose; winners name control, "
                              "owner, evidence, and what happens when the scan fails the gate.",
    "Production Troubleshooting Scenarios": "Production scenarios are scored on the loop: impact, "
                                            "evidence, hypothesis, mitigation, validation, prevention.",
}


def _sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def _analogy_for(topic: str, module: str, easy: str) -> str:
    topic_l = topic.lower()
    for key, analogy in ANALOGIES:
        if key in topic_l:
            return analogy
    # Prefer a concrete sentence from the easy explanation when it is not the generic template.
    for sentence in _sentences(easy):
        low = sentence.lower()
        if low.startswith("in simple terms, this matters because"):
            continue
        if low.startswith("in practice:"):
            continue
        if 40 <= len(sentence) <= 220:
            return sentence
    return MODULE_DEFAULT_ANALOGY.get(module, f"Keep a concrete mental model for {topic}: what owns state, what fails first, and what evidence proves it.")


def _strip_practice_prefix(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^In simple terms, this matters because[^.]*\.\s*", "", text, flags=re.I)
    text = re.sub(r"^In practice:\s*", "", text, flags=re.I)
    text = re.sub(r"^A useful production example is to connect the concept to one observable check or command:\s*", "", text, flags=re.I)
    return text.strip()


def _context_for(raw: RawQuestion) -> str:
    bits: List[str] = []
    prod = _strip_practice_prefix(raw.production)
    strong = raw.strong.strip()
    easy = _strip_practice_prefix(raw.easy)
    if prod:
        bits.append(prod if prod.endswith(".") else prod + ".")
    if easy and easy.lower() not in (prod or "").lower():
        # Keep operational guidance from the explanation.
        practice = easy
        if len(practice) > 40:
            bits.append(practice if practice.endswith(".") else practice + ".")
    if strong:
        bits.append(
            f"In interviews, the strong finish is operational maturity: {strong[0].lower() + strong[1:] if strong else strong}"
        )
    context = " ".join(bits)
    context = re.sub(r"\s+", " ", context).strip()
    if not context.endswith("."):
        context += "."
    return context


def _steps_for(raw: RawQuestion) -> List[str]:
    steps: List[str] = []
    easy = _strip_practice_prefix(raw.easy)
    # Split on sentences and imperative cues.
    for sentence in _sentences(easy):
        cleaned = sentence.strip(" .")
        if len(cleaned) < 25:
            continue
        if cleaned.lower().startswith("in simple terms"):
            continue
        steps.append(cleaned[0].upper() + cleaned[1:] + ".")
        if len(steps) >= 2:
            break

    for sentence in _sentences(raw.strong):
        cleaned = sentence.strip(" .")
        if len(cleaned) < 25:
            continue
        steps.append(cleaned[0].upper() + cleaned[1:] + ".")
        if len(steps) >= 4:
            break

    level = LEVEL_MAP.get(raw.level, FOUNDATION)
    if level == FOUNDATION:
        closer = f"Close by naming the problem {raw.topic} solves and one command you would run to inspect it."
    elif level == INTERMEDIATE:
        closer = f"Describe how you would troubleshoot {raw.topic} with evidence before changing anything."
    else:
        closer = f"Finish with production design for {raw.topic}: failure domains, ownership, and prevention."
    steps.append(closer)

    # Deduplicate while preserving order.
    out: List[str] = []
    seen = set()
    for step in steps:
        key = step.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(step)
    while len(out) < 3:
        out.append(f"Tie {raw.topic} back to a customer-visible symptom and the smallest safe fix.")
    return out[:6]


def _evidence_for(raw: RawQuestion) -> List[str]:
    lines: List[str] = []
    for line in (raw.command or "").splitlines():
        piece = line.strip().rstrip(";")
        if not piece:
            continue
        # Split chained commands on ; when present on one line.
        if ";" in piece and not piece.startswith("for ") and "awk" not in piece:
            for part in piece.split(";"):
                part = part.strip()
                if part:
                    lines.append(part)
        else:
            lines.append(piece)
    if not lines and raw.production:
        prod = _strip_practice_prefix(raw.production)
        if prod:
            lines.append(prod)
    if not lines:
        lines.append(f"# inspect and verify: {raw.topic}")
    # Keep a readable number of evidence lines.
    return lines[:6]


def _deep_dive(raw: RawQuestion) -> str:
    parts = [
        f"Topic focus: {raw.topic}.",
        f"Question type: {raw.qtype}.",
    ]
    if raw.reference:
        parts.append(f"Official reference to skim before the interview: {raw.reference}.")
    parts.append(
        "When the interviewer digs deeper, move from definition to ownership, evidence, blast radius, "
        "and what you would change so the failure cannot silently repeat."
    )
    return " ".join(parts)


def enrich_question(raw: RawQuestion) -> Question:
    level = LEVEL_MAP.get(raw.level, FOUNDATION)
    answer = raw.answer.strip()
    if not answer:
        answer = f"{raw.topic} is a core operational building block you should explain with mechanism, evidence, and failure mode."
    redflag = raw.mistake.strip()
    if redflag and not redflag.lower().startswith("do not"):
        redflag = f"Do not fall into this trap: {redflag[0].lower() + redflag[1:] if redflag else redflag}"
    if not redflag:
        redflag = "Do not recite a definition without naming evidence, blast radius, or how you would verify the fix."

    return Question(
        q=raw.question.strip(),
        level=level,
        answer=answer,
        analogy=_analogy_for(raw.topic, raw.module, raw.easy),
        context=_context_for(raw),
        steps=_steps_for(raw),
        evidence=_evidence_for(raw),
        redflag=redflag,
        followup=raw.followup.strip(),
        qid=raw.qid,
        topic=raw.topic,
        qtype=raw.qtype,
        deep_dive=_deep_dive(raw),
        strong_answer=raw.strong.strip(),
        reference=raw.reference.strip(),
    )


def enrich_module(module: RawModule) -> List[Question]:
    return [enrich_question(q) for q in module.questions]
