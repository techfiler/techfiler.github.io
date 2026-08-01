"""Named infographics referenced by the front matter and by each part."""

from __future__ import annotations

from typing import Callable, Dict

from reportlab.graphics.shapes import Drawing

from . import graphics as gx
from . import theme


def answer_ladder() -> Drawing:
    return gx.ladder(
        "The answer ladder: what each level actually sounds like",
        "Same question - \"What is a PodDisruptionBudget?\" - answered four ways. Interviewers score the "
        "rung you land on, not the number of facts you list.",
        [
            ("Foundation", "Names the object",
             "\"A PDB controls how many pods can be disrupted.\" Correct, forgettable, scores one point."),
            ("Intermediate", "Explains the mechanism",
             "\"It caps voluntary disruptions so a minimum number of replicas stays available during a drain.\""),
            ("Senior", "Adds failure modes and evidence",
             "\"It only covers voluntary eviction, not node crashes. I check the selector and healthy replica "
             "count before maintenance, because a badly sized PDB blocks drains and stalls MCO rollout.\""),
            ("Architect", "Adds trade-off, standard and prevention",
             "\"I pair PDBs with replica minimums, topology spread and tested maintenance headroom, and I "
             "validate them in a game day so the first real drain is not the first test.\""),
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
        "Reading route: seventeen parts, three gears",
        "Parts are ordered so each one only depends on the ones before it. Inside every part the questions "
        "climb from Foundation to Architect, so you can stop at your level and come back later.",
        ["Gear", "Parts", "What you are building", "Stop when you can"],
        [
            ["Basics", "1-4",
             "Linux and container primitives, the control plane, workload objects, scheduling and resources",
             "Explain what happens between oc apply and a running pod without notes"],
            ["Intermediate", "5-11",
             "Networking, storage, security, operators, cluster lifecycle and observability",
             "Trace a request end to end and read a failure from the owning controller's conditions"],
            ["Senior", "12-17",
             "Troubleshooting under pressure, HA and DR, HPC, automation, fleet operations and architecture",
             "Run an incident, defend a design trade-off and describe prevention, not just a fix"],
        ],
        widths=[0.11, 0.09, 0.44, 0.36],
    )


def evidence_first_loop() -> Drawing:
    return gx.cycle(
        "The evidence-first loop - use this for every troubleshooting question",
        "Say these six words out loud before you say anything technical. Candidates who jump straight to "
        "\"I would restart the pod\" lose the point even when restarting works.",
        [
            ("Impact", "Who is affected, since when, how bad, is it getting worse"),
            ("Evidence", "Conditions, events, logs, metrics - from the owning controller"),
            ("Hypothesis", "One testable cause that explains all the evidence"),
            ("Mitigation", "Smallest safe action that restores service"),
            ("Validation", "Prove the customer-visible symptom is gone"),
            ("Prevention", "Alert, guardrail, quota or automation so it cannot recur"),
        ],
        theme.RED, theme.RED_TINT,
    )


def container_stack() -> Drawing:
    return gx.stack(
        "A container is a Linux process wearing five costumes",
        "There is no \"container\" object in the kernel. Every isolation feature you see is a separate Linux "
        "mechanism, which is exactly why container problems are usually Linux problems.",
        [
            ("Namespaces", "What the process can see: PID, network, mount, UTS, IPC, user"),
            ("cgroups v2", "What the process can use: CPU shares and quota, memory limit, IO and PID caps"),
            ("Union filesystem", "What the process reads: stacked read-only image layers plus a thin writable layer"),
            ("SELinux + seccomp", "What the process may do: MCS labels on files, syscall filtering, capability set"),
            ("Image + registry", "What the process is: a manifest of layers addressed by an immutable digest"),
            ("Pod (Kubernetes)", "The shared unit: one network namespace and shared volumes for one or more containers"),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def control_plane_map() -> Drawing:
    return gx.stack(
        "Who owns what in an OpenShift cluster",
        "When something is broken, the fastest question is not \"what is wrong\" but \"who owns this\". Read "
        "the conditions on the owner, not the symptom at the bottom.",
        [
            ("CVO", "Owns the release payload. Drives every Cluster Operator toward the version you asked for."),
            ("Cluster Operators", "Own core capabilities: authentication, ingress, storage, monitoring, network, etcd."),
            ("OLM", "Owns optional add-on operators through CatalogSource, Subscription, InstallPlan and CSV."),
            ("MCO", "Owns node configuration. Renders MachineConfigs and rolls them out pool by pool."),
            ("Machine API", "Owns machine existence: MachineSet, Machine, MachineHealthCheck, autoscaling."),
            ("kube-controller-manager", "Owns workload reconciliation: ReplicaSets, endpoints, node lifecycle, PV binding."),
            ("kubelet + CRI-O", "Owns what actually runs: pod sandboxes, containers, probes, image pulls, node status."),
        ],
    )


def oc_apply_flow() -> Drawing:
    return gx.flow(
        "What really happens after oc apply",
        "The single most asked OpenShift interview question. Walk it as a relay race: every stage hands off to "
        "the next, and every stage can be the one that fails.",
        [
            ("Auth + admission", "OAuth token, RBAC, SCC and webhooks validate and mutate"),
            ("etcd write", "Desired state persisted; the API server returns success"),
            ("Controllers", "Deployment to ReplicaSet to Pod objects created"),
            ("Scheduler", "Filter then score nodes, then bind the pod"),
            ("kubelet + CRI-O", "Pull image, attach CNI and CSI, start containers"),
            ("Probes + endpoints", "Ready pod joins EndpointSlice and takes traffic"),
        ],
    )


def workload_chooser() -> Drawing:
    return gx.matrix(
        "Choosing the right workload object",
        "Interviewers rarely ask \"what is a DaemonSet\". They ask \"which one would you use here, and why\".",
        ["Object", "Use when", "Identity", "Watch out for"],
        [
            ["Deployment", "Interchangeable stateless replicas", "Random pod names",
             "Rolling update surge needs spare capacity"],
            ["StatefulSet", "Ordered, sticky identity and per-pod storage", "Stable ordinal names and PVCs",
             "Scale-down leaves PVCs behind on purpose"],
            ["DaemonSet", "One agent per node: logging, CNI, storage, monitoring", "One pod per matching node",
             "Tolerations decide whether it lands on tainted nodes"],
            ["Job", "Run to completion once", "Pod per attempt", "backoffLimit and cleanup policy"],
            ["CronJob", "Run to completion on a schedule", "Job per firing",
             "concurrencyPolicy and missed-schedule pileups"],
        ],
        widths=[0.14, 0.30, 0.22, 0.34],
    )


def scheduling_funnel() -> Drawing:
    return gx.flow(
        "How a pod finds a node",
        "Pending is not a scheduler bug, it is the scheduler telling you no node survived the filters. The "
        "event message names the exact filter that rejected each node.",
        [
            ("Filter", "Resources, taints, affinity, topology, volume zone"),
            ("Score", "Spread, image locality, least or most allocated"),
            ("Reserve + bind", "Winning node written to pod.spec.nodeName"),
            ("kubelet admits", "Node-level checks, then sandbox and containers"),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def qos_matrix() -> Drawing:
    return gx.matrix(
        "Requests, limits and who dies first",
        "Requests buy you a scheduling guarantee. Limits buy you a ceiling. QoS class decides eviction order "
        "when a node runs out of memory.",
        ["QoS class", "How you get it", "CPU behaviour", "Under node memory pressure"],
        [
            ["Guaranteed", "requests == limits for every container, CPU and memory",
             "Eligible for exclusive CPUs under the static policy", "Evicted last; safest for latency-sensitive work"],
            ["Burstable", "Requests set, limits higher or absent",
             "Throttled at the limit, can borrow idle CPU", "Evicted after BestEffort, ranked by usage over request"],
            ["BestEffort", "No requests and no limits anywhere",
             "First to be starved of CPU", "Evicted first; never use it for anything a customer notices"],
        ],
        widths=[0.15, 0.29, 0.26, 0.30],
    )


def request_path() -> Drawing:
    return gx.flow(
        "One HTTPS request, seven places it can die",
        "Learn this path in order. Almost every \"the app is down\" incident is one hop in this chain, and "
        "naming the hop is how you sound senior.",
        [
            ("DNS", "Wildcard *.apps record resolves to the ingress VIP"),
            ("Load balancer", "Health checks pick a live router node"),
            ("Router", "Route match, TLS termination, HAProxy backend"),
            ("Service", "Stable ClusterIP and port mapping"),
            ("EndpointSlice", "Only Ready pod IPs are listed here"),
            ("OVN", "Flows and NetworkPolicy allow the packet to the pod"),
            ("Container", "Listens on the target port and answers"),
        ],
    )


def ovn_layers() -> Drawing:
    return gx.stack(
        "OVN-Kubernetes from the top down",
        "Every layer is inspectable. When a candidate says \"the SDN is broken\", the follow-up is always "
        "\"which layer, and what did you look at?\"",
        [
            ("Intent", "NetworkPolicy, EgressFirewall, EgressIP, Service and Route objects in the API"),
            ("ovnkube-master", "Translates intent into logical switches, routers and ACLs in the OVN northbound DB"),
            ("ovn-controller", "Compiles logical flows into OpenFlow rules on each node"),
            ("br-int + OVS", "The datapath: actual packet forwarding, NAT and conntrack per node"),
            ("Node NIC / MTU", "Geneve encapsulation overhead; a wrong MTU silently drops large packets only"),
            ("Secondary networks", "Multus attaches extra interfaces: macvlan, bridge, SR-IOV VFs for HPC paths"),
        ],
        theme.BLUE, theme.BLUE_TINT,
    )


def pvc_lifecycle() -> Drawing:
    return gx.flow(
        "From PVC to a mounted filesystem",
        "\"PVC is Pending\" is not one failure, it is four. Knowing which arrow is stuck turns a guess into a "
        "diagnosis.",
        [
            ("PVC created", "StorageClass chosen or default applied"),
            ("Provision", "CSI controller creates the backend volume"),
            ("Bind", "PV and PVC bound; WaitForFirstConsumer waits for a pod"),
            ("Attach", "VolumeAttachment maps the disk to the node"),
            ("Mount", "kubelet formats and mounts into the pod"),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def security_layers() -> Drawing:
    return gx.stack(
        "Defence in depth: six independent gates",
        "Each gate answers a different question. Candidates lose points by collapsing them - RBAC and SCC are "
        "not two names for the same control.",
        [
            ("Identity", "Who are you? OAuth, IdP, ServiceAccount and bound tokens"),
            ("RBAC", "What API calls may you make? Verbs on resources in a scope"),
            ("SCC", "What may your pod be? UID, capabilities, host access, volume types"),
            ("NetworkPolicy", "Who may talk to you? Default-deny plus explicit allow, east-west"),
            ("Runtime", "What may the process do on the node? SELinux MCS, seccomp, dropped capabilities"),
            ("Supply chain", "Is the image trustworthy? Digest pinning, signing, SBOM, scanning, allowed registries"),
        ],
        theme.RED, theme.RED_TINT,
    )


def olm_chain() -> Drawing:
    return gx.flow(
        "How an operator actually gets installed",
        "When an operator will not install, walk this chain forwards and stop at the first object that has no "
        "child. That object's status holds your answer.",
        [
            ("CatalogSource", "Catalog pod serving the operator index"),
            ("Subscription", "Channel and approval mode you asked for"),
            ("InstallPlan", "Resolved bundle; may be waiting for approval"),
            ("CSV", "Operator deployment, RBAC and owned CRDs"),
            ("Operator pod", "Reconciles its CRs and reports status"),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def upgrade_flow() -> Drawing:
    return gx.flow(
        "A supported OpenShift upgrade, in order",
        "Upgrades are the highest-risk routine change you own. The order is not negotiable and \"rollback\" is "
        "not a step that exists.",
        [
            ("Precheck", "Cluster Operators Available, Upgradeable true, alerts clear, backups fresh"),
            ("Acknowledge", "Admin ack for known API removals and deprecations"),
            ("Control plane", "CVO updates operators in dependency order"),
            ("Node pools", "MCO drains and reboots pool by pool, honouring PDBs"),
            ("Validate", "Workload SLOs, ingress, storage, monitoring and a real user path"),
        ],
        theme.AMBER, theme.AMBER_TINT,
    )


def observability_signals() -> Drawing:
    return gx.matrix(
        "Which signal answers which question",
        "Senior answers move between signals deliberately. Junior answers stare at CPU graphs.",
        ["Signal", "Answers", "Where it lives", "Failure mode"],
        [
            ["Metrics", "Is it happening now, and how much?", "Prometheus, ServiceMonitor, PodMonitor",
             "Cardinality explosion kills the stack that was meant to warn you"],
            ["Logs", "What exactly happened in this request?", "Cluster Logging, forwarded to an external store",
             "Unbounded retention on cluster storage; no correlation ID"],
            ["Events", "What did the platform decide, and when?", "oc get events, namespaced and short-lived",
             "Default retention is about three hours - capture them early"],
            ["Traces", "Where did the latency go across services?", "Distributed tracing, sampled",
             "Sampling too low to catch the rare slow path"],
            ["Conditions", "What does the owning controller think?", "status.conditions on every object",
             "Ignored, because pod status looked green"],
        ],
        widths=[0.13, 0.24, 0.28, 0.35],
    )


def recovery_matrix() -> Drawing:
    return gx.matrix(
        "What each recovery mechanism actually protects",
        "The classic senior trap: \"we take etcd backups, so we are covered\". Say which failure each control "
        "answers and you separate yourself instantly.",
        ["Mechanism", "Protects against", "Does not protect against", "Proof it works"],
        [
            ["Multiple replicas + spread", "Single pod, node or zone loss",
             "Bad config or bad image rolled everywhere", "Drain a node in business hours and watch SLOs"],
            ["etcd backup", "Loss of cluster state or quorum",
             "Application data loss; PVs are not in etcd", "Documented, rehearsed restore on a lab cluster"],
            ["OADP / Velero", "Namespace, object and PV loss; migration",
             "Cluster-level corruption or a lost control plane", "Restore into a scratch namespace and run the app"],
            ["CSI snapshots", "Fast rollback of a volume", "Site loss if snapshots live on the same array",
             "Clone the snapshot and mount it read-write"],
            ["Second cluster / ACM DR", "Site or region loss",
             "Human error replicated by GitOps within seconds", "Timed failover test against the stated RTO"],
        ],
        widths=[0.19, 0.24, 0.26, 0.31],
    )


def hpc_alignment() -> Drawing:
    return gx.stack(
        "Why an HPC pod is fast or slow: alignment, not tuning",
        "Latency-sensitive workloads do not need more resources, they need the same NUMA node. Every layer "
        "here has to agree or you pay for a cross-socket hop on every packet.",
        [
            ("Guaranteed QoS", "Integer CPU requests equal to limits - the entry ticket for exclusive CPUs"),
            ("CPU Manager", "Static policy pins the container to dedicated cores; no noisy-neighbour throttling"),
            ("Memory + huge pages", "Pre-allocated huge pages on the same NUMA node reduce TLB misses"),
            ("Device alignment", "SR-IOV VF or GPU must sit on the same NUMA node as the CPUs and memory"),
            ("Topology Manager", "single-numa-node policy refuses the pod rather than silently misaligning it"),
            ("PerformanceProfile", "Isolated and reserved core split, kernel args and tuned profile, applied via MCO"),
        ],
        theme.AMBER, theme.AMBER_TINT,
    )


def gitops_flow() -> Drawing:
    return gx.flow(
        "Change control that survives an audit",
        "The point of GitOps is not the tool, it is that every cluster change has an author, a reviewer, a "
        "timestamp and a revert path.",
        [
            ("Git commit", "Desired state, reviewed in a pull request"),
            ("CI validation", "Lint, policy check, dry-run against a schema"),
            ("Argo CD sync", "Applied in waves; drift detected continuously"),
            ("Cluster reconciled", "Live state matches the commit, or it reports OutOfSync"),
            ("Evidence", "Sync history and audit log answer \"who changed this\""),
        ],
        theme.TEAL, theme.TEAL_TINT,
    )


def acm_hub_spoke() -> Drawing:
    return gx.stack(
        "ACM: one hub, many clusters, four jobs",
        "Fleet questions are really about repeatability. If your answer only works when you log into a "
        "cluster, it does not scale to fifty of them.",
        [
            ("Hub cluster", "Runs the multicluster engine, policy controllers, observability and Argo CD"),
            ("Klusterlet", "Agent on each managed cluster; pulls work, reports status back to the hub"),
            ("Lifecycle", "Create, import, upgrade, hibernate and detach clusters from one place"),
            ("Governance", "Policies in inform mode report drift; enforce mode remediates it"),
            ("Placement", "Label-driven targeting: which clusters get this policy, app or upgrade wave"),
            ("Observability", "Metrics and alerts aggregated centrally with per-cluster drill-down"),
        ],
        theme.PURPLE, theme.PURPLE_TINT,
    )


def star_r() -> Drawing:
    return gx.flow(
        "STAR-R: how to tell a production story in 90 seconds",
        "Behavioural questions are scored on structure. Without the final R most candidates ramble; with it "
        "they sound like someone who has owned a platform.",
        [
            ("Situation", "One sentence of business context and blast radius"),
            ("Task", "What you specifically owned"),
            ("Action", "Evidence you gathered and the decision you made"),
            ("Result", "A measured outcome, with a number"),
            ("Reflection", "What you changed so it cannot happen again"),
        ],
        theme.SLATE, theme.SLATE_TINT,
    )


def scoring_card() -> Drawing:
    return gx.matrix(
        "The scorecard your interviewer is probably using",
        "Score yourself 0-3 on each row after every mock answer. Anything below 2 is where your next hour of "
        "study should go.",
        ["Dimension", "What a 3 sounds like"],
        [
            ["Correctness", "Names the right object, the owning controller and the control loop involved"],
            ["Evidence", "Quotes conditions, events, metrics or a specific command instead of asserting"],
            ["Safety", "Controls blast radius, uses supported procedures, says what could go wrong"],
            ["Validation", "Checks the customer-visible symptom, not just that a resource is green"],
            ["Prevention", "Adds an alert, guardrail or automation so the incident cannot repeat"],
            ["Communication", "States impact and uncertainty plainly, and flags trade-offs without hedging"],
        ],
        widths=[0.24, 0.76],
    )


REGISTRY: Dict[str, Callable[[], Drawing]] = {
    "answer_ladder": answer_ladder,
    "six_layer_method": six_layer_method,
    "learning_route": learning_route,
    "evidence_first_loop": evidence_first_loop,
    "container_stack": container_stack,
    "control_plane_map": control_plane_map,
    "oc_apply_flow": oc_apply_flow,
    "workload_chooser": workload_chooser,
    "scheduling_funnel": scheduling_funnel,
    "qos_matrix": qos_matrix,
    "request_path": request_path,
    "ovn_layers": ovn_layers,
    "pvc_lifecycle": pvc_lifecycle,
    "security_layers": security_layers,
    "olm_chain": olm_chain,
    "upgrade_flow": upgrade_flow,
    "observability_signals": observability_signals,
    "recovery_matrix": recovery_matrix,
    "hpc_alignment": hpc_alignment,
    "gitops_flow": gitops_flow,
    "acm_hub_spoke": acm_hub_spoke,
    "star_r": star_r,
    "scoring_card": scoring_card,
}


def render(name: str) -> Drawing:
    return REGISTRY[name]()
