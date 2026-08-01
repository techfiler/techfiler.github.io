"""Part 1 - Linux, containers and the Kubernetes idea."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=1,
    title="Linux, containers and the Kubernetes idea",
    subtitle="The layer everything else sits on - and the layer most candidates skip",
    intro=(
        "Almost every hard OpenShift problem turns out to be a Linux problem wearing a Kubernetes costume. "
        "A pod that will not start is a runtime, image or SELinux problem. A pod that is slow is a cgroup, "
        "NUMA or filesystem problem. Interviewers know this, which is why a surprising number of senior "
        "interviews open with something that sounds basic - \"what actually is a container?\" - and then "
        "quietly measure how deep you can go before you run out of road. This part builds that floor properly "
        "so the rest of the book has something to stand on."
    ),
    infographics=["container_stack"],
    questions=[
        Q(
            q="What actually is a container?",
            level=FOUNDATION,
            answer=(
                "A container is just a normal Linux process that the kernel has been told to isolate. There "
                "is no container object in the kernel. Namespaces decide what the process can see, cgroups "
                "decide what it can consume, a union filesystem gives it its own root filesystem from stacked "
                "image layers, and SELinux, seccomp and capabilities decide what it is allowed to do. Package "
                "those together and you get something that feels like a lightweight machine but is really one "
                "process tree sharing the host kernel."
            ),
            analogy=(
                "It is an open-plan office, not a separate building. Everyone shares the same air "
                "conditioning - the kernel - but each team gets its own desk, its own filing cabinet and a "
                "badge that only opens certain doors."
            ),
            context=(
                "This matters the moment something misbehaves. Because containers share the host kernel, a "
                "kernel-level problem - an exhausted PID limit, a saturated inode table, a conntrack table "
                "that is full - shows up as several unrelated pods failing on the same node at once. If you "
                "think of a container as a tiny virtual machine you will keep looking inside the pod, and you "
                "will keep missing the node."
            ),
            steps=[
                "Name the four mechanisms out loud: namespaces, cgroups, union filesystem, security context.",
                "Say what each one buys you: visibility, consumption, filesystem, permitted actions.",
                "Point out the shared kernel, because that is where the failure modes and the security "
                "boundary questions come from.",
                "Land it with an operational consequence - node-level limits are shared, so one greedy pod "
                "can hurt its neighbours unless requests and limits are set.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host crictl ps",
                "cat /proc/<pid>/cgroup ; ls -l /proc/<pid>/ns",
                "oc adm top node ; oc describe node <node> | sed -n '/Allocated/,$p'",
            ],
            redflag=(
                "Do not say \"a container is a lightweight VM\". It is the fastest way to signal that you "
                "have used containers but never debugged one from the node."
            ),
            followup="So where exactly is the security boundary, and why is that weaker than a VM?",
        ),
        Q(
            q="How is a container different from a virtual machine?",
            level=FOUNDATION,
            answer=(
                "A VM virtualises hardware and runs its own kernel, so the isolation boundary is the "
                "hypervisor. A container virtualises the operating system view and shares the host kernel, so "
                "the boundary is kernel features. That makes containers start in milliseconds and cost almost "
                "nothing in memory overhead, but it also means a kernel vulnerability is a shared risk. In "
                "practice you choose VMs when you need a different kernel or a hard security boundary, and "
                "containers when you need density and fast, repeatable deployment."
            ),
            analogy=(
                "A VM is a detached house with its own boiler. A container is a flat in a block - cheaper, "
                "faster to move into, but if the building's boiler fails, everyone is cold."
            ),
            context=(
                "The trade-off shows up in real designs. Multi-tenant clusters running untrusted code often "
                "keep hard tenancy at the cluster or node level rather than relying on namespaces alone, "
                "because a container escape crosses namespaces but a hypervisor escape is a different class "
                "of problem. It is also why OpenShift Virtualization exists: some workloads genuinely need a "
                "kernel of their own and you should not pretend otherwise."
            ),
            steps=[
                "State the boundary difference first: hypervisor versus shared kernel.",
                "Give the practical consequence: startup time and density versus isolation strength.",
                "Name when you would still choose a VM - legacy kernel modules, untrusted tenants, "
                "compliance requirements for hard isolation.",
                "Mention that OpenShift can run both, so the answer is a placement decision rather than a "
                "religious one.",
            ],
            evidence=[
                "oc get nodes -o wide   # kernel and container runtime version per node",
                "oc get kubevirt -A     # is OpenShift Virtualization in play for VM workloads",
            ],
            redflag=(
                "Do not claim containers are \"just as isolated as VMs\". Interviewers hear that as a "
                "security answer you have not thought through."
            ),
            followup="Where would you draw the tenancy boundary in a cluster shared by three business units?",
        ),
        Q(
            q="What is a pod, and why not just schedule containers?",
            level=FOUNDATION,
            answer=(
                "A pod is the smallest thing Kubernetes will schedule, and it is a group of containers that "
                "share a network namespace and can share volumes. Sharing the network namespace means the "
                "containers reach each other on localhost and present a single pod IP to the cluster. That "
                "gives you the sidecar pattern - a proxy, a log shipper, a credential helper - without "
                "rebuilding the application image. Kubernetes schedules pods rather than containers because "
                "co-located helpers must land on the same node to be useful at all."
            ),
            analogy=(
                "A pod is a taxi, not a passenger. Everyone in the taxi shares the same address and arrives "
                "at the same time; you book the taxi, not each individual seat."
            ),
            context=(
                "The shared namespace is also a shared fate. If an init container never completes, nothing "
                "else in that pod starts. If one container in the pod eats the memory limit, the whole pod "
                "can be OOM-killed. And because the pod IP is per-pod rather than per-container, two "
                "containers in the same pod cannot both bind port 8080 - a genuinely common cause of a "
                "sidecar that will not start."
            ),
            steps=[
                "Define the pod as the scheduling unit, not as \"a wrapper around a container\".",
                "Explain the shared network namespace and shared volumes, and what they enable.",
                "Give one concrete pattern - sidecar or init container - and why it needs co-location.",
                "Close with the shared-fate consequence, which is what senior candidates add and juniors miss.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.status.podIP}{\"\\n\"}'",
                "oc describe pod <pod> | sed -n '/Init Containers/,/Conditions/p'",
                "oc logs <pod> -c <container> --previous",
            ],
            redflag=(
                "Do not describe a pod as \"one container\". You will be asked about sidecars within thirty "
                "seconds and the answer will unravel."
            ),
            followup="An init container is stuck. How do you tell whether it is the image, the config or a dependency?",
        ),
        Q(
            q="What is a container image, and why do we care about digests instead of tags?",
            level=FOUNDATION,
            answer=(
                "An image is a manifest plus a set of read-only filesystem layers, all content-addressed. A "
                "tag such as latest is a mutable pointer - someone can move it - whereas a digest is a "
                "SHA-256 hash of the manifest and can only ever refer to one exact set of bytes. In "
                "production I pin by digest so that what I tested is what runs, and so an incident "
                "investigation can say with certainty which code was on the node."
            ),
            analogy=(
                "A tag is a nickname and a digest is a fingerprint. Nicknames get reassigned; fingerprints do "
                "not."
            ),
            context=(
                "This is not academic. The classic outage is a Deployment with image:app:latest that has run "
                "fine for six weeks, a node reboots, the image is re-pulled, and a newer latest arrives that "
                "nobody approved. Pinning by digest turns that from an outage into a pull request. It is also "
                "the foundation of everything else in supply chain security - signing, SBOMs and admission "
                "policy all key off an immutable reference."
            ),
            steps=[
                "Describe the structure: manifest, layers, content addressing.",
                "Contrast the mutable tag with the immutable digest.",
                "Give the failure story - a re-pull silently changing the running version.",
                "Connect it forward to signing and admission control, which only work on stable references.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.status.containerStatuses[*].imageID}{\"\\n\"}'",
                "skopeo inspect docker://registry.example.com/app:1.4 | head -20",
                "oc get is <stream> -o jsonpath='{.spec.tags[*].referencePolicy.type}'",
            ],
            redflag=(
                "Do not defend using latest in production because \"it is convenient\". Convenience is the "
                "reason the outage was hard to explain."
            ),
            followup="How would you enforce digest pinning across every namespace in the cluster?",
        ),
        Q(
            q="What do namespaces and cgroups actually do?",
            level=FOUNDATION,
            answer=(
                "Linux namespaces partition what a process can see - its own PID tree, network stack, mount "
                "table, hostname and users. Cgroups, version 2 on RHCOS, partition what a process can "
                "consume: CPU weight and quota, a memory limit, IO throughput and a PID ceiling. Namespaces "
                "are about visibility, cgroups are about accounting and enforcement. Kubernetes requests and "
                "limits are ultimately just values written into cgroup files."
            ),
            analogy=(
                "Namespaces are the walls between offices; cgroups are the electricity meter and the fuse. "
                "One stops you seeing the neighbours, the other stops you tripping the building."
            ),
            context=(
                "Knowing this collapses two mysteries into one. \"Why was my pod killed with exit code 137?\" "
                "is the memory cgroup enforcing a hard limit - the kernel OOM killer, not Kubernetes, made "
                "that decision. \"Why is my app slow when CPU usage looks low?\" is CPU quota throttling "
                "within the cgroup period. Both answers live in cgroup accounting, and both are invisible if "
                "you only look at pod status."
            ),
            steps=[
                "Separate the two concepts cleanly: visibility versus consumption.",
                "Name a couple of namespace types and a couple of cgroup controllers so it is concrete.",
                "Map Kubernetes concepts onto them - requests to CPU weight, limits to quota and memory caps.",
                "Finish with the two symptoms they explain: OOMKilled and CPU throttling.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host cat /sys/fs/cgroup/kubepods.slice/.../memory.max",
                "container_cpu_cfs_throttled_seconds_total   # Prometheus",
                "oc describe pod <pod> | grep -A3 'Last State'",
            ],
            redflag=(
                "Do not say Kubernetes \"kills the pod when it uses too much memory\". The kernel does it, "
                "and the distinction is exactly what the question is testing."
            ),
            followup="A container is being OOMKilled but node memory looks fine. What is happening?",
        ),
        Q(
            q="What does the kubelet do?",
            level=FOUNDATION,
            answer=(
                "The kubelet is the node's agent. It watches the API server for pods bound to its node, asks "
                "the container runtime to create the sandbox and containers, mounts volumes, pulls images "
                "using the node's pull secrets, runs the probes, and reports node and pod status back. It "
                "does not decide where pods go - that is the scheduler - and it does not create pods for "
                "Deployments. It is the thing that turns a scheduling decision into running processes."
            ),
            analogy=(
                "The kubelet is the site foreman. Head office decides what gets built and where; the foreman "
                "makes it happen on that plot and phones in progress."
            ),
            context=(
                "Most \"the node is broken\" incidents are kubelet-shaped. If the kubelet cannot reach the "
                "API server, the node goes NotReady even though its pods are still running and serving "
                "traffic. If the kubelet's disk fills, it starts evicting pods under DiskPressure. Knowing "
                "which decisions belong to the kubelet stops you from restarting a control-plane component "
                "when the problem was local certificate expiry or a full /var."
            ),
            steps=[
                "State its scope: everything on this node, nothing about placement.",
                "List the responsibilities in order - watch, sandbox, volumes, images, probes, status.",
                "Name the boundary explicitly: the scheduler binds, the kubelet executes.",
                "Add the failure signature - a kubelet that cannot talk to the API server produces NotReady "
                "while workloads may still be serving.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host journalctl -u kubelet -n 200 --no-pager",
                "oc get node <node> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc adm node-logs <node> --path=kubelet/",
            ],
            redflag=(
                "Do not say the kubelet schedules pods. It is a small slip that tells the interviewer you "
                "have not read the control flow."
            ),
            followup="A node is NotReady but its pods are still answering traffic. What do you check first?",
        ),
        Q(
            q="What is CRI-O and where does it sit?",
            level=FOUNDATION,
            answer=(
                "CRI-O is the container runtime OpenShift ships, and it exists to do exactly what the "
                "Kubernetes Container Runtime Interface asks and nothing more. The kubelet speaks CRI to "
                "CRI-O, CRI-O pulls images, sets up the sandbox, and calls runc or crun to start the actual "
                "process. Its deliberately narrow scope is the point - it tracks Kubernetes releases and "
                "carries no daemon-level features you did not ask for."
            ),
            analogy=(
                "CRI-O is a specialist contractor with one trade licence. It does not try to also be the "
                "architect, the delivery service and the site office the way a general-purpose container "
                "daemon does."
            ),
            context=(
                "You touch CRI-O directly when the kubelet's view and reality disagree - a pod that shows as "
                "running but has no process, an image pull that fails only on one node, a sandbox that will "
                "not delete. That is when you drop to the node and use crictl, which speaks the same CRI "
                "socket. Being comfortable saying \"I would check with crictl on the node\" is a genuine "
                "seniority signal."
            ),
            steps=[
                "Place it in the chain: kubelet, CRI, CRI-O, runc or crun, Linux process.",
                "Explain the design intent - minimal, Kubernetes-versioned, no extra daemon surface.",
                "Say when you would inspect it directly rather than through the API.",
                "Name the tool: crictl, from oc debug node.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host crictl ps -a",
                "oc debug node/<node> -- chroot /host crictl images | head",
                "oc debug node/<node> -- chroot /host journalctl -u crio -n 100 --no-pager",
            ],
            redflag=(
                "Do not say \"OpenShift uses Docker\". It has not for many major versions and it dates you "
                "immediately."
            ),
            followup="An image pulls on three nodes and fails on the fourth. Where do you look?",
        ),
        Q(
            q="What is Kubernetes actually doing, in one sentence?",
            level=FOUNDATION,
            answer=(
                "Kubernetes stores your desired state and runs control loops that continuously try to make "
                "observed state match it. You do not tell it to start a container; you declare that three "
                "replicas should exist, and a controller notices the gap and closes it. Everything else - "
                "self-healing, rolling updates, autoscaling - is that same loop applied to a different "
                "object. Once you see the pattern, unfamiliar objects stop being scary because they all "
                "behave the same way."
            ),
            analogy=(
                "It is a thermostat, not a light switch. You set twenty-one degrees and walk away; the "
                "thermostat keeps checking and correcting forever."
            ),
            context=(
                "This is the single most load-bearing idea in the whole interview. It tells you where to "
                "look when something is wrong: find the controller that owns the object and read its status "
                "conditions, because that controller is writing down exactly why it cannot reach the desired "
                "state. It also explains why manually deleting a pod is usually pointless - the loop will "
                "just recreate it, and you have destroyed your evidence."
            ),
            steps=[
                "State the loop: desired state in etcd, controller observes, controller acts, status reported.",
                "Give one worked example - three replicas, one node dies, ReplicaSet creates a replacement.",
                "Draw the operational conclusion: read conditions on the owner, not just pod status.",
                "Add the anti-pattern: deleting pods to fix things destroys evidence and fixes nothing.",
            ],
            evidence=[
                "oc get deploy <name> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get events -n <ns> --sort-by=.lastTimestamp | tail -20",
                "oc get <kind> <name> -o yaml | sed -n '/status:/,$p'",
            ],
            redflag=(
                "Do not describe Kubernetes as \"a tool that runs containers\". Every follow-up question in "
                "the interview is really about reconciliation."
            ),
            followup="A Deployment says 3/3 ready but users get errors. Where has the loop misled you?",
        ),
        Q(
            q="What does OpenShift add on top of Kubernetes?",
            level=INTERMEDIATE,
            answer=(
                "OpenShift is Kubernetes with the operational problem solved rather than left as an exercise. "
                "It adds a lifecycle-managed release - the Cluster Version Operator drives a tested payload "
                "of Cluster Operators - plus node configuration through the Machine Config Operator, "
                "integrated OAuth and identity, Routes and a supported ingress layer, Security Context "
                "Constraints that make restricted-by-default real, an integrated registry and build system, "
                "and monitoring and logging that are part of the product rather than a project you assemble."
            ),
            analogy=(
                "Upstream Kubernetes is an engine. OpenShift is the certified car around it - the engine is "
                "the same, but somebody has already solved brakes, airbags, servicing intervals and who you "
                "call when it stops."
            ),
            context=(
                "The reason this matters operationally is supportability. Because the release is a single "
                "digest-addressed payload, an upgrade moves a known set of components together and the "
                "cluster can tell you whether it is Upgradeable. Because node config is declarative through "
                "MCO, a node that drifts gets corrected rather than becoming a snowflake. Those two "
                "properties are what make a fleet of clusters manageable by a small team."
            ),
            steps=[
                "Start with the framing: same Kubernetes API, plus lifecycle and enterprise defaults.",
                "Group the additions - lifecycle, node config, identity, ingress, security defaults, "
                "developer tooling, observability.",
                "Say why each grouping exists operationally rather than listing product names.",
                "Finish with supportability: a tested payload and declarative nodes are what make fleets "
                "possible.",
            ],
            evidence=[
                "oc get clusterversion ; oc get co",
                "oc get mcp ; oc get scc",
                "oc get oauth cluster -o yaml | head -30",
            ],
            redflag=(
                "Do not answer \"OpenShift is Kubernetes with a nicer UI\". The console is the least "
                "interesting thing on the list."
            ),
            followup="Which of those additions would you miss most on day two, and why?",
        ),
        Q(
            q="How does administering RHCOS differ from administering RHEL?",
            level=INTERMEDIATE,
            answer=(
                "RHCOS is immutable and machine-managed. You do not log in and yum install; the filesystem is "
                "largely read-only, packages are layered with rpm-ostree, first boot is configured by "
                "Ignition, and ongoing configuration comes from MachineConfig objects rendered and applied by "
                "the Machine Config Operator. The node is treated as cattle: if it drifts or breaks, you "
                "replace it through the Machine API rather than repairing it by hand."
            ),
            analogy=(
                "RHEL is a house you renovate. RHCOS is a hotel room - you change the booking, not the "
                "wallpaper, and housekeeping resets anything you left behind."
            ),
            context=(
                "The practical consequence is that any manual node change is temporary and invisible to the "
                "next person. Someone edits sysctl by hand, the node reboots into a rendered MachineConfig, "
                "and the fix vanishes at the worst possible moment. Every durable node change - kernel "
                "arguments, chrony, extra certificates, kubelet config - has to become a MachineConfig or a "
                "PerformanceProfile so it survives reboots and applies to every node in the pool."
            ),
            steps=[
                "State the principle: immutable, declaratively configured, replaceable.",
                "Name the mechanisms - Ignition at first boot, MachineConfig plus MCO afterwards, rpm-ostree "
                "for layering.",
                "Explain the operational rule: no durable change without a MachineConfig.",
                "Add the debugging path - oc debug node gives you a shell without making the change durable.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host rpm-ostree status",
                "oc get mc ; oc get mcp -o wide",
                "oc debug node/<node> -- chroot /host journalctl -u machine-config-daemon -n 100 --no-pager",
            ],
            redflag=(
                "Do not describe SSHing to nodes to fix things as your normal workflow. It is the clearest "
                "signal that you would create snowflakes in a fleet."
            ),
            followup="You need a custom kernel argument on GPU nodes only. Walk me through it.",
        ),
        Q(
            q="How do you troubleshoot at the node level in OpenShift?",
            level=INTERMEDIATE,
            answer=(
                "I use oc debug node to get a privileged pod on the node, chroot to /host, and then work with "
                "familiar Linux tools: journalctl for kubelet and CRI-O, crictl for the runtime's own view, "
                "df and lsblk for disk, ip and ss for networking, and dmesg for kernel events such as OOM "
                "kills. I prefer this to SSH because it goes through the API, is audited, and works "
                "identically on every node without managing keys."
            ),
            analogy=(
                "It is the difference between having a key cut for the building and signing in at reception. "
                "Both get you inside; only one leaves a record and works when you change buildings."
            ),
            context=(
                "The order you look in matters more than the commands. Node problems cluster into four "
                "families - disk, memory, runtime and network - and each has a fast test. DiskPressure shows "
                "in df and in the node conditions. Memory shows in dmesg as OOM kills. Runtime shows as "
                "crictl and kubelet disagreeing. Network shows as failing DNS or a hung endpoint from the "
                "node itself. Running those four checks takes two minutes and usually ends the guessing."
            ),
            steps=[
                "Read the node conditions first - the kubelet has often already told you which family it is.",
                "Get a shell: oc debug node/<node>, then chroot /host.",
                "Run the four fast checks - disk, kernel messages, runtime state, node-local network.",
                "Correlate with events and metrics before changing anything, and capture must-gather if it "
                "may become a support case.",
            ],
            evidence=[
                "oc get node <node> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc debug node/<node> -- chroot /host sh -c 'df -h /var; dmesg -T | tail -30'",
                "oc debug node/<node> -- chroot /host crictl pods --state notready",
            ],
            redflag=(
                "Do not start by rebooting the node. It destroys the evidence and often just relocates the "
                "problem to a different node."
            ),
            followup="Everything on the node looks healthy but pods there fail DNS. Now what?",
        ),
        Q(
            q="What is SELinux doing in an OpenShift cluster?",
            level=INTERMEDIATE,
            answer=(
                "SELinux is mandatory access control on the node, enforcing on RHCOS by default. Each pod "
                "gets a Multi-Category Security label, and the files it writes are labelled to match, so even "
                "a process running as root inside a container cannot read another container's data or touch "
                "host paths it was not granted. It is the layer that turns a container escape attempt into a "
                "denied syscall rather than a lateral move."
            ),
            analogy=(
                "It is the hotel key card system. Being inside the building does not mean every door opens - "
                "your card is coded for your floor and your room only."
            ),
            context=(
                "SELinux surfaces in interviews as a mount failure. A pod mounts a hostPath or an NFS share, "
                "the process gets permission denied even though the UNIX permissions look right, and the "
                "AVC denial is sitting in the node's audit log. The correct answer is to fix the label or the "
                "volume's SELinux options - not to set the node to permissive, which is an unsupported "
                "configuration and a security finding waiting to happen."
            ),
            steps=[
                "Define it as mandatory access control layered on top of normal permissions.",
                "Explain per-pod MCS labels and why they isolate pods from each other.",
                "Describe the diagnosis: look for AVC denials in the node audit log, matched by timestamp.",
                "State the fix hierarchy - correct labelling or a supported volume option first, never "
                "disabling enforcement.",
            ],
            evidence=[
                "oc debug node/<node> -- chroot /host ausearch -m avc -ts recent",
                "oc get pod <pod> -o jsonpath='{.spec.securityContext.seLinuxOptions}'",
                "oc debug node/<node> -- chroot /host ls -Z /var/lib/kubelet/pods/<uid>/volumes",
            ],
            redflag=(
                "Do not suggest setenforce 0 as a fix. In a regulated environment that single sentence can "
                "end the interview."
            ),
            followup="A pod mounting an NFS share gets permission denied. Walk me through your diagnosis.",
        ),
        Q(
            q="How would you build a secure, minimal container image for production?",
            level=SENIOR,
            answer=(
                "I start from a small, supported base such as a Red Hat Universal Base Image, build with a "
                "multi-stage Containerfile so compilers and build secrets never reach the final layer, run as "
                "an arbitrary non-root UID with a group-writable filesystem so it satisfies restricted-v2, "
                "drop all capabilities, and pin everything by digest. Then the pipeline scans the image, "
                "generates an SBOM, signs it, and promotes the same digest through environments instead of "
                "rebuilding per stage."
            ),
            analogy=(
                "Ship the finished cake, not the whole kitchen. Nobody needs the mixer, the raw eggs or the "
                "recipe notes in the box you hand to the customer."
            ),
            context=(
                "The arbitrary-UID requirement catches people out constantly. OpenShift's default SCC assigns "
                "a random high UID per namespace, so an image that hardcodes USER 1001 and writes to a "
                "directory owned by 1001 will fail with permission denied. The fix is to make paths "
                "group-writable by the root group, which is what UBI images already do. Getting this right "
                "once removes an entire category of \"it works on my laptop\" tickets."
            ),
            steps=[
                "Choose a supported minimal base and pin it by digest.",
                "Use multi-stage builds so build tooling and secrets stay out of the runtime layer.",
                "Make the image arbitrary-UID safe: no hardcoded UID assumptions, group-writable paths, no "
                "root requirement.",
                "Wire the pipeline: scan, SBOM, sign, then promote the identical digest across environments "
                "with admission policy enforcing signed images.",
            ],
            evidence=[
                "podman build --squash-all -t app:1.4 . ; podman inspect app:1.4 --format '{{.User}}'",
                "syft app:1.4 -o spdx-json > sbom.json ; cosign sign --key <key> <digest>",
                "oc get scc restricted-v2 -o jsonpath='{.runAsUser.type}{\"\\n\"}'",
            ],
            redflag=(
                "Do not solve a permissions problem by granting the anyuid SCC. That is trading a five-minute "
                "image fix for a permanent audit finding."
            ),
            followup="The vendor image insists on running as root. What are your options, ranked?",
        ),
        Q(
            q="How do you decide what belongs in the image versus in configuration?",
            level=ARCHITECT,
            answer=(
                "The image holds anything that must be identical everywhere and is safe to be public inside "
                "the organisation: the runtime, dependencies, the application binary. Configuration that "
                "varies by environment goes in ConfigMaps, and anything secret goes in Secrets or an external "
                "vault injected at runtime. My rule is that one digest should be promotable from development "
                "to production unchanged - if a rebuild is required to move an artefact between environments, "
                "the boundary is drawn in the wrong place."
            ),
            analogy=(
                "The image is the aircraft; configuration is the flight plan. You do not build a new aircraft "
                "because you are flying a different route today."
            ),
            context=(
                "Getting this wrong produces two distinct failures. Baking configuration into images means "
                "every environment runs different bytes, so testing proves nothing and rollbacks are "
                "ambiguous. Pushing too much into runtime configuration produces pods that cannot start "
                "without a dozen ConfigMaps existing first, which turns namespace creation into a fragile "
                "ritual. The middle ground is a small, well-documented set of environment inputs with sane "
                "defaults and schema validation in CI."
            ),
            steps=[
                "State the promotion rule: the same digest moves across environments untouched.",
                "Classify inputs - invariant into the image, environmental into ConfigMaps, sensitive into "
                "Secrets or an external vault.",
                "Validate configuration in CI against a schema so a bad value fails a pipeline rather than a "
                "rollout.",
                "Make the contract explicit in the golden path template so every team draws the line the "
                "same way.",
            ],
            evidence=[
                "oc set env deploy/<name> --list",
                "oc get cm,secret -n <ns> --show-labels",
                "oc rollout history deploy/<name>   # does a config change show as a new revision",
            ],
            redflag=(
                "Do not defend building a separate image per environment. It quietly destroys the value of "
                "everything you tested."
            ),
            followup="How do you roll out a configuration change safely if it does not create a new pod revision?",
        ),
    ],
)
