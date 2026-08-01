"""Part 13 - High availability, backup and disaster recovery."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=13,
    title="High availability, backup and disaster recovery",
    subtitle="Three different problems that people keep answering as if they were one",
    intro=(
        "The fastest way to fail this section is to treat availability, backup and disaster recovery as "
        "synonyms. They answer different questions: availability is about surviving a component failure "
        "without anyone noticing, backup is about recovering data somebody destroyed, and disaster recovery "
        "is about continuing to operate when a whole site is gone. Different mechanisms, different costs, "
        "different tests. The other thing being assessed here is honesty - specifically whether you have "
        "ever actually restored something, or only ever configured a backup job and assumed."
    ),
    infographics=["recovery_matrix"],
    questions=[
        Q(
            q="What does an etcd backup protect, and how do you take one?",
            level=FOUNDATION,
            answer=(
                "An etcd backup is a snapshot of the cluster's own state - every API object, including "
                "Secrets, RBAC, custom resources and workload definitions. OpenShift provides a supported "
                "backup script that runs on a control plane node and produces a snapshot plus the static pod "
                "resources needed to restore. It protects against cluster state loss or corruption. It does "
                "not contain application data, because that lives on persistent volumes."
            ),
            analogy=(
                "It is a photograph of the building's blueprints and tenancy register. Invaluable if the "
                "records room burns down; useless for replacing the contents of the flats."
            ),
            context=(
                "The operational details that matter are cadence, storage location and validation. A backup "
                "sitting on the control plane node it came from protects against very little - it needs to "
                "be off-cluster and, ideally, off-site. And an untested backup is a hypothesis: the only "
                "evidence that it works is having restored it onto a lab cluster and watched the cluster "
                "come up."
            ),
            steps=[
                "Describe what is captured: the etcd snapshot plus the static pod resources.",
                "Run backups on a schedule from a control plane node, and move them off-cluster "
                "immediately.",
                "Encrypt them, because they contain every Secret in the cluster.",
                "Validate by restoring onto a lab cluster periodically and recording the result.",
            ],
            evidence=[
                "oc debug node/<master> -- chroot /host /usr/local/bin/cluster-backup.sh /home/core/backup",
                "ls -lh /home/core/backup   # snapshot and static pod resources",
                "Documented restore test date, target cluster and outcome",
            ],
            redflag=(
                "Do not leave etcd backups on the cluster they came from, unencrypted. They contain every "
                "secret you have."
            ),
            followup="How would you prove your etcd backup actually works?",
        ),
        Q(
            q="How do application backup and etcd backup differ?",
            level=FOUNDATION,
            answer=(
                "They protect different things and neither substitutes for the other. An etcd backup "
                "restores the cluster's definition of the world - namespaces, deployments, secrets, custom "
                "resources - to a point in time. An application backup captures the application's data: "
                "persistent volume contents, database dumps, object storage. If you lose a database's data, "
                "an etcd restore gives you a perfectly reconstructed empty database."
            ),
            analogy=(
                "One is the recipe book, the other is the contents of the fridge. Losing either one leaves "
                "you unable to cook dinner, and they are stored in completely different places."
            ),
            context=(
                "This is the single most common senior-level trap in the whole DR topic, because \"we back "
                "up etcd\" sounds like a complete answer. The follow-up is always about application data, "
                "and the credible response is a matrix: for each critical workload, what protects its "
                "definition, what protects its data, where those copies live, and when each was last "
                "restored successfully."
            ),
            steps=[
                "State the scope of each clearly - cluster state versus application data.",
                "Point out that persistent volume contents are not in etcd at all.",
                "Describe the combination needed for a real recovery of a stateful workload.",
                "Maintain a per-application protection matrix with last successful restore dates.",
            ],
            evidence=[
                "oc get backup -n openshift-adp -o wide   # application backups",
                "Documented etcd backup schedule and location",
                "Protection matrix: workload, state backup, data backup, last restore test",
            ],
            redflag=(
                "Do not answer \"we take etcd backups\" to a question about application data. It is the "
                "exact trap the question was built around."
            ),
            followup="A team deletes their production database's PVC. Does your etcd backup help?",
        ),
        Q(
            q="What are RPO and RTO?",
            level=FOUNDATION,
            answer=(
                "Recovery Point Objective is how much data you can afford to lose, measured in time - an RPO "
                "of one hour means you accept losing up to an hour of transactions. Recovery Time Objective "
                "is how long you can afford to be down before service is restored. They are business "
                "decisions with technical costs: tighter numbers require more replication, more frequent "
                "copies and more standby capacity, and the price rises steeply near zero."
            ),
            analogy=(
                "RPO is how many pages of the manuscript you can bear to rewrite. RTO is how long the "
                "publisher will wait. Both have a price, and the price of zero is enormous."
            ),
            context=(
                "The value of these two numbers is that they turn a vague conversation about \"we need high "
                "availability\" into a design constraint. An RPO of fifteen minutes and an RTO of four hours "
                "points at a very different architecture from an RPO of zero and an RTO of five minutes, and "
                "the cost difference is often an order of magnitude. Getting the business to state them, and "
                "then demonstrating what they actually cost, is the conversation this question is testing."
            ),
            steps=[
                "Define both precisely and note that they are business decisions, not technical ones.",
                "Set them per service tier rather than one number for everything.",
                "Design the mechanism to meet them - backup frequency, replication, standby capacity.",
                "Test and measure the actual achieved numbers, and report the gap honestly.",
            ],
            evidence=[
                "Documented RPO and RTO per service tier, signed off by the business",
                "Measured recovery time from the last DR test, against the target",
                "Backup frequency and replication lag metrics per critical dataset",
            ],
            redflag=(
                "Do not accept \"zero downtime and zero data loss\" as a requirement without pricing it. It "
                "is a wish until somebody has seen the invoice."
            ),
            followup="The business wants RPO zero for everything. How do you run that conversation?",
        ),
        Q(
            q="What does OADP protect, and what does it not?",
            level=INTERMEDIATE,
            answer=(
                "OADP - the OpenShift API for Data Protection, built on Velero - backs up namespaced "
                "resources and their persistent volume data to object storage, and restores them into the "
                "same or a different cluster. That makes it the right tool for namespace-level recovery, "
                "accidental deletion and migration between clusters. It is not a cluster recovery tool: it "
                "does not restore a lost control plane, and it does not replace etcd backups."
            ),
            analogy=(
                "It is a removals company for a flat. Excellent at packing one household and delivering it "
                "elsewhere; not the people you call when the building has collapsed."
            ),
            context=(
                "Two mechanisms matter in practice. CSI snapshots are fast but stay on the same storage "
                "system, so for real durability you want file-system backup or a snapshot that is copied to "
                "object storage. And consistency is your responsibility: without hooks to quiesce the "
                "application, you get a crash-consistent copy that may or may not restore cleanly. Both "
                "details are where a confident-sounding backup strategy quietly fails."
            ),
            steps=[
                "Define the scope: namespaced resources plus volume data, to and from object storage.",
                "Choose the volume method deliberately - snapshot for speed, file-system backup for "
                "portability and durability.",
                "Configure hooks for application consistency on stateful workloads.",
                "Test restores into a scratch namespace regularly, and record the measured restore time.",
            ],
            evidence=[
                "oc get dataprotectionapplication,backupstoragelocation -n openshift-adp",
                "oc get backup <name> -n openshift-adp -o jsonpath='{.status.phase} {.status.progress}{\"\\n\"}'",
                "oc get restore -n openshift-adp -o wide",
            ],
            redflag=(
                "Do not present OADP as your disaster recovery plan for the cluster itself. It restores "
                "namespaces, not control planes."
            ),
            followup="Your OADP backups use CSI snapshots only. What risk have you accepted?",
        ),
        Q(
            q="How do you design application high availability inside one cluster?",
            level=INTERMEDIATE,
            answer=(
                "Multiple replicas as the baseline, spread across failure domains with topology spread "
                "constraints so a node or zone loss cannot take them all. A PodDisruptionBudget that permits "
                "maintenance while protecting a minimum. Honest readiness probes so traffic never reaches a "
                "broken replica, and graceful shutdown so rollouts and drains do not drop connections. Then "
                "enough spare capacity that losing a node does not cause evictions elsewhere."
            ),
            analogy=(
                "It is not enough to have three fire exits if they all open onto the same corridor. Spread "
                "matters as much as count."
            ),
            context=(
                "The part teams miss is capacity headroom. Three replicas spread across three zones is "
                "genuinely resilient only if the cluster can still run all three when one zone is gone - "
                "otherwise the failover produces Pending pods and you have availability on paper only. The "
                "other missing piece is testing: draining a node during business hours, deliberately, is the "
                "cheapest resilience test available and almost nobody does it."
            ),
            steps=[
                "Set replica minimums and spread across real failure domains, not just across nodes.",
                "Add a PDB that permits maintenance while protecting a meaningful minimum.",
                "Get probes and graceful shutdown right, because they govern behaviour during every "
                "disruption.",
                "Maintain capacity headroom for the loss of a domain, and prove it by draining a node "
                "deliberately.",
            ],
            evidence=[
                "oc get deploy <name> -o jsonpath='{.spec.replicas} {.spec.template.spec.topologySpreadConstraints}{\"\\n\"}'",
                "oc get pods -o wide -n <ns> | awk '{print $7}' | sort | uniq -c",
                "oc adm drain <node> --dry-run=server --ignore-daemonsets",
            ],
            redflag=(
                "Do not claim high availability from replica count alone. Three pods on one node is one "
                "node's worth of availability."
            ),
            followup="One zone goes down. Walk me through what happens to your three-replica service.",
        ),
        Q(
            q="What is the etcd restore procedure and what does it cost you?",
            level=INTERMEDIATE,
            answer=(
                "It is a disruptive, last-resort operation. You stop the existing control plane static pods, "
                "restore the snapshot onto one control plane node using the supported restore script, bring "
                "that node up as the single member, then rejoin the others so they resynchronise. Once it "
                "completes, the cluster is at the snapshot's point in time - everything created since is "
                "gone, and certificates and tokens issued since may need attention."
            ),
            analogy=(
                "It is restoring a building's records from last month's photocopy. Everything filed since "
                "then simply never happened, as far as the records are concerned."
            ),
            context=(
                "The consequences are what make this a senior question. Objects created after the snapshot "
                "vanish, but the things they created in the outside world - cloud load balancers, volumes, "
                "DNS entries - still exist and are now orphaned. Nodes that joined after the snapshot are "
                "unknown to the restored cluster and may need to be removed and re-added. That is why an "
                "etcd restore is the option you reach for when there is genuinely nothing else."
            ),
            steps=[
                "Confirm there is no less disruptive option - this is not a routine recovery method.",
                "Follow the documented restore procedure on one control plane node, then rejoin the others.",
                "Reconcile the aftermath: orphaned external resources, unknown nodes, certificate and token "
                "state.",
                "Validate cluster operators, workloads and a real user path before declaring recovery.",
            ],
            evidence=[
                "oc debug node/<master> -- chroot /host /usr/local/bin/cluster-restore.sh <backup-dir>",
                "oc get co ; oc get nodes ; oc get clusterversion",
                "oc get csr | grep -i pending   # nodes re-establishing identity after restore",
            ],
            redflag=(
                "Do not describe etcd restore as a routine recovery step. It is disruptive, lossy and "
                "reserved for genuine cluster loss."
            ),
            followup="After a restore, three nodes are unknown to the cluster. What happened and what do you do?",
        ),
        Q(
            q="How do you back up and restore a stateful application properly?",
            level=INTERMEDIATE,
            answer=(
                "I prefer the application's own mechanism where one exists - a database's native dump or "
                "continuous archiving is consistent by design and understood by the people who run it. That "
                "output is then captured and shipped off-cluster. Where the application has no native "
                "mechanism, I use volume backup with pre and post hooks that quiesce it. Either way, the "
                "backup includes the namespace's objects too, because data without its configuration is not "
                "a recovery."
            ),
            analogy=(
                "You would not back up a bank by photographing the safe. You export the ledger, in a format "
                "the bank can read back."
            ),
            context=(
                "Restore rehearsal is what makes this real, and it exposes things nobody predicted: the "
                "restore takes six hours rather than the assumed one, the application needs a secret that "
                "was never backed up, or the restored data is consistent but the schema version does not "
                "match the deployed image. All three are common, and all three are only ever discovered by "
                "actually doing it."
            ),
            steps=[
                "Prefer the application's native backup mechanism and ship its output off-cluster.",
                "Where none exists, use volume backup with quiesce hooks, and verify the hooks actually ran.",
                "Include the namespace's objects and secrets, because data alone will not start the "
                "application.",
                "Rehearse the full restore on a schedule and record the measured time and any gaps found.",
            ],
            evidence=[
                "oc get backup <name> -n openshift-adp -o jsonpath='{.status.hooks}' | python3 -m json.tool",
                "Restore test log: start time, completion time, verification query result",
                "oc get pvc,secret,cm -n <restored-ns>   # completeness check after restore",
            ],
            redflag=(
                "Do not back up a database by snapshotting its volume with no quiesce and call it done. It "
                "may restore, and you will not know until it matters."
            ),
            followup="Your restore works but takes six hours. Your RTO is two. What now?",
        ),
        Q(
            q="How do you decide between an application restore and an etcd restore?",
            level=SENIOR,
            answer=(
                "By scope. If the damage is confined to one namespace or one application - deleted objects, "
                "corrupted data, a bad release - an application restore is targeted, fast and low risk. An "
                "etcd restore is only appropriate when the cluster's own state is lost or corrupted "
                "cluster-wide, because it rewinds everything and everyone. So my first question is always "
                "how wide the damage is, and my strong default is the narrowest recovery that fixes it."
            ),
            analogy=(
                "One flat has flooded. You do not restore the whole building from last month's plans to fix "
                "one bathroom."
            ),
            context=(
                "The pressure in a real incident pushes the other way, because an etcd restore feels "
                "decisive. Resisting that is the judgement being tested. It is also worth saying that the "
                "two are not mutually exclusive in a genuine disaster: you may restore the cluster state and "
                "then restore application data on top, and the order matters - cluster first, then data, "
                "then validation of a real user path."
            ),
            steps=[
                "Establish the blast radius before choosing a mechanism.",
                "Default to the narrowest recovery that addresses the damage.",
                "Reserve etcd restore for cluster-wide state loss, and state its side effects out loud.",
                "In a genuine disaster, sequence cluster state first, then application data, then end-to-end "
                "validation.",
            ],
            evidence=[
                "Scope assessment: affected namespaces, objects and data",
                "oc get backup,restore -n openshift-adp",
                "Recovery decision log with the reasoning recorded at the time",
            ],
            redflag=(
                "Do not reach for etcd restore to fix a single namespace. You will turn one team's incident "
                "into everybody's."
            ),
            followup="A GitOps prune deleted twelve namespaces. Which mechanism, and why?",
        ),
        Q(
            q="How do you test disaster recovery credibly?",
            level=SENIOR,
            answer=(
                "By running it, on a schedule, with timing. A credible test restores into a real target - a "
                "lab cluster or an isolated namespace - starts the application, runs a functional check, "
                "and measures the elapsed time against the stated RTO. It is run by someone other than the "
                "author of the runbook, because that is what exposes the missing steps. And the result, "
                "including failures, is recorded and reported."
            ),
            analogy=(
                "It is a fire drill rather than a fire policy. Reading the evacuation plan proves nothing "
                "about whether the door at the end of the corridor is locked."
            ),
            context=(
                "The specific value of having someone else run it is that runbooks are always written with "
                "assumed knowledge - a credential the author has, a step they do automatically, a system "
                "they know the address of. A fresh person hits every one of those in twenty minutes. The "
                "other value is the measured time, because stated RTOs are usually optimistic by a factor of "
                "two or three until someone has actually timed a restore."
            ),
            steps=[
                "Schedule tests per critical service, with a defined scenario and success criteria.",
                "Restore into a real target and run a functional verification, not just a status check.",
                "Have someone other than the runbook author execute it, and capture every gap they hit.",
                "Record measured RTO and RPO against target, report the gap, and fix the runbook "
                "immediately.",
            ],
            evidence=[
                "DR test register: date, scenario, executor, measured RTO, gaps found",
                "Restore logs with start and completion timestamps",
                "Runbook change history following each test",
            ],
            redflag=(
                "Do not count a successful backup job as a DR test. Nothing has been proven until something "
                "has been restored and used."
            ),
            followup="Your measured RTO is three times the target. What do you tell the business?",
        ),
        Q(
            q="How would you recover from complete loss of a cluster?",
            level=SENIOR,
            answer=(
                "By rebuilding rather than repairing. The realistic sequence is: provision a new cluster "
                "from infrastructure as code, restore platform configuration from Git through GitOps, "
                "restore application namespaces and data from OADP backups held off-site, repoint DNS and "
                "load balancers, then validate a real user journey before declaring recovery. This only "
                "works if the cluster was reproducible in the first place, which is the actual "
                "prerequisite."
            ),
            analogy=(
                "It is rebuilding from the architectural plans rather than sifting the rubble. The plans "
                "have to exist before the fire."
            ),
            context=(
                "That prerequisite is the point of the question. A cluster built by hand, with configuration "
                "that lives only in the cluster, cannot be recovered this way at all - and that is the "
                "moment people discover their GitOps coverage was partial. The other frequently missing "
                "piece is anything held outside Git and backups: image registry contents, secrets in an "
                "external vault, DNS records, load balancer configuration and certificates."
            ),
            steps=[
                "Provision a replacement cluster from versioned infrastructure as code.",
                "Restore platform configuration through GitOps, and confirm operators reach a healthy state.",
                "Restore application namespaces and data from off-site backups, in dependency order.",
                "Repoint DNS and load balancers, validate a real user journey, then review what was missing "
                "from the automation.",
            ],
            evidence=[
                "Infrastructure as code repository and last successful apply",
                "GitOps repository coverage: what percentage of cluster configuration is in Git",
                "Off-site backup inventory with restore test dates",
            ],
            redflag=(
                "Do not assume the cluster can be rebuilt from Git without checking. Most estates have "
                "configuration that exists nowhere else."
            ),
            followup="What in your current cluster exists only inside the cluster? How would you find out?",
        ),
        Q(
            q="How would you design multi-site disaster recovery for a critical service?",
            level=ARCHITECT,
            answer=(
                "From the RPO and RTO backwards. A warm standby cluster in a second site, with platform and "
                "application configuration delivered to both by GitOps so they never drift, and data "
                "replicated by the application's own mechanism where possible because it understands "
                "consistency better than storage replication does. Then DNS or global load balancing to "
                "shift traffic, a written and rehearsed failover decision process, and an explicit answer "
                "for how you fail back."
            ),
            analogy=(
                "It is a second kitchen in another building, kept stocked and staffed. The point is not that "
                "it exists - it is that you have cooked a full service in it recently."
            ),
            context=(
                "Two things reliably derail these designs. The first is failback, which is almost always "
                "harder than failover because data has diverged, and it is routinely left undesigned. The "
                "second is the human decision: who declares a disaster, on what evidence, and how quickly - "
                "because a technically perfect standby that nobody is authorised to activate at 2am does not "
                "meet any RTO. Both belong in the design, not in a later document."
            ),
            steps=[
                "Derive the topology from RPO and RTO, and price each option honestly.",
                "Deliver configuration to both sites from one Git source so they cannot drift.",
                "Replicate data with the application's own mechanism where it exists, and measure the lag.",
                "Write and rehearse the failover decision process, including authority, and design failback "
                "explicitly.",
            ],
            evidence=[
                "Replication lag metrics per dataset, against the stated RPO",
                "GitOps sync status for both clusters from the same source repository",
                "Failover rehearsal record with measured time and the decision timeline",
            ],
            redflag=(
                "Do not design failover without designing failback. Getting back is usually the harder half "
                "and it is the half nobody rehearses."
            ),
            followup="You failed over successfully. Walk me through how you get back.",
        ),
        Q(
            q="How do you agree and defend RPO and RTO targets with the business?",
            level=ARCHITECT,
            answer=(
                "By pricing the options rather than debating the numbers. I present two or three concrete "
                "architectures with their achievable RPO and RTO, their cost, and their operational burden, "
                "and let the business choose with the trade-off visible. Then I write the chosen numbers "
                "down as a commitment, test against them, and report the measured result - including when "
                "we miss - so the target stays honest rather than aspirational."
            ),
            analogy=(
                "It is insurance. Nobody argues about the premium in the abstract; they choose a policy once "
                "they can see what each level of cover costs and excludes."
            ),
            context=(
                "The failure mode is agreeing to an aspirational number that nobody funds. It survives until "
                "the first real incident, at which point the gap between the commitment and reality becomes "
                "an accountability problem. Reporting measured recovery times against target on a regular "
                "cadence keeps everyone honest, and it is also the most effective way to fund the "
                "improvements you actually need."
            ),
            steps=[
                "Classify services into tiers rather than negotiating each one individually.",
                "Present costed architecture options with achievable numbers for each.",
                "Record the decision as a commitment with an owner, and design to it.",
                "Test against the target and publish measured results, including misses, on a fixed "
                "cadence.",
            ],
            evidence=[
                "Service tier definitions with agreed RPO and RTO and named business owners",
                "Costed options document with achievable numbers per option",
                "Measured recovery times from tests, trended against target",
            ],
            redflag=(
                "Do not agree to a target you cannot demonstrate. The first real incident will convert that "
                "into a much harder conversation."
            ),
            followup="The business will not fund the architecture their stated RTO requires. What do you do?",
        ),
    ],
)
