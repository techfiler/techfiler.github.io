"""Part 10 - Installation, machines and cluster updates."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=10,
    title="Installation, machines and updates",
    subtitle="Bringing a cluster into existence, keeping its nodes honest, and moving versions without drama",
    intro=(
        "Cluster lifecycle is where platform engineering earns its name. Anyone can install a cluster once "
        "with the defaults; the job is doing it repeatably, keeping every node identical to its declared "
        "configuration, and moving through versions on a schedule without turning each upgrade into an "
        "event. Interviewers probe this area hard because it is where the platform's own reliability lives - "
        "and because the words a candidate uses about upgrades, particularly around rollback, reveal "
        "immediately whether they have done one in production."
    ),
    infographics=["upgrade_flow"],
    questions=[
        Q(
            q="How do IPI and UPI installations differ?",
            level=FOUNDATION,
            answer=(
                "With installer-provisioned infrastructure the installer creates the infrastructure itself - "
                "networks, load balancers, machines, DNS on supported platforms - and the cluster then "
                "manages those machines through the Machine API, so scaling and replacement are native. With "
                "user-provisioned infrastructure you build the infrastructure and the installer only "
                "bootstraps the cluster onto it, which gives you full control and means node lifecycle is "
                "your responsibility."
            ),
            analogy=(
                "IPI is buying a house from a developer who also lays the road and connects the utilities. "
                "UPI is being given the plans and doing the groundwork yourself."
            ),
            context=(
                "The choice has a long tail well beyond installation day. With IPI you get MachineSets, "
                "autoscaling and automated node replacement for free. With UPI, adding a worker means "
                "provisioning a machine, booting it with the right Ignition config, and approving its "
                "certificate signing requests - so every capacity change is a runbook rather than a scale "
                "command. Many enterprises still choose UPI because their network and security teams own the "
                "infrastructure, and that is a legitimate reason as long as everyone understands the "
                "operational cost."
            ),
            steps=[
                "State who creates the infrastructure in each model.",
                "Explain the day-two consequence: Machine API integration versus manual node lifecycle.",
                "Name the legitimate reasons to choose UPI - existing infrastructure ownership, unsupported "
                "platforms, strict network control.",
                "Note the hybrid possibility: UPI control plane with machine-managed workers where the "
                "platform supports it.",
            ],
            evidence=[
                "oc get machineset -A ; oc get machine -A -o wide",
                "oc get infrastructure cluster -o jsonpath='{.status.platform}{\"\\n\"}'",
                "oc get csr | grep -i pending   # a UPI signature during node addition",
            ],
            redflag=(
                "Do not claim UPI is simply harder. It is a deliberate trade of automation for control, and "
                "plenty of organisations make it for good reasons."
            ),
            followup="On a UPI cluster, how do you add a worker node? Walk me through it.",
        ),
        Q(
            q="Which DNS records are critical for an OpenShift cluster?",
            level=FOUNDATION,
            answer=(
                "Three groups. The API endpoint, api.<cluster>.<domain>, which clients and nodes use to reach "
                "the control plane. The internal API endpoint, api-int, which the nodes themselves use and "
                "which must resolve inside the cluster network. And the applications wildcard, "
                "*.apps.<cluster>.<domain>, which resolves to the ingress load balancer and is how every "
                "Route is reachable. On UPI you also need forward and reverse records for the nodes."
            ),
            analogy=(
                "They are the building's street address, the internal extension list, and the sign on the "
                "public entrance. Lose any one and a different set of people cannot find you."
            ),
            context=(
                "DNS is the single most common cause of a failed installation and of a cluster that comes "
                "back wrong after a restart. The distinction between api and api-int matters more than it "
                "looks: they can resolve to different addresses, and a node that cannot resolve api-int "
                "cannot join or stay healthy even though administrators using api see a working cluster. "
                "Wildcard problems are equally distinctive - the console and every application fail while "
                "oc works perfectly."
            ),
            steps=[
                "List the three records and who depends on each.",
                "Explain why api and api-int can differ and what breaks when api-int is wrong.",
                "Describe the wildcard symptom: oc works, every application and the console do not.",
                "Verify resolution from a node, not from your workstation, because that is the view that "
                "matters.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host dig +short api-int.<cluster>.<domain>",
                "dig +short console-openshift-console.apps.<cluster>.<domain>",
                "oc get co dns ingress authentication",
            ],
            redflag=(
                "Do not verify DNS only from your laptop. The record that breaks clusters is the one the "
                "nodes resolve, not the one you do."
            ),
            followup="oc works fine but the console is unreachable. Which record do you check first?",
        ),
        Q(
            q="What load-balancer functions does an OpenShift cluster require?",
            level=FOUNDATION,
            answer=(
                "Two distinct roles. An API load balancer in front of the control plane nodes, handling port "
                "6443 for the Kubernetes API and 22623 for the machine config server, which must be reachable "
                "by nodes but not exposed externally. And an ingress load balancer in front of the router "
                "nodes for ports 80 and 443, which is what the applications wildcard points at. Both need "
                "health checks so that a failed backend is removed rather than continuing to receive "
                "traffic."
            ),
            analogy=(
                "One reception desk for staff and deliveries, another for the public. Same building, "
                "different queues, and each needs to notice when a lift is out of service."
            ),
            context=(
                "The port that gets forgotten is 22623, the machine config server, and forgetting it produces "
                "a very specific failure: existing nodes work, but new nodes cannot bootstrap because they "
                "cannot fetch their Ignition configuration. The other classic is a health check configured as "
                "a plain TCP connect rather than a real endpoint check, so the load balancer happily keeps "
                "sending traffic to a control plane node whose API server is failing."
            ),
            steps=[
                "Separate the API and ingress roles and list the ports each carries.",
                "Stress that 22623 is required for node bootstrap and must not be publicly exposed.",
                "Insist on real health checks rather than TCP connect, so failures are detected.",
                "Verify from a node and from outside, because the two paths can differ.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host curl -sk https://api-int.<cluster>.<domain>:22623/healthz -o /dev/null -w '%{http_code}\\n'",
                "curl -sk https://api.<cluster>.<domain>:6443/healthz",
                "oc get co ingress -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not expose port 22623 to the internet. It serves Ignition configuration, and that is not "
                "a public document."
            ),
            followup="New nodes fail to bootstrap while existing ones are healthy. What do you suspect?",
        ),
        Q(
            q="What are Machines and MachineSets?",
            level=FOUNDATION,
            answer=(
                "A Machine represents one host that the cluster manages - a cloud instance or a "
                "bare-metal server - and its lifecycle is owned by the Machine API. A MachineSet is the "
                "template and replica count for a group of identical Machines, so scaling workers means "
                "changing a MachineSet's replica count and the controller provisions or removes machines "
                "accordingly. It is the same declarative pattern as a ReplicaSet, applied to infrastructure."
            ),
            analogy=(
                "A MachineSet is a standing order for staff of a given role: three of these, with this "
                "specification. Individual Machines are the people who arrive to fill it."
            ),
            context=(
                "Because MachineSets are per failure domain on most platforms, you typically have one per "
                "zone, and that is what makes zone-aware scaling and autoscaling work. It is also why "
                "scaling should always be done by editing the MachineSet rather than by touching the "
                "infrastructure directly - a cloud instance created outside the Machine API is invisible to "
                "the cluster's lifecycle management and becomes a snowflake immediately."
            ),
            steps=[
                "Define both objects and the ReplicaSet analogy for infrastructure.",
                "Explain the per-zone MachineSet pattern and why it enables balanced scaling.",
                "State the rule: scale by editing the MachineSet, never by creating instances manually.",
                "Mention MachineAutoscaler as the object that lets the cluster autoscaler drive them.",
            ],
            evidence=[
                "oc get machineset -n openshift-machine-api -o wide",
                "oc scale machineset <name> -n openshift-machine-api --replicas=5",
                "oc get machine -n openshift-machine-api -o wide | grep -v Running",
            ],
            redflag=(
                "Do not create instances outside the Machine API on an IPI cluster. They will not be "
                "managed, replaced or upgraded with everything else."
            ),
            followup="A Machine is stuck in Provisioning. Where do you look?",
        ),
        Q(
            q="Explain the OpenShift bootstrap process.",
            level=INTERMEDIATE,
            answer=(
                "A temporary bootstrap machine starts first and runs a minimal control plane. The permanent "
                "control plane nodes boot, fetch their Ignition configuration from the bootstrap machine, "
                "form the etcd cluster and start the real control plane. Once the permanent control plane is "
                "serving and the bootstrap machine's job is done, it is removed and the cluster continues on "
                "its own, with the Cluster Version Operator installing the rest of the payload."
            ),
            analogy=(
                "It is the scaffolding on a building. Essential while the structure goes up, deliberately "
                "temporary, and its removal is a milestone rather than a loss."
            ),
            context=(
                "Understanding this explains most installation failures. If the control plane nodes cannot "
                "reach the bootstrap machine on port 22623, they never get their configuration and the "
                "install hangs with nothing obviously wrong. If DNS for api-int is incorrect, etcd members "
                "cannot find each other. The bootstrap machine's journal is the single most useful artefact "
                "when an installation fails, and gathering it before tearing the environment down is the "
                "difference between a diagnosis and a repeat."
            ),
            steps=[
                "Describe the three phases: bootstrap control plane, permanent control plane forms, "
                "bootstrap removed.",
                "Name the dependencies at each phase - DNS, load balancer, port 22623, image access.",
                "Explain how to gather bootstrap logs before the environment is destroyed.",
                "Note that the CVO takes over once the permanent control plane is serving.",
            ],
            evidence=[
                "openshift-install wait-for bootstrap-complete --log-level=debug",
                "openshift-install gather bootstrap --bootstrap <ip> --master <ip>",
                "oc get co ; oc get clusterversion",
            ],
            redflag=(
                "Do not destroy a failed installation before gathering the bootstrap logs. You are throwing "
                "away the only evidence of why it failed."
            ),
            followup="The install hangs waiting for the bootstrap to complete. What are your first checks?",
        ),
        Q(
            q="What is a CSR, and what do you do about a node waiting for approval?",
            level=INTERMEDIATE,
            answer=(
                "A CertificateSigningRequest is how a node asks the cluster to issue it a certificate - first "
                "to join, then again for its serving certificate, and periodically on renewal. On IPI "
                "clusters the machine approver handles them automatically for machines it recognises. On UPI "
                "clusters, or when the approver cannot correlate the request to a known machine, they sit "
                "Pending and the node stays NotReady until an administrator approves them."
            ),
            analogy=(
                "It is a new starter waiting at reception for their pass to be printed. They are on the "
                "system, they just cannot get through the barrier yet."
            ),
            context=(
                "The important discipline is verifying before approving. A pending CSR is a request for a "
                "cluster credential, so approving everything in sight is a genuine security risk - you should "
                "know which node you are expecting and that the request matches it. The other thing to watch "
                "is a cluster that has been powered off long enough for certificates to expire: on restart "
                "there can be a burst of CSRs, and nodes will not become Ready until they are handled."
            ),
            steps=[
                "Explain the two CSR types - client for joining, serving for the kubelet endpoint.",
                "Describe automatic approval on IPI and why UPI often needs manual handling.",
                "Verify the requesting identity and the expected node before approving anything.",
                "After approval, confirm the node reaches Ready and check for a second wave of serving CSRs.",
            ],
            evidence=[
                "oc get csr -o wide | grep -i pending",
                "oc adm certificate approve <csr>",
                "oc get nodes -o wide ; oc describe csr <csr> | head -20",
            ],
            redflag=(
                "Do not blanket-approve every pending CSR without checking. You are issuing cluster "
                "credentials to whoever asked."
            ),
            followup="After a long shutdown, dozens of CSRs are pending. What is your sequence?",
        ),
        Q(
            q="What does MachineHealthCheck do?",
            level=INTERMEDIATE,
            answer=(
                "A MachineHealthCheck watches nodes matching a selector and, when a node has been unhealthy "
                "for longer than a configured timeout, deletes its Machine so the MachineSet provisions a "
                "replacement. On infrastructure that supports it, destroying the machine also provides "
                "fencing, which is what makes it safe to reattach storage elsewhere. A maxUnhealthy threshold "
                "stops it acting during a large-scale event."
            ),
            analogy=(
                "It is a rule that replaces a broken machine on the production line automatically - but "
                "stops itself if half the factory is down, because that is a different problem."
            ),
            context=(
                "The maxUnhealthy setting is the part that matters most and the part people forget. Without "
                "it, a network partition that makes twenty nodes appear unhealthy results in twenty machines "
                "being destroyed and recreated, turning a transient event into a genuine outage. Set it "
                "conservatively, and set the unhealthy timeout longer than your longest expected transient - "
                "a node that is briefly busy is not a node that should be destroyed."
            ),
            steps=[
                "Define the watch, the timeout and the remediation - delete the Machine, let the set "
                "replace it.",
                "Explain the fencing benefit for storage reattachment.",
                "Set maxUnhealthy so a mass event does not trigger mass remediation.",
                "Tune the unhealthy timeout above realistic transient conditions and monitor remediation "
                "events.",
            ],
            evidence=[
                "oc get machinehealthcheck -n openshift-machine-api -o wide",
                "oc get machinehealthcheck <name> -n openshift-machine-api -o jsonpath='{.spec.maxUnhealthy}{\"\\n\"}'",
                "oc get events -n openshift-machine-api --field-selector reason=MachineDeleted",
            ],
            redflag=(
                "Do not deploy MachineHealthCheck without maxUnhealthy. A network blip becomes a fleet "
                "rebuild."
            ),
            followup="A network partition makes ten nodes look unhealthy. What should happen, and why?",
        ),
        Q(
            q="How do you apply a custom kernel argument or kubelet setting to a subset of nodes?",
            level=INTERMEDIATE,
            answer=(
                "By creating a custom MachineConfigPool selected by a node label, then applying a "
                "MachineConfig or KubeletConfig targeted at that pool. The MCO renders the merged "
                "configuration for the pool and the Machine Config Daemon rolls it out node by node, "
                "draining and rebooting each one. That gives you a declarative, auditable change that "
                "survives reboots and applies automatically to any new node that joins the pool."
            ),
            analogy=(
                "It is writing a building specification for one floor rather than sending an electrician "
                "round to rewire each office individually."
            ),
            context=(
                "Creating a separate pool is the part that makes this safe. Applying a kernel argument to "
                "the default worker pool means every worker reboots, whereas a dedicated pool limits the "
                "blast radius to the nodes that actually need the change and lets you validate on one node "
                "first. It also matters for upgrades, because pools update independently and you can pause "
                "one while investigating a problem without stalling the rest."
            ),
            steps=[
                "Label the target nodes and create a MachineConfigPool selecting that label.",
                "Apply the MachineConfig or KubeletConfig targeted at the new pool.",
                "Watch the pool roll out with a low maxUnavailable, validating the first node before "
                "continuing.",
                "Confirm the node's current config annotation matches the new rendered config, and record "
                "the change.",
            ],
            evidence=[
                "oc get mcp -o wide ; oc get mc | tail",
                "oc get node <node> -o jsonpath='{.metadata.annotations.machineconfiguration\\.openshift\\.io/currentConfig}{\"\\n\"}'",
                "oc debug node/<node> -- chroot /host cat /proc/cmdline",
            ],
            redflag=(
                "Do not apply node changes to the default worker pool for a subset requirement. You will "
                "reboot every worker in the cluster to configure four of them."
            ),
            followup="The pool is Degraded after your change. What do you do first?",
        ),
        Q(
            q="What do you check before starting an OpenShift update?",
            level=INTERMEDIATE,
            answer=(
                "Every Cluster Operator Available and none Degraded, the ClusterVersion reporting "
                "Upgradeable true with any admin acknowledgements handled, no critical alerts firing, "
                "MachineConfigPools all updated and none paused, a fresh and verified etcd backup, adequate "
                "capacity to drain nodes without evictions, PDBs that will actually permit drains, and "
                "operator channels compatible with the target version. Then a communicated window and a "
                "written validation plan."
            ),
            analogy=(
                "It is a pre-flight checklist. Nothing on it is clever, and skipping items is exactly how "
                "routine flights become incidents."
            ),
            context=(
                "The two items that most often cause a stall are unrelated to the platform itself: a PDB "
                "that cannot be satisfied, so a node will not drain, and insufficient capacity, so evicted "
                "pods cannot be placed and the drain hangs. Both are discoverable in advance with a dry-run "
                "drain, and both are far cheaper to fix the day before than mid-upgrade with a change window "
                "burning."
            ),
            steps=[
                "Verify cluster health: Cluster Operators, ClusterVersion Upgradeable, alerts, pool status.",
                "Verify recoverability: a recent etcd backup you have actually validated.",
                "Verify capacity and drainability with a server-side dry-run drain on a representative node.",
                "Verify compatibility - operator channels and any deprecated API usage - then communicate the "
                "window and the validation plan.",
            ],
            evidence=[
                "oc adm upgrade ; oc get co | grep -v 'True.*False.*False'",
                "oc adm drain <node> --dry-run=server --ignore-daemonsets --delete-emptydir-data",
                "oc get mcp ; oc get pdb -A -o wide",
            ],
            redflag=(
                "Do not start an upgrade with a Degraded Cluster Operator. You are adding a change to a "
                "system that is already telling you something is wrong."
            ),
            followup="Upgradeable is false with a message about a deprecated API. What do you do?",
        ),
        Q(
            q="An update has stalled. How do you investigate?",
            level=SENIOR,
            answer=(
                "I read the ClusterVersion status, which names the operator the CVO is waiting on, then read "
                "that operator's conditions, which name the reason. From there it is usually one of a small "
                "set: a node that will not drain because of a PDB or a pod with no controller, a "
                "MachineConfigPool that is Degraded, a Cluster Operator blocked on an unavailable "
                "dependency such as storage or DNS, or an image that cannot be pulled in a disconnected "
                "cluster."
            ),
            analogy=(
                "The departure board says which flight is delayed and why. You go to that gate rather than "
                "walking the whole terminal."
            ),
            context=(
                "The failure of nerve here is skipping ahead to drastic actions - force-deleting pods, "
                "pausing pools at random, restarting operators. The upgrade is a controlled process and it "
                "will resume once the blocker is cleared, so the job is to identify and clear that one "
                "blocker. It is also worth saying out loud that an upgrade being slow is not the same as an "
                "upgrade being stuck; MCO rollout across a large pool takes hours by design."
            ),
            steps=[
                "Read ClusterVersion conditions to find which component the CVO is waiting on.",
                "Read that component's conditions and take the message literally.",
                "If it is node-related, find the node and the specific pod or PDB blocking the drain.",
                "Clear the single blocker with the smallest safe action, confirm progress resumes, and "
                "capture must-gather if support may be needed.",
            ],
            evidence=[
                "oc get clusterversion version -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get co | grep -v 'True.*False.*False' ; oc get mcp -o wide",
                "oc get pods -A --field-selector spec.nodeName=<node> --sort-by=.metadata.name",
            ],
            redflag=(
                "Do not force-delete pods to speed up a drain without understanding what they are. That is "
                "how a stalled upgrade becomes a data-loss incident."
            ),
            followup="The MachineConfigPool says Degraded with one node stuck. Walk me through it.",
        ),
        Q(
            q="How do you describe rollback of an OpenShift update?",
            level=SENIOR,
            answer=(
                "I do not describe it as rollback, because a general downgrade is not supported. Once the "
                "control plane has moved, CRDs and stored object versions have moved with it, and going "
                "backwards is not a supported path. In limited cases a partially updated cluster can be "
                "returned to the previous minor version under guidance, but the real answer is that recovery "
                "is forward: fix the blocker and complete the update, or restore from backup if the cluster "
                "is genuinely unrecoverable."
            ),
            analogy=(
                "It is a bridge you drive across, not a lift you can send back down. The plan has to be "
                "about not getting stranded halfway, because reversing is not on the menu."
            ),
            context=(
                "This is a deliberate trap question, and answering \"I would roll back\" is a strong signal "
                "that you have never done a production OpenShift upgrade. The credible answer talks about "
                "the things that make forward recovery reliable: staged upgrades through non-production "
                "first, a verified etcd backup, capacity headroom, and a validation plan that catches "
                "problems while the control plane is still on the old version."
            ),
            steps=[
                "State plainly that downgrade is not a supported general operation, and say why.",
                "Describe forward recovery: identify the blocker, fix it, complete the update.",
                "Describe the catastrophic path: restore from a verified etcd backup, with its data-loss "
                "implications.",
                "Emphasise prevention - staged environments, backups, capacity, and a validation plan.",
            ],
            evidence=[
                "oc get clusterversion version -o jsonpath='{.status.history}' | python3 -m json.tool",
                "oc adm upgrade   # available targets from the current version",
                "Verified etcd backup timestamp and location",
            ],
            redflag=(
                "Do not say you would roll back the cluster. It is the fastest way to reveal you have not "
                "run an upgrade in anger."
            ),
            followup="Halfway through an upgrade a critical application breaks. What are your options?",
        ),
        Q(
            q="How do you replace a failed control-plane node safely?",
            level=SENIOR,
            answer=(
                "Carefully and in order, because quorum is at stake. I confirm the remaining members are "
                "healthy and that quorum exists, remove the failed member from the etcd cluster so it is not "
                "counted, remove its secrets and the Machine object, then provision a replacement and let it "
                "join. Throughout, I make sure I am never taking a second member out, and I verify etcd "
                "health at each step rather than at the end."
            ),
            analogy=(
                "It is replacing one leg of a three-legged stool while someone is sitting on it. The order "
                "matters enormously, and you never lift two legs to save time."
            ),
            context=(
                "The reason this is a senior question is that the tempting shortcuts are the dangerous ones. "
                "Provisioning the replacement before removing the failed member leaves a stale member "
                "counted in quorum arithmetic. Doing maintenance on another control plane node at the same "
                "time takes you below quorum. And skipping the etcd health verification between steps means "
                "you discover a problem two steps later, when the recovery is much harder."
            ),
            steps=[
                "Verify quorum and the health of the remaining etcd members before touching anything.",
                "Remove the failed member from etcd and delete its associated secrets.",
                "Delete the Machine object so a replacement is provisioned, or provision manually on UPI.",
                "Watch the new member join, verify etcd health and Cluster Operator status, and only then "
                "consider other maintenance.",
            ],
            evidence=[
                "oc -n openshift-etcd rsh <etcd-pod> etcdctl member list -w table",
                "oc -n openshift-etcd rsh <etcd-pod> etcdctl endpoint health --cluster",
                "oc get machine -n openshift-machine-api -l machine.openshift.io/cluster-api-machine-role=master",
            ],
            redflag=(
                "Do not add the replacement before removing the failed member. You will be reasoning about "
                "quorum with a member that no longer exists."
            ),
            followup="Two of three control plane nodes are down. Does your procedure still apply?",
        ),
        Q(
            q="When would you pause a MachineConfigPool?",
            level=SENIOR,
            answer=(
                "To hold node changes for a specific, time-boxed reason - a business freeze, an "
                "investigation into a suspected bad configuration, or coordinating a large change across "
                "pools. It is a temporary control, not a configuration choice. While a pool is paused, "
                "configuration changes queue rather than apply, so certificate rotation and security fixes "
                "for those nodes are also delayed, and an upgrade will not complete."
            ),
            analogy=(
                "It is holding the lift on a floor. Fine for thirty seconds while you load something; not "
                "fine as a way of running the building."
            ),
            context=(
                "The specific danger is forgetting. A pool paused during an incident and never unpaused "
                "quietly accumulates pending changes, and the first sign is often an upgrade that will not "
                "finish or nodes whose certificates are about to expire. Treat pausing like a change: it "
                "needs a ticket, an owner, an expected duration and an alert if it stays paused beyond that."
            ),
            steps=[
                "Give a specific reason and an expected duration before pausing anything.",
                "Record it as a change with an owner, and alert on pools paused beyond the expected window.",
                "Understand what is being delayed - configuration, certificate rotation, upgrade progress.",
                "Unpause deliberately and watch the queued changes roll out with a low maxUnavailable.",
            ],
            evidence=[
                "oc get mcp -o custom-columns=NAME:.metadata.name,PAUSED:.spec.paused,UPDATED:.status.conditions[?(@.type==\"Updated\")].status",
                "oc patch mcp <pool> --type merge -p '{\"spec\":{\"paused\":false}}'",
                "oc get mcp <pool> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not leave a pool paused indefinitely. You are silently deferring security updates and "
                "certificate rotation."
            ),
            followup="You find a pool that has been paused for three months. What are the risks?",
        ),
        Q(
            q="How do you detect and remediate node configuration drift?",
            level=SENIOR,
            answer=(
                "The MCO already detects it: the Machine Config Daemon compares the node's actual "
                "configuration against the rendered config it should have and marks the node and pool "
                "Degraded when they differ. So detection is mostly about noticing - alerting on Degraded "
                "pools and on nodes whose current config annotation does not match desired. Remediation is "
                "to remove whatever made the manual change, let the MCO reapply, and if the node cannot be "
                "reconciled, replace it."
            ),
            analogy=(
                "It is a building inspector who checks each floor against the plans. Finding the "
                "discrepancy is automatic; the work is in stopping whoever keeps moving the walls."
            ),
            context=(
                "Drift almost always has a human cause: someone SSHed to a node during an incident and "
                "changed something to get through the night. The technical remediation is easy; the "
                "durable fix is making the legitimate version of that change available as a MachineConfig "
                "so nobody needs to do it by hand next time, and removing standing SSH access so it is not "
                "the path of least resistance."
            ),
            steps=[
                "Alert on Degraded MachineConfigPools and on config annotation mismatches per node.",
                "Identify what changed and why - the MCD logs usually name the file or unit.",
                "Reconcile by reapplying the rendered config, or replace the node if it will not converge.",
                "Close the loop: make the legitimate change declarative and reduce the access that allowed "
                "the drift.",
            ],
            evidence=[
                "oc get mcp -o wide ; oc get nodes -o custom-columns=NAME:.metadata.name,CURRENT:.metadata.annotations.machineconfiguration\\.openshift\\.io/currentConfig,DESIRED:.metadata.annotations.machineconfiguration\\.openshift\\.io/desiredConfig",
                "oc -n openshift-machine-config-operator logs ds/machine-config-daemon -c machine-config-daemon --tail=200",
                "oc debug node/<node> -- chroot /host rpm-ostree status",
            ],
            redflag=(
                "Do not treat drift as a purely technical fix. If the process that caused it stays the same, "
                "the drift comes back."
            ),
            followup="A node is Degraded because someone edited a file during an incident. What now?",
        ),
        Q(
            q="How would you design a version lifecycle strategy for your clusters?",
            level=ARCHITECT,
            answer=(
                "I would pick a supported cadence and hold it, rather than upgrading reactively. That means "
                "deciding whether the estate follows the regular stream or Extended Update Support releases, "
                "defining an environment order - development, then test, then a canary production cluster, "
                "then the rest - with a soak period at each stage, and setting a rule that no cluster falls "
                "more than a stated number of versions behind. Then publishing the calendar so application "
                "teams can plan around it."
            ),
            analogy=(
                "It is a service schedule for a fleet of vehicles. Predictable, staggered, and the point is "
                "that nothing is ever so far behind that servicing becomes a rebuild."
            ),
            context=(
                "The failure mode this prevents is the death spiral: upgrades feel risky, so they are "
                "deferred, so the eventual upgrade spans several versions and genuinely is risky, which "
                "confirms the fear. EUS releases exist precisely for organisations that cannot absorb "
                "frequent change, and choosing them deliberately is far better than drifting into being "
                "years behind. The publishing part matters too - teams cannot plan around a calendar they "
                "have never seen."
            ),
            steps=[
                "Choose the stream - regular or EUS - based on the organisation's real change appetite.",
                "Define the environment order and soak period, and a maximum acceptable version lag.",
                "Automate the pre-upgrade checks so each cycle costs less than the last.",
                "Publish the calendar, review after each cycle, and track version lag as a standing metric.",
            ],
            evidence=[
                "Version inventory across the estate with age and target version",
                "oc get clusterversion -o jsonpath='{.status.desired.version}{\"\\n\"}' per cluster",
                "Upgrade cycle metrics: duration, incidents, rollback-free completion rate",
            ],
            redflag=(
                "Do not let clusters drift several versions behind because upgrades feel risky. The risk "
                "grows faster than the delay."
            ),
            followup="Half the estate is two versions behind. What is your recovery plan?",
        ),
        Q(
            q="How would you design node pools for a production cluster?",
            level=ARCHITECT,
            answer=(
                "I separate by role and by failure domain. Control plane on its own dedicated nodes, sized "
                "for etcd's disk latency needs. Infrastructure nodes for routers, monitoring, logging and "
                "the registry, so platform components do not compete with applications and so licensing is "
                "predictable. Then application pools per workload class - general purpose, memory-heavy, "
                "GPU or latency-sensitive - each as its own MachineSet per zone with taints and labels that "
                "make placement explicit."
            ),
            analogy=(
                "It is zoning a building: plant rooms, offices and the loading bay each get space suited to "
                "them, rather than everyone sharing one open floor and competing for the lift."
            ),
            context=(
                "Infrastructure nodes are the design decision with the clearest payoff. Routers and the "
                "monitoring stack are latency-sensitive and resource-hungry, and leaving them to compete "
                "with application pods produces exactly the intermittent problems that are hardest to "
                "diagnose. Separating pools also gives you independent MachineConfigPools, so a kernel "
                "change or an upgrade can be validated on one class of node without touching the rest."
            ),
            steps=[
                "Separate control plane, infrastructure and application roles onto distinct pools.",
                "Create one MachineSet per pool per failure domain so scaling stays balanced.",
                "Use taints, tolerations and labels so placement is explicit rather than accidental.",
                "Size each pool for its workload profile and validate with real utilisation data, "
                "revisiting quarterly.",
            ],
            evidence=[
                "oc get nodes -L node-role.kubernetes.io/infra -L topology.kubernetes.io/zone",
                "oc get machineset -n openshift-machine-api -o wide",
                "oc get mcp ; oc describe node <infra-node> | sed -n '/Taints/,/Capacity/p'",
            ],
            redflag=(
                "Do not run routers and monitoring on the same nodes as applications in a production "
                "cluster. The contention shows up as latency nobody can attribute."
            ),
            followup="How would you move the router and monitoring workloads onto infra nodes with no downtime?",
        ),
    ],
)
