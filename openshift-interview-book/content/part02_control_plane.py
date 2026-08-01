"""Part 2 - The OpenShift control plane."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=2,
    title="The control plane and who owns what",
    subtitle="Where desired state lives, who reconciles it, and where to look when it stops",
    intro=(
        "If you can only prepare one thing properly, prepare this. Every serious OpenShift interview comes "
        "back to a single skill: given a symptom, can you name the component that owns it and read its "
        "status rather than guessing? The control plane is not a list of daemons to memorise, it is a chain "
        "of ownership. The API server is the front door, etcd is the record, controllers close the gap "
        "between record and reality, and OpenShift layers its own operators on top so that the cluster can "
        "upgrade and repair itself. Learn the chain and most troubleshooting questions answer themselves."
    ),
    infographics=["control_plane_map", "oc_apply_flow"],
    questions=[
        Q(
            q="What does the Kubernetes API server do?",
            level=FOUNDATION,
            answer=(
                "The API server is the only component that talks to etcd, and it is the single front door for "
                "every request. It authenticates the caller, authorises them through RBAC, runs mutating and "
                "then validating admission - which in OpenShift includes Security Context Constraints - "
                "validates the object against its schema, and persists it. It also serves watches, which is "
                "how every controller and kubelet learns that something changed."
            ),
            analogy=(
                "It is the registry office. Nothing is legally true until it is written in the ledger there, "
                "and everyone else finds out by subscribing to the ledger's updates."
            ),
            context=(
                "Because it is the only writer to etcd and the source of every watch, API server health is "
                "cluster health. When it is slow, symptoms appear everywhere at once and look unrelated: "
                "controllers lag, kubelets are late reporting status, nodes flap between Ready and NotReady, "
                "and oc commands feel sticky. Recognising that pattern - many unrelated symptoms, one shared "
                "dependency - is what separates a fast diagnosis from an hour of chasing pods."
            ),
            steps=[
                "State the request pipeline in order: authenticate, authorise, mutate, validate, persist.",
                "Point out that it is the only component with etcd access - everything else goes through it.",
                "Mention watches, because that is how the declarative model actually propagates.",
                "Give the failure signature: broad, simultaneous, unrelated-looking symptoms mean you should "
                "check the API server before the workloads.",
            ],
            evidence=[
                "oc get --raw /readyz?verbose | head",
                "apiserver_request_duration_seconds_bucket   # Prometheus, by verb and resource",
                "oc get co kube-apiserver openshift-apiserver",
            ],
            redflag=(
                "Do not describe the API server as \"where you run kubectl\". It is an admission and "
                "persistence pipeline, and that pipeline is what interviewers probe."
            ),
            followup="Which admission step would reject a pod asking to run as root, and why that one?",
        ),
        Q(
            q="What is etcd and what does it actually store?",
            level=FOUNDATION,
            answer=(
                "etcd is the cluster's consistent key-value store and it holds every API object: Deployments, "
                "Secrets, ConfigMaps, node registrations, RBAC, custom resources. It is the desired and "
                "recorded state of the cluster. What it does not hold is application data - your database "
                "contents live on a persistent volume in the storage backend, not in etcd. That distinction "
                "drives the whole backup and recovery conversation."
            ),
            analogy=(
                "etcd is the building's blueprint and tenancy register. Restoring it rebuilds who is supposed "
                "to live where; it does not restore the furniture inside the flats."
            ),
            context=(
                "The consequence is one interviewers ask about constantly: an etcd restore recovers cluster "
                "state to a point in time, but everything that happened since - new objects, new secrets, "
                "new certificates - is gone, and persistent volume data is untouched. So an etcd backup is a "
                "cluster-recovery tool, not an application-recovery tool, and you need both. It also explains "
                "why etcd performance is so sensitive to disk latency: every write is a consensus round trip "
                "that must be fsynced."
            ),
            steps=[
                "Define it as the consistent store behind the API server.",
                "Say what is in it - all API objects - and what is not: PV contents and application state.",
                "Note the disk-latency sensitivity, because that is the number one etcd production problem.",
                "Draw the recovery conclusion: etcd backup and application backup solve different failures.",
            ],
            evidence=[
                "oc get etcd cluster -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "etcd_disk_wal_fsync_duration_seconds_bucket   # p99 should stay in low milliseconds",
                "oc -n openshift-etcd rsh <etcd-pod> etcdctl endpoint status -w table",
            ],
            redflag=(
                "Do not say \"we back up etcd so our applications are protected\". That single sentence is a "
                "well-known senior-level trap."
            ),
            followup="You restore etcd from twelve hours ago. What is now broken that was fine before?",
        ),
        Q(
            q="What is etcd quorum, and why an odd number of members?",
            level=FOUNDATION,
            answer=(
                "etcd uses Raft, which requires a majority of members to agree before a write is committed. "
                "With three members the quorum is two, so you survive one failure; with five it is three, so "
                "you survive two. Odd numbers are used because adding an even member increases the quorum "
                "requirement without increasing fault tolerance - four members still only tolerate one "
                "failure, but give you one more thing that can break."
            ),
            analogy=(
                "It is a committee that needs a majority to sign off. Adding a fourth member to a committee "
                "of three does not make decisions easier; it just adds another person who can be off sick."
            ),
            context=(
                "Lose quorum and the API server goes read-only or fails entirely - the cluster stops "
                "accepting changes, though already-running pods keep serving traffic. This is why control "
                "plane nodes must sit in separate failure domains and why you never take two of three down "
                "for maintenance at the same time. In stretched or three-zone designs, quorum placement is "
                "the whole design conversation: two zones cannot give you a safe majority."
            ),
            steps=[
                "Define quorum as a strict majority under Raft.",
                "Do the arithmetic out loud: 3 tolerates 1, 5 tolerates 2, 4 still only tolerates 1.",
                "State the failure behaviour - no quorum means no writes, but existing workloads keep running.",
                "Connect it to placement: separate failure domains, and never drain two control plane nodes "
                "together.",
            ],
            evidence=[
                "oc -n openshift-etcd rsh <etcd-pod> etcdctl endpoint health --cluster",
                "oc get nodes -l node-role.kubernetes.io/master -o wide",
                "oc get co etcd -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not say more etcd members means more resilience without qualification. Beyond five, write "
                "latency gets worse and resilience does not."
            ),
            followup="Two of three control plane nodes are lost. What is your recovery sequence?",
        ),
        Q(
            q="What is a controller, and what does the controller manager do?",
            level=FOUNDATION,
            answer=(
                "A controller is a loop that watches one kind of object, compares desired state with observed "
                "state, and acts to close the gap. The kube-controller-manager bundles many of these together "
                "- the Deployment controller creating ReplicaSets, the ReplicaSet controller creating pods, "
                "the node lifecycle controller marking nodes unhealthy, the PV binder matching claims to "
                "volumes. Each one writes what it thinks into the object's status, which is why status "
                "conditions are the best diagnostic in the cluster."
            ),
            analogy=(
                "Each controller is a shopkeeper who keeps glancing at the shelf. Two loaves missing, so bake "
                "two more. Nobody instructed them; they are simply comparing shelf to plan, continuously."
            ),
            context=(
                "This is why chasing pods is usually the wrong instinct. If pods are missing, the interesting "
                "object is the ReplicaSet or the Deployment, because its conditions will say whether it is "
                "blocked by quota, by an admission webhook, or by a failing image. Reading down the ownership "
                "chain - Deployment, ReplicaSet, Pod - takes three commands and replaces a lot of guessing."
            ),
            steps=[
                "Define the loop: watch, diff, act, report status.",
                "Name three concrete controllers so it is not abstract.",
                "Explain that status conditions are the controller's own explanation of what is blocking it.",
                "Show the diagnostic habit: walk the ownership chain from the top object down to the pod.",
            ],
            evidence=[
                "oc get deploy <name> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get rs -n <ns> --sort-by=.metadata.creationTimestamp | tail -3",
                "oc get events -n <ns> --field-selector type=Warning --sort-by=.lastTimestamp",
            ],
            redflag=(
                "Do not say Kubernetes \"just runs your containers\". The whole interview is about "
                "reconciliation loops."
            ),
            followup="A Deployment reports ReplicaFailure. Which controller wrote that, and what would it mean?",
        ),
        Q(
            q="What is a CustomResourceDefinition?",
            level=FOUNDATION,
            answer=(
                "A CRD extends the Kubernetes API with a new object type. Once it is registered you get a "
                "first-class resource - it can be created with oc apply, protected with RBAC, watched, and "
                "validated against an OpenAPI schema, exactly like a built-in object. On its own a CRD does "
                "nothing; it is just a data shape. It becomes useful when a controller watches those objects "
                "and acts on them, which is what an operator is."
            ),
            analogy=(
                "A CRD is a new form in the filing system. Printing the form changes nothing - it matters "
                "once there is a clerk whose job is to read it and act."
            ),
            context=(
                "In production the CRD and its controller can fail independently, and that produces a "
                "confusing symptom: your custom resource applies successfully and then nothing happens. That "
                "is almost always a controller that is not running, is missing RBAC for the resource, or is "
                "watching a different API version. Knowing to check the operator's own logs and RBAC first "
                "makes you look like you have actually run operators rather than only installed them."
            ),
            steps=[
                "Define it as an API extension with a schema, not a piece of logic.",
                "Point out what you get for free: RBAC, validation, watch, oc tooling.",
                "Separate the CRD from its controller, and say why that separation causes silent no-ops.",
                "Give the diagnostic order - is the CR accepted, is the controller running, does it have RBAC, "
                "does the version match.",
            ],
            evidence=[
                "oc get crd | grep <domain>",
                "oc explain <kind>.spec --recursive | head -30",
                "oc -n <operator-ns> logs deploy/<operator> --tail=100",
            ],
            redflag=(
                "Do not conflate a CRD with an operator. The CRD is the noun, the operator is the verb."
            ),
            followup="Your custom resource applies cleanly but nothing happens. Diagnose it.",
        ),
        Q(
            q="What is an ownerReference and why does it matter?",
            level=FOUNDATION,
            answer=(
                "An ownerReference records that one object was created by and belongs to another - a pod "
                "points at its ReplicaSet, which points at its Deployment. Garbage collection uses this: "
                "delete the owner and the dependants are cleaned up automatically. It also gives you the "
                "ownership chain you walk during troubleshooting, and it is why deleting a pod directly gets "
                "you a new pod instead of an empty namespace."
            ),
            analogy=(
                "It is a parent's name on a school form. Remove the family from the register and the "
                "children's records go with them - nobody has to tidy up each one by hand."
            ),
            context=(
                "Two operational consequences come up regularly. First, cascading deletes are the reason "
                "removing a Deployment is safe and tidy, while orphaning a ReplicaSet by hand leaves pods "
                "nobody manages. Second, when a namespace refuses to delete, ownership and finalizers are "
                "the pair you investigate together - something is either waiting on a dependant or waiting "
                "on a finalizer that no controller is left to clear."
            ),
            steps=[
                "Define it as a parent pointer used by garbage collection.",
                "Walk one chain out loud: Deployment owns ReplicaSet owns Pod.",
                "Explain cascading deletion and what orphaning does instead.",
                "Link it to troubleshooting: the chain tells you which controller to interrogate.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.metadata.ownerReferences}' | python3 -m json.tool",
                "oc delete deploy <name> --cascade=orphan   # know what this leaves behind",
                "oc get rs -n <ns> -o custom-columns=NAME:.metadata.name,OWNER:.metadata.ownerReferences[0].name",
            ],
            redflag=(
                "Do not say pods are deleted \"automatically by Kubernetes\" without naming the mechanism. "
                "The mechanism is the answer."
            ),
            followup="What happens to the pods if you delete a ReplicaSet with --cascade=orphan?",
        ),
        Q(
            q="What is a finalizer?",
            level=FOUNDATION,
            answer=(
                "A finalizer is a string on an object that blocks deletion until a controller has finished "
                "its cleanup and removes that string. When you delete such an object, the API server sets a "
                "deletionTimestamp and the object stays visible in a Terminating state until every finalizer "
                "is gone. It exists so that external resources - a cloud load balancer, a storage volume, a "
                "DNS record - can be released before the record disappears."
            ),
            analogy=(
                "It is a checkout hold on a hotel room. You have handed back the key, but the room stays "
                "flagged until housekeeping confirms the minibar and the safe are clear."
            ),
            context=(
                "This is the mechanism behind namespaces stuck in Terminating forever. The usual cause is a "
                "finalizer belonging to a controller that no longer exists - an operator was uninstalled "
                "before its custom resources were removed, so nobody is left to do the cleanup. Force-editing "
                "the finalizer out works, but it silently leaks whatever the finalizer was going to release, "
                "so it is a last resort after you have identified what is missing."
            ),
            steps=[
                "Define it as a deletion guard owned by a controller.",
                "Explain the Terminating state and deletionTimestamp.",
                "Give the common failure - orphaned finalizer after an operator was removed.",
                "State the safe order: restore or reinstall the controller first, remove the finalizer only "
                "as a documented last resort.",
            ],
            evidence=[
                "oc get ns <ns> -o jsonpath='{.spec.finalizers}{\"\\n\"}'",
                "oc api-resources --verbs=list --namespaced -o name | xargs -n1 oc get -n <ns> --ignore-not-found",
                "oc get <kind> <name> -o jsonpath='{.metadata.finalizers}{\"\\n\"}'",
            ],
            redflag=(
                "Do not offer \"just patch the finalizers out\" as your first move. It works, and it is how "
                "clusters end up leaking cloud resources nobody can account for."
            ),
            followup="A namespace has been Terminating for an hour. What is your sequence?",
        ),
        Q(
            q="What does the Cluster Version Operator do?",
            level=INTERMEDIATE,
            answer=(
                "The CVO owns the cluster's version. It takes a release image - a single digest that "
                "describes every component in that OpenShift release - and drives each Cluster Operator "
                "toward the manifests in that payload, in dependency order. It reports overall progress on "
                "the ClusterVersion object, including whether the cluster is Upgradeable. It is what makes an "
                "OpenShift upgrade a single supported transaction rather than a set of independent component "
                "upgrades."
            ),
            analogy=(
                "The CVO is the conductor with the only copy of the score. Individual sections do not decide "
                "their own tempo; they follow the release the conductor is playing."
            ),
            context=(
                "Understanding this reframes upgrade troubleshooting. When an upgrade stalls, the "
                "ClusterVersion status names the operator it is waiting on, and that operator's conditions "
                "name the reason - a degraded dependency, a node that will not drain, an unavailable API. You "
                "do not fix the CVO, you fix what it is blocked on. It also explains why you should not "
                "hand-edit resources the CVO owns: it will simply put them back."
            ),
            steps=[
                "Define the release image as a digest-addressed payload of all components.",
                "Explain that the CVO reconciles Cluster Operators toward that payload in dependency order.",
                "Show where to read progress and blockage - ClusterVersion conditions, then the named "
                "operator's conditions.",
                "Add the rule: do not hand-edit CVO-managed resources, because reconciliation reverts them.",
            ],
            evidence=[
                "oc get clusterversion version -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc adm upgrade   # available targets and current state",
                "oc get co --sort-by=.metadata.name | grep -v 'True.*False.*False'",
            ],
            redflag=(
                "Do not talk about upgrading individual OpenShift components independently. That is not how "
                "the product is supported."
            ),
            followup="An upgrade has sat at 62% for an hour. What is your first command and why?",
        ),
        Q(
            q="What is the difference between a Cluster Operator and an OLM-managed operator?",
            level=INTERMEDIATE,
            answer=(
                "A Cluster Operator is part of the OpenShift release payload and is managed by the CVO - "
                "authentication, ingress, storage, monitoring, etcd. You do not install or uninstall them, "
                "and their version moves with the cluster. An OLM-managed operator is an optional add-on you "
                "chose to install from a catalog - it has a Subscription, an InstallPlan and a CSV, and it "
                "has its own update channel independent of the cluster version."
            ),
            analogy=(
                "Cluster Operators are the organs you were born with. OLM operators are the apps you "
                "installed - both essential to how the system behaves, but only one set has an uninstall "
                "button and its own update schedule."
            ),
            context=(
                "The distinction determines where you look and what you are allowed to do. A degraded "
                "Cluster Operator is a cluster health and upgrade blocker, diagnosed through oc get co and "
                "resolved through supported procedures. A stuck OLM operator is diagnosed by walking "
                "CatalogSource to Subscription to InstallPlan to CSV. Mixing these up sends candidates "
                "looking for a Subscription that will never exist."
            ),
            steps=[
                "Split them by lifecycle owner: CVO versus OLM.",
                "Give examples of each so the boundary is concrete.",
                "State the different diagnostic entry points - oc get co versus the OLM object chain.",
                "Mention the upgrade implication: an OLM operator's channel must be compatible with the "
                "target cluster version before you upgrade.",
            ],
            evidence=[
                "oc get co ; oc get csv -A | head",
                "oc get subscription -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,CHANNEL:.spec.channel",
                "oc get installplan -A",
            ],
            redflag=(
                "Do not call everything \"an operator\" without saying who manages its lifecycle. That "
                "distinction is the whole question."
            ),
            followup="You are about to upgrade the cluster. What do you check about your OLM operators first?",
        ),
        Q(
            q="What does the Machine Config Operator do, and what is a rendered MachineConfig?",
            level=INTERMEDIATE,
            answer=(
                "The MCO owns node configuration. You write MachineConfig objects - kernel arguments, files, "
                "systemd units, kubelet settings - and label them for a pool. The MCO merges every "
                "MachineConfig that applies to a pool, in name order, into a single rendered MachineConfig, "
                "and then the Machine Config Daemon on each node applies it, draining and rebooting the node "
                "one at a time according to the pool's maxUnavailable."
            ),
            analogy=(
                "It is a building's standard fit-out spec. You do not renovate each flat individually; you "
                "publish one merged spec and the contractor works through the block, one flat at a time."
            ),
            context=(
                "Two things make this interview-relevant. First, the rendered config is the source of truth - "
                "when a node's configuration looks wrong, you compare its current and desired rendered config "
                "rather than reading individual MachineConfigs. Second, MCO rollout is where PodDisruption"
                "Budgets and drains collide with change management: a workload with a badly sized PDB will "
                "stall a node update and therefore stall a cluster upgrade, and the pool will sit Degraded "
                "telling you exactly that."
            ),
            steps=[
                "Describe the object flow: MachineConfig, merged into rendered config per pool, applied by MCD.",
                "Explain the rollout: one node at a time, cordon, drain, apply, reboot, uncordon.",
                "Name where to read state - MachineConfigPool conditions and the node's current versus "
                "desired config annotations.",
                "Call out the classic blocker: a drain stuck on a PDB or a pod with no controller.",
            ],
            evidence=[
                "oc get mcp -o wide",
                "oc get node <node> -o jsonpath='{.metadata.annotations.machineconfiguration\\.openshift\\.io/currentConfig}{\"\\n\"}'",
                "oc -n openshift-machine-config-operator logs ds/machine-config-daemon -c machine-config-daemon --tail=100",
            ],
            redflag=(
                "Do not describe editing files on nodes by hand as an alternative. The MCD will revert it and "
                "may flag the node as degraded."
            ),
            followup="A MachineConfigPool is Degraded with one node stuck. Walk me through it.",
        ),
        Q(
            q="Walk me through everything that happens after oc apply.",
            level=INTERMEDIATE,
            answer=(
                "The client sends the object to the API server, which authenticates the token, authorises via "
                "RBAC, runs mutating admission - including SCC deciding what the pod may be - then validating "
                "admission and schema validation, and writes to etcd. Controllers watching that type wake up: "
                "the Deployment controller creates a ReplicaSet, which creates pods. The scheduler filters "
                "and scores nodes and binds the pod. The kubelet on that node pulls the image, sets up the "
                "network through CNI and storage through CSI, and starts containers. Probes pass, the pod "
                "goes Ready, and the endpoint controller adds it to the EndpointSlice so it takes traffic."
            ),
            analogy=(
                "It is a relay race with six batons. Reception, filing, planning, allocation, construction, "
                "opening. Any runner can drop the baton, and the whole point is knowing which one did."
            ),
            context=(
                "This question is really a diagnostic map in disguise. Rejected at admission means RBAC, SCC "
                "or a webhook. Object exists but no pods means a controller problem or quota. Pod Pending "
                "means the scheduler found no fit. Pod ContainerCreating means image, CNI or CSI. Pod Running "
                "but not Ready means probes. Ready but no traffic means EndpointSlice, Service selector or "
                "NetworkPolicy. If you can recite the stages, you can localise almost any workload failure "
                "in under a minute."
            ),
            steps=[
                "Say the six stages in order, briefly, without drowning in detail.",
                "For each stage, name the observable symptom when it fails.",
                "Highlight the OpenShift-specific step: SCC admission deciding the pod's security context.",
                "Close by using it as a triage map rather than trivia - that is the point of knowing it.",
            ],
            evidence=[
                "oc get events -n <ns> --sort-by=.lastTimestamp | tail -20",
                "oc describe pod <pod> | sed -n '/Events/,$p'",
                "oc get endpointslice -n <ns> -l kubernetes.io/service-name=<svc>",
            ],
            redflag=(
                "Do not stop at \"the scheduler places it and it runs\". The value of this answer is in the "
                "stages you skipped."
            ),
            followup="At which stage would a Security Context Constraint reject the pod, and what would you see?",
        ),
        Q(
            q="What is API Priority and Fairness, and why does it matter?",
            level=INTERMEDIATE,
            answer=(
                "APF replaces the old global max-in-flight limits with fair queueing. Requests are sorted "
                "into flow schemas and priority levels, each with its own concurrency share, so one noisy "
                "client - a runaway controller, a mis-tuned CI job listing every pod in the cluster - gets "
                "throttled in its own queue instead of starving the whole API server. Critical traffic like "
                "leader election has a protected level."
            ),
            analogy=(
                "It is separate queues at the airport rather than one line. The person with twelve suitcases "
                "still gets served, but they do not hold up everyone behind them."
            ),
            context=(
                "You meet APF when clients start getting 429s and someone asks whether the API server is "
                "\"broken\". Usually it is doing its job: something is generating an enormous request rate "
                "and APF is containing the damage. The right response is to find the offending flow, fix the "
                "client - add a resourceVersion, use informers instead of polling, filter by label - and only "
                "then consider adjusting concurrency shares."
            ),
            steps=[
                "Explain the model: flow schemas map requests to priority levels with concurrency shares.",
                "Say what problem it solves - isolating a noisy client from everyone else.",
                "Describe the symptom: 429 responses and rising request wait duration for one flow.",
                "Give the fix order - identify the flow, fix the client's request pattern, tune shares last.",
            ],
            evidence=[
                "oc get flowschema ; oc get prioritylevelconfiguration",
                "apiserver_flowcontrol_rejected_requests_total   # by flow schema",
                "apiserver_flowcontrol_request_wait_duration_seconds_bucket",
            ],
            redflag=(
                "Do not immediately propose raising limits. Raising the ceiling for a client that is polling "
                "in a loop just moves the outage."
            ),
            followup="A team says their operator is being rate limited. How do you confirm and what do you advise?",
        ),
        Q(
            q="How do you investigate a degraded Cluster Operator?",
            level=SENIOR,
            answer=(
                "I start at the operator itself: oc get co to see which conditions are set, then read the "
                "message on Degraded or Progressing, because it usually names the dependency. Then I look at "
                "the operator's namespace - its pods, events and logs - and at what it depends on: nodes, "
                "storage, DNS, certificates, the network. I state impact first, gather that evidence, and "
                "only then take the smallest action, because most degraded operators are symptoms of an "
                "infrastructure problem rather than causes."
            ),
            analogy=(
                "The warning light on the dashboard is not the fault. You read the code, then check the "
                "system it points at - you do not replace the dashboard."
            ),
            context=(
                "The most common trap is treating the operator as the problem and restarting its pods. That "
                "clears the evidence and, in the common cases, changes nothing: the ingress operator is "
                "degraded because a load balancer health check is failing, the storage operator because a CSI "
                "driver cannot reach its backend, the authentication operator because the OAuth route is "
                "unreachable or an IdP certificate expired. The message on the condition almost always names "
                "the real subject."
            ),
            steps=[
                "Establish impact and scope: is a customer-facing capability affected, or only cluster "
                "management?",
                "Read the operator's conditions and take the message literally - it names the dependency.",
                "Inspect the operator's own namespace: pod state, recent events, logs at the time of change.",
                "Check the named dependency - node, certificate, load balancer, storage backend, DNS - and "
                "fix there; capture must-gather if this may become a support case.",
            ],
            evidence=[
                "oc get co ; oc describe co <name>",
                "oc get pods -n openshift-<component> ; oc logs -n openshift-<component> <pod> --tail=200",
                "oc adm must-gather -- /usr/bin/gather_<component>",
            ],
            redflag=(
                "Do not delete operator pods as a first step. It is the platform equivalent of turning it off "
                "and on again, and it destroys the evidence you would need for support."
            ),
            followup="The authentication operator is degraded but users can still log in. What does that tell you?",
        ),
        Q(
            q="How do you investigate API server latency?",
            level=SENIOR,
            answer=(
                "I confirm the symptom with the request duration metrics broken down by verb and resource, "
                "because a slow LIST on one custom resource is a very different problem from broad slowness. "
                "Then I check etcd, since API latency is usually etcd disk latency - fsync and backend commit "
                "durations. In parallel I look for a client generating heavy uncached LIST or WATCH traffic, "
                "and at APF rejections. Only after that do I consider control plane sizing."
            ),
            analogy=(
                "The queue at the counter can be long for three different reasons: the clerk is slow, the "
                "filing cabinet is slow, or one customer is ordering for the entire street. You check which "
                "before hiring another clerk."
            ),
            context=(
                "The single most common root cause in real clusters is disk. etcd needs consistently low "
                "write latency, and a control plane on shared or throttled storage will produce API slowness "
                "that looks like a Kubernetes problem and is actually an infrastructure one. The second most "
                "common is a badly written controller that lists all pods cluster-wide every few seconds. "
                "Naming both, in that order, is what a senior answer sounds like."
            ),
            steps=[
                "Quantify it: request duration by verb and resource, plus which clients are affected.",
                "Check etcd health first - fsync and backend commit p99, database size, leader elections.",
                "Look for abusive clients and APF rejections; identify the flow schema being throttled.",
                "Then consider capacity - control plane CPU, memory and disk class - and change one thing "
                "with a measured before and after.",
            ],
            evidence=[
                "histogram_quantile(0.99, sum by (le,verb) (rate(apiserver_request_duration_seconds_bucket[5m])))",
                "etcd_disk_backend_commit_duration_seconds_bucket ; etcd_server_leader_changes_seen_total",
                "oc get --raw /metrics | grep apiserver_current_inflight_requests",
            ],
            redflag=(
                "Do not jump to \"add more control plane nodes\". More etcd members usually makes write "
                "latency worse, not better."
            ),
            followup="etcd fsync p99 is 90ms. What does that tell you and what would you do?",
        ),
        Q(
            q="What are etcd fragmentation and defragmentation, and when do you care?",
            level=SENIOR,
            answer=(
                "etcd keeps historical revisions, and compaction removes old ones logically but leaves free "
                "space inside the database file. Defragmentation reclaims that space and shrinks the file. "
                "You care when the database approaches its size quota, because hitting it puts the cluster "
                "into a no-space alarm and the API server goes read-only. Defragmentation is done one member "
                "at a time, during a maintenance window, because the member being defragmented blocks."
            ),
            analogy=(
                "It is a filing cabinet where removing documents leaves the gaps behind. Compaction shreds "
                "the old copies; defragmentation is the tidy-up that actually closes the gaps."
            ),
            context=(
                "This appears in interviews as a scale question - what happens to a cluster with heavy object "
                "churn, such as thousands of short-lived Jobs or an operator rewriting status constantly. The "
                "senior answer is not just \"defragment\", it is to reduce the churn: fix the controller that "
                "is hot-looping, add TTLs to Jobs, and monitor database size with an alert well before the "
                "quota. Defragmentation treats the symptom."
            ),
            steps=[
                "Separate compaction, which is automatic and logical, from defragmentation, which reclaims "
                "file space.",
                "State the risk: approaching the space quota makes the API server read-only.",
                "Describe the safe procedure - one member at a time, watch for leader changes, verify health "
                "before moving on.",
                "Add the real fix: find and stop the churn, and alert on database size ahead of the quota.",
            ],
            evidence=[
                "etcd_mvcc_db_total_size_in_bytes ; etcd_mvcc_db_total_size_in_use_in_bytes",
                "oc -n openshift-etcd rsh <etcd-pod> etcdctl endpoint status -w table",
                "oc get events -A --field-selector reason=Unhealthy -n openshift-etcd",
            ],
            redflag=(
                "Do not defragment all members at once. You will take the control plane down while trying to "
                "protect it."
            ),
            followup="Which workload patterns cause the most etcd churn, and how would you find them?",
        ),
        Q(
            q="Why are ClusterVersion overrides risky?",
            level=SENIOR,
            answer=(
                "An override tells the CVO to stop managing a specific component. That immediately makes the "
                "cluster unsupported for upgrades in most cases, because the CVO can no longer guarantee the "
                "payload is consistent, and it silently freezes that component at whatever state it was in - "
                "including missing security fixes. Overrides exist for narrow, time-boxed, "
                "support-directed situations, not as a way to keep a resource edited the way you like it."
            ),
            analogy=(
                "It is disabling one smoke detector because it keeps chirping. The noise stops, the "
                "protection stops, and everyone forgets it was ever disabled."
            ),
            context=(
                "The realistic scenario is someone edited a CVO-managed resource, the CVO reverted it, and "
                "the team's instinct is to add an override so their change sticks. The senior response is to "
                "ask why the change is needed and find the supported knob - a Custom Resource on the owning "
                "operator, an IngressController field, a MachineConfig - because those exist for almost every "
                "legitimate case. If an override truly is required, it should be a documented, expiring "
                "decision with a ticket attached."
            ),
            steps=[
                "Explain what an override actually does: CVO stops reconciling that manifest.",
                "State the consequences - support posture, upgrade blocking, frozen component.",
                "Redirect to the supported alternative: the owning operator's own API almost always exposes "
                "the setting.",
                "If unavoidable, time-box it, document it, alert on it and remove it as part of the fix.",
            ],
            evidence=[
                "oc get clusterversion version -o jsonpath='{.spec.overrides}' | python3 -m json.tool",
                "oc get co <component> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc adm upgrade   # will report why the cluster is not Upgradeable",
            ],
            redflag=(
                "Do not present overrides as a normal customisation technique. It reads as someone who "
                "fights the platform instead of using its API."
            ),
            followup="A team wants to change a CVO-managed Deployment's replica count. What do you tell them?",
        ),
        Q(
            q="How would you choose a control plane topology for a new cluster?",
            level=ARCHITECT,
            answer=(
                "I start from the availability requirement and the failure domains actually available, not "
                "from a preferred number. Three control plane nodes across three independent domains is the "
                "default because it gives quorum with one failure. If only two domains exist, I say plainly "
                "that a stretched cluster cannot give a safe majority and propose two clusters with "
                "application-level replication instead. For small edge sites I consider compact three-node or "
                "single-node OpenShift, and I make the recovery expectation explicit up front."
            ),
            analogy=(
                "You do not decide how many lifeboats to carry by preference. You count passengers, then "
                "count the exits the ship actually has."
            ),
            context=(
                "The mistake this question is designed to catch is answering with a number instead of a "
                "requirement. Every topology carries an implied recovery story: single-node OpenShift means "
                "the site is down while it rebuilds, compact clusters mean control plane and workload "
                "contention, stretched clusters mean latency-sensitive quorum. Stating the recovery "
                "consequence alongside the topology is what turns this from a fact into a design answer."
            ),
            steps=[
                "Capture requirements first: RTO, RPO, latency between sites, regulatory placement, expected "
                "scale.",
                "Enumerate real failure domains, then choose a topology that gives quorum across them.",
                "Name the trade-off explicitly - cost and operational complexity versus tolerated failures.",
                "Write down the recovery expectation for the chosen topology and schedule a test that proves "
                "it.",
            ],
            evidence=[
                "oc get nodes -L topology.kubernetes.io/zone -l node-role.kubernetes.io/master",
                "oc get infrastructure cluster -o jsonpath='{.status.controlPlaneTopology}{\"\\n\"}'",
                "Documented DR test results with measured RTO against the stated target",
            ],
            redflag=(
                "Do not propose a two-zone stretched control plane. It looks highly available and cannot "
                "survive losing the wrong zone."
            ),
            followup="The customer only has two data centres and wants active-active. What do you propose?",
        ),
    ],
)
