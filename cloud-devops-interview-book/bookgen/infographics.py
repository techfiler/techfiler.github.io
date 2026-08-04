"""Named infographics and mindmaps for the Cloud & DevOps interview book."""

from __future__ import annotations

from typing import Callable, Dict

from reportlab.graphics.shapes import Drawing

from . import graphics as gx
from . import theme


def answer_ladder() -> Drawing:
    return gx.ladder(
        "The answer ladder: what each level actually sounds like",
        "Same topic - Kubernetes probes - answered three ways. Interviewers score the rung you land on.",
        [
            ("Foundation", "Names the objects",
             "\"Liveness, readiness and startup probes check container health.\" Correct, thin, easy to forget."),
            ("Intermediate", "Explains the mechanism",
             "\"Readiness controls Service membership; liveness triggers restarts; startup shields slow boots "
             "from liveness kills.\""),
            ("Senior", "Adds failure modes and evidence",
             "\"I keep probes cheap and faithful to user traffic. A false liveness loop can thrash pods; I "
             "check probe timing, restart counts and EndpointSlices before changing manifests.\""),
        ],
    )


def six_layer_method() -> Drawing:
    return gx.stack(
        "How every answer in this book is built",
        "Six layers per question. Under pressure you speak layers 1-2; when the interviewer digs, you already "
        "have layers 3-6 loaded.",
        [
            ("1. Say this", "The 45-90 second spoken answer. Plain words, no padding, leads with the point."),
            ("2. Think of it like", "One analogy that makes the mechanism obvious and buys you thinking time."),
            ("3. Why it matters", "The production context: what breaks, who notices, what it costs."),
            ("4. Step by step", "The ordered procedure or diagnostic path you would actually follow."),
            ("5. Evidence", "The commands and signals that prove your claim instead of asserting it."),
            ("6. Red flag", "The answer that quietly loses the offer, plus the follow-up you should expect."),
        ],
    )


def learning_route() -> Drawing:
    return gx.matrix(
        "Reading route: twelve modules, three gears",
        "Modules are ordered from machine fundamentals to cloud delivery and incident scenarios. Inside each "
        "module, questions climb Foundation to Senior.",
        ["Gear", "Modules", "What you are building", "Stop when you can"],
        [
            ["Basics", "1-4",
             "Linux, networking, Docker and Kubernetes mental models",
             "Explain a request path and a crash without notes"],
            ["Platform", "5-8",
             "AWS services, Terraform, Python automation and Airflow",
             "Defend identity, state, and data-interval trade-offs"],
            ["Delivery", "9-12",
             "CI/CD, observability, DevSecOps and production scenarios",
             "Run an incident loop and name prevention, not only a fix"],
        ],
        widths=[0.11, 0.10, 0.42, 0.37],
    )


def evidence_first_loop() -> Drawing:
    return gx.cycle(
        "The evidence-first loop - use this for every troubleshooting question",
        "Say these six words out loud before you say anything technical. Candidates who jump straight to "
        "restart lose the point even when restarting works.",
        [
            ("Impact", "Who is affected, since when, how bad, is it getting worse"),
            ("Evidence", "Metrics, logs, events, traces - from the owning layer"),
            ("Hypothesis", "One testable cause that explains all the evidence"),
            ("Mitigation", "Smallest safe action that restores service"),
            ("Validation", "Prove the customer-visible symptom is gone"),
            ("Prevention", "Alert, guardrail, quota or automation so it cannot recur"),
        ],
        theme.RED, theme.RED_TINT,
    )


def scoring_card() -> Drawing:
    return gx.matrix(
        "The scorecard your interviewer is probably using",
        "Score yourself 0-3 on each row after every mock answer. Anything below 2 is where your next study "
        "block should go.",
        ["Dimension", "What a 3 sounds like"],
        [
            ["Correctness", "Names the right mechanism, owner and control loop involved"],
            ["Evidence", "Quotes metrics, logs, events or a specific command instead of asserting"],
            ["Safety", "Controls blast radius, uses supported procedures, says what could go wrong"],
            ["Validation", "Checks the customer-visible symptom, not just that a resource is green"],
            ["Prevention", "Adds an alert, guardrail or automation so the incident cannot repeat"],
            ["Communication", "States impact and uncertainty plainly, and flags trade-offs without hedging"],
        ],
        widths=[0.24, 0.76],
    )


def linux_mindmap() -> Drawing:
    return gx.mindmap(
        "Linux interview mindmap",
        "If you can place a symptom on this map, you already sound organised.",
        "Linux",
        [
            ("Identity", ["users/groups", "permissions/ACLs", "capabilities"]),
            ("Process", ["PID/FD", "signals", "systemd units"]),
            ("Resources", ["CPU/load", "memory/PSI", "cgroups"]),
            ("Storage", ["filesystems", "inodes", "LVM/RAID"]),
            ("Network", ["sockets", "routes", "packet path"]),
            ("Automation", ["shell", "cron/timers", "safe scripts"]),
        ],
    )


def linux_troubleshoot_flow() -> Drawing:
    return gx.flow(
        "Host troubleshooting order that interviewers trust",
        "Start wide enough to see the machine, then narrow. Skipping straight to kill -9 loses evidence.",
        [
            ("Impact", "Which service and since when"),
            ("Saturation", "CPU, mem, IO, inode, FD"),
            ("Owner", "process, unit, mount, socket"),
            ("Evidence", "journal, ps, ss, df"),
            ("Action", "smallest safe change"),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def network_mindmap() -> Drawing:
    return gx.mindmap(
        "Networking interview mindmap",
        "Name the layer before you name the tool.",
        "Networking",
        [
            ("Models", ["OSI floors", "TCP/IP reality"]),
            ("Addressing", ["IPv4/CIDR", "routes", "NAT"]),
            ("Name/Trust", ["DNS", "TLS/HTTPS"]),
            ("Transport", ["TCP", "UDP", "MTU"]),
            ("Policy", ["SG/NACL", "firewalls"]),
            ("Scale path", ["LB/proxy", "e2e trace"]),
        ],
        theme.BLUE, theme.BLUE_TINT,
    )


def packet_path_flow() -> Drawing:
    return gx.flow(
        "One request, six places it can die",
        "Learn this path cold. Almost every outage interview is one hop in this chain.",
        [
            ("DNS", "Name resolves to the right target"),
            ("Route/NAT", "Return path exists"),
            ("Firewall", "Allow is real, not assumed"),
            ("LB/Proxy", "Pool members healthy"),
            ("Listener", "Port is open and bound"),
            ("App/TLS", "Certificate and handler OK"),
        ],
    )


def docker_mindmap() -> Drawing:
    return gx.mindmap(
        "Docker interview mindmap",
        "Containers are processes with packaging and policy.",
        "Docker",
        [
            ("Build", ["Dockerfile", "context", "multi-stage"]),
            ("Image", ["layers", "tags", "digests"]),
            ("Runtime", ["lifecycle", "logs", "health"]),
            ("Data", ["volumes", "bind mounts"]),
            ("Net", ["bridges", "published ports"]),
            ("Hardening", ["user", "caps", "limits"]),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def image_to_runtime_flow() -> Drawing:
    return gx.flow(
        "From Dockerfile to a healthy container",
        "Interviewers follow this relay. Every arrow is a failure mode you should be able to name.",
        [
            ("Dockerfile", "Instructions + context"),
            ("Build", "Layers and cache"),
            ("Registry", "Tag or digest pull"),
            ("Create/Run", "Namespaces + mounts"),
            ("Health", "Ready for traffic"),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def kubernetes_mindmap() -> Drawing:
    return gx.mindmap(
        "Kubernetes interview mindmap",
        "Always ask: which object owns reconciliation?",
        "Kubernetes",
        [
            ("Control plane", ["API/etcd", "scheduler", "controllers"]),
            ("Workloads", ["Pod/Deploy", "STS/DS", "Job/Cron"]),
            ("Traffic", ["Service/DNS", "Ingress", "NetPolicy"]),
            ("Config/State", ["Config/Secret", "PVC/CSI"]),
            ("Schedule", ["requests", "affinity", "autoscaling"]),
            ("Secure/Observe", ["RBAC", "admission", "events"]),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def kubectl_apply_flow() -> Drawing:
    return gx.flow(
        "What really happens after kubectl apply",
        "Walk it as a relay race. Every stage can be the one that fails.",
        [
            ("API + RBAC", "Authn/authz and admission"),
            ("etcd write", "Desired state stored"),
            ("Controllers", "Create child objects"),
            ("Scheduler", "Bind pod to a node"),
            ("kubelet", "Pull, mount, start"),
            ("Ready", "Probes + Endpoints"),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def workload_chooser() -> Drawing:
    return gx.matrix(
        "Choosing the right workload object",
        "Interviewers rarely ask only definitions. They ask which object and why.",
        ["Object", "Use when", "Identity", "Watch out for"],
        [
            ["Deployment", "Interchangeable stateless replicas", "Random pod names",
             "Surge needs spare capacity"],
            ["StatefulSet", "Ordered identity and per-pod storage", "Stable names + PVCs",
             "Scale-down keeps PVCs"],
            ["DaemonSet", "One agent per matching node", "Per-node pod",
             "Tolerations decide coverage"],
            ["Job/CronJob", "Run to completion", "Attempt pods",
             "backoffLimit and concurrency"],
        ],
        widths=[0.16, 0.30, 0.22, 0.32],
    )


def aws_mindmap() -> Drawing:
    return gx.mindmap(
        "AWS interview mindmap",
        "Lead with identity and blast radius, then the service.",
        "AWS",
        [
            ("Identity", ["IAM", "roles", "SCP/orgs"]),
            ("Network", ["VPC", "SG/NACL", "LB"]),
            ("Compute", ["EC2/ASG", "ECS/EKS", "Lambda"]),
            ("Data", ["S3", "RDS/Aurora", "DynamoDB"]),
            ("Events", ["SQS/SNS", "EventBridge"]),
            ("Operate", ["CloudWatch", "KMS/Secrets", "WAFR"]),
        ],
        theme.AMBER, theme.AMBER_TINT,
    )


def aws_request_path() -> Drawing:
    return gx.flow(
        "Typical public HTTPS path on AWS",
        "Use this when an interviewer says the website is down - name the hop before the console click.",
        [
            ("Route 53", "DNS to the edge"),
            ("CloudFront", "Cache and TLS"),
            ("ALB/NLB", "Health-checked targets"),
            ("Compute", "EC2/ECS/EKS/Lambda"),
            ("Data", "RDS/Dynamo/S3"),
        ],
        theme.AMBER, theme.AMBER_TINT,
    )


def terraform_mindmap() -> Drawing:
    return gx.mindmap(
        "Terraform interview mindmap",
        "State safety beats clever HCL.",
        "Terraform",
        [
            ("Language", ["resources", "vars/locals", "modules"]),
            ("Graph", ["deps", "count/for_each", "lifecycle"]),
            ("State", ["backend", "locking", "drift"]),
            ("Change", ["plan", "apply", "import/moved"]),
            ("Scale", ["workspaces", "envs", "CI"]),
            ("Guard", ["validate", "tests", "policy"]),
        ],
    )


def terraform_workflow_flow() -> Drawing:
    return gx.flow(
        "Safe Terraform change workflow",
        "If your answer skips plan review or state locking, seniors will notice.",
        [
            ("Write", "Module + vars"),
            ("Plan", "Review blast radius"),
            ("Policy", "Guardrails in CI"),
            ("Apply", "Locked state"),
            ("Verify", "Cloud + outputs"),
        ],
        theme.BLUE, theme.BLUE_TINT,
    )


def python_mindmap() -> Drawing:
    return gx.mindmap(
        "Python for DevOps mindmap",
        "Readable glue with explicit failure modes.",
        "Python",
        [
            ("Core", ["types", "functions", "collections"]),
            ("Structure", ["classes", "exceptions", "context mgr"]),
            ("I/O", ["files/JSON", "HTTP APIs", "CLI"]),
            ("Quality", ["logging", "tests", "packaging"]),
            ("Concurrency", ["threads", "asyncio", "safety"]),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def airflow_mindmap() -> Drawing:
    return gx.mindmap(
        "Airflow interview mindmap",
        "DAGs are code; production is executors, metadata, and backfills.",
        "Airflow",
        [
            ("Model", ["DAG", "tasks", "operators"]),
            ("Time", ["intervals", "catchup", "timetables"]),
            ("Data pass", ["XCom", "params", "connections"]),
            ("Resilience", ["retries", "sensors", "trigger rules"]),
            ("Scale", ["executors", "pools", "workers"]),
            ("Operate", ["secrets", "metrics", "backfills"]),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def airflow_task_lifecycle() -> Drawing:
    return gx.flow(
        "Airflow task lifecycle under pressure",
        "Queue time and executor capacity matter as much as DAG code.",
        [
            ("Scheduler", "Claims the timeslot"),
            ("Queue", "Executor accepts work"),
            ("Worker", "Runs the operator"),
            ("State", "Success/fail in metadata"),
            ("Downstream", "Trigger rules fire"),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def cicd_mindmap() -> Drawing:
    return gx.mindmap(
        "CI/CD interview mindmap",
        "Prove artefact, identity, and rollback.",
        "CI/CD",
        [
            ("Git", ["commits", "branching", "recovery"]),
            ("Pipeline", ["stages", "jobs", "runners"]),
            ("Quality", ["tests", "scans", "gates"]),
            ("Identity", ["secrets", "OIDC", "roles"]),
            ("Release", ["artefacts", "promote", "strategies"]),
            ("Reliability", ["flakes", "debug", "governance"]),
        ],
        theme.SLATE, theme.SLATE_TINT,
    )


def delivery_flow() -> Drawing:
    return gx.flow(
        "A delivery path that survives audit questions",
        "Say this sequence when asked how you ship safely.",
        [
            ("Commit", "Reviewed change"),
            ("Build", "Reproducible artefact"),
            ("Prove", "Tests + scans"),
            ("Deploy", "Staged strategy"),
            ("Verify", "SLOs + rollback"),
        ],
        theme.SLATE, theme.SLATE_TINT,
    )


def observability_mindmap() -> Drawing:
    return gx.mindmap(
        "Observability interview mindmap",
        "Pick the signal that answers the question.",
        "Observability",
        [
            ("Signals", ["metrics", "logs", "traces"]),
            ("Prometheus", ["series", "PromQL", "alerts"]),
            ("UX", ["Grafana", "runbooks"]),
            ("OTel", ["instrument", "collector"]),
            ("SRE", ["SLI/SLO", "error budget"]),
            ("Cost", ["cardinality", "retention"]),
        ],
        theme.BLUE, theme.BLUE_TINT,
    )


def signal_chooser() -> Drawing:
    return gx.matrix(
        "Which signal answers which question",
        "Senior answers move between signals deliberately.",
        ["Signal", "Answers", "Failure mode"],
        [
            ["Metrics", "Is it happening now, and how much?", "Wrong labels / cardinality explosion"],
            ["Logs", "What exactly happened in this request?", "No correlation IDs; unbounded retention"],
            ["Events", "What did the platform decide?", "Short retention; never captured"],
            ["Traces", "Where did latency go?", "Sampling misses the rare slow path"],
            ["SLOs", "Are we burning budget?", "SLIs that do not match user pain"],
        ],
        widths=[0.16, 0.40, 0.44],
    )


def security_mindmap() -> Drawing:
    return gx.mindmap(
        "DevSecOps interview mindmap",
        "Controls need owners and failure behaviour.",
        "DevSecOps",
        [
            ("Identity", ["least privilege", "Zero Trust"]),
            ("Secrets", ["vault", "rotation", "KMS"]),
            ("Build", ["SAST", "SCA", "SBOM"]),
            ("Test", ["DAST", "runtime"]),
            ("Platform", ["image/K8s", "supply chain"]),
            ("Respond", ["vuln triage", "incident"]),
        ],
        theme.RED, theme.RED_TINT,
    )


def security_layers() -> Drawing:
    return gx.stack(
        "Defence in depth for cloud platforms",
        "Each layer answers a different question. Do not collapse them into 'we are secure'.",
        [
            ("Identity", "Who are you? Humans, roles, workload identity"),
            ("AuthZ", "What may you do? IAM, RBAC, policy engines"),
            ("Secrets", "What must stay sealed? Vault, KMS, rotation"),
            ("Supply chain", "Is the artefact trustworthy? Sign, scan, pin digests"),
            ("Runtime", "What may the process do? Non-root, caps, NetworkPolicy"),
            ("Detect/Respond", "How fast do we see and contain? Findings, IR, lessons"),
        ],
        theme.RED, theme.RED_TINT,
    )


def scenario_mindmap() -> Drawing:
    return gx.mindmap(
        "Production scenario mindmap",
        "Bucket the incident before you dig.",
        "Incidents",
        [
            ("Host", ["CPU", "mem/OOM", "disk/inode"]),
            ("Net", ["DNS", "TLS", "MTU/loss"]),
            ("Container", ["exit", "image size", "CrashLoop"]),
            ("K8s", ["Pending", "NotReady", "502/PVC"]),
            ("Cloud", ["IAM", "ASG", "EKS join"]),
            ("Data/CI", ["state", "pipeline", "deploy"]),
        ],
        theme.AMBER, theme.AMBER_TINT,
    )


REGISTRY: Dict[str, Callable[[], Drawing]] = {
    "answer_ladder": answer_ladder,
    "six_layer_method": six_layer_method,
    "learning_route": learning_route,
    "evidence_first_loop": evidence_first_loop,
    "scoring_card": scoring_card,
    "linux_mindmap": linux_mindmap,
    "linux_troubleshoot_flow": linux_troubleshoot_flow,
    "network_mindmap": network_mindmap,
    "packet_path_flow": packet_path_flow,
    "docker_mindmap": docker_mindmap,
    "image_to_runtime_flow": image_to_runtime_flow,
    "kubernetes_mindmap": kubernetes_mindmap,
    "kubectl_apply_flow": kubectl_apply_flow,
    "workload_chooser": workload_chooser,
    "aws_mindmap": aws_mindmap,
    "aws_request_path": aws_request_path,
    "terraform_mindmap": terraform_mindmap,
    "terraform_workflow_flow": terraform_workflow_flow,
    "python_mindmap": python_mindmap,
    "airflow_mindmap": airflow_mindmap,
    "airflow_task_lifecycle": airflow_task_lifecycle,
    "cicd_mindmap": cicd_mindmap,
    "delivery_flow": delivery_flow,
    "observability_mindmap": observability_mindmap,
    "signal_chooser": signal_chooser,
    "security_mindmap": security_mindmap,
    "security_layers": security_layers,
    "scenario_mindmap": scenario_mindmap,
}


def render(name: str) -> Drawing:
    return REGISTRY[name]()
