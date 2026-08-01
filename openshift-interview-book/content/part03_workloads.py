"""Part 3 - Workload objects and the application contract."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=3,
    title="Workloads, controllers and the application contract",
    subtitle="Choosing the right object, and the behaviours that make a workload survivable",
    intro=(
        "Workload questions look easy and are scored hard. Nobody is impressed that you know what a "
        "Deployment is; they want to know which object you would choose for a given requirement, what "
        "happens to it during a node drain, and what contract you expect application teams to meet before "
        "you will call something production ready. That contract - probes, graceful shutdown, resource "
        "requests, replica minimums - is the difference between a platform that survives routine maintenance "
        "and one where every upgrade becomes an incident."
    ),
    infographics=["workload_chooser"],
    questions=[
        Q(
            q="What is a ReplicaSet?",
            level=FOUNDATION,
            answer=(
                "A ReplicaSet keeps a specified number of identical pods running. It watches pods matching "
                "its selector, and if there are too few it creates more, if too many it deletes some. You "
                "rarely create one directly - a Deployment creates and owns ReplicaSets on your behalf, one "
                "per revision, which is how rollbacks work."
            ),
            analogy=(
                "It is a shift manager who only counts heads. Three people should be on the floor; someone "
                "leaves, so someone is called in. No judgement about who, just the count."
            ),
            context=(
                "The reason it matters operationally is that the ReplicaSet is where rollout failures become "
                "visible. If pods are not appearing, the ReplicaSet's events and conditions will tell you "
                "why - quota exceeded, a failing admission webhook, an image that cannot be pulled - long "
                "before you find it by staring at the Deployment. Old ReplicaSets sticking around with zero "
                "replicas is normal and deliberate: they are the previous revisions you can roll back to."
            ),
            steps=[
                "Define it as a count-keeping controller driven by a label selector.",
                "Explain its relationship to the Deployment: one ReplicaSet per revision.",
                "Say why the old zero-replica ReplicaSets exist - rollback history.",
                "Note the diagnostic value: ReplicaSet events explain why pods are not being created.",
            ],
            evidence=[
                "oc get rs -n <ns> --sort-by=.metadata.creationTimestamp",
                "oc describe rs <rs> | sed -n '/Events/,$p'",
                "oc get rs <rs> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not say you would manage ReplicaSets directly. It suggests you have not used rollout "
                "history or rollbacks."
            ),
            followup="Your Deployment says 3 desired but 0 available, and no pods exist. Where do you look?",
        ),
        Q(
            q="What is a Deployment, and how does a rolling update actually work?",
            level=FOUNDATION,
            answer=(
                "A Deployment manages stateless replicas through ReplicaSets and gives you declarative "
                "updates. On a change it creates a new ReplicaSet and shifts replicas across gradually, "
                "governed by maxSurge and maxUnavailable: maxSurge is how many extra pods it may create above "
                "the desired count, maxUnavailable is how many it may take away. A new pod only counts as "
                "available once its readiness probe passes, which is what stops a broken image from replacing "
                "a working one."
            ),
            analogy=(
                "It is replacing the tyres on a moving lorry, one at a time. You need at least one spare "
                "position free, and you do not remove the next tyre until the new one is proven to grip."
            ),
            context=(
                "Two production consequences follow. First, if maxSurge is zero and maxUnavailable is zero, "
                "the rollout deadlocks - it cannot add or remove anything. Second, if readiness is defined "
                "badly, for example returning healthy before dependencies are reachable, the rollout happily "
                "replaces every working pod with a broken one and the Deployment reports success. Rollout "
                "safety is entirely a function of honest readiness probes."
            ),
            steps=[
                "Describe the ReplicaSet swap and the two knobs that govern its pace.",
                "Stress that readiness gates availability, so probes control rollout safety.",
                "Mention progressDeadlineSeconds - the rollout gives up and reports failure rather than "
                "hanging forever.",
                "State the rollback path and that it works by scaling the previous ReplicaSet back up.",
            ],
            evidence=[
                "oc rollout status deploy/<name> --timeout=5m",
                "oc rollout history deploy/<name> ; oc rollout undo deploy/<name>",
                "oc get deploy <name> -o jsonpath='{.spec.strategy.rollingUpdate}{\"\\n\"}'",
            ],
            redflag=(
                "Do not describe a rolling update as \"it just restarts the pods\". The surge and readiness "
                "mechanics are the whole answer."
            ),
            followup="Your rollout has been Progressing for twenty minutes with no new ready pods. What now?",
        ),
        Q(
            q="What is a StatefulSet and when do you need one?",
            level=FOUNDATION,
            answer=(
                "A StatefulSet gives pods stable identity: predictable ordinal names, stable DNS through a "
                "headless Service, and a persistent volume per pod that follows that identity across "
                "restarts. It also creates and deletes pods in order by default. You need it when the "
                "workload cares which member it is - databases, message brokers, quorum-based systems - "
                "rather than treating replicas as interchangeable."
            ),
            analogy=(
                "A Deployment is a pool of taxi drivers; any one will do. A StatefulSet is a set of numbered "
                "hotel rooms - room three always has room three's safe and room three's key."
            ),
            context=(
                "The behaviour that catches people out is scale-down: the PersistentVolumeClaims are "
                "deliberately left behind, because deleting a database replica's data on a scale-down would "
                "be catastrophic. So shrinking a StatefulSet leaves orphaned PVCs consuming quota until "
                "someone cleans them up intentionally. The other one is ordered rollout - a StatefulSet "
                "update that stalls on pod zero will never reach pod one, which looks like a hang."
            ),
            steps=[
                "Name the three guarantees: stable identity, stable storage, ordered operations.",
                "Say when you need them - quorum members, primary/replica databases, brokers with partitions.",
                "Call out the PVC retention behaviour on scale-down, and why it is intentional.",
                "Mention that ordered updates mean one stuck pod blocks the rest, and where to see that.",
            ],
            evidence=[
                "oc get sts <name> -o wide ; oc get pvc -n <ns>",
                "oc get sts <name> -o jsonpath='{.spec.updateStrategy}{\"\\n\"}'",
                "oc describe pod <name>-0 | sed -n '/Events/,$p'",
            ],
            redflag=(
                "Do not say a StatefulSet is \"a Deployment with storage\". Identity and ordering are the "
                "point, not the volume."
            ),
            followup="You scale a StatefulSet from five to three. What is left behind and why?",
        ),
        Q(
            q="What is a DaemonSet?",
            level=FOUNDATION,
            answer=(
                "A DaemonSet runs one pod on every node that matches its selector, and it automatically "
                "places a pod on any node that joins later. It is the pattern for node-level agents: log "
                "collectors, monitoring exporters, CNI and CSI components, security agents. Because "
                "infrastructure agents need to run even on nodes that are tainted for dedicated workloads, "
                "DaemonSets usually carry broad tolerations."
            ),
            analogy=(
                "It is the fire extinguisher rule - one on every floor, and when a new floor is built, one "
                "appears there too without anyone filing a request."
            ),
            context=(
                "The interview angle is usually placement and upgrade behaviour. If your logging agent is "
                "missing from GPU nodes, the cause is nearly always a missing toleration for the taint that "
                "protects those nodes. And during node maintenance, DaemonSet pods are not evicted by a "
                "normal drain - they are ignored - which is why a drain can succeed while a node-level agent "
                "is still running."
            ),
            steps=[
                "Define it as one pod per matching node, including future nodes.",
                "Give the canonical use cases so it is clearly infrastructure, not application, workload.",
                "Explain the taint and toleration interaction, which is the usual reason one is missing.",
                "Note drain behaviour: DaemonSet pods are skipped, which surprises people during maintenance.",
            ],
            evidence=[
                "oc get ds -A -o wide",
                "oc get ds <name> -o jsonpath='{.spec.template.spec.tolerations}' | python3 -m json.tool",
                "oc get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints",
            ],
            redflag=(
                "Do not use a DaemonSet to get \"one replica per node\" for an application. That is a "
                "scheduling requirement, and topology spread constraints are the right tool."
            ),
            followup="Your log collector is missing on three nodes. Diagnose it.",
        ),
        Q(
            q="What are Jobs and CronJobs, and what goes wrong with them?",
            level=FOUNDATION,
            answer=(
                "A Job runs pods until a specified number complete successfully, retrying failures up to "
                "backoffLimit. A CronJob creates Jobs on a schedule. What goes wrong is usually "
                "accumulation and overlap: without ttlSecondsAfterFinished, completed Jobs and their pods "
                "pile up and pressure etcd, and without a concurrencyPolicy a slow run overlaps the next "
                "trigger and you get two copies doing the same work."
            ),
            analogy=(
                "A Job is a task with a tick box. A CronJob is a recurring calendar reminder. If nobody "
                "clears finished tasks and the reminder fires while you are still working, your desk "
                "disappears under duplicates."
            ),
            context=(
                "These are a real source of cluster-level pain, not just application annoyance. Thousands of "
                "completed Job objects are thousands of etcd records and a slow LIST for anything that "
                "enumerates pods. And overlapping runs against a shared database are the classic cause of a "
                "batch job that works for months and then corrupts data the first time it runs long. Setting "
                "TTLs and concurrencyPolicy in your golden path template prevents both by default."
            ),
            steps=[
                "Define completion semantics: completions, parallelism, backoffLimit.",
                "Set ttlSecondsAfterFinished so finished Jobs clean themselves up.",
                "Choose a concurrencyPolicy deliberately - Forbid for anything that mutates shared state.",
                "Add startingDeadlineSeconds and alert on missed schedules rather than discovering them "
                "monthly.",
            ],
            evidence=[
                "oc get jobs -n <ns> --sort-by=.status.startTime | tail",
                "oc get cronjob <name> -o jsonpath='{.spec.concurrencyPolicy} {.spec.startingDeadlineSeconds}{\"\\n\"}'",
                "oc get pods -n <ns> --field-selector status.phase=Succeeded | wc -l",
            ],
            redflag=(
                "Do not leave concurrencyPolicy at its default for a job that writes to a database, and then "
                "call the resulting corruption an application bug."
            ),
            followup="A nightly CronJob occasionally runs twice. How do you prove it and how do you fix it?",
        ),
        Q(
            q="What is a Namespace and what does it actually isolate?",
            level=FOUNDATION,
            answer=(
                "A namespace is a scope for names, RBAC, quotas and network policy. It isolates API objects "
                "and gives you a boundary for permissions, resource limits and default network rules. It "
                "does not isolate the kernel, the node, or the network by default - pods in different "
                "namespaces can reach each other unless a NetworkPolicy says otherwise, and they share the "
                "same nodes and the same kernel."
            ),
            analogy=(
                "It is a floor in an office building, not a separate building. Different teams, different "
                "door codes, different budgets - same air conditioning, same fire risk."
            ),
            context=(
                "This is the foundation of every multi-tenancy question. Soft tenancy - namespaces plus RBAC, "
                "quota, LimitRange and default-deny NetworkPolicy - is right for teams inside one "
                "organisation. Hard tenancy, where you genuinely cannot trust the workload, needs a stronger "
                "boundary: dedicated node pools at minimum, and often separate clusters. Being clear about "
                "which one a namespace gives you is the difference between a confident answer and a "
                "hand-wave."
            ),
            steps=[
                "List what it scopes: names, RBAC, quota, LimitRange, NetworkPolicy, some admission behaviour.",
                "State plainly what it does not isolate: kernel, node resources, network by default.",
                "Describe the standard hardening set applied at namespace creation.",
                "Say when you would escalate from soft to hard tenancy, and what that costs.",
            ],
            evidence=[
                "oc get resourcequota,limitrange -n <ns>",
                "oc get networkpolicy -n <ns>",
                "oc auth can-i --list -n <ns> --as=system:serviceaccount:<ns>:default",
            ],
            redflag=(
                "Do not claim namespaces provide security isolation on their own. Without NetworkPolicy they "
                "do not even isolate traffic."
            ),
            followup="What exactly would you apply to every new namespace, automatically?",
        ),
        Q(
            q="What is a ServiceAccount and how do pods use it?",
            level=FOUNDATION,
            answer=(
                "A ServiceAccount is the identity a pod uses to talk to the API server. Every pod gets one - "
                "the namespace's default if you do not specify - and receives a short-lived, audience-bound "
                "projected token. RBAC is then granted to that ServiceAccount rather than to a person, and "
                "SCC is also matched against it, so the ServiceAccount determines both what API calls the pod "
                "can make and what the pod is allowed to be."
            ),
            analogy=(
                "It is the contractor's site pass rather than a personal one. It says which areas this job "
                "may enter, it expires, and it does not belong to any individual."
            ),
            context=(
                "The habit that matters is one ServiceAccount per workload with only the permissions that "
                "workload needs. The anti-pattern is everything running as default with a cluster-admin "
                "binding somewhere in its history, which means a single compromised pod inherits the keys to "
                "the cluster. Modern tokens are projected, time-limited and audience-scoped, so a leaked "
                "token is far less useful than the old permanent secrets - as long as you are not still "
                "creating long-lived token secrets by hand."
            ),
            steps=[
                "Define it as workload identity, distinct from user identity.",
                "Explain projected, short-lived, audience-bound tokens and why that is better than static "
                "secrets.",
                "Say that both RBAC and SCC bind to it, so it controls capability and permission together.",
                "Give the practice: one ServiceAccount per workload, least privilege, never reuse default for "
                "anything privileged.",
            ],
            evidence=[
                "oc get sa -n <ns> ; oc describe sa <name> -n <ns>",
                "oc auth can-i --list --as=system:serviceaccount:<ns>:<sa>",
                "oc get rolebinding,clusterrolebinding -A -o wide | grep <sa>",
            ],
            redflag=(
                "Do not run workloads as the default ServiceAccount with elevated permissions. It is the "
                "single most common finding in a cluster security review."
            ),
            followup="How would you find every ServiceAccount in the cluster with cluster-admin?",
        ),
        Q(
            q="When would you use a Deployment rather than a DeploymentConfig?",
            level=INTERMEDIATE,
            answer=(
                "Deployment is the Kubernetes-native, portable choice and it is what I use by default. "
                "DeploymentConfig is the older OpenShift-specific object with features Deployments did not "
                "originally have - image change triggers, config change triggers, and lifecycle hooks. It is "
                "deprecated, so new work should use Deployments, and the OpenShift-specific behaviours are "
                "replaced by pipelines, GitOps or explicit init containers."
            ),
            analogy=(
                "It is the difference between a manufacturer's proprietary charging cable and USB-C. The old "
                "one still works on your device; you would not design a new product around it."
            ),
            context=(
                "The interesting part of this question is what you do about the lost features. Image change "
                "triggers were genuinely convenient, and the modern replacement is either a pipeline that "
                "updates the image digest in Git, or an image updater controller. Lifecycle hooks become "
                "init containers or Jobs. Saying that out loud shows you understand the migration rather "
                "than just knowing which object is newer."
            ),
            steps=[
                "State the default clearly: Deployment for anything new.",
                "Name what DeploymentConfig gave you that is not native - triggers and hooks.",
                "Give the modern replacement for each of those, so migration is concrete.",
                "Mention portability: Deployments move between Kubernetes distributions unchanged.",
            ],
            evidence=[
                "oc get dc -A   # anything still here is migration backlog",
                "oc get deploy <name> -o jsonpath='{.spec.template.spec.containers[0].image}{\"\\n\"}'",
                "oc rollout status deploy/<name>",
            ],
            redflag=(
                "Do not recommend DeploymentConfig for new applications. It signals that your OpenShift "
                "knowledge stopped several releases ago."
            ),
            followup="A team relies on image change triggers. How do you migrate them?",
        ),
        Q(
            q="Why does a StatefulSet usually need a headless Service?",
            level=INTERMEDIATE,
            answer=(
                "Because clients of a stateful system need to reach a specific member, not a random one. A "
                "headless Service - clusterIP set to None - makes DNS return the individual pod addresses "
                "instead of a single virtual IP, and combined with the StatefulSet's stable ordinal names "
                "that gives every member a predictable DNS name. Cluster members use those names to find each "
                "other for replication and quorum."
            ),
            analogy=(
                "A normal Service is a call centre number - you get whoever is free. A headless Service is "
                "the internal directory, where you can dial the specific person you need."
            ),
            context=(
                "This is why a database StatefulSet that appears healthy can still fail to form a cluster: "
                "the pods are running, but if serviceName is wrong or the headless Service is missing, "
                "members cannot resolve each other and each one sits waiting to join a cluster that never "
                "forms. The symptom is peer resolution errors in the application logs, not anything visible "
                "in pod status."
            ),
            steps=[
                "Explain what headless means: no ClusterIP, DNS returns pod records.",
                "Connect it to stable ordinal names giving predictable per-member DNS.",
                "Give the failure symptom - members cannot discover peers, cluster never forms.",
                "Check serviceName on the StatefulSet matches the headless Service's name.",
            ],
            evidence=[
                "oc get svc <name> -o jsonpath='{.spec.clusterIP}{\"\\n\"}'   # expect None",
                "oc exec <pod> -- getent hosts <name>-0.<svc>.<ns>.svc.cluster.local",
                "oc get sts <name> -o jsonpath='{.spec.serviceName}{\"\\n\"}'",
            ],
            redflag=(
                "Do not suggest putting a load balancer in front of database replicas that need per-member "
                "addressing. It will work until it very badly does not."
            ),
            followup="Pods are Running but the cluster never forms. Where do you start?",
        ),
        Q(
            q="How should startup, readiness and liveness probes be designed?",
            level=INTERMEDIATE,
            answer=(
                "Startup probes cover slow initialisation so the liveness probe does not kill a container "
                "that is legitimately still booting. Readiness gates traffic - a pod that is not ready is "
                "removed from the EndpointSlice but left running. Liveness restarts a container that is "
                "genuinely wedged. The rule I apply is that readiness may depend on downstream dependencies, "
                "liveness must not, because a shared dependency failure would otherwise restart every pod in "
                "the fleet simultaneously."
            ),
            analogy=(
                "Readiness is a shop turning its Open sign around. Liveness is the fire alarm. You flip the "
                "sign often; you do not evacuate the building because the supplier is late."
            ),
            context=(
                "Badly designed probes cause more self-inflicted outages than almost anything else. A "
                "liveness probe that checks a database connection turns a slow database into a cluster-wide "
                "restart storm, which adds load and makes the database slower. A readiness probe that is too "
                "shallow lets a broken pod take traffic and turns a safe rolling update into an outage. "
                "Timeouts matter too: a probe timeout shorter than the endpoint's real latency under load "
                "produces restarts that only happen at peak."
            ),
            steps=[
                "Assign each probe its job: startup for boot time, readiness for traffic, liveness for "
                "deadlock.",
                "Keep liveness local and cheap - no downstream dependency checks.",
                "Make readiness honest: it should fail when the pod genuinely cannot serve.",
                "Tune timing against measured p99 latency under load, not against a default you copied.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.containers[0].livenessProbe}' | python3 -m json.tool",
                "oc describe pod <pod> | grep -E 'Liveness|Readiness|Startup|Restart Count'",
                "kube_pod_container_status_restarts_total   # correlate restarts with dependency latency",
            ],
            redflag=(
                "Do not put a dependency check in a liveness probe. It converts a partial outage into a "
                "total one, automatically."
            ),
            followup="Every pod in a service restarted at once. How do probes explain that?",
        ),
        Q(
            q="How do you implement graceful shutdown?",
            level=INTERMEDIATE,
            answer=(
                "When a pod is terminating, two things happen in parallel: it is removed from EndpointSlices, "
                "and it receives SIGTERM. Those are not synchronised, so the application must keep serving "
                "for a short while after SIGTERM to drain in-flight requests and let the routing layer catch "
                "up. I fail readiness first, add a small preStop sleep, handle SIGTERM to stop accepting new "
                "work while finishing current work, and set terminationGracePeriodSeconds longer than the "
                "worst-case drain."
            ),
            analogy=(
                "It is closing a shop properly. You stop letting new customers in, serve the people already "
                "inside, then lock the door - you do not turn the lights off with people at the till."
            ),
            context=(
                "This is the invisible cause of \"we get 502s during every deploy\". The pod exits instantly "
                "on SIGTERM while the router is still sending it requests for another second or two. Nobody "
                "notices in staging because there is no traffic. The fix is entirely in the application "
                "contract, which is why platform teams put it in the golden path template rather than "
                "discovering it per team."
            ),
            steps=[
                "Explain the race: endpoint removal and SIGTERM are concurrent, not ordered.",
                "Fail readiness immediately so new traffic stops being routed.",
                "Use a preStop hook with a short sleep to cover propagation delay.",
                "Handle SIGTERM to drain, and set terminationGracePeriodSeconds above the real worst case.",
            ],
            evidence=[
                "oc get deploy <name> -o jsonpath='{.spec.template.spec.terminationGracePeriodSeconds}{\"\\n\"}'",
                "oc get pod <pod> -o jsonpath='{.spec.containers[0].lifecycle}' | python3 -m json.tool",
                "Router or ingress 5xx rate during a rollout window",
            ],
            redflag=(
                "Do not blame the router for deploy-time 502s without checking the application's shutdown "
                "behaviour first. It is almost always the application."
            ),
            followup="You cannot change the application. What can the platform do to reduce the 502s?",
        ),
        Q(
            q="How do you run batch and scheduled work safely at cluster scale?",
            level=INTERMEDIATE,
            answer=(
                "I treat batch as a first-class tenant rather than an afterthought. That means TTLs on "
                "finished Jobs so they do not accumulate, an explicit concurrencyPolicy, resource requests so "
                "the scheduler can place them honestly, a PriorityClass below interactive workloads so batch "
                "yields under pressure, and quota on the namespace so a runaway loop cannot consume the "
                "cluster. Failures should alert, not just retry forever."
            ),
            analogy=(
                "Batch work is the delivery lorry. It belongs on the road, but it uses the service entrance, "
                "off-peak, and it does not get to block the ambulance."
            ),
            context=(
                "Batch is where clusters quietly fall over. Uncapped parallelism plus BestEffort QoS means a "
                "single misconfigured Job can evict production pods from a dozen nodes. Unbounded retries "
                "against a failing dependency turn one broken integration into a permanent load generator. "
                "Setting priority, quota and backoff limits as defaults - not as a per-team decision - is "
                "what keeps this boring."
            ),
            steps=[
                "Give every Job requests and limits, and never leave batch at BestEffort.",
                "Set ttlSecondsAfterFinished, backoffLimit and activeDeadlineSeconds so failures end.",
                "Assign a lower PriorityClass than interactive workloads so preemption favours users.",
                "Apply namespace quota and alert on failed and missed schedules, not just on Job existence.",
            ],
            evidence=[
                "oc get jobs -A --field-selector status.successful=0",
                "kube_cronjob_status_last_schedule_time   # compare against expected cadence",
                "oc get resourcequota -n <batch-ns> -o yaml",
            ],
            redflag=(
                "Do not let batch workloads run without resource requests. They will be BestEffort and the "
                "first thing evicted - or the thing that evicts everyone else."
            ),
            followup="A batch namespace is causing evictions in production namespaces. What is your fix?",
        ),
        Q(
            q="How would you choose between rolling, blue-green and canary deployments on OpenShift?",
            level=SENIOR,
            answer=(
                "Rolling is the default and it is right when the change is backward compatible and you can "
                "tolerate mixed versions briefly. Blue-green is right when you cannot tolerate mixed versions "
                "- an incompatible schema change, for example - and you can afford double capacity for the "
                "cutover. Canary is right when you want production traffic to be the test, and you have the "
                "observability to detect a regression in a small slice. On OpenShift I usually implement "
                "canary with weighted Routes or a service mesh, and blue-green by switching the Route target."
            ),
            analogy=(
                "Rolling is repainting a room wall by wall. Blue-green is building the new room and moving "
                "everyone across in one step. Canary is inviting five people into the new room first and "
                "watching their faces."
            ),
            context=(
                "The part interviewers listen for is the rollback story, because that is what the strategy is "
                "really buying. Rolling rollback means another rolling update, so recovery time equals "
                "rollout time. Blue-green rollback is a Route switch, measured in seconds, which is why it "
                "suits high-risk changes. Canary limits blast radius but only works if you have per-version "
                "metrics - otherwise you are shipping to a small group and hoping."
            ),
            steps=[
                "Start from the constraint: is a mixed-version state acceptable, and what is the required "
                "rollback time?",
                "Match the strategy to that constraint, and state the capacity cost of each.",
                "Describe the OpenShift mechanism - rollout parameters, weighted Routes, or a mesh.",
                "Define the abort criteria in advance: which metric, what threshold, who decides, how fast.",
            ],
            evidence=[
                "oc get route <name> -o jsonpath='{.spec.alternateBackends}' | python3 -m json.tool",
                "oc set route-backends <route> app-v1=90 app-v2=10",
                "Error rate and latency split by version label in Prometheus",
            ],
            redflag=(
                "Do not propose canary without saying which metric decides success. Without that it is just "
                "a slower way to ship a bug."
            ),
            followup="Your canary shows a 0.3% error increase. Roll back or continue? Justify it.",
        ),
        Q(
            q="How do you design namespace tenancy for a shared cluster?",
            level=SENIOR,
            answer=(
                "I define a tenancy unit - usually team plus environment - and make every namespace come with "
                "the same guardrails automatically: RBAC bound to a group rather than individuals, "
                "ResourceQuota, LimitRange to give sane defaults, a default-deny NetworkPolicy with explicit "
                "allows, and labels that drive policy, monitoring and chargeback. Namespaces are created "
                "through automation from a template, never by hand, so no namespace can exist without its "
                "guardrails."
            ),
            analogy=(
                "It is renting serviced offices, not empty units. Every tenant gets the same locks, the same "
                "meter and the same fire policy on day one - you do not negotiate them per tenant."
            ),
            context=(
                "The failure mode of hand-created namespaces is invisible until it hurts: one namespace with "
                "no quota consumes a node's memory during an incident, another has no NetworkPolicy and "
                "becomes the lateral movement path in a security review, a third has a RoleBinding to a "
                "person who left. Templating removes the whole class. It also makes the platform's offer "
                "legible to teams, which reduces the number of one-off exception requests."
            ),
            steps=[
                "Define the tenancy unit and the labelling scheme that drives everything else.",
                "Bundle the guardrails - RBAC to groups, quota, LimitRange, default-deny NetworkPolicy.",
                "Automate creation through GitOps or a template so guardrails cannot be skipped.",
                "Decide the escalation path to hard tenancy - dedicated nodes or a separate cluster - and "
                "the criteria that trigger it.",
            ],
            evidence=[
                "oc get ns --show-labels",
                "oc get resourcequota,limitrange,networkpolicy -A | head -30",
                "oc get rolebinding -A -o wide | grep -v ServiceAccount   # user bindings to review",
            ],
            redflag=(
                "Do not bind roles to individual users. When they change teams, nobody remembers, and the "
                "access outlives the reason for it."
            ),
            followup="A team asks for cluster-scoped permissions to install a CRD. How do you handle it?",
        ),
        Q(
            q="What does your platform's golden path actually contain?",
            level=ARCHITECT,
            answer=(
                "A golden path is the paved route from repository to running service: a templated project "
                "with a Containerfile that satisfies restricted-v2, a pipeline that builds, scans, signs and "
                "produces an SBOM, GitOps manifests with probes, requests, limits, a PDB and topology spread "
                "already set, a default dashboard and alert set, and documented SLOs. Teams may leave the "
                "path, but then they own the parts they replaced, and that trade is explicit."
            ),
            analogy=(
                "It is the paved footpath across the park. People are free to walk on the grass, but if the "
                "path goes where they need to go, almost nobody does - and the grass survives."
            ),
            context=(
                "The purpose is to move the platform team from reviewing every deployment to reviewing "
                "exceptions. It works because it makes the safe option also the fast option: a team using "
                "the template gets probes, security context, monitoring and a working pipeline for free, "
                "while a team going their own way has to build all of it. The measure of success is the "
                "percentage of services on the path and the number of production incidents traced to "
                "off-path configuration."
            ),
            steps=[
                "Enumerate the artefacts: project template, pipeline, manifests, dashboards, alerts, SLO doc.",
                "Encode the non-negotiables as defaults in the template, not as review checklists.",
                "Publish the exception process so leaving the path is possible but visible and owned.",
                "Measure adoption and off-path incident rate, and use those numbers to prioritise "
                "improvements.",
            ],
            evidence=[
                "Percentage of Deployments carrying required labels, probes, requests and PDBs",
                "oc get deploy -A -o json | jq '[.items[] | select(.spec.template.spec.containers[0].resources.requests == null)] | length'",
                "Pipeline compliance report: signed images, SBOM present, scan passed",
            ],
            redflag=(
                "Do not describe a golden path as documentation. If it is a wiki page rather than a working "
                "template, adoption will be near zero."
            ),
            followup="How would you migrate fifty existing services onto the golden path without a big bang?",
        ),
        Q(
            q="What is your definition of production ready for a workload?",
            level=ARCHITECT,
            answer=(
                "Concretely: more than one replica with topology spread across failure domains, a "
                "PodDisruptionBudget that permits maintenance, resource requests and limits that reflect "
                "measured usage, honest readiness and safe liveness probes, graceful shutdown, no hardcoded "
                "secrets, images pinned by digest and signed, a documented SLO with an alert tied to it, a "
                "tested rollback path, and a runbook that a person on call at 3am can follow without "
                "context."
            ),
            analogy=(
                "It is an aircraft's pre-flight checklist. Not one of the items is clever; skipping any of "
                "them is how routine flights become incidents."
            ),
            context=(
                "The value of writing this down is that it converts arguments into checks. Instead of "
                "debating whether a service is ready, the pipeline reports which items are missing, and the "
                "conversation becomes about the two that failed rather than about opinions. It also gives "
                "the platform team a defensible position: the answer to \"can we go live without probes?\" is "
                "a published standard rather than a personal judgement."
            ),
            steps=[
                "Publish the checklist as a short, testable list - each item must be machine-checkable.",
                "Enforce what you can in CI and admission policy; report the rest on a dashboard.",
                "Require evidence for the untestable ones: a rollback that was actually performed, a runbook "
                "that was actually used in a game day.",
                "Review the list after every incident and add the item that would have prevented it.",
            ],
            evidence=[
                "Readiness report per namespace: replicas, PDB, requests, probes, spread constraints",
                "oc get pdb -A ; oc get deploy -A -o wide",
                "Alert-to-SLO mapping: every page traces to a user-visible objective",
            ],
            redflag=(
                "Do not make the list so long that nobody completes it. A checklist people bypass is worse "
                "than a short one they follow."
            ),
            followup="A critical service fails two checklist items and the launch is tomorrow. What do you do?",
        ),
    ],
)
