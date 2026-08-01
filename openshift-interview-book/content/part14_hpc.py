"""Part 14 - HPC and performance engineering."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=14,
    title="HPC and performance engineering",
    subtitle="Latency-sensitive workloads, and why alignment beats tuning every time",
    intro=(
        "High-performance workloads on OpenShift are less about making things faster and more about "
        "removing sources of variability. A trading engine, a real-time telecom function or a GPU training "
        "job does not need extra resources so much as it needs the same resources, on the same NUMA node, "
        "without being interrupted. That is why almost every answer in this part comes back to alignment: "
        "CPUs, memory, huge pages and devices all sitting on the same socket, with the scheduler refusing "
        "the pod rather than quietly placing it badly. Interviewers here reward measurement and caution far "
        "more than they reward knowing tuning parameters."
    ),
    infographics=["hpc_alignment"],
    questions=[
        Q(
            q="What is NUMA, and why does it matter to a container?",
            level=FOUNDATION,
            answer=(
                "Non-Uniform Memory Access means a multi-socket server's memory is divided between sockets, "
                "and a CPU reaches its own socket's memory much faster than the other socket's. For most "
                "workloads the difference is invisible. For latency-sensitive ones it is not: a process "
                "pinned to socket zero reading memory attached to socket one pays a cross-socket penalty on "
                "every access, and the same applies to devices such as NICs and GPUs."
            ),
            analogy=(
                "It is a library with two floors. Books on your floor take seconds; books on the other floor "
                "mean a trip up the stairs each time. Fine occasionally, disastrous as your main workflow."
            ),
            context=(
                "The practical consequence is that performance can vary run to run for reasons invisible in "
                "any dashboard: the same pod, the same node, different NUMA placement, measurably different "
                "latency. That non-determinism is what Topology Manager exists to eliminate. For interview "
                "purposes, the sign of experience is talking about NUMA as a consistency problem rather than "
                "a raw speed one."
            ),
            steps=[
                "Define NUMA as per-socket memory with asymmetric access cost.",
                "Extend it to devices - NICs and accelerators are also attached to a specific socket.",
                "Explain the symptom: run-to-run variability rather than uniform slowness.",
                "Point forward to CPU Manager and Topology Manager as the mechanisms that make placement "
                "deterministic.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host lscpu | grep -i numa",
                "oc debug node/<node> -- chroot /host numactl --hardware",
                "oc debug node/<node> -- chroot /host cat /sys/class/net/<nic>/device/numa_node",
            ],
            redflag=(
                "Do not dismiss NUMA as irrelevant on modern hardware. For latency-sensitive workloads it is "
                "usually the largest single factor."
            ),
            followup="The same pod is 30% slower on some nodes than others. How does NUMA explain that?",
        ),
        Q(
            q="What are huge pages and when do they help?",
            level=FOUNDATION,
            answer=(
                "Normal memory pages are four kilobytes, so a process using many gigabytes needs an enormous "
                "number of page-table entries and the translation lookaside buffer misses constantly. Huge "
                "pages - typically two megabytes or one gigabyte - reduce the number of entries dramatically, "
                "cutting TLB misses and page-table walk overhead. They help memory-intensive workloads with "
                "large working sets: databases, in-memory analytics, packet processing."
            ),
            analogy=(
                "It is moving house with a few large crates instead of hundreds of small boxes. Fewer trips, "
                "less time spent checking labels."
            ),
            context=(
                "The operational catch is that huge pages are pre-allocated on the node and reserved from "
                "general memory, so they are unavailable to everything else whether or not they are used. "
                "They are also NUMA-specific, which is why they belong in the same conversation as CPU "
                "pinning. And a pod must request them explicitly as a resource - a workload that would "
                "benefit but does not request them simply does not get them."
            ),
            steps=[
                "Explain the TLB and page-table cost that huge pages reduce.",
                "Name the workloads that benefit and those that do not.",
                "Describe the pre-allocation trade-off: reserved memory is unavailable to other workloads.",
                "Configure them per NUMA node through a PerformanceProfile, and have pods request them "
                "explicitly.",
            ],
            evidence=[
                "oc get node <node> -o jsonpath='{.status.allocatable}' | python3 -m json.tool | grep -i hugepages",
                "oc debug node/<node> -- chroot /host cat /proc/meminfo | grep -i huge",
                "oc get pod <pod> -o jsonpath='{.spec.containers[0].resources}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not enable huge pages cluster-wide by default. You are reserving memory that most "
                "workloads cannot use."
            ),
            followup="You allocate huge pages and general workloads start getting evicted. Why?",
        ),
        Q(
            q="What does the CPU Manager static policy do?",
            level=FOUNDATION,
            answer=(
                "With the static policy, containers in Guaranteed QoS pods that request whole CPUs get "
                "exclusive access to specific cores - they are pinned, and no other container is scheduled "
                "onto those cores. That removes CPU contention and the context switching that comes with "
                "sharing, which is what latency-sensitive workloads actually need. The requirements are "
                "strict: Guaranteed QoS, and integer CPU requests equal to limits."
            ),
            analogy=(
                "It is a reserved parking space rather than a permit for the shared car park. Nobody else "
                "can be in it, so you never circle looking for a spot."
            ),
            context=(
                "The requirement people trip over is the integer one - a request of 1.5 CPUs is not eligible "
                "for pinning, so a workload configured with fractional CPUs silently gets shared cores and "
                "the tuning appears to do nothing. The other consideration is capacity: pinned cores are "
                "removed from the shared pool, so a node running several pinned workloads has meaningfully "
                "less capacity for everything else, and that needs to be planned rather than discovered."
            ),
            steps=[
                "State the eligibility rules: Guaranteed QoS and integer CPU request equal to limit.",
                "Explain what exclusivity buys - no contention, no context switching, predictable latency.",
                "Note the capacity cost: pinned cores leave the shared pool.",
                "Enable it through a KubeletConfig or PerformanceProfile on a dedicated pool, and validate "
                "with measurements.",
            ],
            evidence=[
                "oc get kubeletconfig -o yaml | grep -i cpumanager",
                "oc debug node/<node> -- chroot /host cat /var/lib/kubelet/cpu_manager_state",
                "oc get pod <pod> -o jsonpath='{.status.qosClass}{\"\\n\"}'",
            ],
            redflag=(
                "Do not promise CPU pinning for a pod with fractional CPU requests. It will not be pinned "
                "and nobody will notice until performance testing."
            ),
            followup="A pod requests 1500m CPU and is not being pinned. Explain why.",
        ),
        Q(
            q="What do Topology Manager policies do?",
            level=INTERMEDIATE,
            answer=(
                "Topology Manager coordinates the hints from CPU Manager, memory manager and device plugins "
                "so that a pod's CPUs, memory and devices come from the same NUMA node. The policies "
                "escalate in strictness: none does nothing, best-effort tries and continues either way, "
                "restricted rejects the pod if the preferred alignment cannot be met for a container, and "
                "single-numa-node requires everything on one node or the pod is not admitted."
            ),
            analogy=(
                "It is seating a team together for a workshop. Best-effort means they will try; "
                "single-numa-node means if they cannot all sit together, the workshop does not happen."
            ),
            context=(
                "For genuinely latency-sensitive workloads, single-numa-node is usually right, and the "
                "reason is counter-intuitive: you want the pod to fail admission rather than run "
                "misaligned. A pod that runs with cross-socket access produces intermittent latency that "
                "nobody can attribute, whereas a pod that refuses to schedule produces a clear event and a "
                "capacity conversation. Choosing predictable failure over silent degradation is the senior "
                "instinct here."
            ),
            steps=[
                "Explain the hint-coordination role across CPU, memory and devices.",
                "Walk the four policies and what each does when alignment is impossible.",
                "Argue for single-numa-node on latency-critical pools, and say why failure is preferable to "
                "misalignment.",
                "Expect and plan for admission failures as nodes fill unevenly, and monitor for them.",
            ],
            evidence=[
                "oc get kubeletconfig -o yaml | grep -i topologyManagerPolicy",
                "oc describe pod <pod> | grep -i topology",
                "oc get events -n <ns> --field-selector reason=TopologyAffinityError",
            ],
            redflag=(
                "Do not choose best-effort for a workload with a hard latency requirement. Silent "
                "misalignment is worse than a clear rejection."
            ),
            followup="Pods start failing admission with a topology error. Is that a bug or working as intended?",
        ),
        Q(
            q="What is a PerformanceProfile?",
            level=INTERMEDIATE,
            answer=(
                "A PerformanceProfile is a single declarative object, handled by the Node Tuning Operator, "
                "that configures a node pool for low-latency work: which cores are isolated for workloads "
                "and which are reserved for the system, huge page allocation per NUMA node, kernel arguments "
                "and optionally a real-time kernel, the CPU and Topology Manager policies, and the "
                "associated tuned profile. It renders into MachineConfigs, so applying it triggers a rolling "
                "reboot of the pool."
            ),
            analogy=(
                "It is a single specification sheet for a class of machine, rather than a folder of "
                "individual work orders that might not agree with each other."
            ),
            context=(
                "The two things to say about it operationally are that it applies per MachineConfigPool - so "
                "you create a dedicated pool for HPC nodes rather than applying it to all workers - and that "
                "it reboots nodes. That makes it a change-controlled operation with a validation step, not "
                "something to iterate on interactively. Reserved core sizing is the setting most often "
                "wrong: too few reserved cores and the kubelet and system daemons contend with the workload "
                "they were meant to serve."
            ),
            steps=[
                "Describe what it configures and that it renders into MachineConfigs.",
                "Apply it to a dedicated MachineConfigPool, never to all workers.",
                "Size reserved versus isolated cores deliberately, leaving enough for system daemons.",
                "Roll out to one node first, measure against a baseline, then widen.",
            ],
            evidence=[
                "oc get performanceprofile -o yaml | head -40",
                "oc get mcp ; oc debug node/<node> -- chroot /host cat /proc/cmdline",
                "oc debug node/<node> -- chroot /host tuned-adm active",
            ],
            redflag=(
                "Do not apply a PerformanceProfile to the default worker pool. Every worker in the cluster "
                "will reboot to tune the four nodes that needed it."
            ),
            followup="How many cores would you reserve for the system, and how would you decide?",
        ),
        Q(
            q="What does the Node Tuning Operator do, and when would you use a real-time kernel?",
            level=INTERMEDIATE,
            answer=(
                "The Node Tuning Operator manages tuned profiles across nodes, so kernel and sysctl "
                "settings are applied declaratively per node pool rather than by hand. It is also what "
                "implements PerformanceProfile. A real-time kernel goes further, trading throughput for "
                "determinism - it bounds worst-case scheduling latency, which matters for workloads with a "
                "hard deadline such as telecom signalling or industrial control."
            ),
            analogy=(
                "A standard kernel is a commuter train optimised for total passengers carried. A real-time "
                "kernel is a courier that guarantees delivery within the hour, even if it carries less."
            ),
            context=(
                "The decision hinges on whether the requirement is average performance or worst-case "
                "bounded latency. Most workloads described as latency-sensitive actually want good average "
                "latency, and a real-time kernel makes them slower overall for no benefit. Real-time is "
                "right when missing a deadline is a functional failure rather than a slow response, and "
                "that distinction is worth drawing out explicitly before agreeing to it."
            ),
            steps=[
                "Describe tuned profile management and the relationship to PerformanceProfile.",
                "Distinguish average latency requirements from hard deadline requirements.",
                "Choose real-time only for bounded worst-case needs, and expect lower total throughput.",
                "Apply to a dedicated pool, measure worst-case latency, and validate the workload actually "
                "benefits.",
            ],
            evidence=[
                "oc get tuned -A ; oc debug node/<node> -- chroot /host tuned-adm active",
                "oc get performanceprofile <name> -o jsonpath='{.spec.realTimeKernel}{\"\\n\"}'",
                "Worst-case latency measurement, for example cyclictest results, before and after",
            ],
            redflag=(
                "Do not deploy a real-time kernel because a workload is described as latency-sensitive. "
                "Ask whether a missed deadline is a failure or just a slow response."
            ),
            followup="How would you prove a workload actually needs a real-time kernel?",
        ),
        Q(
            q="How do SR-IOV and RDMA help latency-sensitive workloads?",
            level=INTERMEDIATE,
            answer=(
                "SR-IOV lets a physical NIC present virtual functions that are assigned directly to a pod, "
                "so packets bypass the software networking stack entirely - lower latency, less jitter, less "
                "CPU spent on packet processing. RDMA goes further and lets one machine read or write "
                "another's memory without involving the remote CPU, which is what makes tightly coupled HPC "
                "and distributed training workloads scale."
            ),
            analogy=(
                "SR-IOV is a private lane onto the motorway instead of queueing at the roundabout. RDMA is a "
                "conveyor belt directly into the other warehouse."
            ),
            context=(
                "What you give up is worth stating, because it is significant. A pod on an SR-IOV interface "
                "is outside the normal cluster network for that traffic: no Service abstraction, no standard "
                "NetworkPolicy, IP addressing you manage, and a hard dependency on specific hardware and "
                "firmware. It also has to be NUMA-aligned with the CPUs to deliver the benefit, which brings "
                "you straight back to Topology Manager."
            ),
            steps=[
                "Explain the mechanism: direct device assignment bypassing the software datapath.",
                "State the requirements - supported NIC, BIOS and firmware settings, the SR-IOV operator.",
                "Name what you lose: Services, standard policy, portability, simple IPAM.",
                "Insist on NUMA alignment between the device and the pinned CPUs, and measure the gain.",
            ],
            evidence=[
                "oc get sriovnetworknodestate -n openshift-sriov-network-operator -o yaml | head -40",
                "oc exec <pod> -- ip -br addr",
                "Latency percentiles before and after, measured with a repeatable tool",
            ],
            redflag=(
                "Do not adopt SR-IOV without measuring the current latency first. You may be paying a large "
                "complexity cost for a gain nobody can detect."
            ),
            followup="Which policy layer protects an SR-IOV interface, given NetworkPolicy does not?",
        ),
        Q(
            q="How do you make performance-related node changes safely?",
            level=SENIOR,
            answer=(
                "By treating them like any other high-risk change, because a PerformanceProfile change "
                "reboots nodes. I measure a baseline first with a repeatable benchmark, apply the change to "
                "a dedicated pool with a single canary node, measure again with the same tool, and only "
                "widen when the improvement is real and nothing else regressed. Every change is one variable "
                "at a time, recorded, with a documented revert."
            ),
            analogy=(
                "It is engine tuning on a dynamometer. Measure, change one thing, measure again. Change "
                "three things at once and you have learned nothing except that something happened."
            ),
            context=(
                "The failure mode is a well-intentioned tuning session that applies several kernel "
                "parameters, isolates cores and enables huge pages in one change, after which the workload "
                "is faster and nobody knows which part mattered - or, worse, it is slower and nobody knows "
                "what to revert. Because each iteration costs a reboot cycle, the discipline of one variable "
                "at a time is not pedantry; it is the only way to converge."
            ),
            steps=[
                "Establish a baseline with a repeatable benchmark and record the exact conditions.",
                "Apply one change, to a dedicated pool, starting with a single canary node.",
                "Re-measure with the identical method and compare, including the metrics you did not expect "
                "to move.",
                "Record the result and the revert path, then widen the rollout or roll back deliberately.",
            ],
            evidence=[
                "Benchmark results before and after, same tool and parameters",
                "oc get mcp -o wide during rollout ; node reboot timeline",
                "oc debug node/<node> -- chroot /host cat /proc/cmdline   # confirm the change applied",
            ],
            redflag=(
                "Do not change several tuning parameters in one rollout. You will not be able to attribute "
                "the result in either direction."
            ),
            followup="Your change improved latency and increased CPU usage 20%. Ship it or not?",
        ),
        Q(
            q="A latency-sensitive workload is missing its target. How do you investigate?",
            level=SENIOR,
            answer=(
                "I check alignment before I check tuning. Is the pod actually Guaranteed and actually "
                "pinned? Are its CPUs, memory and device on the same NUMA node? Is it sharing cores with "
                "system daemons because reserved cores were undersized? Then I look for interference - "
                "another workload on the node, interrupts landing on the isolated cores, throttling - and "
                "only then at the application itself and its dependencies."
            ),
            analogy=(
                "Before adjusting the engine you check the handbrake is off. Most disappointing performance "
                "results are something not being applied at all."
            ),
            context=(
                "In practice the most common finding is that the configuration people believed was in effect "
                "is not: fractional CPU requests so no pinning, a device on a different NUMA node than the "
                "pinned cores, or a PerformanceProfile that never finished rolling out because the pool is "
                "Degraded. Verifying what is actually true on the node - rather than what the manifest says "
                "- is the step that resolves most of these."
            ),
            steps=[
                "Verify QoS class, pinning and actual CPU assignment on the node.",
                "Verify NUMA alignment of CPUs, memory, huge pages and the device.",
                "Look for interference: co-tenants, interrupts on isolated cores, throttling metrics.",
                "Only then investigate the application and its dependencies, with per-hop measurement.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host cat /var/lib/kubelet/cpu_manager_state",
                "container_cpu_cfs_throttled_seconds_total{pod=\"<pod>\"}",
                "oc debug node/<node> -- chroot /host cat /proc/interrupts | head -20",
            ],
            redflag=(
                "Do not start tuning kernel parameters before verifying the pod is pinned at all. That is "
                "how a week disappears."
            ),
            followup="The pod is Guaranteed but not pinned. Give me two possible reasons.",
        ),
        Q(
            q="How would you design a node pool for HPC or AI workloads?",
            level=ARCHITECT,
            answer=(
                "As a dedicated pool with its own MachineConfigPool, taints so only opted-in workloads land "
                "there, and a PerformanceProfile setting isolated and reserved cores, huge pages per NUMA "
                "node and the topology policy. Hardware chosen for the workload - accelerators and NICs "
                "on the sockets the workload will use - with the device plugins and SR-IOV configuration to "
                "expose them. Then a validation suite that runs after every change so the pool's behaviour "
                "is a known quantity."
            ),
            analogy=(
                "It is a specialist workshop rather than a corner of the general factory floor. Different "
                "tools, different rules, different people allowed in."
            ),
            context=(
                "The dedicated pool is not primarily about performance, it is about change isolation: "
                "kernel arguments, real-time settings and reboot cycles that are appropriate for HPC nodes "
                "would be reckless applied to the whole worker fleet. It also lets you upgrade and validate "
                "the pool independently, which matters because performance-sensitive nodes are exactly where "
                "you want the longest soak time before rolling a change further."
            ),
            steps=[
                "Separate into a dedicated MachineConfigPool with taints and labels for explicit opt-in.",
                "Specify hardware with NUMA topology in mind, including accelerator and NIC placement.",
                "Configure PerformanceProfile, device plugins and SR-IOV, and document the intended "
                "topology.",
                "Build a validation suite - latency, throughput, alignment checks - and run it after every "
                "change.",
            ],
            evidence=[
                "oc get mcp ; oc get nodes -l node-role.kubernetes.io/hpc -o wide",
                "oc get performanceprofile,sriovnetworknodepolicy -o wide",
                "Validation suite results per node after the last change",
            ],
            redflag=(
                "Do not mix HPC and general workloads on the same pool. The tuning that helps one actively "
                "harms the other."
            ),
            followup="How do you stop general workloads landing on your expensive GPU nodes?",
        ),
        Q(
            q="How do you balance performance isolation against cluster utilisation?",
            level=ARCHITECT,
            answer=(
                "By being explicit that isolation costs utilisation and deciding where that trade is worth "
                "it. Pinned cores, reserved huge pages and dedicated pools all reduce how much of the "
                "hardware is usable by anything else, and for a genuinely latency-critical service that is a "
                "reasonable price. For everything else it is waste. So I tier workloads, apply isolation "
                "only to the tier that needs it, and report utilisation per pool so the cost is visible "
                "rather than assumed."
            ),
            analogy=(
                "It is reserved seating in a restaurant. Worth it for the regular who books every Friday; "
                "ruinous if you reserve every table for people who might turn up."
            ),
            context=(
                "The conversation this enables is the useful one: a workload owner asking for dedicated "
                "nodes can be shown what that costs in utilisation terms and asked to justify it with "
                "measured latency requirements. Often the honest answer is that the workload has never been "
                "measured and the request is precautionary - and measuring first resolves it without "
                "spending anything."
            ),
            steps=[
                "Tier workloads by measured latency requirement, not by team preference.",
                "Apply isolation only to the top tier, and document what it costs in usable capacity.",
                "Report utilisation per pool so the cost of isolation is visible to the people requesting "
                "it.",
                "Require measurement before granting isolation, and review allocations as workloads change.",
            ],
            evidence=[
                "Utilisation per node pool: allocatable, requested, used",
                "Latency measurements justifying each isolated workload",
                "Cost per pool, compared against the general worker pool",
            ],
            redflag=(
                "Do not grant dedicated nodes on request without measurement. You will end up with an "
                "expensive, half-idle cluster and no way to argue it back."
            ),
            followup="A team wants dedicated nodes but has never measured their latency. What do you say?",
        ),
        Q(
            q="How do you validate that a performance change actually worked?",
            level=SENIOR,
            answer=(
                "By comparing against a recorded baseline using the same benchmark, the same load pattern "
                "and the same measurement points, and by looking at the distribution rather than an average. "
                "Percentiles matter most - p99 and p99.9 - because latency-sensitive workloads are judged on "
                "their tail. I also check what got worse: CPU cost, utilisation, another workload's "
                "behaviour, or the cluster's capacity for everything else."
            ),
            analogy=(
                "It is a before-and-after photo taken from the same spot in the same light. Anything else is "
                "an impression, not a comparison."
            ),
            context=(
                "The discipline of looking for regressions is what distinguishes this from marketing. A "
                "change that improves p99 latency by 15% while raising CPU consumption by 40% may be a good "
                "trade or a terrible one depending on the cluster's capacity, and the only way to have that "
                "conversation is to have measured both. Recording the result - including the conditions - "
                "also means the next person does not repeat the experiment."
            ),
            steps=[
                "Use the identical benchmark, load and measurement points as the baseline.",
                "Compare percentiles and the full distribution, not averages.",
                "Explicitly check for regressions in CPU, memory, capacity and neighbouring workloads.",
                "Record the result with conditions and conclusions, and keep it with the change record.",
            ],
            evidence=[
                "Baseline and post-change percentile latency, same tool and parameters",
                "Node CPU and memory utilisation before and after",
                "Neighbouring workload SLI over the same window",
            ],
            redflag=(
                "Do not report an average improvement for a latency-sensitive workload. The tail is the "
                "thing users experience."
            ),
            followup="p99 improved but p50 got worse. What would you conclude?",
        ),
    ],
)
