"""Part 8 - HPC and AI workloads on OpenShift."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=8,
    title="HPC and AI on OpenShift",
    subtitle="GPUs, RDMA, MPI and the operators that turn a Kubernetes cluster into an AI factory",
    intro=(
        "Running AI on OpenShift is not as simple as scheduling a pod with nvidia.com/gpu. The NVIDIA GPU "
        "Operator installs drivers and the container toolkit cluster-wide; Node Feature Discovery labels "
        "the hardware; ClusterPolicy is the single knob that must match your OpenShift version; and "
        "training jobs need RDMA, NUMA alignment and MPI launcher patterns that general workloads never "
        "touch. Interviewers use this part to see whether you have operated a GPU cluster or only read "
        "the documentation — the difference shows up in how you talk about placement, monitoring and what "
        "breaks when someone upgrades the operator without a rollback plan."
    ),
    infographics=["hpc_alignment"],
    questions=[
        Q(
            q="What does the NVIDIA GPU Operator install and manage on OpenShift?",
            level=FOUNDATION,
            answer=(
                "The GPU Operator is a bundle of controllers and DaemonSets that automate everything "
                "required to run CUDA workloads on OpenShift without hand-installing drivers on each node. "
                "It deploys the NVIDIA driver container, the device plugin that advertises nvidia.com/gpu "
                "resources, the container toolkit so runtimes inject GPU libraries, optional DCGM for "
                "monitoring, MIG manager when partitioning is enabled, and supporting validators that "
                "confirm the stack is healthy before marking nodes ready for GPU pods."
            ),
            analogy=(
                "It is a turnkey AV installer — amplifier, speakers, wiring and calibration — instead of "
                "buying each component and hoping they are compatible."
            ),
            context=(
                "Before the operator, platform teams SSHed to nodes, installed drivers, rebooted, and "
                "fought drift every upgrade. The operator makes GPU nodes cattle, but it also centralises "
                "risk: a bad ClusterPolicy upgrade can drain every GPU node at once. Interviewers want you "
                "to name the moving parts, not just say 'install the operator from OperatorHub'."
            ),
            steps=[
                "Install the NVIDIA GPU Operator from OperatorHub or a mirrored catalog.",
                "Define a ClusterPolicy matched to your OpenShift version and driver branch.",
                "Wait for driver daemonsets, device plugin and toolkit pods to reach Ready on GPU nodes.",
                "Validate with an CUDA sample pod requesting nvidia.com/gpu.",
            ],
            evidence=[
                "oc get clusterpolicy -n nvidia-gpu-operator -o yaml | head -40",
                "oc get pods -n nvidia-gpu-operator -o wide",
                "oc describe node <gpu-node> | grep -A3 'Allocatable'",
            ],
            redflag=(
                "Do not install GPU drivers manually on operator-managed nodes. Two driver stacks on one "
                "node is a support nightmare."
            ),
            followup="GPU operator pods are Ready but workloads fail with 'unknown device'. What next?",
        ),
        Q(
            q="What is Node Feature Discovery and why does the GPU Operator depend on it?",
            level=FOUNDATION,
            answer=(
                "Node Feature Discovery runs a worker on each node that detects hardware and kernel "
                "features — CPU flags, PCI devices, kernel modules, memory — and publishes them as node "
                "labels. The GPU Operator uses those labels to decide which daemonsets to schedule: only "
                "nodes with NVIDIA PCI IDs get driver pods; only nodes with the right CPU features get "
                "certain validators. Without NFD, the operator cannot distinguish a GPU server from a "
                "generic worker and will either skip hardware or attempt installs on the wrong machines."
            ),
            analogy=(
                "NFD is the inventory scanner in a warehouse. Without labels on the shelves, the forklift "
                "driver does not know which aisle has GPUs."
            ),
            context=(
                "NFD is easy to overlook because it installs quietly alongside the GPU Operator, but it "
                "is the scheduling glue for every accelerated workload on OpenShift. Custom rules can "
                "expose InfiniBand HCAs, SR-IOV VFs or storage accelerators using the same mechanism. "
                "When labels are missing after a BIOS change, every downstream operator looks broken even "
                "though the hardware is fine."
            ),
            steps=[
                "Deploy NFD operator and NodeFeatureRules for GPU PCI vendor IDs and related features.",
                "Confirm nfd-worker pods label nodes with feature.node.kubernetes.io/pci-* labels.",
                "Install GPU Operator with node affinity keyed on those labels.",
                "Extend rules for InfiniBand, NVMe or custom accelerators as needed.",
            ],
            evidence=[
                "oc get nodefeaturediscovery -A",
                "oc get node <gpu-node> --show-labels | grep feature.node.kubernetes.io",
                "oc get nodefeaturerules -n openshift-nfd -o yaml | head -30",
            ],
            redflag=(
                "Do not assume all GPU nodes auto-label correctly after a firmware upgrade. Re-run "
                "discovery or verify rules after hardware changes."
            ),
            followup="A new GPU node never gets driver pods. Which labels do you check first?",
        ),
        Q(
            q="What is a ClusterPolicy and what does it configure?",
            level=INTERMEDIATE,
            answer=(
                "ClusterPolicy is the GPU Operator's cluster-wide configuration custom resource. One object "
                "declares the driver version, whether MIG or GPUDirect RDMA is enabled, daemonset "
                "placement tolerations, container registry mirrors, toolkit settings, DCGM exporter "
                "options, and validator behaviour. Changing it triggers a rolling reconcile across GPU "
                "nodes — driver pods restart, device plugins re-register — so it is the equivalent of a "
                "MachineConfig for the entire GPU software stack."
            ),
            analogy=(
                "It is the single thermostat for the whole building's heating system. Turn it without "
                "telling anyone and every room changes temperature at once."
            ),
            context=(
                "Version skew between ClusterPolicy and OpenShift is the most common production incident "
                "in GPU clusters. Teams upgrade OpenShift, leave the policy on an old driver branch, and "
                "wonder why pods hang in ContainerCreating. Senior answers treat ClusterPolicy changes "
                "like kernel upgrades: canary node, workload test, documented rollback."
            ),
            steps=[
                "Match driver and operator versions to the OpenShift release compatibility matrix.",
                "Set daemonset tolerations and node selectors for dedicated GPU pools.",
                "Enable optional components — DCGM, MIG manager, sandbox workloads — explicitly.",
                "Apply to one node pool first; run a CUDA validation job before fleet-wide rollout.",
            ],
            evidence=[
                "oc get clusterpolicy cluster-policy -n nvidia-gpu-operator -o yaml",
                "oc get pods -n nvidia-gpu-operator -l app=nvidia-driver-daemonset",
                "GPU operator validator pod logs after a policy change",
            ],
            redflag=(
                "Do not edit ClusterPolicy during active training jobs without maintenance windows. Driver "
                "pod restarts evict running GPU workloads."
            ),
            followup="OpenShift upgraded but GPU pods fail with driver version mismatch. Where do you look?",
        ),
        Q(
            q="What is GPUDirect RDMA and when does it matter for AI?",
            level=INTERMEDIATE,
            answer=(
                "GPUDirect RDMA lets a GPU read and write memory on a remote machine — or on a local NIC "
                "— without copying through host CPU buffers. For distributed training, that means "
                "all-reduce and parameter exchange use the NIC and GPU DMA engines directly, cutting latency "
                "and CPU overhead compared with staging tensors in pinned host memory first. It matters "
                "when training spans multiple GPUs on multiple nodes and the network — usually InfiniBand "
                "or RoCE — is the bottleneck."
            ),
            analogy=(
                "Normal I/O is handing a package to a courier who drives it across town. GPUDirect RDMA is "
                "a pneumatic tube straight into the other office."
            ),
            context=(
                "Enabling GPUDirect RDMA in ClusterPolicy is only half the story. You still need "
                "compatible NIC firmware, correct PCI topology, often ACS settings in BIOS, and "
                "NCCL or MPI configured to use the right transport. Interviewers probe whether you "
                "understand it as a system requirement — driver, NIC, topology, library — not a checkbox "
                "in the operator."
            ),
            steps=[
                "Enable GPUDirect RDMA in ClusterPolicy when hardware supports it.",
                "Verify NIC and GPU share favourable PCI topology; disable ACS if vendor guidance requires.",
                "Install and configure the Network Operator for SR-IOV or macvlan as your CNI needs.",
                "Validate with NCCL tests or vendor micro-benchmarks across nodes.",
            ],
            evidence=[
                "oc get clusterpolicy -o jsonpath='{.items[0].spec.gdrcopy/gpudirectRdma}{\"\\n\"}'",
                "nvidia-smi topo -m   # run on GPU node via oc debug",
                "NCCL all_reduce_perf or equivalent multi-node benchmark output",
            ],
            redflag=(
                "Do not enable GPUDirect RDMA without measuring baseline training throughput first. "
                "Misconfigured RDMA can be slower than TCP."
            ),
            followup="NCCL hangs at init despite GPUDirect enabled. What topology issues do you suspect?",
        ),
        Q(
            q="How do InfiniBand and SR-IOV support AI networking on OpenShift?",
            level=INTERMEDIATE,
            answer=(
                "InfiniBand provides high-bandwidth, low-latency RDMA-capable networking ideal for "
                "multi-node training collectives. SR-IOV exposes virtual functions from a physical HCA or "
                "NIC directly into pods, bypassing the OVS kernel path for data-plane traffic. On OpenShift "
                "the SR-IOV Network Operator configures NodePolicy objects, creates SriovNetwork "
                "definitions and attaches VF interfaces to pods that need bare-metal-like performance. "
                "Together they give MPI and NCCL a direct path from GPU memory to the fabric."
            ),
            analogy=(
                "InfiniBand is the dedicated race track. SR-IOV is giving each driver their own lane instead "
                "of sharing the public motorway."
            ),
            context=(
                "AI networking on OpenShift trades Kubernetes convenience for performance. SR-IOV pods "
                "lose standard ClusterIP Services for that interface, need their own IPAM and sit outside "
                "default NetworkPolicy enforcement. Interviewers want you to state those trade-offs and "
                "tie them back to NUMA — the VF must sit on the same socket as the GPU."
            ),
            steps=[
                "Install SR-IOV Network Operator; define SriovNetworkNodePolicy for HCAs or NICs.",
                "Create SriovNetwork objects for the training VLAN or partition keys.",
                "Schedule training pods with resource requests for VF devices and GPU resources.",
                "Align CPU, GPU and HCA on one NUMA node; verify with topology tools.",
            ],
            evidence=[
                "oc get sriovnetworknodepolicy,sriovnetwork -n openshift-sriov-network-operator",
                "oc get sriovnetworknodestate -n openshift-sriov-network-operator -o yaml | head -40",
                "Inside training pod: ibstat ; ip -br link",
            ],
            redflag=(
                "Do not deploy SR-IOV for AI without a network security model. Default NetworkPolicy "
                "does not protect VF traffic."
            ),
            followup="Training pods need both GPU and IB VF. How do you prevent them landing on the wrong NUMA node?",
        ),
        Q(
            q="How do you run MPI workloads on OpenShift?",
            level=INTERMEDIATE,
            answer=(
                "MPI on OpenShift uses a launcher pattern: a Kubernetes Job or Operator-managed "
                "MPIJob creates a launcher pod that invokes mpirun or horovodrun, which spawns worker "
                "pods — one per rank — with shared SSH keys or the PMI2/PMIx interface over the cluster "
                "network. Workers need predictable DNS, often a headless Service, compatible RDMA "
                "interfaces if using InfiniBand, and the same container image on every rank. The OpenShift "
                "MPI Operator or Kubeflow Training Operator wraps this lifecycle so you submit a CR "
                "instead of hand-writing mpirun commands."
            ),
            analogy=(
                "MPI is an orchestra conductor with musicians in separate rooms. The launcher is the "
                "conductor; headless Services are the intercom; every musician needs the same sheet music "
                "— the container image."
            ),
            context=(
                "The failure modes are familiar to anyone who has run HPC on Kubernetes: DNS latency "
                "during scale-up, ranks starting before workers are ready, SELinux blocking intra-pod "
                "communication, and NCCL picking the wrong interface. Interviewers reward mentioning "
                "gang scheduling — all ranks or none — and resource quotas on GPU namespaces."
            ),
            steps=[
                "Build or pull an MPI-enabled CUDA image with OpenMPI or Intel MPI and NCCL.",
                "Install an MPIJob-capable operator; define worker and launcher resource requests.",
                "Expose a headless Service for rank discovery; mount SSH secrets or use PMI.",
                "Test with a small ring benchmark before scaling to full node count.",
            ],
            evidence=[
                "oc get mpijob -A   # or training.kubeflow.org MPIJob CR",
                "oc logs <launcher-pod> | grep -i 'rank\\|connected'",
                "ompi_info --param btl tcp   # inside worker pod",
            ],
            redflag=(
                "Do not run MPI at scale without testing DNS and NCCL socket selection at half scale first. "
                "Failures compound with rank count."
            ),
            followup="Rank 0 starts but workers never connect. What do you check in order?",
        ),
        Q(
            q="What is MIG and when would you partition a GPU?",
            level=SENIOR,
            answer=(
                "Multi-Instance GPU is an NVIDIA A100-and-newer feature that splits one physical GPU "
                "into up to seven isolated instances, each with dedicated compute and memory. The GPU "
                "Operator's MIG manager applies a MIG partition profile on the node and advertises "
                "separate extended resources such as nvidia.com/mig-1g.5gb. You partition when many "
                "small inference or development workloads need GPU isolation but a full GPU each would "
                "leave expensive silicon idle — not when a single training job needs the entire device."
            ),
            analogy=(
                "MIG is subdividing a house into flats with separate meters. Great for tenants who need "
                "privacy; wrong if one family wants the whole building for a party."
            ),
            context=(
                "MIG profiles are fixed at node boot and require draining GPU workloads to change. "
                "Mixing MIG and full-GPU nodes in one pool demands clear taints and resource names so "
                "schedulers do not place a eight-GPU training job on MIG slices. Interviewers probe "
                "whether you know MIG is an operational commitment, not a runtime slider."
            ),
            steps=[
                "Enable MIG in ClusterPolicy and deploy mig-manager on A100-or-newer nodes.",
                "Choose a profile — e.g. 1g.5gb times seven — matching workload memory needs.",
                "Taint MIG nodes; update pod specs to request nvidia.com/mig-* resources.",
                "Plan profile changes as maintenance events requiring node drain.",
            ],
            evidence=[
                "oc get node <node> -o json | jq '.status.allocatable | with_entries(select(.key|test(\"nvidia.com/mig\")))'",
                "nvidia-smi -L   # on node via oc debug",
                "oc get clusterpolicy -o yaml | grep -i mig",
            ],
            redflag=(
                "Do not enable MIG on nodes running large multi-GPU training. Those jobs need full devices "
                "and NCCL across NVLink."
            ),
            followup="Inference needs three profiles on one A100. How do you model that in Kubernetes resources?",
        ),
        Q(
            q="What makes a container CUDA-capable on OpenShift?",
            level=FOUNDATION,
            answer=(
                "Three layers must align. The node runs an NVIDIA driver installed by the GPU Operator. "
                "The container runtime uses the NVIDIA container toolkit to inject driver libraries and "
                "device nodes when a pod requests nvidia.com/gpu. The image carries the CUDA user-space "
                "libraries and application binaries compatible with that driver version — typically from "
                "nvidia/cuda or a derived training framework image. Missing any layer produces errors "
                "ranging from 'cannot load libcuda.so' to silent CPU fallback."
            ),
            analogy=(
                "CUDA in a container is a rental car: the road is the driver, the key is the device "
                "plugin, and the car itself is your image. You need all three to drive."
            ),
            context=(
                "Platform teams own the first two layers; data science owns the image — until something "
                "breaks and both sides blame each other. Interview answers that mention driver/CUDA "
                "compatibility matrices and the difference between CUDA forward compatibility and exact "
                "version match sound experienced. OpenShift's restricted SCC also means images must not "
                "assume root-only GPU paths without testing."
            ),
            steps=[
                "Confirm GPU Operator driver daemonset is Ready on the target node.",
                "Request nvidia.com/gpu in pod resources limits; use runtimeClassName if configured.",
                "Pull an image whose CUDA tag matches the deployed driver branch.",
                "Run nvidia-smi inside the pod as a smoke test before the real workload.",
            ],
            evidence=[
                "oc run cuda-test --image=nvidia/cuda:12.2.0-base-ubuntu22.04 --restart=Never "
                "--overrides='{\"spec\":{\"containers\":[{\"name\":\"cuda-test\",\"image\":\"nvidia/cuda:12.2.0-base-ubuntu22.04\","
                "\"command\":[\"nvidia-smi\"],\"resources\":{\"limits\":{\"nvidia.com/gpu\":\"1\"}}}]}}'",
                "oc exec <pod> -- ls -l /usr/local/nvidia/lib64/libcuda.so*",
                "oc describe pod <pod> | grep -i nvidia",
            ],
            redflag=(
                "Do not pin ancient CUDA images against a new driver without checking compatibility. "
                "Framework wheels often lag driver releases."
            ),
            followup="Pod shows GPU allocated but nvidia-smi fails with driver/library version mismatch. Cause?",
        ),
        Q(
            q="How do training and inference workloads differ in placement requirements?",
            level=SENIOR,
            answer=(
                "Training is throughput-oriented and gang-scheduled: all GPUs across all nodes must start "
                "together, stay co-located for hours or days, and prefer NVLink within nodes and RDMA "
                "across nodes. Inference is latency- and density-oriented: many smaller pods, horizontal "
                "scaling, possibly MIG slices, strict pod anti-affinity for HA, and autoscaling based on "
                "queue depth or request rate. Training belongs on dedicated tainted pools with full GPUs; "
                "inference often shares nodes with careful quota and uses HPA or KEDA."
            ),
            analogy=(
                "Training is a film crew on location for six weeks — everyone must arrive the same day with "
                "all the kit. Inference is a chain of coffee shops — open more counters when the queue "
                "grows."
            ),
            context=(
                "Mixing them on one pool without taints is how production inference gets evicted by a "
                "researcher's multi-node Job. Interviewers want tiering: separate MachineConfigPools or "
                "node labels, different ClusterPolicy options — MIG on inference, full GPU on training — "
                "and different SLOs reflected in quotas and priority classes."
            ),
            steps=[
                "Label and taint training nodes for exclusive multi-GPU Jobs with PriorityClass.",
                "Place inference on MIG or fractional-GPU pools with HPA/KEDA and PodDisruptionBudgets.",
                "Use topology spread for inference HA; use gang scheduling for training.",
                "Monitor each tier separately — DCGM for utilisation, SLIs for inference latency.",
            ],
            evidence=[
                "oc get nodes -l nvidia.com/gpu.product -L node-role,cluster.ocs.io/openshift-storage",
                "oc describe quota -n ai-training ; oc describe quota -n ai-inference",
                "DCGM_FI_DEV_GPU_UTIL metrics split by namespace label",
            ],
            redflag=(
                "Do not run bursty inference autoscaling on the same nodes as a week-long training job "
                "without isolation. Capacity math is not additive."
            ),
            followup="A researcher wants inference on training nodes 'just for a demo'. What do you say?",
        ),
        Q(
            q="What does the OpenShift Network Operator provide for GPU clusters?",
            level=INTERMEDIATE,
            answer=(
                "The Network Operator manages cluster networking components as a coordinated stack: "
                "CNI plugin — OVN-Kubernetes by default — kube-multus for secondary interfaces, SR-IOV "
                "operator dependencies, IPAM controllers and sometimes Whereabouts or static IPAM for "
                "secondary networks. For GPU clusters it is the layer that lets training pods attach an "
                "SR-IOV or macvlan interface alongside the default pod network, which NCCL and MPI need "
                "when they cannot use the overlay."
            ),
            analogy=(
                "The default CNI is the office LAN. Multus and SR-IOV are pulling a dedicated fibre "
                "cable straight to the machine room for workloads that outgrow Wi-Fi."
            ),
            context=(
                "Candidates often conflate the GPU Operator with networking. The GPU Operator delivers "
                "drivers; the Network Operator delivers interfaces. A common incident is Multus configured "
                "but SriovNetworkNodePolicy missing, so pods declare a secondary net-attach-def and hang "
                "in ContainerCreating. Architecturally both operators must be upgraded and tested together."
            ),
            steps=[
                "Confirm Network Operator is Healthy in ClusterOperator status.",
                "Install SR-IOV or configure Multus net-attach-defs for the training network.",
                "Annotate pods with k8s.v1.cni.cncf.io/networks for secondary interfaces.",
                "Validate NCCL or MPI uses the intended interface name inside the pod.",
            ],
            evidence=[
                "oc get clusteroperator network -o yaml | grep -A5 conditions",
                "oc get net-attach-def -A",
                "oc describe pod <training-pod> | grep -i multus",
            ],
            redflag=(
                "Do not attach SR-IOV networks without coordinating with the network team on VLANs and "
                "switch port modes. Kubernetes cannot fix a misconfigured top-of-rack."
            ),
            followup="Pod has Multus annotation but no secondary interface appears. Where do you debug?",
        ),
        Q(
            q="How do you monitor GPUs with DCGM on OpenShift?",
            level=SENIOR,
            answer=(
                "DCGM — Data Center GPU Manager — exposes detailed GPU telemetry: utilisation, memory, "
                "temperature, power, ECC errors, NVLink counters and process-level stats. The GPU Operator "
                "deploys DCGM exporter as a daemonset that translates those metrics into Prometheus format "
                "on a scrape endpoint. You wire ServiceMonitor into the platform monitoring stack, build "
                "dashboards for utilisation and thermals, and alert on sustained thermal throttle, XID "
                "errors or zero utilisation on allocated GPUs — the classic sign of a stuck training job."
            ),
            analogy=(
                "DCGM is the aircraft black box and instrument panel combined. Utilisation tells you the "
                "engines are running; XID errors tell you something is about to fall off."
            ),
            context=(
                "Monitoring GPUs is not optional at scale — finance sees idle A100s, and silent ECC "
                "errors corrupt weeks of training. Interviewers want Prometheus metric names, integration "
                "with User Workload Monitoring for tenant namespaces, and the habit of correlating DCGM "
                "with node conditions and driver pod restarts after upgrades."
            ),
            steps=[
                "Enable DCGM exporter in ClusterPolicy or the operator's monitoring section.",
                "Create or enable ServiceMonitor so platform Prometheus scrapes GPU metrics.",
                "Import NVIDIA or community Grafana dashboards for DCGM_FI_* metrics.",
                "Alert on XID errors, thermal limits, and allocation-with-zero-utilisation.",
            ],
            evidence=[
                "oc get servicemonitor -n nvidia-gpu-operator",
                "curl -s http://<dcgm-exporter>:9400/metrics | grep DCGM_FI_DEV_GPU_UTIL",
                "Prometheus: DCGM_FI_DEV_XID_ERRORS > 0",
            ],
            redflag=(
                "Do not rely on nvidia-smi polling scripts in production. They miss ECC and NVLink "
                "counters DCGM exposes."
            ),
            followup="Metrics show 100% GPU utilisation but training loss is flat. What else do you check?",
        ),
        Q(
            q="How would you design an AI node pool on OpenShift?",
            level=ARCHITECT,
            answer=(
                "I split training and inference into separate MachineConfigPools with taints, labels and "
                "quotas. GPU Operator ClusterPolicy is pinned to tested driver branches per pool. NFD rules "
                "label GPU model and NIC type; SR-IOV policies expose HCAs on training nodes only. "
                "Network Operator delivers Multus definitions for RDMA VLANs. Monitoring via DCGM and "
                "User Workload Monitoring is mandatory before tenants arrive. Upgrade order is documented: "
                "OpenShift, then Network Operator, then GPU Operator, then validation Jobs — never the "
                "reverse."
            ),
            analogy=(
                "It is building a hospital wing: separate theatres for surgery and clinics for outpatient, "
                "shared utilities, but different staffing rules and equipment in each room."
            ),
            context=(
                "The architect answer ties hardware BOM to software policy: A100 nodes with NVSwitch for "
                "training, L40S or MIG-enabled nodes for inference, InfiniBand only where NCCL benchmarks "
                "justify it. It also covers tenancy — namespaces, quotas, PriorityClasses — and a golden "
                "path CI job that must pass after every platform change. That is what separates platform "
                "engineering from 'we installed the GPU operator once'."
            ),
            steps=[
                "Define hardware SKUs per tier; document PCI topology and NIC placement per SKU.",
                "Create dedicated MCPs with taints, PerformanceProfile if low-latency CPU matters.",
                "Install NFD, Network Operator, GPU Operator with tier-specific ClusterPolicy.",
                "Publish a tenant onboarding guide: quotas, MPIJob template, monitoring dashboards, "
                "upgrade windows.",
            ],
            evidence=[
                "Reference design: node pool diagram with taints, labels and network VLANs",
                "oc get mcp,gpu,performanceprofile,sriovnetworknodepolicy -A",
                "Golden path Job: CUDA + NCCL benchmark results after last platform change",
            ],
            redflag=(
                "Do not buy GPUs before defining upgrade and rollback procedures. The most expensive "
                "component is downtime during a failed driver migration."
            ),
            followup="Finance wants one pool to cut cost. How do you explain why training and inference differ?",
        ),
    ],
)
