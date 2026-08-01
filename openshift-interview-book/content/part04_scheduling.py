"""Part 4 - Scheduling, resources and capacity."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=4,
    title="Scheduling, resources and capacity",
    subtitle="Where pods go, what they are allowed to consume, and who loses when the node runs out",
    intro=(
        "Scheduling is the part of Kubernetes that most directly shapes reliability, and it is also where "
        "the most expensive misunderstandings live. Requests are not limits. A limit is not a reservation. "
        "Pending is not a bug. Autoscaling does not create capacity that does not exist. Interviewers probe "
        "here because the answers reveal whether you have run a busy cluster or only a demo one: on a quiet "
        "cluster every scheduling decision looks correct, and on a full one every shortcut becomes an "
        "incident."
    ),
    infographics=["scheduling_funnel", "qos_matrix"],
    questions=[
        Q(
            q="How does the Kubernetes scheduler decide where a pod goes?",
            level=FOUNDATION,
            answer=(
                "It runs in two phases. Filtering removes every node that cannot host the pod - not enough "
                "allocatable resources, an untolerated taint, a failed node selector or affinity rule, a "
                "volume that is bound to another zone. Scoring then ranks the survivors using plugins such as "
                "spreading across zones, image locality and how balanced the resulting allocation would be. "
                "The highest scoring node wins and the pod is bound to it by writing nodeName."
            ),
            analogy=(
                "It is seating people in a restaurant. First you exclude tables that are too small, "
                "reserved or in the wrong section. Then you pick the best of what is left - near a window, "
                "away from the kitchen door."
            ),
            context=(
                "The practical payoff is that Pending is never mysterious. The scheduler records exactly why "
                "each node was rejected, in the pod's events, in the form \"3 node(s) had untolerated taint, "
                "2 Insufficient memory\". Reading that line and translating it is a thirty-second diagnosis. "
                "It also explains why scheduling is a point-in-time decision: the scheduler does not move a "
                "pod later just because the cluster changed."
            ),
            steps=[
                "Say the two phases: filter for feasibility, score for preference.",
                "Name a few real filters and a couple of scoring plugins so it is concrete.",
                "Explain binding - the decision is recorded on the pod, and the kubelet acts on it.",
                "Point out that the scheduler never revisits the decision; that is the descheduler's job.",
            ],
            evidence=[
                "oc describe pod <pod> | sed -n '/Events/,$p'",
                "oc get events -n <ns> --field-selector reason=FailedScheduling",
                "oc describe node <node> | sed -n '/Allocated resources/,$p'",
            ],
            redflag=(
                "Do not say the scheduler \"picks a node with space\". Filtering versus scoring is precisely "
                "what is being asked."
            ),
            followup="A pod is Pending with 'Insufficient cpu' on every node. Is adding nodes the right fix?",
        ),
        Q(
            q="Explain requests, limits and QoS classes.",
            level=FOUNDATION,
            answer=(
                "A request is what the scheduler reserves for the pod and it is the only number that "
                "influences placement. A limit is the hard ceiling the kernel enforces at runtime - CPU is "
                "throttled at the limit, memory over the limit gets the container OOM-killed. The "
                "relationship between the two sets the QoS class: equal requests and limits everywhere means "
                "Guaranteed, requests below limits means Burstable, nothing set means BestEffort. QoS then "
                "decides eviction order under node pressure."
            ),
            analogy=(
                "A request is the seat you booked; a limit is how far you may recline. Booking nothing gets "
                "you on the plane only if there is room, and you are the first one bumped."
            ),
            context=(
                "Two symptoms fall directly out of this. Exit code 137 with OOMKilled means the memory limit "
                "was hit - the kernel did it, not Kubernetes, and raising the limit or fixing the leak are "
                "the only real options. An application that is slow while CPU usage looks low is being "
                "throttled against its CPU quota, visible in the throttled seconds metric. Being able to name "
                "which of the two you are looking at, from the metric, is the whole point of the question."
            ),
            steps=[
                "Separate the roles: requests drive scheduling, limits drive runtime enforcement.",
                "Explain the asymmetry - CPU throttles, memory kills.",
                "Derive the three QoS classes and say what each means at eviction time.",
                "Set requests from measured usage percentiles rather than guesses, and revisit them.",
            ],
            evidence=[
                "oc adm top pod -n <ns> --containers",
                "container_cpu_cfs_throttled_seconds_total ; container_memory_working_set_bytes",
                "oc get pod <pod> -o jsonpath='{.status.qosClass}{\"\\n\"}'",
            ],
            redflag=(
                "Do not say limits reserve capacity. That single misunderstanding leads to clusters that are "
                "either wildly overcommitted or half empty."
            ),
            followup="Would you set a CPU limit on a latency-sensitive service? Argue both sides.",
        ),
        Q(
            q="What are taints and tolerations, and what do the three effects do?",
            level=FOUNDATION,
            answer=(
                "A taint is a property on a node that repels pods; a toleration on a pod says it accepts that "
                "taint. NoSchedule means new pods without the toleration will not be placed there. "
                "PreferNoSchedule is a soft version - the scheduler avoids it if it can. NoExecute is the "
                "strong one: it also evicts pods already running that do not tolerate it, optionally after a "
                "grace period set by tolerationSeconds."
            ),
            analogy=(
                "A taint is a Staff Only sign. NoSchedule means new people do not go in. PreferNoSchedule "
                "means please avoid it. NoExecute means everyone without a badge leaves now."
            ),
            context=(
                "Two operational uses dominate. First, dedicating nodes - GPU, infrastructure or "
                "licence-restricted nodes carry a taint so only workloads that explicitly opt in land there. "
                "Second, node failure handling: the node lifecycle controller applies a NoExecute "
                "not-ready taint, and the default toleration of around five minutes is why pods do not move "
                "instantly when a node dies. Tuning that number is a real trade-off between recovery speed "
                "and thrashing during transient network blips."
            ),
            steps=[
                "Define taint and toleration as a repel-and-accept pair, not as a scheduling preference.",
                "Walk the three effects and what each does to new versus existing pods.",
                "Give the dedicated-node use case and the node-failure use case.",
                "Mention that tolerating a taint does not attract a pod - you still need affinity or a "
                "selector for that.",
            ],
            evidence=[
                "oc get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints",
                "oc adm taint nodes <node> workload=gpu:NoSchedule",
                "oc get pod <pod> -o jsonpath='{.spec.tolerations}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not say a toleration makes a pod prefer that node. Tolerations permit; they never "
                "attract."
            ),
            followup="You taint GPU nodes and your monitoring agent disappears from them. Why, and what fixes it?",
        ),
        Q(
            q="What is node affinity?",
            level=FOUNDATION,
            answer=(
                "Node affinity constrains which nodes a pod may run on based on node labels. The required "
                "form is a hard filter - if no node matches, the pod stays Pending. The preferred form is a "
                "scoring hint with a weight, so the scheduler tries to honour it but will place the pod "
                "elsewhere rather than leave it unscheduled. It is the modern, more expressive replacement "
                "for a plain nodeSelector."
            ),
            analogy=(
                "Required affinity is \"I must have a ground-floor room\". Preferred affinity is \"I would "
                "like a sea view\". One of those can leave you sleeping in the lobby."
            ),
            context=(
                "The choice between required and preferred is a genuine availability decision, and "
                "interviewers listen for whether you notice. Required affinity on a label that only three "
                "nodes carry means losing those three nodes takes your service down completely, even though "
                "the cluster has capacity. Preferred affinity degrades instead - the pod lands somewhere less "
                "ideal and keeps serving. Use required only when running elsewhere would be actually wrong, "
                "such as a licence or data residency constraint."
            ),
            steps=[
                "Distinguish required from preferred and state the consequence of each.",
                "Show the label-based matching and why labels must be applied consistently by automation.",
                "Give the availability trade-off: hard constraints reduce the pool you can fail over into.",
                "Mention that node affinity is evaluated at scheduling time only, not continuously.",
            ],
            evidence=[
                "oc get nodes --show-labels",
                "oc get pod <pod> -o jsonpath='{.spec.affinity.nodeAffinity}' | python3 -m json.tool",
                "oc get events -n <ns> --field-selector reason=FailedScheduling",
            ],
            redflag=(
                "Do not use required node affinity for a preference. It converts a capacity shortage into an "
                "outage."
            ),
            followup="How would you place a workload on GPU nodes without hard-pinning it to three machines?",
        ),
        Q(
            q="What are pod affinity and pod anti-affinity?",
            level=FOUNDATION,
            answer=(
                "They place a pod relative to other pods rather than relative to node labels. Pod affinity "
                "attracts - put this cache next to the application that uses it, within the same zone or "
                "node. Anti-affinity repels - keep replicas of the same service apart so a single node or "
                "zone failure cannot take them all. The topologyKey defines what apart means: hostname, zone, "
                "or any node label."
            ),
            analogy=(
                "Affinity is seating a family together. Anti-affinity is not putting all the fire marshals "
                "on the same floor."
            ),
            context=(
                "Anti-affinity is expensive to evaluate at scale, because the scheduler has to compare "
                "against existing pods across the topology domain, and required anti-affinity on a large "
                "deployment can slow scheduling noticeably or leave pods Pending when the domain runs out. "
                "That is exactly why topology spread constraints were introduced, and saying so is a good "
                "signal that you have hit the limit in practice rather than read about the feature."
            ),
            steps=[
                "Define both, and stress that topologyKey is what gives the rule meaning.",
                "Give the standard uses: co-locate for latency, separate for availability.",
                "Note the scheduling cost and the Pending risk of required anti-affinity at scale.",
                "Say when you would switch to topology spread constraints instead.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.affinity.podAntiAffinity}' | python3 -m json.tool",
                "oc get pods -o wide -n <ns> --sort-by=.spec.nodeName",
                "oc get events -n <ns> --field-selector reason=FailedScheduling",
            ],
            redflag=(
                "Do not apply required anti-affinity to a hundred-replica Deployment without checking node "
                "count. You will simply run out of places to put pods."
            ),
            followup="Why might topology spread constraints be a better fit than anti-affinity here?",
        ),
        Q(
            q="What is a topology spread constraint?",
            level=FOUNDATION,
            answer=(
                "It tells the scheduler to distribute matching pods evenly across a topology domain - zones, "
                "nodes, racks - with a maxSkew that bounds how uneven the distribution may become. "
                "whenUnsatisfiable decides what happens if the constraint cannot be met: DoNotSchedule leaves "
                "the pod Pending, ScheduleAnyway places it and accepts the imbalance. It expresses \"spread "
                "these out\" more efficiently and more precisely than anti-affinity."
            ),
            analogy=(
                "It is dealing cards evenly around the table rather than just insisting no two cards touch. "
                "The skew is how many more cards one player may hold before you stop dealing them."
            ),
            context=(
                "This is the mechanism behind genuine zone resilience, and the setting people get wrong is "
                "whenUnsatisfiable. DoNotSchedule with maxSkew of one across three zones sounds strict and "
                "correct, right up until one zone is down for maintenance and new pods refuse to schedule "
                "because spreading them would breach the skew. For most applications ScheduleAnyway plus an "
                "alert on imbalance gives you the availability benefit without the self-inflicted outage."
            ),
            steps=[
                "Define topologyKey, maxSkew and whenUnsatisfiable as the three knobs.",
                "Explain the difference in behaviour between DoNotSchedule and ScheduleAnyway.",
                "Recommend the safer default for most workloads and say why.",
                "Pair it with a PDB and replica minimum, because spread alone does not guarantee capacity.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.topologySpreadConstraints}' | python3 -m json.tool",
                "oc get pods -o wide -n <ns> | awk '{print $7}' | sort | uniq -c",
                "oc get nodes -L topology.kubernetes.io/zone",
            ],
            redflag=(
                "Do not set DoNotSchedule with a tight skew on a critical service without thinking about "
                "zone maintenance. It will refuse to schedule exactly when you need it to."
            ),
            followup="One zone is down. Explain what happens to your spread constraints and your PDB.",
        ),
        Q(
            q="What is a PriorityClass, and how does preemption work?",
            level=FOUNDATION,
            answer=(
                "A PriorityClass assigns a numeric priority to pods. When a high-priority pod cannot be "
                "scheduled, the scheduler may preempt - evict lower-priority pods on a node to make room, "
                "then schedule the high-priority pod there. Preempted pods are terminated gracefully and go "
                "back to Pending, where they compete for capacity again. Priority also influences eviction "
                "ordering under node pressure."
            ),
            analogy=(
                "It is triage in an emergency department. The ambulance case takes the bay; the person "
                "waiting with a sprained wrist goes back to the waiting room, not out of the building."
            ),
            context=(
                "The risk is that priority values get inflated until everything is critical and the mechanism "
                "stops meaning anything. A workable scheme is a small number of published classes with clear "
                "criteria - platform and system components highest, customer-facing services next, batch and "
                "development lowest - assigned by policy rather than by whoever writes the manifest. Without "
                "that governance, priority becomes a way for one team to evict another's pods."
            ),
            steps=[
                "Define priority and preemption, and note that preemption is graceful, not a kill.",
                "Explain that preempted pods return to Pending and may cause a cascade if capacity is tight.",
                "Propose a small, governed set of classes with documented criteria.",
                "Mention preemptionPolicy Never for high-priority pods that should wait rather than evict.",
            ],
            evidence=[
                "oc get priorityclass",
                "oc get events -A --field-selector reason=Preempted --sort-by=.lastTimestamp",
                "oc get pod <pod> -o jsonpath='{.spec.priorityClassName} {.spec.priority}{\"\\n\"}'",
            ],
            redflag=(
                "Do not let teams set their own priority values. Everything becomes the highest priority and "
                "you are back where you started, with extra churn."
            ),
            followup="Preemption is causing repeated evictions in one namespace. How do you stabilise it?",
        ),
        Q(
            q="What is a PodDisruptionBudget, and what does it not protect against?",
            level=INTERMEDIATE,
            answer=(
                "A PDB limits voluntary disruptions - drains, evictions, MCO node updates - by declaring "
                "either minAvailable or maxUnavailable for pods matching a selector. The eviction API "
                "respects it and refuses evictions that would breach it. What it does not protect against is "
                "involuntary disruption: a node crashing, a kernel panic, a hypervisor failure or a zone "
                "outage ignore PDBs entirely, because nothing asked permission."
            ),
            analogy=(
                "It is a rota rule saying at least two staff must be on the floor. It stops the manager "
                "scheduling everyone off at once; it does not stop three people catching flu."
            ),
            context=(
                "PDBs are where availability meets maintainability, and they cut both ways. Too permissive "
                "and a node drain takes your service below capacity. Too strict - minAvailable equal to the "
                "replica count, or a PDB on a single-replica Deployment - and the drain can never succeed, "
                "which stalls MachineConfig rollout and therefore stalls cluster upgrades. That stall is one "
                "of the most common real-world upgrade blockers."
            ),
            steps=[
                "Define voluntary versus involuntary disruption and say which one a PDB governs.",
                "Explain how minAvailable and maxUnavailable interact with replica count.",
                "Give the blocking failure mode - a PDB that can never be satisfied stalls drains and "
                "upgrades.",
                "Pair PDBs with adequate replicas and spread, and test them by actually draining a node.",
            ],
            evidence=[
                "oc get pdb -A -o wide",
                "oc adm drain <node> --ignore-daemonsets --delete-emptydir-data --dry-run=server",
                "oc get events -A --field-selector reason=EvictionBlocked",
            ],
            redflag=(
                "Do not claim a PDB protects against node failure. It is the classic senior trap and it is "
                "asked deliberately."
            ),
            followup="A drain has been blocked for thirty minutes by a PDB. What are your options, in order?",
        ),
        Q(
            q="How do ResourceQuota and LimitRange work together?",
            level=INTERMEDIATE,
            answer=(
                "ResourceQuota caps the total a namespace may consume - aggregate CPU and memory requests and "
                "limits, storage, and object counts. LimitRange operates per object, setting defaults and "
                "minimum and maximum values for individual containers. They are complementary: LimitRange "
                "makes sure every pod has sensible requests, and ResourceQuota makes sure the namespace as a "
                "whole cannot exceed its share."
            ),
            analogy=(
                "ResourceQuota is the household's monthly electricity budget. LimitRange is the rule that no "
                "single appliance may draw more than a certain wattage, and that unlabelled appliances get a "
                "default rating."
            ),
            context=(
                "There is an interaction that surprises people: once a ResourceQuota that limits requests "
                "exists, every pod in the namespace must specify requests, or creation is rejected. Without a "
                "LimitRange supplying defaults, that breaks every existing manifest that omitted them. So the "
                "correct rollout order is LimitRange first, then quota - and doing it in the wrong order in "
                "production is a memorable way to learn the lesson."
            ),
            steps=[
                "Separate the scopes: namespace aggregate versus per-container.",
                "State the rejection behaviour when quota exists and requests are missing.",
                "Roll out LimitRange first so defaults exist, then apply the quota.",
                "Monitor quota utilisation and alert before it is exhausted, because exhaustion looks like a "
                "scheduling bug to the team.",
            ],
            evidence=[
                "oc describe quota -n <ns>",
                "oc get limitrange -n <ns> -o yaml",
                "kube_resourcequota{type=\"used\"} / kube_resourcequota{type=\"hard\"}",
            ],
            redflag=(
                "Do not apply a quota to a live namespace without a LimitRange in place. Every deployment "
                "without explicit requests will start failing immediately."
            ),
            followup="A team says their deployments started failing after you enabled quota. What happened?",
        ),
        Q(
            q="Why might a HorizontalPodAutoscaler fail to scale?",
            level=INTERMEDIATE,
            answer=(
                "Usually one of five things. The metric is unavailable - CPU-based HPA needs resource "
                "requests set, and custom metrics need an adapter. The metric never crosses the target. There "
                "is no cluster capacity, so new pods go Pending and the HPA looks stuck. Stabilisation "
                "windows and scaling policies are damping the change deliberately. Or something else is "
                "writing the replica count - a GitOps controller reconciling replicas will fight the HPA "
                "forever."
            ),
            analogy=(
                "It is a thermostat that will not turn the heating up. Either it cannot read the temperature, "
                "the room is not actually cold, the boiler has no fuel, it is waiting out its cycle, or "
                "someone else keeps turning the dial back."
            ),
            context=(
                "The GitOps conflict is the one that produces the most confusing incident. Argo CD sees "
                "replicas: 3 in Git, the HPA sets 8, Argo reverts to 3, the HPA scales up again, and the "
                "service oscillates under load while both systems believe they are correct. The fix is to "
                "remove replicas from the tracked manifest or tell the GitOps tool to ignore that field - "
                "and knowing that specific interaction is a strong practical signal."
            ),
            steps=[
                "Check the HPA's own status conditions - they name the reason directly.",
                "Verify metrics are available and that resource requests exist for CPU-based targets.",
                "Look for Pending pods, which means the constraint is cluster capacity, not the HPA.",
                "Check for a competing writer of replicas, especially a GitOps controller, and resolve "
                "ownership of the field.",
            ],
            evidence=[
                "oc describe hpa <name> | sed -n '/Conditions/,$p'",
                "oc get --raw /apis/metrics.k8s.io/v1beta1/namespaces/<ns>/pods | head -c 400",
                "oc get pods -n <ns> --field-selector status.phase=Pending",
            ],
            redflag=(
                "Do not conclude \"the HPA is broken\" without reading its conditions. They usually contain "
                "the literal answer."
            ),
            followup="The HPA and Argo CD are fighting over replica count. How do you resolve it properly?",
        ),
        Q(
            q="When do you use the ClusterAutoscaler versus an HPA?",
            level=INTERMEDIATE,
            answer=(
                "They solve different shortages and you usually need both. The HPA adds pod replicas when a "
                "workload metric rises. The ClusterAutoscaler adds nodes when pods are Pending because no "
                "node can fit them, and removes underutilised nodes when their pods can be placed elsewhere. "
                "The HPA is useless without capacity, and the ClusterAutoscaler is useless if nothing is "
                "asking for more pods."
            ),
            analogy=(
                "The HPA hires more staff for the shift. The ClusterAutoscaler opens another floor of the "
                "building. Hiring twenty people into a room with ten desks helps nobody."
            ),
            context=(
                "Scale-down is where the real operational detail lives. The autoscaler will not remove a node "
                "if it hosts pods that cannot be rescheduled - pods without a controller, pods with strict "
                "PDBs, pods using local storage, or pods in namespaces excluded by annotation. That is why "
                "clusters end up paying for near-empty nodes, and being able to name those blockers is a "
                "strong practical signal. Scale-up latency also matters: node provisioning takes minutes, so "
                "burst-sensitive services need headroom or over-provisioning pods rather than pure "
                "autoscaling."
            ),
            steps=[
                "Separate the two axes: replicas versus nodes.",
                "Explain the trigger for each - workload metric versus unschedulable pods.",
                "Name the common scale-down blockers, because that is where money is wasted.",
                "Address scale-up latency with headroom or low-priority placeholder pods for bursty "
                "workloads.",
            ],
            evidence=[
                "oc get clusterautoscaler,machineautoscaler -A",
                "oc -n openshift-machine-api logs deploy/cluster-autoscaler-default --tail=100",
                "oc get pods -A --field-selector status.phase=Pending -o wide",
            ],
            redflag=(
                "Do not present autoscaling as a substitute for capacity planning. It changes how you buy "
                "capacity, not whether you need to think about it."
            ),
            followup="Nodes never scale down even at 20% utilisation. Give me three likely causes.",
        ),
        Q(
            q="What problem does the descheduler solve?",
            level=INTERMEDIATE,
            answer=(
                "The scheduler places a pod once and never revisits it, so over time a cluster drifts: nodes "
                "added after a rollout stay empty, pods violate affinity rules that were introduced later, "
                "and load becomes lumpy. The descheduler periodically evicts pods that now sit badly "
                "according to configured strategies - duplicates on one node, low node utilisation, violated "
                "topology constraints - and lets the scheduler place them again."
            ),
            analogy=(
                "It is rebalancing an investment portfolio. Nothing was wrong when you bought it; drift is "
                "just what time does to a fixed allocation."
            ),
            context=(
                "The important caveat is that the descheduler evicts, it does not place. Eviction respects "
                "PDBs and priority, but if the cluster is genuinely full the evicted pod may come back to the "
                "same node or sit Pending - so an aggressive configuration on a tight cluster produces churn "
                "rather than balance. Start with conservative strategies, run it during quiet periods, and "
                "watch eviction counts before widening its remit."
            ),
            steps=[
                "Explain the drift problem the scheduler cannot solve by design.",
                "Name a couple of concrete strategies and what each one is for.",
                "State clearly that it evicts rather than reschedules, and what that implies on a full "
                "cluster.",
                "Introduce it conservatively, respect PDBs, and monitor eviction rate as a safety metric.",
            ],
            evidence=[
                "oc get kubedescheduler cluster -n openshift-kube-descheduler-operator -o yaml",
                "oc get events -A --field-selector reason=Evicted --sort-by=.lastTimestamp | tail -20",
                "oc get pods -o wide -A | awk '{print $8}' | sort | uniq -c | sort -rn | head",
            ],
            redflag=(
                "Do not enable aggressive descheduling on a cluster that is already near capacity. You will "
                "trade imbalance for continuous churn."
            ),
            followup="After enabling the descheduler, eviction counts spiked. What would you change?",
        ),
        Q(
            q="A pod has been Pending for ten minutes. Walk me through the diagnosis.",
            level=SENIOR,
            answer=(
                "I start with impact - is this one pod or a whole service - then read the FailedScheduling "
                "event, because it states the reason per node. From there it is a short decision tree: "
                "insufficient resources points at capacity or oversized requests; untolerated taints points "
                "at node dedication; node affinity or selector mismatch points at labels; volume node "
                "affinity conflict points at a PV bound to a different zone; and no events at all points at a "
                "scheduler or admission problem rather than a placement one."
            ),
            analogy=(
                "The rejection letter tells you why. You do not need to guess whether it was your grades or "
                "your postcode - it is written at the bottom of the page."
            ),
            context=(
                "The distinguishing senior move is checking whether the request is realistic before adding "
                "capacity. A pod asking for 16 CPUs on a cluster of 8-core nodes will be Pending forever and "
                "no amount of scaling fixes it. Equally, a PVC bound in zone A pins the pod to zone A, so a "
                "cluster with plenty of capacity in zones B and C still cannot place it. Both are common and "
                "both look like capacity problems until you read the event."
            ),
            steps=[
                "State impact and scope first - one pod, one Deployment, or cluster-wide Pending.",
                "Read the FailedScheduling event verbatim and translate each clause.",
                "Sanity-check the request against the largest allocatable node before considering capacity.",
                "Check zone-bound volumes and node labels, then take the smallest fix: adjust requests, "
                "relax a constraint, or add capacity deliberately.",
            ],
            evidence=[
                "oc describe pod <pod> | sed -n '/Events/,$p'",
                "oc describe node <node> | sed -n '/Allocated resources/,$p'",
                "oc get pv <pv> -o jsonpath='{.spec.nodeAffinity}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not add nodes as a reflex. If the request exceeds any single node's allocatable capacity, "
                "more nodes change nothing."
            ),
            followup="The event says 'volume node affinity conflict'. Explain what happened.",
        ),
        Q(
            q="What are the considerations for the Vertical Pod Autoscaler?",
            level=SENIOR,
            answer=(
                "VPA recommends and can apply right-sized requests based on observed usage, which is "
                "genuinely useful because most requests are guesses that were never revisited. The catch is "
                "that changing a pod's resources requires recreating it, so applying mode causes restarts, "
                "and VPA in applying mode conflicts with an HPA on the same resource metric. In practice I "
                "run VPA in recommendation mode, feed the numbers into a right-sizing review, and change "
                "requests through Git."
            ),
            analogy=(
                "It is a tailor measuring you accurately. Very useful - but you do not want the alterations "
                "happening while you are wearing the suit in a meeting."
            ),
            context=(
                "Recommendation mode solves a real and expensive problem: clusters routinely run at low "
                "actual utilisation while appearing full, because requests are two or three times real usage. "
                "Feeding VPA recommendations into a quarterly right-sizing exercise typically reclaims "
                "meaningful capacity with no risk. Turning on applying mode without understanding the restart "
                "behaviour is how you get a surprise rolling restart of production at 2pm."
            ),
            steps=[
                "Explain what VPA observes and what it produces.",
                "State the restart consequence of applying mode and the HPA conflict on the same metric.",
                "Recommend recommendation mode plus a human-reviewed change through Git.",
                "Quantify the benefit - compare requested versus actually used resources cluster-wide.",
            ],
            evidence=[
                "oc get vpa -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,MODE:.spec.updatePolicy.updateMode",
                "oc describe vpa <name> | sed -n '/Recommendation/,$p'",
                "sum(kube_pod_container_resource_requests{resource=\"cpu\"}) vs sum(rate(container_cpu_usage_seconds_total[1h]))",
            ],
            redflag=(
                "Do not run VPA in applying mode alongside an HPA on CPU. They will fight, and the pods will "
                "restart while they do."
            ),
            followup="Cluster CPU requests are at 85% but actual usage is 25%. What do you do about it?",
        ),
        Q(
            q="How do you do capacity planning for an OpenShift cluster?",
            level=SENIOR,
            answer=(
                "I plan against four numbers, not one. Allocatable capacity after system and platform "
                "reservations. Committed capacity, meaning the sum of requests. Actual utilisation. And "
                "failure headroom - the capacity that must stay free so that losing a node, or draining one "
                "for an upgrade, does not cause evictions. Then I project growth from real trend data and buy "
                "before the headroom is consumed, rather than reacting to the first Pending pod."
            ),
            analogy=(
                "It is planning a car park. Total spaces, spaces already allocated to permit holders, spaces "
                "actually occupied at peak, and the row you keep clear for the fire engine."
            ),
            context=(
                "The distinction between committed and used is where most clusters are mismanaged. A cluster "
                "can be 90% committed and 25% used, which means it refuses new work while sitting nearly "
                "idle - the answer there is right-sizing requests, not buying nodes. The reverse, high "
                "utilisation with low commitment, means requests are too low and you are one traffic spike "
                "away from evictions. Naming which of those you are in, with numbers, is the answer."
            ),
            steps=[
                "Measure all four numbers per node pool, not as a cluster average.",
                "Define failure headroom explicitly: N+1 node loss plus one node drained for maintenance.",
                "Diagnose the gap between committed and used, and fix requests before buying capacity.",
                "Forecast from trend, set a threshold that triggers procurement, and review it monthly.",
            ],
            evidence=[
                "oc describe node | grep -A6 'Allocated resources'",
                "sum by (node) (kube_pod_container_resource_requests{resource=\"memory\"})",
                "oc adm top nodes ; oc get machineset -A -o wide",
            ],
            redflag=(
                "Do not plan capacity from average utilisation alone. Averages hide both the peak that "
                "evicts you and the commitment that blocks scheduling."
            ),
            followup="Committed CPU is 90%, used is 25%. Do you buy nodes? Defend your answer.",
        ),
        Q(
            q="How would you set overcommit policy for a shared cluster?",
            level=ARCHITECT,
            answer=(
                "I set it per workload class rather than cluster-wide. Latency-sensitive and regulated "
                "workloads get Guaranteed QoS on dedicated or lightly overcommitted node pools. General "
                "services run Burstable with requests set from measured p95 and limits at a defensible "
                "multiple. Batch and development run on heavily overcommitted pools with low priority, so "
                "they absorb the risk of the overcommit. The policy is published, enforced by LimitRange and "
                "admission, and reviewed against actual eviction and throttling data."
            ),
            analogy=(
                "Airlines overbook economy, not the flight deck. The policy is deliberate, differentiated, "
                "and based on measured no-show rates rather than optimism."
            ),
            context=(
                "The reason to make this explicit is that overcommit is happening whether or not you decided "
                "it. Without a policy, each team picks requests independently and the cluster's real "
                "overcommit ratio is an accident. With a policy, you can answer the two questions that "
                "matter to a business: what does this cluster cost per workload class, and what is the "
                "probability that a spike causes an eviction. Reviewing eviction and throttling metrics "
                "closes the loop."
            ),
            steps=[
                "Define workload classes and the QoS and node pool each is entitled to.",
                "Set requests from measured percentiles and document the limit multiple per class.",
                "Enforce with LimitRange, quota, priority classes and node pool separation.",
                "Review quarterly against eviction counts, throttling rates and cost per class, and adjust "
                "the ratios with evidence.",
            ],
            evidence=[
                "kube_pod_container_resource_requests vs container_memory_working_set_bytes by workload class",
                "oc get events -A --field-selector reason=Evicted | wc -l",
                "container_cpu_cfs_throttled_periods_total / container_cpu_cfs_periods_total",
            ],
            redflag=(
                "Do not apply one overcommit ratio to the whole cluster. It will be too risky for the "
                "critical workloads and too wasteful for the batch ones."
            ),
            followup="Finance wants 30% cost reduction. Which lever do you pull first, and what is the risk?",
        ),
    ],
)
