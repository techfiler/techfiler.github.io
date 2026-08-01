"""Part 15 - Automation, GitOps and change control."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=15,
    title="Automation, GitOps and change control",
    subtitle="Making change repeatable, reviewable and reversible - and knowing what not to automate",
    intro=(
        "Automation questions are really change-management questions. The interviewer is not checking "
        "whether you can write a playbook; they are checking whether changes to your platform have an "
        "author, a reviewer, a timestamp and a way back. That is why GitOps comes up so often, and why the "
        "best answers talk about drift detection, emergency changes and secret handling rather than about "
        "tools. The other thing being assessed is judgement about scope: automating the wrong thing, or "
        "automating something nobody understands manually yet, creates a machine for producing incidents at "
        "speed."
    ),
    infographics=["gitops_flow"],
    questions=[
        Q(
            q="What is idempotency and why does it matter in automation?",
            level=FOUNDATION,
            answer=(
                "An idempotent operation produces the same result whether you run it once or fifty times. In "
                "practice it means describing the desired state - this package installed, this file with "
                "this content, this object present - rather than the actions to get there. It matters "
                "because automation gets re-run: after a partial failure, during a retry, on a schedule. "
                "Non-idempotent automation turns a re-run into a new incident."
            ),
            analogy=(
                "\"Make sure there are three chairs in the room\" is idempotent. \"Add three chairs\" is not, "
                "and after four runs the room is unusable."
            ),
            context=(
                "This is also why declarative tools are preferred for infrastructure: Kubernetes objects, "
                "Ansible modules that describe state, Terraform resources. The classic failure is a shell "
                "script that appends a line to a configuration file - run it three times and the file has "
                "three copies, and the failure appears days later when something parses it. Testing "
                "automation by running it twice in a row is a trivially cheap check that catches most of "
                "these."
            ),
            steps=[
                "Define idempotency and connect it to describing state rather than actions.",
                "Give the appending-to-a-file example as the canonical failure.",
                "Prefer declarative modules and objects over imperative commands.",
                "Test by running twice and asserting that the second run reports no change.",
            ],
            evidence=[
                "ansible-playbook site.yml --check --diff   # second run should show no changes",
                "oc apply -f manifests/ --dry-run=server",
                "CI job that applies the same change twice and asserts a no-op",
            ],
            redflag=(
                "Do not present a script that only works on a clean system as automation. Real systems are "
                "never clean and re-runs always happen."
            ),
            followup="How would you make a config-file-appending script idempotent?",
        ),
        Q(
            q="What is GitOps and what problem does it solve?",
            level=FOUNDATION,
            answer=(
                "GitOps means the desired state of the cluster lives in Git, and a controller in the cluster "
                "continuously reconciles reality toward it. The problem it solves is not deployment - it is "
                "accountability and recoverability. Every change has an author, a review, a timestamp and a "
                "revert. Drift is detected because the controller keeps comparing. And rebuilding a cluster "
                "becomes pointing the controller at the repository rather than remembering what was done."
            ),
            analogy=(
                "It is the difference between a building maintained by whoever was on shift and one "
                "maintained to a documented specification that is checked weekly."
            ),
            context=(
                "The audit and recovery benefits are what make this land with senior interviewers. \"Who "
                "changed this and why\" becomes a Git question rather than an investigation. \"Can we "
                "rebuild this cluster\" becomes a test rather than a hope. The caveat worth adding is "
                "coverage: GitOps only helps for what is actually in Git, and most estates have "
                "configuration that lives only in the cluster until somebody checks."
            ),
            steps=[
                "Define the model: Git as desired state, an in-cluster controller reconciling continuously.",
                "Name the real benefits - attribution, review, revert, drift detection, reproducibility.",
                "Note that manual changes are reverted, which is the feature and the friction.",
                "Measure coverage: what fraction of cluster configuration is actually in Git.",
            ],
            evidence=[
                "oc get application -n openshift-gitops -o wide",
                "oc get application <app> -n openshift-gitops -o jsonpath='{.status.sync.status} {.status.health.status}{\"\\n\"}'",
                "Git history for the manifest in question",
            ],
            redflag=(
                "Do not describe GitOps as just a deployment method. The value is in change control, and "
                "that is what the question is about."
            ),
            followup="What in your cluster is not in Git today, and how would you find out?",
        ),
        Q(
            q="What is Ansible check mode and when do you use it?",
            level=FOUNDATION,
            answer=(
                "Check mode runs a playbook without making changes and reports what would have changed, "
                "especially useful combined with diff output. You use it to preview a change before a "
                "maintenance window, to validate that a playbook is genuinely idempotent - a second run in "
                "check mode should report nothing - and as a drift detector, since a check-mode run against "
                "production that reports changes means something has drifted."
            ),
            analogy=(
                "It is a dress rehearsal with no audience. You find out what is missing without anyone "
                "seeing it go wrong."
            ),
            context=(
                "The limitation to state honestly is that check mode is not a perfect simulation: modules "
                "that depend on the results of earlier tasks, or custom modules that do not implement check "
                "mode, can report inaccurately. So it is a strong signal rather than a guarantee, and it "
                "does not replace testing in a non-production environment. Using it as a scheduled drift "
                "detector is the underused application."
            ),
            steps=[
                "Explain what check mode does and pair it with diff for readable output.",
                "Use it as a pre-change preview and as an idempotency test.",
                "Run it on a schedule against production as a drift detector.",
                "State the limitation - dependent tasks and modules without check support can mislead.",
            ],
            evidence=[
                "ansible-playbook site.yml --check --diff --limit <host>",
                "Scheduled check-mode run output, compared over time",
                "Molecule or equivalent test results for the role",
            ],
            redflag=(
                "Do not treat a clean check-mode run as proof it is safe. It is evidence, not a guarantee."
            ),
            followup="Check mode reports changes on a host you have not touched. What does that mean?",
        ),
        Q(
            q="What is an Ansible execution environment?",
            level=FOUNDATION,
            answer=(
                "It is a container image containing the Ansible runtime, the collections and the Python "
                "dependencies your automation needs. Instead of every control node and laptop having a "
                "slightly different set of versions, the automation runs inside a versioned image that is "
                "identical everywhere. It makes runs reproducible, makes dependency upgrades a deliberate "
                "change, and removes the entire class of \"it works on my machine\" failures."
            ),
            analogy=(
                "It is a toolbox that travels with the job, rather than hoping the site has the right "
                "spanner."
            ),
            context=(
                "The operational benefit is that dependency changes become reviewable. Upgrading a "
                "collection is a new image with a new tag, tested in a pipeline, promoted deliberately - "
                "rather than someone running a package upgrade on the control node and discovering three "
                "playbooks now behave differently. In disconnected environments it is close to mandatory, "
                "because it removes the need to fetch collections at runtime."
            ),
            steps=[
                "Define it as a versioned container image carrying runtime, collections and dependencies.",
                "Explain reproducibility across control nodes, CI and developer machines.",
                "Build and promote images through a pipeline, pinned by digest.",
                "Note the disconnected benefit: no runtime dependency fetching.",
            ],
            evidence=[
                "ansible-builder build -t ee-platform:1.4",
                "ansible-navigator run site.yml --execution-environment-image ee-platform:1.4",
                "Image inventory: which execution environment each job template uses",
            ],
            redflag=(
                "Do not run production automation from a laptop's local Ansible install. Nobody can "
                "reproduce what you ran."
            ),
            followup="Two engineers get different results from the same playbook. How does this fix it?",
        ),
        Q(
            q="What is drift, and how does GitOps handle it?",
            level=INTERMEDIATE,
            answer=(
                "Drift is the difference between what Git says should exist and what actually exists, "
                "usually created by someone making a manual change. A GitOps controller detects it "
                "continuously by comparing, and reports the application as OutOfSync. Whether it corrects it "
                "depends on configuration: with automated self-healing it reverts the change; without it, it "
                "reports and waits for a human decision."
            ),
            analogy=(
                "It is a stocktake that runs every few minutes. Whether it puts things back on the shelf or "
                "just tells you they moved is your policy choice."
            ),
            context=(
                "The self-healing choice is a genuine trade-off. Automatic reversion enforces the model "
                "strictly and is right for platform configuration, but it will fight anyone making an "
                "emergency change and it will fight an HPA over replica count unless that field is "
                "excluded. Reporting only preserves human control at the cost of drift persisting quietly. "
                "Most mature setups use self-healing for platform repositories and reporting for application "
                "ones, and are explicit about which is which."
            ),
            steps=[
                "Define drift and how continuous comparison detects it.",
                "Explain self-healing versus report-only and where each is appropriate.",
                "Configure field-level exclusions for things legitimately managed elsewhere, such as HPA "
                "replica counts.",
                "Alert on sustained OutOfSync so drift is noticed rather than accumulating.",
            ],
            evidence=[
                "oc get application -A -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status",
                "oc get application <app> -n openshift-gitops -o jsonpath='{.spec.syncPolicy}' | python3 -m json.tool",
                "Argo CD diff view for the OutOfSync resource",
            ],
            redflag=(
                "Do not enable self-healing on a repository whose replica counts are managed by an HPA. The "
                "two will fight continuously."
            ),
            followup="Argo CD and the HPA are fighting over replicas. How do you fix it properly?",
        ),
        Q(
            q="What are sync waves and why do you need ordering?",
            level=INTERMEDIATE,
            answer=(
                "Sync waves let you order the application of resources so dependencies exist before the "
                "things that need them - namespaces and CRDs before the custom resources that use them, "
                "secrets and config before the workloads that mount them, database migrations before the "
                "application that expects the new schema. Without ordering, a first-time apply fails on "
                "resources whose prerequisites have not been created yet."
            ),
            analogy=(
                "It is a construction schedule. Foundations, then walls, then roof. The materials list does "
                "not tell you the order, and the order is what makes it stand up."
            ),
            context=(
                "The tell-tale symptom of missing ordering is an apply that fails the first time and "
                "succeeds on retry, because by then the prerequisites exist. That is a genuine bug even "
                "though it looks harmless, because it means a fresh cluster cannot be built from the "
                "repository in one pass - which is exactly the property you rely on during a recovery. "
                "Hooks are the related tool for one-off tasks such as migrations."
            ),
            steps=[
                "Explain waves as explicit ordering annotations applied to resources.",
                "Give concrete dependency examples: CRDs, namespaces, secrets, migrations.",
                "Name the symptom of missing ordering: fails once, succeeds on retry.",
                "Test by applying to an empty cluster in a single pass, which is the recovery scenario.",
            ],
            evidence=[
                "grep -r 'argocd.argoproj.io/sync-wave' manifests/ | head",
                "oc get application <app> -o jsonpath='{.status.operationState.phase}{\"\\n\"}'",
                "Fresh-cluster bootstrap test result",
            ],
            redflag=(
                "Do not accept \"it works on the second sync\". It means you cannot rebuild from scratch, "
                "which is the whole point."
            ),
            followup="Your bootstrap fails on the first apply and succeeds on the second. Why does that matter?",
        ),
        Q(
            q="How would you structure an enterprise Ansible automation framework?",
            level=INTERMEDIATE,
            answer=(
                "Roles and collections for reusable logic, kept small and single-purpose; inventories and "
                "group variables that separate environment data from logic; versioned execution "
                "environments; secrets from a vault rather than from files; and job templates in a "
                "controller with role-based access, surveys for parameters, and scheduling. Everything is in "
                "Git, tested in CI with linting and Molecule, and promoted through environments in the same "
                "way application code is."
            ),
            analogy=(
                "It is a professional workshop: standard parts, labelled drawers, a jobs board and a "
                "sign-out sheet - not a shed where each person keeps their own tools."
            ),
            context=(
                "The organisational benefit is bigger than the technical one. A controller with job "
                "templates means a service desk or an application team can run a vetted operation without "
                "having cluster credentials, which removes a large category of privilege that would "
                "otherwise be granted permanently. It also produces an audit trail of who ran what, which is "
                "usually the thing that makes the compliance team stop asking questions."
            ),
            steps=[
                "Separate logic from data: roles and collections versus inventories and group variables.",
                "Version execution environments and promote them like any other artefact.",
                "Source secrets from a vault at runtime, never from the repository.",
                "Publish operations as controller job templates with RBAC, surveys and an audit trail.",
            ],
            evidence=[
                "Repository structure: collections, roles, inventories, molecule scenarios",
                "CI results: ansible-lint, yamllint, molecule converge and idempotence",
                "Controller job history with initiating user and outcome",
            ],
            redflag=(
                "Do not keep environment-specific values inside roles. It guarantees a role that only works "
                "in the environment it was written for."
            ),
            followup="How would you let an application team restart a service without giving them cluster access?",
        ),
        Q(
            q="How do you write safe shell automation for cluster operations?",
            level=INTERMEDIATE,
            answer=(
                "Fail fast and loudly - set -euo pipefail, quote everything, and check that required tools "
                "and context exist before acting. Confirm which cluster you are pointed at, because the "
                "worst shell incidents are correct scripts run against the wrong context. Support a dry-run "
                "mode, act on a narrow selector rather than everything, log what is being done, and make it "
                "idempotent so a re-run after failure is safe."
            ),
            analogy=(
                "It is a power tool with a guard and a trigger lock. The tool is fine; the missing safety "
                "features are what remove fingers."
            ),
            context=(
                "The single highest-value safety feature is the context check. A script that deletes "
                "resources matching a label is completely reasonable in a development cluster and "
                "catastrophic in production, and the difference is one environment variable nobody looked "
                "at. Printing the cluster name and requiring confirmation for destructive actions costs "
                "three lines and prevents the incident that ends careers."
            ),
            steps=[
                "Start with strict mode, quoting and explicit dependency checks.",
                "Verify and print the target cluster context, and require confirmation for destructive "
                "operations.",
                "Provide a dry-run mode and act on narrow, explicit selectors.",
                "Log actions with timestamps and make the script safe to re-run after a partial failure.",
            ],
            evidence=[
                "set -euo pipefail ; oc whoami --show-server",
                "shellcheck script.sh",
                "Script log output showing dry-run and confirmed-run modes",
            ],
            redflag=(
                "Do not write a destructive script without a cluster context check. Everyone who has skipped "
                "it has a story about it."
            ),
            followup="What is the single most valuable safety line in a cluster automation script?",
        ),
        Q(
            q="When and how would you use Python for OpenShift automation?",
            level=INTERMEDIATE,
            answer=(
                "When the task needs real logic - conditional branching, data transformation, calling "
                "several APIs and correlating the results, or generating reports. I use the official "
                "Kubernetes client, authenticate through the in-cluster ServiceAccount when it runs as a "
                "Job, handle errors and retries explicitly with backoff, and treat it like production code: "
                "version control, tests, linting and a pinned dependency set in a container image."
            ),
            analogy=(
                "Shell is a screwdriver and Ansible is a power tool. Python is the workshop you build when "
                "the job needs measuring, cutting and fitting rather than turning one screw."
            ),
            context=(
                "The boundary worth stating is that Python should not be a way to reimplement declarative "
                "operations. Applying manifests is better done by GitOps; configuring nodes is better done "
                "by MachineConfig. Python earns its place for reporting, reconciliation checks, "
                "cross-system integration and one-off analyses - and the moment it starts continuously "
                "reconciling state, you have written an operator and should treat it as one."
            ),
            steps=[
                "Choose Python when logic, correlation or data transformation is genuinely needed.",
                "Use the official client and in-cluster ServiceAccount authentication with least "
                "privilege.",
                "Handle API errors, rate limits and retries explicitly with backoff.",
                "Package it as a container image with pinned dependencies, tests and a CI pipeline.",
            ],
            evidence=[
                "Repository with tests, lint configuration and pinned requirements",
                "oc get cronjob <automation-job> -o yaml   # runs in-cluster with a scoped ServiceAccount",
                "oc auth can-i --list --as=system:serviceaccount:<ns>:<sa>",
            ],
            redflag=(
                "Do not write Python that applies manifests in a loop. You have rebuilt GitOps without the "
                "audit trail."
            ),
            followup="At what point does your Python script become an operator?",
        ),
        Q(
            q="An emergency change needs to be made and GitOps keeps reverting it. What do you do?",
            level=SENIOR,
            answer=(
                "I stop fighting the controller. The clean options are to make the change in Git and sync it "
                "immediately - which is often quicker than people assume - or, if Git is unavailable or the "
                "change genuinely cannot wait, to suspend automated sync for that application, apply the "
                "change with a documented reason, and open the corresponding pull request straight away so "
                "the emergency state has an expiry."
            ),
            analogy=(
                "It is breaking the glass on a fire alarm. Legitimate, loud, and it leaves visible evidence "
                "that someone has to account for afterwards."
            ),
            context=(
                "The real risk is the forgotten suspension. An application left with sync disabled after an "
                "incident drifts silently for weeks, and nobody discovers it until a rebuild fails or a "
                "config nobody remembers turns out to be load-bearing. Alerting on applications with sync "
                "disabled, and reviewing them in the incident follow-up, is what makes the emergency path "
                "safe to use."
            ),
            steps=[
                "Try the fast path first: commit and sync, which is often quicker than the workaround.",
                "If not possible, suspend sync for that specific application only, with a recorded reason.",
                "Apply the change, and open the pull request immediately so the state is temporary.",
                "Alert on suspended applications and clear them as part of the incident follow-up.",
            ],
            evidence=[
                "oc get application -A -o json | jq '.items[]|select(.spec.syncPolicy.automated==null)|.metadata.name'",
                "Incident record with the emergency change and its reason",
                "Pull request linking back to the incident",
            ],
            redflag=(
                "Do not disable sync cluster-wide to get past one change. You have turned off change control "
                "for everything to fix one thing."
            ),
            followup="Two weeks later you find an application still has sync disabled. What now?",
        ),
        Q(
            q="How do you handle secrets in a GitOps workflow?",
            level=SENIOR,
            answer=(
                "Secrets do not go in Git in plaintext, and I prefer them not to go in Git at all. The "
                "cleanest pattern is an external secret manager with an operator that pulls values into "
                "Kubernetes Secrets at runtime, so Git holds only a reference. Where an external manager is "
                "not available, sealed secrets encrypted to a cluster-held key are an acceptable second "
                "choice - as long as the key management story is written down and the key itself is backed "
                "up somewhere other than the cluster."
            ),
            analogy=(
                "The recipe book can say \"add the house spice mix\". It should not print the formula, and "
                "it definitely should not print it in a code that everyone on the team can read."
            ),
            context=(
                "The reason to prefer external references is rotation. With a sealed secret, rotating a "
                "credential means re-encrypting and committing, so rotation is a code change and therefore "
                "rarely happens. With an external manager, rotation happens in the manager on a schedule "
                "and the cluster picks it up, which is the behaviour you actually want. The gap that remains "
                "in both cases is whether the workload reloads or needs a restart."
            ),
            steps=[
                "Keep plaintext secrets out of Git entirely; store references instead.",
                "Prefer an external manager with an operator syncing into Kubernetes Secrets.",
                "If using sealed secrets, document key management and back the key up off-cluster.",
                "Define the rotation path per workload, including whether a restart is required.",
            ],
            evidence=[
                "oc get externalsecret,secretstore -A",
                "git log --all -p | grep -i -c 'BEGIN PRIVATE KEY'   # should be zero",
                "Rotation schedule and last-rotated timestamps per secret class",
            ],
            redflag=(
                "Do not commit encrypted secrets without a key management plan. If the key lives only in the "
                "cluster you cannot recover, you have encrypted nothing useful."
            ),
            followup="Your sealing key is lost with the cluster. What can you recover?",
        ),
        Q(
            q="How do you test automation before it touches production?",
            level=SENIOR,
            answer=(
                "In layers. Static checks first - linting, schema validation, policy checks in CI. Then "
                "functional tests against an ephemeral or non-production cluster, including running the "
                "automation twice to prove idempotency. Then a canary: apply to one namespace, one node or "
                "one cluster and validate before widening. And for destructive operations, a dry-run mode "
                "that is exercised in the pipeline rather than only documented."
            ),
            analogy=(
                "It is testing a new medicine: laboratory, then trial, then limited release, then general "
                "availability. Nobody skips to the last step because they are confident."
            ),
            context=(
                "The step most often skipped is the idempotency run, and it is the cheapest of the lot. "
                "Running the same automation twice and asserting no changes on the second pass catches a "
                "large fraction of real bugs before they reach anything important. The canary step is the "
                "one that saves you from the bugs testing cannot catch, because production always has "
                "something the test environment does not."
            ),
            steps=[
                "Run static analysis and policy checks on every commit.",
                "Test functionally against a non-production cluster, and run twice to assert idempotency.",
                "Canary to a limited scope and validate before widening.",
                "Exercise dry-run paths in CI so they are known to work when someone needs them.",
            ],
            evidence=[
                "CI pipeline stages and their pass rates",
                "Ephemeral cluster test results including the idempotency run",
                "Canary scope definition and validation criteria per automation",
            ],
            redflag=(
                "Do not rely on review alone for automation that changes many things at once. Reviews catch "
                "intent errors, not behaviour."
            ),
            followup="Your automation passed every test and broke production. What layer was missing?",
        ),
        Q(
            q="How do you decide what to automate and what to leave manual?",
            level=ARCHITECT,
            answer=(
                "I automate work that is frequent, well understood and low variance - node scaling, "
                "certificate renewal, namespace creation, routine checks. I leave manual, for now, anything "
                "rare, poorly understood, or where the cost of an automated mistake is very high and "
                "recovery is slow. And I never automate a procedure nobody can perform by hand, because "
                "when the automation fails - and it will - somebody needs to be able to finish the job."
            ),
            analogy=(
                "You automate the assembly line, not the emergency surgery. And you keep surgeons who can "
                "still operate when the machine is down."
            ),
            context=(
                "The frequency-times-risk framing is what makes this defensible in a design review. High "
                "frequency and low risk is obvious automation. Low frequency and high risk usually deserves "
                "a good runbook and a rehearsal instead, because automation that runs twice a year is never "
                "tested and rots quietly. The interesting middle is high frequency and high risk, where the "
                "answer is usually to automate with strong guardrails and a human approval gate."
            ),
            steps=[
                "Score candidate tasks by frequency, risk and variance.",
                "Automate high-frequency low-risk work first; it pays back fastest and builds confidence.",
                "For high-risk work, automate with guardrails and an approval gate rather than fully "
                "autonomously.",
                "Keep runbooks current for the manual path, and rehearse them so the skill survives.",
            ],
            evidence=[
                "Task inventory with frequency, duration and risk rating",
                "Toil measurement: hours per week spent on repeated manual work",
                "Runbook currency: last reviewed and last rehearsed dates",
            ],
            redflag=(
                "Do not automate a rare, high-risk procedure that nobody has performed manually. You have "
                "built something untested that runs when you are least able to check it."
            ),
            followup="Which of your current manual tasks would you automate first, and why that one?",
        ),
        Q(
            q="How would you design change control for the platform end to end?",
            level=ARCHITECT,
            answer=(
                "Everything that defines the platform lives in Git. Changes arrive as pull requests with "
                "automated validation - lint, policy, dry-run - and human review proportional to risk. "
                "Promotion runs through environments in a fixed order with a soak period. Deployment is by "
                "GitOps so the applied state is always the reviewed state. Emergency changes have a defined "
                "break-glass path that is visible and expires. And the evidence for an auditor is the Git "
                "history plus the controller's sync history."
            ),
            analogy=(
                "It is planning permission for a building. Proposal, review proportional to the size of the "
                "change, inspection, and a record anyone can look up years later."
            ),
            context=(
                "The design decision that determines whether people follow this is proportionality. If a "
                "one-line label change requires the same approval as a network redesign, engineers route "
                "around the process and the audit trail becomes fiction. Tiering changes by blast radius - "
                "auto-merge for low-risk, peer review for medium, change board for high - keeps the process "
                "credible and keeps the evidence real."
            ),
            steps=[
                "Put all platform configuration in Git and define the repository structure and ownership.",
                "Automate validation in CI and tier human review by blast radius.",
                "Promote through environments in a fixed order with a defined soak period.",
                "Define and monitor the break-glass path, and use Git plus sync history as the audit "
                "evidence.",
            ],
            evidence=[
                "Pull request history with review evidence and CI results",
                "GitOps sync history per environment with timestamps",
                "Break-glass usage log with reasons and follow-up pull requests",
            ],
            redflag=(
                "Do not apply the same heavyweight approval to every change. People will bypass it, and "
                "then you have no change control at all."
            ),
            followup="How would you prove to an auditor that no unreviewed change reached production?",
        ),
    ],
)
