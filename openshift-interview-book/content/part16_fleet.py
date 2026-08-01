"""Part 16 - Advanced Cluster Management and fleet operations."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=16,
    title="Fleet operations with Advanced Cluster Management",
    subtitle="Doing everything you have just learned, fifty times, without doing it fifty times",
    intro=(
        "Once an organisation has more than a handful of clusters, the interesting questions change. It is "
        "no longer \"how do I configure this\" but \"how do I know every cluster is configured this way, and "
        "what do I do about the three that are not\". That shift - from cluster administration to fleet "
        "operations - is what this part is about, and it is where interviews for senior platform roles "
        "usually end up. The test is simple: if your answer only works when you log into a cluster, it does "
        "not scale to the estate you are being hired to run."
    ),
    infographics=["acm_hub_spoke"],
    questions=[
        Q(
            q="What is Advanced Cluster Management and what does the hub do?",
            level=FOUNDATION,
            answer=(
                "ACM is Red Hat's fleet management layer. One hub cluster runs the management components, "
                "and every other cluster is imported or created as a managed cluster. From the hub you get "
                "cluster lifecycle - create, import, upgrade, hibernate, detach - policy-based governance, "
                "application placement and delivery, and aggregated observability. The point is to make "
                "operations declarative and label-driven rather than repeated per cluster."
            ),
            analogy=(
                "It is head office for a chain of shops. Each shop runs itself day to day; head office sets "
                "the standards, sees the numbers, and rolls out changes."
            ),
            context=(
                "The design consequence people forget is that the hub is itself a critical cluster. If it is "
                "down, managed clusters keep running - workloads are unaffected - but you lose central "
                "governance, observability and the ability to roll out changes. So the hub needs the same "
                "availability treatment as anything else critical, and it is worth being explicit about "
                "which operations degrade when it is unavailable."
            ),
            steps=[
                "Describe the hub and spoke model and the four capability areas.",
                "State the failure behaviour: managed clusters keep serving, central operations stop.",
                "Treat the hub as a critical cluster with its own HA and DR plan.",
                "Emphasise label-driven targeting as the mechanism that makes it scale.",
            ],
            evidence=[
                "oc get managedcluster ; oc get multiclusterhub -A",
                "oc get managedcluster -o custom-columns=NAME:.metadata.name,AVAILABLE:.status.conditions[?(@.type==\"ManagedClusterConditionAvailable\")].status",
                "oc -n open-cluster-management get pods | head",
            ],
            redflag=(
                "Do not describe ACM as a dashboard. It is a control plane for the fleet, and the "
                "interesting questions are about what it enforces."
            ),
            followup="The hub is down for four hours. What actually stops working?",
        ),
        Q(
            q="What is the klusterlet and how does a cluster become managed?",
            level=FOUNDATION,
            answer=(
                "The klusterlet is the agent installed on each managed cluster. It registers with the hub, "
                "pulls work - policies, application manifests, upgrade instructions - and reports status "
                "back. The connection is initiated outbound from the managed cluster, which matters for "
                "network design because the hub does not need inbound access to every cluster. Importing a "
                "cluster is essentially installing and registering that agent."
            ),
            analogy=(
                "It is the branch manager who phones head office for instructions and reports the numbers. "
                "Head office never has to phone the branch."
            ),
            context=(
                "The outbound-only model is worth knowing because it makes ACM viable in network topologies "
                "where the hub could never reach the managed clusters directly - clusters behind NAT, in "
                "customer environments, or at edge sites on intermittent links. It also means that when a "
                "cluster appears unavailable in the hub, the first thing to check is the klusterlet's "
                "connectivity outbound, not the hub's ability to reach it."
            ),
            steps=[
                "Define the klusterlet as the pull-based agent on each managed cluster.",
                "Explain the outbound-only connection model and why it matters for network design.",
                "Describe import: install the agent, register, accept on the hub.",
                "For an unavailable cluster, check klusterlet pods and outbound connectivity first.",
            ],
            evidence=[
                "oc -n open-cluster-management-agent get pods   # on the managed cluster",
                "oc get managedcluster <name> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc -n open-cluster-management-agent logs deploy/klusterlet --tail=100",
            ],
            redflag=(
                "Do not assume the hub connects into managed clusters. The direction of the connection is "
                "often the reason the architecture works at all."
            ),
            followup="A managed cluster shows Unknown on the hub but is serving traffic fine. Where do you look?",
        ),
        Q(
            q="What is a ManagedClusterSet?",
            level=FOUNDATION,
            answer=(
                "A ManagedClusterSet is a grouping of managed clusters that acts as an RBAC and placement "
                "boundary. You put clusters into a set - production, development, a particular business "
                "unit, a region - and then bind that set to namespaces on the hub. Teams with access to "
                "those namespaces can place workloads and policies onto the clusters in their set and "
                "nothing else."
            ),
            analogy=(
                "It is a region assigned to a regional manager. They can act across their region, and they "
                "cannot touch anyone else's shops."
            ),
            context=(
                "This is how you delegate fleet operations without giving everyone the whole estate. Without "
                "cluster sets, the practical choice is between doing everything centrally - which does not "
                "scale - and giving broad hub access, which is unacceptable. With them, an application team "
                "can manage placement across their own clusters while the platform team retains "
                "cluster-wide governance."
            ),
            steps=[
                "Define it as a grouping that serves as both an RBAC and a placement boundary.",
                "Explain binding to hub namespaces and what that grants.",
                "Give the delegation use case, which is the reason it exists.",
                "Design the set structure to match your real organisational boundaries, not the "
                "infrastructure layout.",
            ],
            evidence=[
                "oc get managedclusterset ; oc get managedclustersetbinding -A",
                "oc get managedcluster --show-labels | head",
                "oc auth can-i --list -n <hub-ns> --as=<user>",
            ],
            redflag=(
                "Do not give teams hub-wide access instead of using cluster sets. It is the difference "
                "between delegation and handing over the estate."
            ),
            followup="How would you let an application team deploy to their clusters but not to production?",
        ),
        Q(
            q="How does Placement work?",
            level=INTERMEDIATE,
            answer=(
                "Placement selects which managed clusters a policy, application or upgrade applies to, based "
                "on labels and cluster claims rather than on a hard-coded list. You express intent - all "
                "production clusters in Europe, all clusters with GPU nodes, any three clusters from this "
                "set - and the result is a PlacementDecision naming the matching clusters. New clusters that "
                "match the criteria are picked up automatically."
            ),
            analogy=(
                "It is a mailing list defined by a rule rather than by names. New joiners who meet the "
                "criteria start receiving the newsletter without anyone editing a list."
            ),
            context=(
                "Label discipline is what determines whether this works. If clusters are labelled "
                "inconsistently - some with env=prod, some with environment=production - placement silently "
                "misses clusters, and a policy you believe is enforced everywhere is enforced on two thirds "
                "of the estate. Defining and enforcing a cluster labelling standard is unglamorous and it is "
                "the single highest-value thing you can do for fleet operations."
            ),
            steps=[
                "Explain label and claim based selection producing a PlacementDecision.",
                "Stress that new matching clusters are included automatically, which is the point.",
                "Insist on a documented cluster labelling standard, applied at import.",
                "Verify by reading PlacementDecisions rather than assuming the selector matched.",
            ],
            evidence=[
                "oc get placement,placementdecision -A",
                "oc get placementdecision <name> -o jsonpath='{.status.decisions}' | python3 -m json.tool",
                "oc get managedcluster --show-labels",
            ],
            redflag=(
                "Do not hard-code cluster names in placement. The whole value is that the fleet can grow "
                "without editing every policy."
            ),
            followup="A policy is not applying to two clusters. How do you find out why?",
        ),
        Q(
            q="How do inform and enforce governance modes differ?",
            level=INTERMEDIATE,
            answer=(
                "Inform detects and reports non-compliance without changing anything - you get visibility "
                "and a compliance status per cluster. Enforce actively remediates: it applies the desired "
                "configuration and keeps applying it. Inform is where you start, because it tells you what "
                "the estate actually looks like before you change anything, and because enforcing a policy "
                "against unknown drift can break workloads you did not know depended on it."
            ),
            analogy=(
                "Inform is an inspection that leaves a report. Enforce is an inspector who fixes the wiring "
                "while they are there, whether or not you were using it."
            ),
            context=(
                "The progression matters as much as the definition. Start in inform, look at the "
                "non-compliance report, understand every deviation - some will be legitimate exceptions you "
                "did not know about - then move to enforce on a subset, validate, and widen. Going straight "
                "to enforce across a fleet is how a well-intentioned security policy causes a "
                "multi-cluster outage."
            ),
            steps=[
                "Define both modes and what each does on detecting non-compliance.",
                "Always start in inform and read the resulting compliance report properly.",
                "Investigate every deviation before enforcing, because some are legitimate.",
                "Move to enforce progressively by placement, validating at each stage.",
            ],
            evidence=[
                "oc get policy -A -o custom-columns=NAME:.metadata.name,REMEDIATION:.spec.remediationAction,COMPLIANCE:.status.compliant",
                "oc get policy <name> -n <ns> -o jsonpath='{.status.status}' | python3 -m json.tool",
                "Compliance report per cluster before and after enforcement",
            ],
            redflag=(
                "Do not deploy a new policy in enforce mode across the fleet. You are making an untested "
                "change to every cluster simultaneously."
            ),
            followup="Inform mode shows 12 of 40 clusters non-compliant. What do you do next?",
        ),
        Q(
            q="What is a PolicySet?",
            level=INTERMEDIATE,
            answer=(
                "A PolicySet groups related policies so they can be placed and reported on together - a "
                "security baseline, a compliance profile, a set of operational standards. Instead of "
                "attaching placement to twenty individual policies and reading twenty compliance statuses, "
                "you place the set once and get a single rolled-up view alongside the per-policy detail."
            ),
            analogy=(
                "It is a building regulations package rather than a hundred separate rules. Adopt the "
                "package, get one certificate, and the details are still there if you need them."
            ),
            context=(
                "The practical benefit is that it makes governance legible to people outside the platform "
                "team. \"Cluster X is 94% compliant with the security baseline\" is a sentence an "
                "auditor or a manager can act on, whereas twenty individual policy statuses is not. It also "
                "makes onboarding a new cluster a single placement change rather than twenty."
            ),
            steps=[
                "Define it as a grouping of policies with shared placement and rolled-up status.",
                "Organise sets around meaningful bundles - security baseline, compliance profile, "
                "operational standards.",
                "Use the rolled-up view for reporting and the per-policy detail for remediation.",
                "Onboard new clusters by adding them to the placement, not by attaching policies "
                "individually.",
            ],
            evidence=[
                "oc get policyset -A ; oc get policy -A | wc -l",
                "oc get policyset <name> -o jsonpath='{.status}' | python3 -m json.tool",
                "Compliance dashboard grouped by policy set and cluster",
            ],
            redflag=(
                "Do not manage placement on dozens of individual policies. It becomes unmaintainable at "
                "exactly the scale where you need it."
            ),
            followup="How would you onboard a new cluster into your full governance baseline?",
        ),
        Q(
            q="How does multi-cluster observability work in ACM?",
            level=INTERMEDIATE,
            answer=(
                "An observability add-on is deployed to managed clusters, which forwards a selected set of "
                "metrics to a central store on the hub backed by object storage. You then get "
                "cross-cluster dashboards and the ability to query the fleet, with drill-down into "
                "individual clusters. Alerting still evaluates locally on each cluster, so a cluster that "
                "loses connectivity to the hub keeps alerting rather than going silent."
            ),
            analogy=(
                "It is regional sales figures sent to head office nightly. Head office sees the trend across "
                "the chain; each shop still has its own fire alarm."
            ),
            context=(
                "The cost decision is the metric allow-list. Forwarding everything from fifty clusters "
                "produces a central store that is expensive to run and slow to query, and most of the "
                "series are never looked at. Curating the forwarded set to what fleet-level dashboards and "
                "reports actually use typically cuts volume dramatically with no loss of usefulness, and it "
                "is worth revisiting as dashboards change."
            ),
            steps=[
                "Describe the add-on, forwarding, and central storage backed by object storage.",
                "Note that alert evaluation stays local so partitions degrade gracefully.",
                "Curate the forwarded metric list against what fleet dashboards actually query.",
                "Size and monitor the object storage, and review cost against value periodically.",
            ],
            evidence=[
                "oc get multiclusterobservability -A -o yaml | head -30",
                "oc -n open-cluster-management-observability get pods",
                "Central store ingestion rate and storage growth per cluster",
            ],
            redflag=(
                "Do not forward every metric from every cluster. The cost curve is steeper than anyone "
                "expects and most of it is never queried."
            ),
            followup="Central observability storage is growing 40% a month. What do you look at first?",
        ),
        Q(
            q="How would you upgrade a fleet of clusters through ACM?",
            level=SENIOR,
            answer=(
                "In waves defined by placement, not all at once. Development clusters first, then a canary "
                "production cluster, then production in groups, with a soak period and validation criteria "
                "between waves. Each wave has explicit gates - cluster operators healthy, application SLOs "
                "steady, no new alerts - and a documented decision to proceed. ACM handles the mechanics; "
                "the discipline is in the wave structure and the gates."
            ),
            analogy=(
                "It is rolling out a new aircraft procedure across a fleet. One route first, observed, then "
                "a region, then everywhere - never all at once regardless of how confident you are."
            ),
            context=(
                "The gate that matters most is the soak period, because the problems that only appear at "
                "scale or over time - a memory leak, a certificate that rotates weekly, a batch job that "
                "runs monthly - are invisible in the first hour. Defining the soak duration and the specific "
                "signals you will watch turns \"we upgraded and it seemed fine\" into a repeatable process "
                "with evidence."
            ),
            steps=[
                "Define waves by placement labels, starting with non-production and a production canary.",
                "Set explicit gate criteria and a soak period between waves.",
                "Verify operator channel compatibility across the fleet before starting.",
                "Track progress per cluster from the hub, and hold the wave if any gate fails.",
            ],
            evidence=[
                "oc get managedcluster -o custom-columns=NAME:.metadata.name,VERSION:.status.version.kubernetes",
                "oc get clustercurator -A   # upgrade orchestration state",
                "Wave gate evidence: operator health, SLO stability, alert delta per cluster",
            ],
            redflag=(
                "Do not upgrade the whole fleet in one operation because ACM makes it possible. Capability "
                "is not a reason."
            ),
            followup="Wave two shows a regression in one application. What do you do about waves three to six?",
        ),
        Q(
            q="How do ApplicationSets support fleet GitOps?",
            level=SENIOR,
            answer=(
                "An ApplicationSet generates Argo CD Applications from a template plus a generator - a "
                "cluster list, a placement decision, a directory structure in Git. So one definition "
                "produces a deployment for every matching cluster, with per-cluster values substituted. Add "
                "a new cluster with the right labels and it gets the application automatically; remove it "
                "and the application goes away."
            ),
            analogy=(
                "It is a mail merge for deployments. One letter, one list, and the list can change without "
                "rewriting the letter."
            ),
            context=(
                "This is what makes fleet GitOps sustainable, because the alternative - one Application per "
                "cluster per workload - grows multiplicatively and nobody keeps it in sync. The care needed "
                "is around the generator and the prune behaviour: a mistake in the generator can remove "
                "applications from clusters that should have kept them, so changes to ApplicationSets "
                "deserve more review than changes to a single application."
            ),
            steps=[
                "Explain generators and templating producing per-cluster Applications.",
                "Connect it to ACM placement so the fleet and GitOps share one source of truth about "
                "targeting.",
                "Handle per-cluster differences through values rather than forked manifests.",
                "Review generator changes carefully and understand prune behaviour before applying.",
            ],
            evidence=[
                "oc get applicationset -A ; oc get application -A | wc -l",
                "oc get applicationset <name> -o jsonpath='{.spec.generators}' | python3 -m json.tool",
                "Argo CD application list grouped by destination cluster",
            ],
            redflag=(
                "Do not maintain one Application per cluster by hand. It works for three clusters and "
                "collapses at thirty."
            ),
            followup="A generator change removes applications from five clusters. How do you prevent that?",
        ),
        Q(
            q="When would you use Submariner?",
            level=SENIOR,
            answer=(
                "When workloads in different clusters need direct pod-to-pod or service-to-service "
                "connectivity across the cluster boundary - a stateful system replicating between clusters, "
                "or a service in one cluster consuming another's internal service without going out through "
                "ingress. Submariner builds the cross-cluster network and provides service discovery across "
                "them. If the requirement is just north-south traffic through public endpoints, you do not "
                "need it."
            ),
            analogy=(
                "It is a private tunnel between two office buildings. Worth building if people cross "
                "constantly; unnecessary if they occasionally send an email."
            ),
            context=(
                "The prerequisites are the part that decides feasibility: non-overlapping pod and service "
                "CIDRs across the clusters, and network paths that permit the tunnels. Overlapping CIDRs is "
                "extremely common in estates that grew organically, and discovering it late turns a "
                "connectivity project into a re-addressing project. Ask about CIDR planning before agreeing "
                "to the design."
            ),
            steps=[
                "Establish the requirement: genuine east-west cross-cluster traffic, not north-south.",
                "Check the prerequisites - non-overlapping CIDRs and permitted network paths - before "
                "committing.",
                "Consider simpler alternatives such as exposed endpoints or a service mesh gateway.",
                "Plan for the operational cost: another network layer to monitor, secure and upgrade.",
            ],
            evidence=[
                "oc get submariner -A ; subctl show all",
                "oc get network.config cluster -o jsonpath='{.status.clusterNetwork}' per cluster",
                "Cross-cluster connectivity test results",
            ],
            redflag=(
                "Do not propose Submariner without checking CIDR overlap first. It is the constraint that "
                "most often kills the design."
            ),
            followup="Two clusters have overlapping pod CIDRs. What are your options?",
        ),
        Q(
            q="How would you decide how many clusters an organisation should have?",
            level=ARCHITECT,
            answer=(
                "From boundaries that genuinely need separating, then from operational capacity. Real "
                "boundaries are regulatory or data residency requirements, blast radius for critical "
                "services, environment separation, network or latency constraints, and untrusted tenancy. "
                "Everything else is better served by namespaces in a shared cluster, because every cluster "
                "carries a fixed cost in control plane, upgrades, monitoring and human attention."
            ),
            analogy=(
                "It is deciding how many offices to open. Each one needs a lease, a manager and a fire "
                "certificate, so you open one where the business genuinely needs presence - not because a "
                "department asked."
            ),
            context=(
                "Both failure modes are expensive. Too few clusters means one incident affects everyone and "
                "upgrades become impossible to schedule because there is no window that suits every tenant. "
                "Too many means the platform team spends its time on cluster maintenance rather than "
                "capability, and consistency degrades because nobody can keep forty snowflakes aligned. The "
                "honest answer names both and states the criteria you would use."
            ),
            steps=[
                "List the boundaries that genuinely require separation and test each request against them.",
                "Estimate the fixed cost per cluster - control plane, upgrades, monitoring, attention.",
                "Default to namespaces within a shared cluster unless a real boundary applies.",
                "Ensure whatever number you choose is manageable by fleet automation, not by people.",
            ],
            evidence=[
                "Cluster inventory with purpose, tenant, criticality and justification",
                "Platform team effort per cluster: upgrade hours, incident hours, maintenance hours",
                "Utilisation per cluster - a fleet of half-empty clusters is a design smell",
            ],
            redflag=(
                "Do not give every team their own cluster. You have distributed the platform team's "
                "attention until none of the clusters get enough of it."
            ),
            followup="A team demands their own cluster for isolation. How do you evaluate the request?",
        ),
        Q(
            q="How do you keep configuration consistent across a fleet while allowing exceptions?",
            level=ARCHITECT,
            answer=(
                "One source of truth in Git, delivered by placement so targeting is label-driven, with "
                "policies in inform mode giving continuous compliance reporting. Exceptions exist - they "
                "always do - but they are declared, not discovered: a documented deviation with an owner, a "
                "justification and a review date, expressed as a label that changes placement rather than as "
                "a manual change on the cluster."
            ),
            analogy=(
                "It is a building standard with a register of approved variations. The variation is fine; "
                "the undocumented variation is what fails the inspection."
            ),
            context=(
                "The reason to make exceptions first-class is that suppressing them does not work. Teams "
                "have genuine needs, and if the process offers no legitimate route they make the change "
                "manually and nobody records it. A visible exception register with expiry dates turns "
                "invisible drift into a managed backlog, and it gives you a number to report - how many "
                "exceptions exist and how old they are - which is what drives them down over time."
            ),
            steps=[
                "Define the baseline in Git and deliver it by label-driven placement.",
                "Run compliance policies in inform mode continuously to see reality, not intent.",
                "Make exceptions declared objects with owner, justification and expiry.",
                "Report exception count and age as a standing metric, and drive it down deliberately.",
            ],
            evidence=[
                "Compliance percentage per policy set across the fleet",
                "Exception register with owner, justification and review date",
                "oc get managedcluster --show-labels   # exception labels visible in placement",
            ],
            redflag=(
                "Do not pretend exceptions do not exist. Undeclared exceptions are just drift with better "
                "manners."
            ),
            followup="You have 30 exceptions, half of them over a year old. What is your plan?",
        ),
    ],
)
