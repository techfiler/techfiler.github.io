"""Part 4 - Advanced Ansible for senior platform engineers."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=4,
    title="Advanced Ansible for senior platform engineers",
    subtitle="Variable precedence, testing, execution environments and enterprise controller patterns",
    intro=(
        "Senior Ansible questions assume you have run playbooks in anger and now own the framework other "
        "teams depend on. Interviewers probe whether you understand precedence rules well enough to debug "
        "surprising values, whether you test roles before production, whether automation runs from "
        "reproducible execution environments, and whether your controller setup gives auditability without "
        "turning every change into a ticket. Strong answers tie Ansible mechanics to change control and "
        "operational safety."
    ),
    infographics=["gitops_flow"],
    questions=[
        Q(
            q="What is Ansible variable precedence and why does it confuse people?",
            level=FOUNDATION,
            answer=(
                "Variable precedence defines which value wins when the same variable is defined in multiple "
                "places - extra vars on the command line beat most other sources, then task vars, block "
                "vars, role and include vars, host and group vars, inventory file vars, role defaults, "
                "and finally facts. People get confused because group_vars/all.yml and host_vars/myhost.yml "
                "feel authoritative until someone passes -e on the command line or a role default silently "
                "loses to a higher layer they forgot existed."
            ),
            analogy=(
                "It is a stack of memos on a desk. The top one wins, and the memo you wrote last week is "
                "still there underneath even if you forgot about it."
            ),
            context=(
                "Most real debugging sessions start with \"why did this host get that value\". Without "
                "precedence in muscle memory, engineers add another definition somewhere higher rather "
                "than finding the conflicting one. ansible-inventory --host and --graph, plus "
                "ansible-playbook with -e ansible_debug=true or community.general.var_dump, make the "
                "effective value visible. Documenting where environment-specific data lives prevents the "
                "next person from fighting the same battle."
            ),
            steps=[
                "State the precedence order from highest (extra vars) to lowest (role defaults and facts).",
                "Use ansible-inventory --host hostname to dump merged variables for one host.",
                "Search group_vars, host_vars, role defaults and play vars when values surprise you.",
                "Document the intended source of truth per variable class in the repository README.",
            ],
            evidence=[
                "ansible-inventory -i inventories/prod --host web01.example.com",
                "ansible-playbook site.yml -e @extra.yml --check -v | grep -i myvar",
                "grep -r 'myvar:' inventories/ roles/ | head",
            ],
            redflag=(
                "Do not fix surprising values by adding yet another definition at a random layer. Find "
                "the conflict or you will inherit it forever."
            ),
            followup="A host_var and a group_var disagree. Which wins and how do you prove it?",
        ),
        Q(
            q="How do you use Ansible Vault to protect secrets?",
            level=FOUNDATION,
            answer=(
                "Ansible Vault encrypts sensitive strings or entire files with a password or key file. "
                "Encrypted content lives in Git safely; at runtime you provide the vault password via "
                "prompt, a permissions-restricted file, or a controller credential injected by AAP. I "
                "encrypt group_vars or dedicated vault files rather than sprinkling vault blocks through "
                "roles, rotate the vault password on a schedule, and never commit the password alongside "
                "the ciphertext."
            ),
            analogy=(
                "The recipe is in the shared cookbook, but the safe combination is in a separate envelope "
                "only the head chef opens at service time."
            ),
            context=(
                "Vault solves storage in Git, not runtime secrecy on the target host. After decryption, "
                "secrets appear in task arguments and can leak into logs if no_log is missing. Enterprise "
                "setups often combine vault for static secrets with an external lookup plugin pulling "
                "from HashiCorp Vault or AWS Secrets Manager at runtime, so rotation does not require "
                "re-encrypting files."
            ),
            steps=[
                "Create encrypted files with ansible-vault create or encrypt existing files with encrypt.",
                "Store vault IDs and passwords in a controller credential or a restricted file outside Git.",
                "Mark tasks handling secrets with no_log: true to keep them out of job output.",
                "Document rotation: new secret, re-encrypt, deploy, revoke old credential.",
            ],
            evidence=[
                "ansible-vault view inventories/prod/group_vars/all/vault.yml",
                "ansible-playbook site.yml --ask-vault-pass --check",
                "grep -r 'no_log: true' roles/ | head",
            ],
            redflag=(
                "Do not commit vault_password_file to the repository. You have shipped the key with the "
                "lock."
            ),
            followup="How would you rotate a database password stored in vault without downtime?",
        ),
        Q(
            q="What are handlers and how do they differ from regular tasks?",
            level=FOUNDATION,
            answer=(
                "Handlers are tasks that run once at the end of the play, and only if notified by another "
                "task that reported a change. They are the right tool for actions that should happen after "
                "configuration changes - restarting a service when a config file changes, reloading "
                "systemd when a unit file changes. Regular tasks run every time unless a when condition "
                "stops them; handlers coalesce multiple notifications into a single run."
            ),
            analogy=(
                "Regular tasks are the chef cooking every course. Handlers are \"only preheat the oven if "
                "at least one dish actually needed baking, and do it once at the end\"."
            ),
            context=(
                "The classic mistake is using a handler to restart a service when a task uses changed_when: "
                "false or when copy reports ok instead of changed - the handler never fires and production "
                "runs stale config until someone notices. The other mistake is notifying from every task "
                "when a single meta: flush_handlers mid-play is needed for ordering. Handlers belong in "
                "roles, named consistently, and documented so application teams know what triggers a restart."
            ),
            steps=[
                "Define handlers in handlers/main.yml with clear names matching their action.",
                "Notify from tasks only when a meaningful change occurred; verify changed_when if needed.",
                "Use listen to alias multiple notify strings to one handler.",
                "Use meta: flush_handlers when later tasks depend on the handler having run.",
            ],
            evidence=[
                "grep -r 'notify:' roles/myapp/ | head",
                "ansible-playbook site.yml --check --diff -v | grep -i 'RUNNING HANDLER'",
                "molecule converge --scenario-name default",
            ],
            redflag=(
                "Do not restart services with a regular task on every playbook run. You cause unnecessary "
                "outages and hide whether config actually changed."
            ),
            followup="Your handler never runs but the config file did change. What do you check?",
        ),
        Q(
            q="What are Ansible tags and when do you use them?",
            level=FOUNDATION,
            answer=(
                "Tags label tasks and roles so you can run a subset of a playbook with --tags or skip "
                "parts with --skip-tags. I tag by concern - packages, config, monitoring, never - and "
                "use never on destructive or slow tasks that should run only when explicitly requested. "
                "Tags make large site.yml playbooks usable for targeted maintenance without copying "
                "playbooks into fragments that drift apart."
            ),
            analogy=(
                "Tags are coloured stickers on workshop drawers. You can pull just the electrical tools "
                "without emptying every drawer onto the floor."
            ),
            context=(
                "Tags are powerful and easy to misuse. Untagged tasks always run, which surprises people "
                "who expect --tags to limit everything. Duplicate tag names across roles can pull in more "
                "than intended. Document the tag vocabulary in the README and test tagged runs in CI so "
                "a --tags config run still converges correctly."
            ),
            steps=[
                "Define a consistent tag vocabulary: config, packages, services, monitoring, never.",
                "Apply tags at role level where the whole role shares a concern, task level for exceptions.",
                "Run ansible-playbook site.yml --tags config --list-tasks before executing.",
                "Test tagged runs in Molecule or CI to ensure partial runs leave the host valid.",
            ],
            evidence=[
                "ansible-playbook site.yml --tags config --list-tasks",
                "ansible-playbook site.yml --tags never,destructive --list-tasks",
                "grep -r 'tags:' roles/ | sort | uniq -c | head",
            ],
            redflag=(
                "Do not rely on tags as your only safety gate for destructive tasks. A forgotten tag "
                "still runs if the task is untagged."
            ),
            followup="Someone runs --tags config and a database task still executes. Why?",
        ),
        Q(
            q="What is Molecule and how do you use it to test Ansible roles?",
            level=INTERMEDIATE,
            answer=(
                "Molecule is a testing framework for Ansible roles. It creates ephemeral test instances "
                "with a driver like Docker or libvirt, applies your role with ansible-playbook, runs "
                "verify steps with either Ansible assert tasks or Testinfra, and destroys the instance. "
                "The idempotence test runs converge twice and expects no changes on the second pass. It "
                "turns \"works on my laptop\" into evidence in CI."
            ),
            analogy=(
                "It is a crash test for a car part before it goes on the production line, using a cheap "
                "dummy vehicle you can wreck and rebuild."
            ),
            context=(
                "Roles without tests rot quietly as platforms upgrade underneath them. Molecule scenarios "
                "per OS version or major configuration variant catch module deprecations, wrong package "
                "names and broken templates before AAP job templates run against production inventory. "
                "The cost is maintaining Docker images or cloud templates for the driver; execution "
                "environments make the Ansible side reproducible."
            ),
            steps=[
                "Init a scenario with molecule init scenario -d docker -r myrole.",
                "Write converge.yml to apply the role and verify.yml with assertions on final state.",
                "Run molecule test locally and in CI on every pull request touching the role.",
                "Include the idempotence stage so the second converge reports zero changes.",
            ],
            evidence=[
                "cd roles/myrole && molecule test",
                "molecule converge && molecule idempotence",
                "grep -r 'molecule' .gitlab-ci.yml .github/workflows/",
            ],
            redflag=(
                "Do not skip the idempotence test. It is the cheapest check that your role is safe to "
                "re-run after a partial failure."
            ),
            followup="Your role passes on Rocky 9 but fails on RHEL 8. How do you structure scenarios?",
        ),
        Q(
            q="What is ansible-lint and what does it catch?",
            level=INTERMEDIATE,
            answer=(
                "ansible-lint statically analyses playbooks, roles and collections against rules for "
                "correctness, style and security. It flags bare variables that need quoting, risky shell "
                "usage, missing name keys, deprecated modules, privilege escalation mistakes and "
                "filename violations. Running it in CI on every commit prevents low-quality content from "
                "reaching the controller and gives reviewers a baseline beyond opinion."
            ),
            analogy=(
                "It is spell-check and grammar-check for automation, with a few rules that also stop "
                "you from leaving the stove on."
            ),
            context=(
                "ansible-lint profiles let you ramp strictness: min for legacy repos, production for "
                "new work. Some rules are stylistic; others catch real bugs like command-instead-of-shell "
                "without creates/removes guards. Suppressing rules needs a comment explaining why, or "
                "the exception becomes permanent. Pair lint with yamllint for formatting and schema "
                "validation for inventory structure."
            ),
            steps=[
                "Run ansible-lint on the repository root or per collection with a pinned version.",
                "Enable a profile appropriate to the repo age and tighten it over time.",
                "Fix or justify violations; use noqa comments sparingly with a reason.",
                "Gate merges in CI on ansible-lint exit code zero.",
            ],
            evidence=[
                "ansible-lint roles/myrole",
                "ansible-lint --profile production .",
                "grep ansible-lint .gitlab-ci.yml",
            ],
            redflag=(
                "Do not disable ansible-lint globally because the legacy repo is noisy. Fix or profile "
                "incrementally or quality never improves."
            ),
            followup="Which ansible-lint rule has caught a real bug for you, not just style?",
        ),
        Q(
            q="What is dynamic inventory and when do you use it?",
            level=INTERMEDIATE,
            answer=(
                "Dynamic inventory generates the host list at runtime from a script or plugin querying a "
                "source of truth - cloud APIs, a CMDB, VMware, OpenShift - instead of maintaining static "
                "INI files that drift. Inventory plugins are the modern form: YAML config pointing at a "
                "plugin like amazon.aws.aws_ec2 or constructed to build groups from host vars. The "
                "automation always targets what actually exists now."
            ),
            analogy=(
                "Static inventory is a printed phone book. Dynamic inventory is directory enquiry: you "
                "get today's numbers, not the ones from three years ago."
            ),
            context=(
                "Hybrid estates often combine constructed inventory: a dynamic plugin pulls cloud hosts, "
                "then inventory plugins add groups by tags, and group_vars layer environment config. "
                "Caching with cache_plugin helps rate limits but can serve stale data; tune timeout for "
                "your change velocity. For OpenShift, the kubernetes.core.k8s inventory targets pods or "
                "nodes when you need to automate inside the cluster boundary."
            ),
            steps=[
                "Choose an inventory plugin matching the source of truth, not a hand-maintained export.",
                "Configure authentication via environment or credential plugin, not keys in the repo.",
                "Validate with ansible-inventory -i config.yml --graph and --host for sample hosts.",
                "Set cache timeout consciously if using inventory caching.",
            ],
            evidence=[
                "ansible-inventory -i inventories/aws_ec2.yml --graph | head -30",
                "ansible-inventory -i inventories/aws_ec2.yml --list --export | jq '.meta.hostvars | keys | length'",
                "ansible-inventory --graph -i inventories/ | grep -c 'orphan'",
            ],
            redflag=(
                "Do not export cloud inventory to a static file on a cron job without noticing when the "
                "export fails. You automate against ghosts."
            ),
            followup="Inventory cache shows terminated hosts. What failed and how do you detect it?",
        ),
        Q(
            q="What are Ansible collections and how do you manage them?",
            level=INTERMEDIATE,
            answer=(
                "Collections are distributable packages of modules, plugins, roles and playbooks under a "
                "namespace, installed with ansible-galaxy collection install from Galaxy, Automation Hub "
                "or a private index. requirements.yml pins names and versions; execution environments "
                "install them at build time so runtime does not depend on the public internet. Vendoring "
                "collections into the repo is an option for disconnected sites but shifts upgrade "
                "responsibility to you."
            ),
            analogy=(
                "Collections are app store packages for Ansible. The core engine stays slim; you install "
                "the AWS shelf, the Windows shelf and the network shelf separately."
            ),
            context=(
                "Most production modules live in collections now, not ansible.builtin alone. Pinning "
                "versions matters because collection majors change module parameters and deprecate old "
                "names. CI should run ansible-galaxy collection install -r requirements.yml --force "
                "followed by tests so a broken pin fails before the controller job template does."
            ),
            steps=[
                "Declare dependencies in requirements.yml with explicit versions or version ranges.",
                "Install with ansible-galaxy collection install -r requirements.yml -p ./collections.",
                "Build execution environments that bake the same requirements for controller jobs.",
                "Review release notes before bumping collection majors in production.",
            ],
            evidence=[
                "cat requirements.yml",
                "ansible-galaxy collection list | grep amazon.aws",
                "grep collections requirements.yml execution-environment.yml",
            ],
            redflag=(
                "Do not run ansible-galaxy install latest on every job without pins. You will upgrade "
                "into a breaking module change mid-incident."
            ),
            followup="A collection major upgrade renames a module. How do you migrate safely?",
        ),
        Q(
            q="What is ansible-builder and how does it relate to execution environments?",
            level=INTERMEDIATE,
            answer=(
                "ansible-builder reads an execution-environment definition - base image, Python packages, "
                "system packages, ansible-core version, collections - and produces a container image "
                "with everything installed. That image is what ansible-navigator, AAP job templates and "
                "CI pipelines run. It replaces ad hoc pip install on control nodes with a versioned "
                "artefact built once, scanned, signed and promoted."
            ),
            analogy=(
                "ansible-builder is the factory that assembles the toolbox. The execution environment is "
                "the finished toolbox on the truck."
            ),
            context=(
                "The definition file lives in Git and changes like application code: pull request, CI "
                "build, test playbooks against the new image, promote by tag or digest. Multi-stage "
                "builds keep images smaller. Disconnected environments pre-build on a connected builder, "
                "push to a private registry, and AAP pulls from there. Pin ansible-builder itself so "
                "image layout does not shift unexpectedly."
            ),
            steps=[
                "Author execution-environment.yml with base image, deps and galaxy requirements.",
                "Run ansible-builder build -t ee-platform:1.2 -f execution-environment.yml.",
                "Test the image with ansible-navigator or a CI playbook before promoting.",
                "Reference the image by digest in AAP, not only by floating tags.",
            ],
            evidence=[
                "ansible-builder build -t ee-platform:1.2 -f execution-environment.yml",
                "podman inspect ee-platform:1.2 | jq '.[0].Digest'",
                "ansible-navigator run site.yml --execution-environment-image ee-platform:1.2",
            ],
            redflag=(
                "Do not let every job template build its own EE on the fly. You have no idea what ran "
                "last Tuesday."
            ),
            followup="Two job templates use different EE images with different collection versions. What breaks?",
        ),
        Q(
            q="What is an Ansible execution environment in practice?",
            level=INTERMEDIATE,
            answer=(
                "An execution environment is a container image containing ansible-core, collections, "
                "Python dependencies and optionally system binaries your modules need. AAP and "
                "ansible-navigator run playbooks inside this image so developer laptops, CI and "
                "production controllers execute identical automation. It eliminates \"works on my control "
                "node\" and is the standard delivery mechanism on Ansible Automation Platform 2."
            ),
            analogy=(
                "It is the standard issue toolkit every engineer gets on day one, identical down to the "
                "serial number, instead of everyone bringing their own mismatched screwdrivers."
            ),
            context=(
                "Legacy virtualenv on the control node still appears in older estates but does not scale "
                "when fifty job templates need different collection sets. Execution environments compose "
                "with private automation hub for validated content. Operational concerns include image "
                "size, pull secrets on disconnected controllers, and RBAC over who can publish new "
                "image versions."
            ),
            steps=[
                "Define one EE per logical dependency profile, not one per playbook.",
                "Build from execution-environment.yml with ansible-builder and store in a trusted registry.",
                "Assign EE images to job templates and project sync jobs in AAP.",
                "Rotate and scan images on the same schedule as other production container artefacts.",
            ],
            evidence=[
                "ansible-navigator images",
                "awx --help 2>/dev/null; oc get automationcontroller -n aap 2>/dev/null | head",
                "grep execution_environment inventories/controller/job_templates/",
            ],
            redflag=(
                "Do not run production jobs from the controller's bundled EE if it drifted from what "
                "you tested in CI."
            ),
            followup="How do you debug a module missing from the execution environment?",
        ),
        Q(
            q="How do block, rescue and always work in Ansible playbooks?",
            level=SENIOR,
            answer=(
                "block groups tasks with optional error handling: tasks in block run normally; if one "
                "fails, rescue tasks run instead; always tasks run regardless of success or failure, "
                "like a finally block. Use it for transactional sections - attempt a change, run cleanup "
                "on failure, notify monitoring in always. It does not replace proper idempotency; it "
                "contains failure blast radius within a play."
            ),
            analogy=(
                "block is the main procedure, rescue is the spill kit when something breaks, always is "
                "turning the lights off and signing the logbook before you leave."
            ),
            context=(
                "Rescue runs only on task failures, not on unreachable hosts unless you handle that "
                "separately with max_fail_percentage or ignore_unreachable. Always runs even when rescue "
                "also runs, which is useful for slack notifications or metric emission. Overusing block "
                "for flow control when when conditions suffice makes playbooks harder to read than "
                "straight-line tasks with clear names."
            ),
            steps=[
                "Wrap risky task groups in block with a descriptive name on the block itself.",
                "Write rescue tasks that restore safe state or gather diagnostics, not hide errors.",
                "Use always for notifications, log uploads and metric pushes.",
                "Re-raise or fail explicitly in rescue when the play should stop.",
            ],
            evidence=[
                "grep -A20 'block:' playbooks/rolling_update.yml | head -25",
                "ansible-playbook site.yml -v | grep -E 'RESCUE|ALWAYS'",
                "molecule verify --scenario-name failure_path",
            ],
            redflag=(
                "Do not use rescue to swallow errors and continue as if nothing happened. The playbook "
                "shows ok and production is broken."
            ),
            followup="Rescue runs but always reports success while the service is down. What went wrong?",
        ),
        Q(
            q="How do you perform rolling updates with Ansible safely?",
            level=SENIOR,
            answer=(
                "Use serial or max_fail_percentage on the play to limit concurrent hosts - for example "
                "serial: \"10%\" or serial: 1 for one-at-a-time. Combine with health checks after each "
                "batch, delegate_to monitoring for verification, and stop the play if a batch fails "
                "before touching the rest. Pre-tasks drain connections where applicable; handlers restart "
                "services only after config validates."
            ),
            analogy=(
                "It is renovating one hotel floor at a time while checking guests can still reach the "
                "reception desk, not closing the entire building at once."
            ),
            context=(
                "Rolling updates intersect with load balancers: remove from pool, patch, wait for health, "
                "return to pool. Ansible orchestrates the steps but the pattern belongs in a role with "
                "variables for batch size and health check URL. For Kubernetes workloads Ansible is "
                "often the wrong tool; for VMs and appliances it remains essential. Document rollback "
                "per batch because serial forward is only half the story."
            ),
            steps=[
                "Set serial or max_fail_percentage appropriate to service tolerance and capacity headroom.",
                "Remove host from load balancer or mark out of service before destructive tasks.",
                "Run post-update validation tasks; fail the play if health checks do not pass.",
                "Use run_once or delegate_to for monitoring integration and audit logging.",
            ],
            evidence=[
                "grep -E 'serial:|max_fail_percentage:' playbooks/rolling_update.yml",
                "ansible-playbook rolling_update.yml --limit webservers --check -v",
                "Controller job output showing batch boundaries and health check results",
            ],
            redflag=(
                "Do not run the same play against all hosts with no serial on a stateful service. You "
                "will take the entire fleet offline simultaneously."
            ),
            followup="Batch two fails health checks. How do you roll back batch one hosts?",
        ),
        Q(
            q="How does Ansible Automation Platform change how you run Ansible at scale?",
            level=SENIOR,
            answer=(
                "AAP adds a controller for job templates, schedules, surveys, RBAC, credential injection, "
                "execution environments, automation hub for curated collections, and an audit trail of "
                "who launched what against which inventory. Teams run vetted automation without SSH keys "
                "to every host or direct access to playbooks. It turns Ansible from individual scripts "
                "into a shared service with governance."
            ),
            analogy=(
                "It is the difference between everyone driving their own car to a job site and a "
                "dispatch office that assigns certified drivers, tracked vehicles and signed work orders."
            ),
            context=(
                "The interview is about governance, not feature lists. Job templates expose parameters "
                "through surveys while hiding inventory credentials. Workflow templates chain jobs with "
                "approval nodes for change windows. Event-driven ansible rulebooks react to webhooks. "
                "Integration with IdM maps LDAP groups to roles so application teams can restart a "
                "service without seeing database passwords."
            ),
            steps=[
                "Publish roles as projects synced from Git with CI-tested commit SHAs.",
                "Create job templates with scoped inventories, credentials and execution environments.",
                "Use RBAC so teams run only what they need; audit logs capture user and outcome.",
                "Chain high-risk operations through workflow templates with approval gates.",
            ],
            evidence=[
                "awx job_templates list 2>/dev/null || echo 'query controller API'",
                "Controller job history: user, template, inventory, start time, status",
                "grep -r 'survey' controller/job_templates/ | head",
            ],
            redflag=(
                "Do not give everyone admin on the controller to save ticket time. You have centralised "
                "all credentials in one place with no gate."
            ),
            followup="How would you let an app team restart a service without exposing SSH or vault passwords?",
        ),
        Q(
            q="How would you design an enterprise Ansible framework end to end?",
            level=ARCHITECT,
            answer=(
                "Collections and small roles in Git with semver tags; inventories separated from logic; "
                "dynamic inventory from the CMDB or cloud; secrets from vault or external lookups; "
                "execution environments built with ansible-builder and pinned in AAP; CI running "
                "ansible-lint, yamllint and Molecule; job templates as the only production entry point "
                "with RBAC and surveys; promotion through dev, staging and prod inventories mirroring "
                "application release trains."
            ),
            analogy=(
                "It is building a municipal water system with treatment plants, tested pipes and metered "
                "connections - not asking each house to dig its own well."
            ),
            context=(
                "The architect question is organisational as much as technical. A framework nobody uses "
                "because it is slower than SSH loses by default. Success means application teams get "
                "self-service within guardrails, platform teams own the EE and collection upgrades, and "
                "auditors get job history plus Git blame. The anti-pattern is a monolithic site.yml with "
                "environment if-statements copied into every role."
            ),
            steps=[
                "Separate content (collections/roles), data (inventories/group_vars), and runtime (EE images).",
                "Enforce quality gates in CI: lint, test, build EE, scan image.",
                "Expose operations through controller job templates with tiered RBAC and documented surveys.",
                "Measure adoption: which manual tasks remain and why teams bypass the framework.",
            ],
            evidence=[
                "Repository layout: collections/, inventories/, execution-environment.yml, .gitlab-ci.yml",
                "CI pipeline stages: lint, molecule, ee-build, deploy-template",
                "Controller metrics: job count by team, failure rate, template age",
            ],
            redflag=(
                "Do not centralise automation without a migration path for existing playbooks. Teams will "
                "parallel-run shadow automation forever."
            ),
            followup="Teams bypass AAP and run ansible-playbook from laptops. What is missing from your design?",
        ),
    ],
)
