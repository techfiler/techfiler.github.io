"""Part 6 - OVN-Kubernetes, egress control and secondary networks."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=6,
    title="OVN-Kubernetes, egress and secondary networks",
    subtitle="The layer under the Service - where packets are actually forwarded, dropped or silently lost",
    intro=(
        "This is where networking stops being objects and starts being packets. The questions here separate "
        "people who have read about the software-defined network from people who have opened it up during an "
        "incident at two in the morning. The recurring theme is that the SDN is not a black box: intent "
        "becomes logical flows, logical flows become OpenFlow rules, and OpenFlow rules become packets on a "
        "NIC. Every one of those layers is inspectable, and being able to say which layer you would inspect "
        "is worth more than memorising any single command."
    ),
    infographics=["ovn_layers"],
    questions=[
        Q(
            q="What is a CNI plugin?",
            level=FOUNDATION,
            answer=(
                "CNI is the interface the runtime uses to attach a pod to a network. When a pod sandbox is "
                "created, the runtime calls the configured CNI plugin, which creates the interface, assigns "
                "an IP from the cluster's pod network, and sets up routes - then tears it all down when the "
                "pod goes away. On OpenShift the default is OVN-Kubernetes, and it is what gives every pod "
                "its own routable address inside the cluster."
            ),
            analogy=(
                "It is the utility company connecting a new building to the grid. Standard socket, standard "
                "process, whichever supplier you have contracted."
            ),
            context=(
                "The reason to know this precisely is that CNI failures have a specific signature: pods stick "
                "in ContainerCreating with a sandbox creation error mentioning the network plugin. That is "
                "not an image problem or a scheduling problem, and it usually means the CNI pods on that node "
                "are unhealthy or the node has run out of pod IPs. Recognising the message saves you from "
                "investigating the application."
            ),
            steps=[
                "Define CNI as the contract between the runtime and the network plugin.",
                "Describe what happens at pod creation - interface, address, routes - and at deletion.",
                "Name OVN-Kubernetes as the OpenShift default and where its pods run.",
                "Give the failure signature: ContainerCreating with a sandbox or network plugin error.",
            ],
            evidence=[
                "oc describe pod <pod> | grep -i -A5 sandbox",
                "oc -n openshift-ovn-kubernetes get pods -o wide | grep <node>",
                "oc debug node/<node> -- chroot /host ls /etc/cni/net.d",
            ],
            redflag=(
                "Do not treat a sandbox creation failure as an application problem. The message names the "
                "network plugin for a reason."
            ),
            followup="Pods on one node are stuck in ContainerCreating. What do you check?",
        ),
        Q(
            q="What is MTU and why does it matter so much in a cluster network?",
            level=FOUNDATION,
            answer=(
                "MTU is the largest packet a link will carry. The cluster network encapsulates pod traffic - "
                "Geneve in OVN-Kubernetes - which adds header overhead, so the pod MTU must be smaller than "
                "the underlying node MTU by that overhead. If it is not, large packets are dropped somewhere "
                "in the middle of the path while small ones sail through, which produces a failure that looks "
                "nothing like a network problem."
            ),
            analogy=(
                "It is a low bridge on a delivery route. Vans get through all day; the one lorry that matters "
                "does not, and nobody connects the two events."
            ),
            context=(
                "This is the classic silent failure. Health checks pass because they are tiny. DNS works "
                "because queries are small. Then a large HTTP response or a database result set hangs "
                "forever, and the application team reports intermittent timeouts. The giveaway is that small "
                "payloads always work and large ones always fail, and the test is a ping with the "
                "do-not-fragment flag at increasing sizes."
            ),
            steps=[
                "Define MTU and the encapsulation overhead that makes pod MTU smaller than node MTU.",
                "Describe the signature: small packets fine, large packets lost, no errors logged.",
                "Test with do-not-fragment pings at increasing sizes to find the actual limit.",
                "Fix it at the source - node or fabric MTU misconfiguration - rather than by lowering "
                "application payload sizes.",
            ],
            evidence=[
                "oc exec <pod> -- ping -M do -s 1400 -c 2 <target-pod-ip>",
                "oc debug node/<node> -- chroot /host ip -d link show br-ex | head",
                "oc get network.operator cluster -o jsonpath='{.spec.defaultNetwork.ovnKubernetesConfig.mtu}{\"\\n\"}'",
            ],
            redflag=(
                "Do not describe this as an intermittent application bug. Size-dependent failure is a "
                "signature, not a coincidence."
            ),
            followup="Small requests work, large responses hang. Prove it is MTU in two commands.",
        ),
        Q(
            q="What is a NetworkAttachmentDefinition?",
            level=FOUNDATION,
            answer=(
                "It is the custom resource that defines an additional network a pod can attach to - the CNI "
                "configuration for a secondary interface, expressed as a Kubernetes object. A pod requests it "
                "with an annotation, and Multus attaches the extra interface at creation time. It is how you "
                "give a pod a macvlan interface onto a VLAN, a bridge to a storage network, or an SR-IOV "
                "virtual function."
            ),
            analogy=(
                "It is a second phone line specification for a desk. The main line is standard for everyone; "
                "this describes the dedicated line and who is allowed to have one."
            ),
            context=(
                "Because it is a namespaced object, it is also an access control point: a team can only "
                "attach to networks defined in, or shared with, their namespace. That matters because a "
                "secondary interface typically bypasses the cluster's normal policy path - traffic on a "
                "macvlan interface is not subject to standard NetworkPolicy - so who may create and use these "
                "definitions is a security decision, not just a networking one."
            ),
            steps=[
                "Define it as CNI configuration expressed as a namespaced custom resource.",
                "Explain how a pod requests it and that Multus performs the attachment.",
                "Name typical types: macvlan, bridge, ipvlan, SR-IOV.",
                "Call out the governance angle - secondary networks sidestep default policy, so restrict who "
                "can define and use them.",
            ],
            evidence=[
                "oc get net-attach-def -A",
                "oc get pod <pod> -o jsonpath='{.metadata.annotations.k8s\\.v1\\.cni\\.cncf\\.io/networks}{\"\\n\"}'",
                "oc exec <pod> -- ip -br addr",
            ],
            redflag=(
                "Do not treat secondary networks as a purely technical detail. They can quietly bypass the "
                "network policy you spent months rolling out."
            ),
            followup="How do you stop a tenant attaching to a network they should not reach?",
        ),
        Q(
            q="What is OVN-Kubernetes and how is it structured?",
            level=INTERMEDIATE,
            answer=(
                "OVN-Kubernetes is the default OpenShift network plugin. It translates Kubernetes intent - "
                "Services, NetworkPolicies, EgressFirewalls - into OVN logical switches, routers and access "
                "control lists held in a northbound database. ovn-controller on each node compiles those "
                "logical flows into OpenFlow rules in the node's integration bridge, and Open vSwitch "
                "forwards the actual packets, with Geneve encapsulation for traffic between nodes."
            ),
            analogy=(
                "It is a rail network. The timetable is the logical intent, the signalling system compiles it "
                "into instructions for each junction, and the trains are the packets. A delay can come from "
                "the timetable, the signals or the track."
            ),
            context=(
                "The structure is the diagnostic map. A policy that never takes effect is a problem between "
                "intent and the northbound database, so you look at ovnkube-master. A policy that exists "
                "everywhere but fails on one node is a compilation or datapath problem, so you look at "
                "ovn-controller and OVS flows on that node. Being able to split the problem that way is what "
                "keeps an OVN incident from becoming an all-hands guessing session."
            ),
            steps=[
                "Describe the four layers: Kubernetes intent, OVN northbound, ovn-controller, OVS datapath.",
                "Say where each component runs and which pods represent it.",
                "Map symptoms to layers - cluster-wide policy failure versus single-node forwarding failure.",
                "Note that Geneve encapsulation is why node MTU and the underlay fabric matter.",
            ],
            evidence=[
                "oc -n openshift-ovn-kubernetes get pods -o wide",
                "oc -n openshift-ovn-kubernetes rsh <ovnkube-node-pod> ovn-nbctl show | head -30",
                "oc debug node/<node> -- chroot /host ovs-ofctl dump-flows br-int | wc -l",
            ],
            redflag=(
                "Do not call it \"the SDN\" and leave it there. The follow-up is always which layer you would "
                "inspect."
            ),
            followup="A NetworkPolicy works on every node except one. Which layer, and why?",
        ),
        Q(
            q="What is Multus and when would you use it?",
            level=INTERMEDIATE,
            answer=(
                "Multus is a meta-plugin that lets a pod have more than one network interface. The default "
                "cluster network stays as eth0 for Services, DNS and normal traffic, and Multus attaches "
                "additional interfaces defined by NetworkAttachmentDefinitions. You use it when a workload "
                "genuinely needs a separate path - a VLAN carrying storage or telecom signalling traffic, a "
                "dedicated high-throughput interface, or an SR-IOV virtual function for latency-sensitive "
                "work."
            ),
            analogy=(
                "It is a second network card in a server. The office LAN is still there for email; the extra "
                "card is for the thing that cannot share a queue."
            ),
            context=(
                "The trap is assuming the secondary interface behaves like the primary one. Kubernetes "
                "Services do not front it, standard NetworkPolicy does not filter it, cluster DNS does not "
                "know about it, and IP address management is your responsibility. So it is the right tool for "
                "a real requirement and the wrong tool for \"we want faster networking\", where the honest "
                "answer is usually to measure first."
            ),
            steps=[
                "Explain the model: default interface plus additional attachments.",
                "Give real use cases - separated traffic planes, high throughput, SR-IOV.",
                "State plainly what you lose: Services, standard policy, cluster DNS, automatic IPAM.",
                "Insist on measuring the requirement before adding an interface, because complexity is "
                "permanent.",
            ],
            evidence=[
                "oc exec <pod> -- ip -br addr",
                "oc get net-attach-def -n <ns> -o yaml | head -30",
                "oc get pod <pod> -o jsonpath='{.metadata.annotations.k8s\\.v1\\.cni\\.cncf\\.io/network-status}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not add a secondary network to solve a performance complaint you have not measured. You "
                "will inherit an IPAM problem and keep the latency."
            ),
            followup="Traffic on the secondary interface bypasses your NetworkPolicy. How do you control it?",
        ),
        Q(
            q="What is an EgressFirewall?",
            level=INTERMEDIATE,
            answer=(
                "EgressFirewall is an OVN-Kubernetes object that controls which external destinations pods in "
                "a namespace may reach. Rules are ordered allow and deny entries matched on CIDR, DNS name or "
                "node selector, and the first match wins. It complements NetworkPolicy: NetworkPolicy is "
                "mostly about east-west traffic between pods, EgressFirewall is about north-south traffic "
                "leaving the cluster."
            ),
            analogy=(
                "NetworkPolicy is the rules about which rooms staff may enter. EgressFirewall is the rule "
                "about which addresses the company car may drive to."
            ),
            context=(
                "In regulated environments this is how you demonstrate that a workload cannot exfiltrate data "
                "to arbitrary internet destinations, so it appears in compliance conversations as often as "
                "technical ones. The operational subtlety is DNS-based rules: they resolve names periodically, "
                "so a destination behind a large CDN with rotating addresses can intermittently fail. Where "
                "reliability matters, CIDR rules or an egress proxy are the more predictable answer."
            ),
            steps=[
                "Define it as ordered, first-match egress control at namespace scope.",
                "Contrast it with NetworkPolicy: north-south versus east-west.",
                "Warn about DNS-based rules and rotating addresses, and offer CIDR or a proxy instead.",
                "Verify from inside a pod after applying, and keep a documented rollback.",
            ],
            evidence=[
                "oc get egressfirewall -A -o yaml | head -40",
                "oc exec <pod> -- curl -sS -m 5 https://<external>   # expected allow and expected deny",
                "Network Observability flows filtered by namespace with a dropped verdict",
            ],
            redflag=(
                "Do not rely on DNS-name egress rules for a critical integration behind a CDN. The "
                "intermittent failures will be blamed on the application for weeks."
            ),
            followup="A namespace intermittently loses access to an allowed external API. What do you suspect?",
        ),
        Q(
            q="What is EgressIP, and what are its operational risks?",
            level=INTERMEDIATE,
            answer=(
                "EgressIP pins the source address that a namespace's outbound traffic appears to come from, "
                "so an external firewall or database can allow-list a stable IP. OVN assigns that address to "
                "an eligible node and source-NATs matching traffic through it. The risks are that the address "
                "is hosted on one node at a time, so node failure moves it and briefly interrupts connections, "
                "and that it depends on the underlying network allowing that address to move between nodes."
            ),
            analogy=(
                "It is a company car with a recognised number plate that the security gate lets through. If "
                "the car is off the road, someone else has to take the plate - and the gate needs a moment to "
                "notice."
            ),
            context=(
                "The reason this is asked at senior level is that EgressIP is usually adopted to satisfy an "
                "external team's firewall requirement, and it quietly creates a dependency between your node "
                "lifecycle and their access control. Node maintenance, autoscaling and address exhaustion all "
                "become externally visible events. Where the external system supports it, an egress proxy or "
                "identity-based access is a more robust answer, and saying that shows architectural "
                "judgement."
            ),
            steps=[
                "Explain the mechanism: namespace selection, node assignment, source NAT.",
                "Name the failure behaviour on node loss and what it does to long-lived connections.",
                "Check that the underlay permits the address to move and that eligible nodes are labelled.",
                "Offer the alternative - proxy or identity-based allow-listing - and state the trade-off.",
            ],
            evidence=[
                "oc get egressip ; oc get nodes -l k8s.ovn.org/egress-assignable",
                "oc get egressip <name> -o jsonpath='{.status.items}' | python3 -m json.tool",
                "oc exec <pod> -- curl -sS https://<echo-service>   # confirm observed source address",
            ],
            redflag=(
                "Do not present EgressIP as free. It couples your node lifecycle to somebody else's firewall "
                "policy."
            ),
            followup="You need to drain the node currently hosting an EgressIP. What do you tell the "
                     "dependent team?",
        ),
        Q(
            q="What is the device plugin pattern?",
            level=INTERMEDIATE,
            answer=(
                "A device plugin is a DaemonSet that advertises specialised hardware on a node as an extended "
                "resource - GPUs, SR-IOV virtual functions, FPGAs, QAT. It reports how many are available, "
                "and the scheduler then treats them like any other countable resource: a pod requests one, "
                "the scheduler only considers nodes with a free unit, and the plugin performs the device "
                "allocation and injects what the container needs to use it."
            ),
            analogy=(
                "It is the hire desk for specialist equipment. It publishes how many units are on the shelf, "
                "and nobody is sent to a depot that has none left."
            ),
            context=(
                "The important consequence is that these resources are integers and cannot be overcommitted - "
                "one virtual function is either yours or it is not. So a pod requesting a device that is fully "
                "allocated stays Pending regardless of CPU and memory availability, and the event says "
                "insufficient for a resource name most people do not recognise. Knowing to check the device "
                "plugin's health, and the node's advertised allocatable for that resource, is the fast path."
            ),
            steps=[
                "Define the plugin as a DaemonSet advertising extended resources to the kubelet.",
                "Explain that scheduling treats them as countable, non-overcommittable integers.",
                "Give the Pending signature and where to read advertised versus allocated counts.",
                "Check plugin pod health first - a crashed plugin makes the whole node's devices vanish.",
            ],
            evidence=[
                "oc get node <node> -o jsonpath='{.status.allocatable}' | python3 -m json.tool",
                "oc get pods -n openshift-sriov-network-operator -o wide",
                "oc describe pod <pod> | grep -i insufficient",
            ],
            redflag=(
                "Do not treat extended resources as best-effort. They are exact counts, and the scheduler "
                "will never round down for you."
            ),
            followup="A GPU pod is Pending while nodes show plenty of CPU. What is your first check?",
        ),
        Q(
            q="How do you diagnose an MTU black hole?",
            level=SENIOR,
            answer=(
                "I confirm the signature first: small payloads succeed, large ones hang or reset, and the "
                "failure is reproducible by size rather than by time. Then I use do-not-fragment pings at "
                "increasing sizes from a pod to find the actual maximum, repeat between nodes to see whether "
                "the limit is in the overlay or the underlay, and compare configured pod MTU against the node "
                "and fabric MTU. The fix belongs at whichever layer is inconsistent, usually the underlay."
            ),
            analogy=(
                "You establish that vans get through and lorries do not, then you drive the route measuring "
                "bridge heights until you find the one that is too low."
            ),
            context=(
                "These incidents are expensive because the symptom is reported as an application bug and "
                "everyone investigates the application. They often appear after an infrastructure change "
                "nobody told you about - a new switch, a VPN or tunnel inserted in the path, a migration to "
                "different hypervisor networking. Asking \"what changed in the underlay\" early is often "
                "faster than any packet capture."
            ),
            steps=[
                "Establish the size-dependent signature and confirm it is reproducible.",
                "Binary-search the working size with do-not-fragment pings, pod to pod and node to node.",
                "Compare configured cluster MTU with node interface MTU and the documented fabric MTU.",
                "Fix at the inconsistent layer, then re-test the original application path and record the "
                "expected values so it is caught by monitoring next time.",
            ],
            evidence=[
                "oc exec <pod> -- ping -M do -s 1472 -c 2 <peer-pod-ip>",
                "oc debug node/<node> -- chroot /host ping -M do -s 8972 -c 2 <other-node-ip>",
                "oc get network.operator cluster -o jsonpath='{.status.defaultNetwork}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not lower the application's payload size as the fix. You have hidden a fabric "
                "misconfiguration that will resurface elsewhere."
            ),
            followup="The cluster MTU is correct but node-to-node large pings fail. Where is the problem?",
        ),
        Q(
            q="How do you isolate a node-specific OVN-Kubernetes failure?",
            level=SENIOR,
            answer=(
                "I prove it is node-specific first by running the same test from pods on several nodes, "
                "because that single fact eliminates most of the search space. Then I look at the ovnkube "
                "pods on the affected node, at ovn-controller's connection to the databases, and at whether "
                "OpenFlow rules were actually programmed in the integration bridge. If intent is correct "
                "cluster-wide but flows are missing on one node, the problem is compilation or the local "
                "datapath, not policy."
            ),
            analogy=(
                "One junction on the rail network is not following the timetable. Everyone else is running "
                "fine, so you go to that signal box rather than reprinting the timetable."
            ),
            context=(
                "The most common causes are an ovn-controller that lost its database connection and is "
                "serving stale flows, a node under such memory pressure that the OVS process is being "
                "starved, and a node that was cordoned or partially drained leaving inconsistent state. "
                "Restarting the ovnkube pod on that node often clears it, but doing that before you have "
                "captured flow state means you will never know why - and it will happen again."
            ),
            steps=[
                "Prove node-specificity by testing the same path from pods on at least three nodes.",
                "Check ovnkube pod health and ovn-controller connectivity to the OVN databases on that node.",
                "Compare programmed flows on the affected node against a healthy one for the same policy.",
                "Capture evidence, then restart the node's ovnkube pod as the smallest safe mitigation and "
                "verify.",
            ],
            evidence=[
                "oc -n openshift-ovn-kubernetes get pods -o wide | grep <node>",
                "oc debug node/<node> -- chroot /host ovs-ofctl dump-flows br-int | grep <podIP>",
                "oc -n openshift-ovn-kubernetes logs <ovnkube-node-pod> -c ovn-controller --tail=200",
            ],
            redflag=(
                "Do not reboot the node as a first response. You will lose the evidence and inherit the same "
                "incident next week."
            ),
            followup="Flows are missing only for one namespace on one node. What does that narrow it to?",
        ),
        Q(
            q="How do you troubleshoot an SR-IOV pod that will not schedule?",
            level=SENIOR,
            answer=(
                "I check the chain from hardware to request. Does the node advertise the extended resource, "
                "and how many are allocatable versus allocated? Is the SR-IOV operator healthy and has the "
                "policy actually configured virtual functions on that node's NIC? Does the pod request the "
                "right resource name and reference the right NetworkAttachmentDefinition? And is anything "
                "else on the node holding the remaining functions - because they cannot be shared."
            ),
            analogy=(
                "It is checking whether the specialist tool exists in the depot, whether it is on the shelf, "
                "and whether the request form names the tool you actually meant."
            ),
            context=(
                "Beyond simple exhaustion, the usual causes are a policy whose node selector does not match "
                "the nodes you expected, a NIC whose firmware or BIOS settings do not have virtualisation "
                "enabled, or a resource name mismatch between the policy and the pod spec. There is also a "
                "timing element: applying an SR-IOV policy triggers a MachineConfig rollout and node reboots, "
                "so the capacity genuinely does not exist until the pool has finished updating."
            ),
            steps=[
                "Read the FailedScheduling event and note the exact resource name it reports as insufficient.",
                "Compare node allocatable against allocated for that resource across candidate nodes.",
                "Verify the SR-IOV policy applied - node selector, NIC selector, number of virtual functions, "
                "and that the pool finished rolling out.",
                "Confirm the pod's resource name and network annotation match the policy exactly.",
            ],
            evidence=[
                "oc get sriovnetworknodestate -n openshift-sriov-network-operator -o yaml | head -60",
                "oc get node <node> -o jsonpath='{.status.allocatable}' | python3 -m json.tool",
                "oc get sriovnetworknodepolicy -A -o wide ; oc get mcp",
            ],
            redflag=(
                "Do not conclude the hardware is faulty before checking that the MachineConfig rollout "
                "completed. The functions do not exist until the node has rebooted."
            ),
            followup="Half the nodes advertise the resource and half do not. Where do you look?",
        ),
        Q(
            q="What does Kubernetes NMState provide, and how do you design node networking with it?",
            level=SENIOR,
            answer=(
                "NMState lets you declare node network configuration - bonds, VLANs, bridges, static "
                "addresses, routes - as NodeNetworkConfigurationPolicy objects, applied by an operator and "
                "reported back through NodeNetworkState. That turns node networking from something configured "
                "by hand or by an installer into something versioned, selectable by node label, and "
                "observable. For design I bond physical interfaces for redundancy, carry separate traffic "
                "classes on VLANs, and roll changes out to one node first."
            ),
            analogy=(
                "It is building regulations for the wiring rather than trusting each electrician's habits. "
                "Same standard, applied per building type, inspected afterwards."
            ),
            context=(
                "Node network changes are uniquely dangerous because a mistake can make the node unreachable, "
                "and you cannot fix it through the API you just cut off. That is why the practice matters "
                "more than the syntax: apply to a single labelled canary node, verify NodeNetworkState "
                "reports success and the node stays Ready, and only then widen the selector. Having "
                "out-of-band console access before you start is not optional."
            ),
            steps=[
                "Declare the intended state as a policy selected by node label, not applied cluster-wide.",
                "Design for redundancy - bonded uplinks, separated VLANs per traffic class, explicit MTU.",
                "Roll out to one canary node, verify NodeNetworkState and node readiness, then widen.",
                "Ensure out-of-band access exists before any change, and keep a documented revert policy.",
            ],
            evidence=[
                "oc get nncp ; oc get nnce",
                "oc get nns <node> -o yaml | sed -n '/interfaces:/,/routes:/p' | head -40",
                "oc get nodes -o wide   # readiness after each wave",
            ],
            redflag=(
                "Do not apply a network policy to every node at once. The failure mode is a cluster you "
                "cannot reach to fix."
            ),
            followup="You apply a bond change and the node goes NotReady. What is your recovery path?",
        ),
        Q(
            q="What is the Network Observability Operator used for?",
            level=SENIOR,
            answer=(
                "It collects flow-level data from the cluster network using eBPF agents on each node, "
                "enriches it with Kubernetes identity - namespace, pod, service, node - and lets you query "
                "and visualise it. It answers questions that metrics and logs cannot: who is actually talking "
                "to whom, what is being dropped and by which rule, where cross-zone traffic is coming from, "
                "and what a namespace's real dependencies are before you apply a policy."
            ),
            analogy=(
                "It is CCTV for the network with name badges attached. Not just that a packet moved, but "
                "which service sent it and which policy stopped it."
            ),
            context=(
                "The highest-value use is de-risking NetworkPolicy rollout: instead of guessing dependencies "
                "from an architecture diagram, you observe two weeks of real flows and write allow rules from "
                "evidence. It is also how you find expensive cross-zone traffic and how you prove, during an "
                "incident, whether traffic is being dropped by policy or never arrived at all. The cost is "
                "real - flow collection consumes CPU and storage - so sampling and retention need deliberate "
                "tuning."
            ),
            steps=[
                "Describe the mechanism: eBPF agents, flow records, Kubernetes enrichment.",
                "Give the primary use cases - dependency discovery, drop attribution, cross-zone cost.",
                "Tune sampling and retention against the cluster's traffic volume and storage budget.",
                "Use it before and after a policy change as the evidence that the change was safe.",
            ],
            evidence=[
                "oc get flowcollector cluster -o yaml | head -40",
                "oc -n netobserv get pods -o wide",
                "Flow query filtered by namespace and drop reason around the incident window",
            ],
            redflag=(
                "Do not enable full-fidelity flow collection cluster-wide without capacity planning. You can "
                "generate more data than the cluster you are observing."
            ),
            followup="How would you use flow data to write NetworkPolicy for an existing namespace?",
        ),
        Q(
            q="What are the operational considerations for a dual-stack cluster?",
            level=SENIOR,
            answer=(
                "Dual-stack means Services and pods can have both IPv4 and IPv6 addresses, and the "
                "considerations are mostly about consistency across the whole path. Every layer needs to "
                "support both - load balancers, DNS records, firewalls, the application libraries - and "
                "Services need an explicit ipFamilyPolicy rather than relying on defaults. Address planning "
                "and monitoring have to cover both families, and troubleshooting means checking both, "
                "because a service can be reachable on one and broken on the other."
            ),
            analogy=(
                "It is running a bilingual service. Every sign, every form and every member of staff has to "
                "handle both languages, or customers get a confusing half-service."
            ),
            context=(
                "The realistic failure is partial support somewhere in the chain: an external firewall that "
                "only has IPv4 rules, a client library that prefers IPv6 and times out, a health check "
                "configured for one family only. The result is intermittent behaviour that depends on which "
                "address a client happened to resolve. Deciding the policy up front - which family is "
                "preferred, which services are single-stack - avoids most of it."
            ),
            steps=[
                "Confirm end-to-end support across load balancers, DNS, firewalls and client libraries.",
                "Set ipFamilyPolicy explicitly per Service rather than accepting defaults.",
                "Plan addressing and NetworkPolicy for both families; policies must cover both or they leak.",
                "Test and monitor both paths independently, and record which family clients actually use.",
            ],
            evidence=[
                "oc get svc <svc> -o jsonpath='{.spec.ipFamilies} {.spec.ipFamilyPolicy}{\"\\n\"}'",
                "oc get network.config cluster -o jsonpath='{.status.clusterNetwork}' | python3 -m json.tool",
                "oc exec <pod> -- curl -sS -m 3 -6 http://<svc>:<port>/healthz",
            ],
            redflag=(
                "Do not assume a NetworkPolicy written with IPv4 CIDRs also restricts IPv6. It does not, and "
                "that is an open path you did not intend."
            ),
            followup="A service is reachable over IPv4 and times out over IPv6. Where do you start?",
        ),
        Q(
            q="How would you establish a network performance baseline for a new cluster?",
            level=ARCHITECT,
            answer=(
                "I measure before anyone depends on it, so that future complaints have something to compare "
                "against. That means pod-to-pod throughput and latency within a node, across nodes and across "
                "zones; DNS resolution latency; ingress request latency at a known concurrency; and packet "
                "loss under load. I record the numbers, the MTU, the topology and the date, publish them, and "
                "re-run the same tests after significant infrastructure changes."
            ),
            analogy=(
                "It is weighing yourself the day you buy the scales. Without that first number, every later "
                "reading is an opinion."
            ),
            context=(
                "The value shows up during arguments, not during the test. When an application team says the "
                "network is slow, a baseline lets you answer in minutes with data rather than defending the "
                "platform on instinct. It also catches infrastructure regressions that nobody announced - a "
                "firmware change, a new switch, a hypervisor migration - because the same test suddenly "
                "returns a different number."
            ),
            steps=[
                "Define the test matrix: intra-node, inter-node, inter-zone, ingress path, DNS.",
                "Run it with a repeatable tool and fixed parameters, and record MTU and topology alongside.",
                "Publish the results with the date and the cluster configuration they describe.",
                "Re-run after infrastructure changes and upgrades, and alert on regression beyond a "
                "threshold.",
            ],
            evidence=[
                "iperf3 between pods on different nodes and different zones, recorded",
                "Ingress p50 and p99 latency at a fixed concurrency, from a fixed client location",
                "DNS resolution latency histogram from a test pod, per zone",
            ],
            redflag=(
                "Do not wait for a complaint to measure. Without a baseline every performance discussion "
                "becomes a matter of opinion."
            ),
            followup="A team claims the network got slower after an upgrade. How do you settle it?",
        ),
    ],
)
