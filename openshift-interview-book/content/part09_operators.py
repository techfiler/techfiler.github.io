"""Part 9 - Operators and the Operator Lifecycle Manager."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=9,
    title="Operators and lifecycle management",
    subtitle="The chain from catalogue to running controller, and what to do when it stops halfway",
    intro=(
        "Operators are how OpenShift ships almost everything optional, so being fluent in the OLM object "
        "chain is a practical skill rather than trivia. The chain is short - CatalogSource, Subscription, "
        "InstallPlan, ClusterServiceVersion, operator pod - and almost every installation problem is "
        "diagnosed by walking it forwards and stopping at the first object that has no child. The other half "
        "of this topic is judgement: which operators you should adopt at all, and what you take on when you "
        "put someone else's controller in your cluster with cluster-wide permissions."
    ),
    infographics=["olm_chain"],
    questions=[
        Q(
            q="What is an Operator?",
            level=FOUNDATION,
            answer=(
                "An operator is a controller that encodes the operational knowledge for a specific "
                "application. It watches custom resources and reconciles the real world toward them - "
                "installing, configuring, upgrading, backing up, failing over. The idea is that the "
                "instructions that used to live in a runbook and a person's head become code that runs "
                "continuously, so the system repairs and manages itself the same way Kubernetes manages "
                "pods."
            ),
            analogy=(
                "It is hiring a specialist who never sleeps. Instead of a runbook that says how to add a "
                "database replica, you have someone watching who does it whenever the spec says so."
            ),
            context=(
                "The reason this matters beyond definitions is that installing an operator is a trust "
                "decision. You are placing a controller with broad permissions into your cluster, and it will "
                "act on its own schedule - including upgrading itself if you chose automatic approval. That "
                "is enormously valuable when the operator is mature and enormously risky when it is not, "
                "which is why maturity level and permission scope are the questions to ask before "
                "installation, not after."
            ),
            steps=[
                "Define it as a controller plus custom resources encoding operational knowledge.",
                "Give the capability spectrum - install, configure, upgrade, backup, autopilot behaviours.",
                "Point out the trust implication: broad permissions and autonomous action.",
                "State what you check before adopting one: maturity, permissions, update channel, support "
                "status.",
            ],
            evidence=[
                "oc get csv -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase",
                "oc get csv <csv> -n <ns> -o jsonpath='{.spec.install.spec.clusterPermissions}' | python3 -m json.tool",
                "oc get crd | grep <operator-domain>",
            ],
            redflag=(
                "Do not describe an operator as \"an installer\". Installation is the least interesting "
                "thing a good operator does."
            ),
            followup="What do you check before installing a third-party operator in production?",
        ),
        Q(
            q="What is a CatalogSource?",
            level=FOUNDATION,
            answer=(
                "A CatalogSource is a pod serving an index of available operator bundles, and it is where OLM "
                "looks to find operators you can install. OpenShift ships default sources - the Red Hat "
                "operators catalogue, certified operators, community operators - and you can add your own, "
                "which is exactly what you do in a disconnected environment where the catalogue is mirrored "
                "into an internal registry."
            ),
            analogy=(
                "It is the shop's catalogue. Nothing can be ordered that is not in a catalogue the shop "
                "actually has on the shelf."
            ),
            context=(
                "The reason to know this precisely is that a broken CatalogSource makes operators disappear "
                "from the console with no obvious explanation, and it is the first link in the install chain. "
                "In disconnected clusters it is also the most common failure point: the catalogue pod cannot "
                "pull its index image because of a proxy, a missing trust bundle, or a mirror that was never "
                "refreshed after an upgrade."
            ),
            steps=[
                "Define it as an index-serving pod that OLM queries.",
                "Name the default sources and the disconnected use case for custom ones.",
                "Explain the symptom of failure: operators missing from the catalogue entirely.",
                "Check the catalog pod's status and logs first - image pull, proxy, and trust are the usual "
                "causes.",
            ],
            evidence=[
                "oc get catalogsource -A ; oc -n openshift-marketplace get pods",
                "oc get catalogsource <name> -n openshift-marketplace -o jsonpath='{.status}' | python3 -m json.tool",
                "oc -n openshift-marketplace logs <catalog-pod> --tail=50",
            ],
            redflag=(
                "Do not conclude an operator \"does not exist\" because it is not in the console. Check "
                "whether its catalogue is healthy first."
            ),
            followup="In a disconnected cluster, no operators are listed at all. What do you check?",
        ),
        Q(
            q="What is a Subscription?",
            level=FOUNDATION,
            answer=(
                "A Subscription is your declaration that you want a particular operator, from a particular "
                "catalogue, following a particular channel, with either automatic or manual approval for "
                "updates. OLM reads it and resolves an InstallPlan. The channel is the important part - it "
                "determines which stream of versions you follow, and choosing a channel that is not "
                "compatible with your cluster version is a common way to get stuck."
            ),
            analogy=(
                "It is a magazine subscription. You choose the title, the edition and whether new issues "
                "arrive automatically or wait for you to say yes."
            ),
            context=(
                "The automatic versus manual choice is a real operational decision rather than a preference. "
                "Automatic keeps you current with security fixes and is right for well-tested platform "
                "operators; manual gives you a change window and is right for anything that touches data or "
                "that you want to test first. Whichever you choose, the Subscription's status is where OLM "
                "reports resolution failures, and that message is usually specific enough to act on."
            ),
            steps=[
                "Define the four inputs: operator name, catalogue, channel, approval mode.",
                "Explain channel selection and its relationship to the cluster version.",
                "Contrast automatic and manual approval and say when each is appropriate.",
                "Read the Subscription's status conditions when nothing installs - it names the resolution "
                "failure.",
            ],
            evidence=[
                "oc get subscription -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,CHANNEL:.spec.channel,APPROVAL:.spec.installPlanApproval",
                "oc get subscription <name> -n <ns> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get packagemanifest <name> -o jsonpath='{.status.channels[*].name}{\"\\n\"}'",
            ],
            redflag=(
                "Do not set every operator to automatic approval without thinking. Some of them will upgrade "
                "themselves during your busiest week."
            ),
            followup="How do you decide between automatic and manual approval for a data-plane operator?",
        ),
        Q(
            q="What is a ClusterServiceVersion?",
            level=FOUNDATION,
            answer=(
                "The CSV is the manifest for a specific operator version: the deployment that runs the "
                "operator, the RBAC it requires, the CRDs it owns, its dependencies, and metadata such as "
                "install modes and upgrade edges. When you look at whether an operator is actually installed "
                "and healthy, the CSV's phase is the authoritative answer - Succeeded means it installed, "
                "anything else has a reason attached."
            ),
            analogy=(
                "It is the appointment letter for a specific employee: their job title, their access rights, "
                "their responsibilities and who they report to."
            ),
            context=(
                "The CSV is where you go to answer the security question that should always be asked about a "
                "third-party operator: what permissions does it want? The clusterPermissions section lists "
                "the RBAC it will be granted, and it is not unusual to find operators requesting far more "
                "than they need. Reading it before installation takes two minutes and occasionally changes "
                "the decision entirely."
            ),
            steps=[
                "Define the CSV as the versioned operator manifest with deployment, RBAC and owned CRDs.",
                "Use its phase and conditions as the source of truth for install health.",
                "Read clusterPermissions before adopting a third-party operator.",
                "Note install modes, which determine whether it can watch one namespace or must be "
                "cluster-wide.",
            ],
            evidence=[
                "oc get csv -n <ns> -o custom-columns=NAME:.metadata.name,PHASE:.status.phase,MESSAGE:.status.message",
                "oc get csv <csv> -n <ns> -o jsonpath='{.spec.installModes}' | python3 -m json.tool",
                "oc describe csv <csv> -n <ns> | sed -n '/Conditions/,$p'",
            ],
            redflag=(
                "Do not install a third-party operator without reading the permissions in its CSV. You are "
                "granting them, whether or not you looked."
            ),
            followup="An operator requests cluster-wide secret read access. What do you do?",
        ),
        Q(
            q="What is an InstallPlan and how does approval work?",
            level=INTERMEDIATE,
            answer=(
                "An InstallPlan is the concrete set of resources OLM has resolved for a Subscription - the "
                "CSV to install, its dependencies, and the CRDs to create. With automatic approval it is "
                "approved and executed immediately. With manual approval it sits in a pending state until "
                "someone approves it, which is what gives you a change window. An InstallPlan that stays "
                "pending forever is usually a manual approval nobody knew about."
            ),
            analogy=(
                "It is the quotation before the work starts. Automatic approval means the builders begin "
                "immediately; manual means it waits on your desk for a signature."
            ),
            context=(
                "The failure this produces is quietly common: an operator is on manual approval, a new "
                "version becomes available, an InstallPlan is created and never approved, and months later "
                "someone notices the operator has not been updated since installation. Alerting on pending "
                "InstallPlans older than a threshold turns that from an audit finding into a routine ticket."
            ),
            steps=[
                "Define the InstallPlan as the resolved set of resources for a Subscription.",
                "Explain the two approval modes and where the approval is recorded.",
                "Describe the stuck-pending symptom and how long it typically goes unnoticed.",
                "Alert on pending InstallPlans and review them as part of routine maintenance.",
            ],
            evidence=[
                "oc get installplan -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,APPROVED:.spec.approved,PHASE:.status.phase",
                "oc patch installplan <name> -n <ns> --type merge -p '{\"spec\":{\"approved\":true}}'",
                "oc get installplan -A -o json | jq '.items[]|select(.spec.approved==false)|.metadata.name'",
            ],
            redflag=(
                "Do not use manual approval without an alert on pending plans. You have created a process "
                "with no reminder attached."
            ),
            followup="An operator has not updated in eight months. Give me the two most likely causes.",
        ),
        Q(
            q="What is an OperatorGroup?",
            level=INTERMEDIATE,
            answer=(
                "An OperatorGroup declares which namespaces the operators in its namespace are allowed to "
                "watch. It gives the operator the target namespace list and the RBAC scope to match. If it is "
                "missing, misconfigured, or if two OperatorGroups exist in one namespace, operator "
                "installation fails or the operator sits doing nothing, because it has no valid watch scope."
            ),
            analogy=(
                "It is the territory assigned to a regional manager. Without a defined territory they turn "
                "up for work and have no idea which branches are theirs."
            ),
            context=(
                "This is one of the most confusing OLM failures because the symptom - a CSV stuck in a "
                "pending or failed phase with a message about install modes - does not obviously point at "
                "the OperatorGroup. The usual cause is a mismatch between the operator's supported install "
                "modes and what the OperatorGroup asks for: an operator that only supports AllNamespaces "
                "placed in an OperatorGroup scoped to a single namespace, or two groups in the same "
                "namespace."
            ),
            steps=[
                "Define it as the watch-scope declaration for operators in a namespace.",
                "Connect it to the CSV's supported install modes - they must be compatible.",
                "Name the failure signatures: no valid OperatorGroup, multiple groups, unsupported mode.",
                "Check it early when a CSV will not reach Succeeded and the message mentions install modes.",
            ],
            evidence=[
                "oc get operatorgroup -A",
                "oc get csv <csv> -n <ns> -o jsonpath='{.status.message}{\"\\n\"}'",
                "oc get operatorgroup <og> -n <ns> -o jsonpath='{.spec.targetNamespaces}{\"\\n\"}'",
            ],
            redflag=(
                "Do not create a second OperatorGroup in a namespace to fix a scope problem. Two groups is "
                "itself an error state."
            ),
            followup="A CSV is stuck with an install mode message. Walk me through it.",
        ),
        Q(
            q="How do operator reconciliation loops work in practice?",
            level=INTERMEDIATE,
            answer=(
                "The operator watches its custom resources and the objects it owns. On any change - or on a "
                "periodic resync - it computes the difference between the spec and the observed world and "
                "takes action, then writes what it did and what it is blocked on into the custom resource's "
                "status conditions. Well-behaved operators are idempotent and level-triggered, meaning they "
                "act on current state rather than on the event that woke them."
            ),
            analogy=(
                "It is a gardener who walks the whole garden each morning rather than remembering every "
                "instruction they were given. The state of the garden is the instruction."
            ),
            context=(
                "The operational consequence is that the custom resource's status is your primary "
                "diagnostic, and the operator's logs are your secondary one. It also explains a specific "
                "frustration: manual changes to objects an operator owns are reverted, sometimes within "
                "seconds. The right response is to change the custom resource, not the managed object - and "
                "if the custom resource does not expose what you need, that is a conversation with the "
                "operator's maintainers, not a reason to fight the loop."
            ),
            steps=[
                "Describe the loop: watch, diff, act, write status.",
                "Explain level-triggered versus edge-triggered and why idempotency matters.",
                "Use the CR's status conditions as the first diagnostic, operator logs as the second.",
                "State the rule: change the CR, never the managed object, because reconciliation reverts it.",
            ],
            evidence=[
                "oc get <cr-kind> <name> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc -n <operator-ns> logs deploy/<operator> --tail=200",
                "oc get events -n <ns> --sort-by=.lastTimestamp | tail -20",
            ],
            redflag=(
                "Do not edit a resource an operator owns and expect it to stick. The loop will undo it and "
                "you will have learned nothing."
            ),
            followup="Your change to an operator-managed Deployment keeps disappearing. What do you do?",
        ),
        Q(
            q="How do you sequence operator updates around a cluster upgrade?",
            level=INTERMEDIATE,
            answer=(
                "Before upgrading the cluster I check every installed operator's channel against the target "
                "OpenShift version, because an operator on a channel that does not support the target can "
                "block the upgrade or break afterwards. Where a newer channel is required, I move the "
                "operator first, in a maintenance window, and validate. Then I upgrade the cluster, then I "
                "revisit operators that have newer channels aligned with the new version."
            ),
            analogy=(
                "It is checking that your plugins support the new version of the application before "
                "upgrading the application, not after it fails to start."
            ),
            context=(
                "This is one of the most common causes of an upgrade that technically succeeded but left "
                "something broken. Operators declare compatibility, and the cluster's Upgradeable condition "
                "can reflect it, but not every operator is well-behaved about signalling. Building an "
                "explicit pre-upgrade inventory - operator, current version, channel, supported cluster "
                "versions - turns this from a surprise into a checklist item."
            ),
            steps=[
                "Inventory installed operators with current version, channel and stated compatibility.",
                "Move operators to a compatible channel first, one at a time, with validation.",
                "Check the cluster's Upgradeable condition and any operator-reported blockers.",
                "Upgrade the cluster, validate, then align operators with the new version's channels.",
            ],
            evidence=[
                "oc get subscription -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,CHANNEL:.spec.channel,CSV:.status.installedCSV",
                "oc adm upgrade   # Upgradeable condition and any blocking messages",
                "oc get clusterversion version -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not upgrade the cluster and deal with operators afterwards. Some of them will not start "
                "on the new version and you will be debugging two changes at once."
            ),
            followup="An operator's channel does not support your target version. What are your options?",
        ),
        Q(
            q="An operator will not install. Walk me through it.",
            level=SENIOR,
            answer=(
                "I walk the chain forwards and stop at the first object with no child. Is the CatalogSource "
                "pod running and serving? Does the Subscription resolve, or does its status name a "
                "resolution failure? Was an InstallPlan created, and is it waiting for approval? Did the CSV "
                "install, and if it is failed, what does its message say? Is there a valid OperatorGroup with "
                "a compatible install mode? Only then do I look at the operator pod itself."
            ),
            analogy=(
                "It is following a paper trail through an office. You do not search the whole building - you "
                "find the desk where the form stopped moving."
            ),
            context=(
                "In practice most failures cluster into four causes: a catalogue that cannot pull its index "
                "image, especially behind a proxy or in a disconnected cluster; a pending InstallPlan on "
                "manual approval; an OperatorGroup mismatch; and dependency resolution failing because "
                "another operator's version conflicts. Each has a distinct message, so the discipline of "
                "reading the status rather than guessing pays off immediately."
            ),
            steps=[
                "Check CatalogSource pod health and whether the package appears in the package manifests.",
                "Read the Subscription's status conditions for a resolution failure message.",
                "Check whether an InstallPlan exists and whether it is approved.",
                "Read the CSV phase and message, verify the OperatorGroup and install mode, then inspect the "
                "operator pod's logs.",
            ],
            evidence=[
                "oc get catalogsource,subscription,installplan,csv -n <ns>",
                "oc get subscription <name> -n <ns> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc -n openshift-operator-lifecycle-manager logs deploy/catalog-operator --tail=100",
            ],
            redflag=(
                "Do not delete and reinstall the Subscription as a first response. You lose the status "
                "message that was about to tell you the answer."
            ),
            followup="The Subscription reports a constraints-not-satisfiable error. What does that mean?",
        ),
        Q(
            q="How do you run operators in a disconnected environment?",
            level=SENIOR,
            answer=(
                "Everything has to be mirrored and the cluster has to be told where to find it. I use "
                "oc-mirror to pull the release payload, the operator catalogues and their bundle images into "
                "an internal registry, then configure the cluster with ImageDigestMirrorSet and "
                "ImageTagMirrorSet so image references are redirected, add the registry's CA to the cluster "
                "trust bundle, and replace the default CatalogSources with the mirrored ones. Then I verify "
                "before anyone depends on it."
            ),
            analogy=(
                "It is stocking a remote site's warehouse before winter. Nothing can be ordered later, so "
                "the inventory list has to be right the first time."
            ),
            context=(
                "The failures here are almost always trust and redirection rather than the mirroring itself. "
                "A catalogue pod that cannot pull its index because the registry CA is not trusted, an image "
                "reference that was not covered by the mirror set, or a proxy configuration that intercepts "
                "registry traffic. It is also a recurring obligation: every cluster upgrade needs its "
                "payload and catalogues re-mirrored first, and forgetting that is what leaves a disconnected "
                "cluster unable to upgrade."
            ),
            steps=[
                "Mirror the release payload and the required operator catalogues with oc-mirror, using a "
                "pinned image set configuration.",
                "Apply ImageDigestMirrorSet and ImageTagMirrorSet, and add the registry CA to the cluster "
                "trust bundle.",
                "Disable the default sources and create CatalogSources pointing at the mirrored index.",
                "Verify by installing a test operator, and re-mirror as a standing step before every "
                "upgrade.",
            ],
            evidence=[
                "oc get imagedigestmirrorset,imagetagmirrorset",
                "oc get catalogsource -n openshift-marketplace -o wide",
                "oc -n openshift-marketplace logs <catalog-pod> | grep -i -E 'x509|refused|denied'",
            ],
            redflag=(
                "Do not forget the trust bundle. A perfectly mirrored registry is useless if the cluster "
                "does not trust its certificate."
            ),
            followup="A mirrored catalogue pod crashes with an x509 error. What is missing?",
        ),
        Q(
            q="How do you evaluate whether to adopt a third-party operator?",
            level=SENIOR,
            answer=(
                "I look at four things. Support status - is it Red Hat supported, certified, or community, "
                "and who do I call at 3am. Permission scope - what does the CSV request, and is it "
                "proportionate. Failure behaviour - what happens to running workloads if the operator is "
                "down, upgraded badly, or removed. And exit cost - can I uninstall it cleanly, or does it "
                "leave finalizers and CRDs behind that make the cluster hard to clean up."
            ),
            analogy=(
                "It is hiring a contractor with keys to the building. References, scope of access, what "
                "happens if they do not turn up, and how hard it is to end the arrangement."
            ),
            context=(
                "The exit cost question is the one people skip and later regret. Operators that own CRDs with "
                "finalizers can make namespaces impossible to delete once the operator is gone, and "
                "uninstalling in the wrong order - operator first, custom resources second - is exactly how "
                "you get stuck. Testing the uninstall path in a non-production cluster before adopting is "
                "cheap insurance."
            ),
            steps=[
                "Establish support status and the escalation path for production incidents.",
                "Read the requested RBAC in the CSV and challenge anything disproportionate.",
                "Test failure behaviour: stop the operator and confirm running workloads survive.",
                "Test the uninstall path, including custom resource removal order, before adopting.",
            ],
            evidence=[
                "oc get csv <csv> -o jsonpath='{.spec.install.spec.clusterPermissions}' | python3 -m json.tool",
                "oc get packagemanifest <name> -o jsonpath='{.status.catalogSource}{\"\\n\"}'",
                "Documented uninstall test result from a non-production cluster",
            ],
            redflag=(
                "Do not adopt an operator without testing what happens when it is not running. Some of them "
                "take the workload with them."
            ),
            followup="An operator you removed left a namespace stuck Terminating. How do you recover?",
        ),
        Q(
            q="When would you write your own operator rather than use Helm or GitOps?",
            level=ARCHITECT,
            answer=(
                "Only when the thing you need is genuinely continuous and stateful - ongoing reconciliation, "
                "failover, backup orchestration, complex upgrade sequencing that depends on runtime state. "
                "If the requirement is templating and deploying manifests, Helm plus GitOps does it with far "
                "less to maintain. An operator is a long-lived piece of software with its own upgrade, "
                "security and on-call burden, and that cost is easy to underestimate at the point of "
                "writing it."
            ),
            analogy=(
                "You do not build a robot to hang your washing out twice a week. You build one when the job "
                "has to be done continuously, precisely, and while nobody is watching."
            ),
            context=(
                "The pattern that usually wins in enterprises is to reserve operators for the two or three "
                "genuinely stateful platform capabilities and use GitOps for everything else. The teams that "
                "write operators for every internal service end up with a dozen controllers that all need "
                "maintaining, none of which anyone remembers how to debug. If you do write one, the operator "
                "SDK and a clear conditions contract matter more than clever logic."
            ),
            steps=[
                "Ask whether the work is continuous and state-dependent, or a deployment of static manifests.",
                "Prefer GitOps plus Helm or Kustomize for anything declarative and stateless.",
                "If an operator is justified, scope it narrowly and define its status conditions contract "
                "first.",
                "Budget for its lifecycle - upgrades, CVEs, on-call ownership - before committing.",
            ],
            evidence=[
                "Inventory of in-house controllers with owner, last release and open issue count",
                "oc get crd -l app.kubernetes.io/managed-by=<team>",
                "Comparison of maintenance effort: GitOps application versus custom controller",
            ],
            redflag=(
                "Do not write an operator to deploy static YAML. You have replaced a template with a "
                "codebase and an on-call rota."
            ),
            followup="A team wants an operator for their microservice deployment. How do you respond?",
        ),
    ],
)
