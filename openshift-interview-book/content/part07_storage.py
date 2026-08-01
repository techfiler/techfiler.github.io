"""Part 7 - Persistent storage."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=7,
    title="Storage that survives the pod",
    subtitle="Provisioning, attachment, snapshots and the failures that lose data",
    intro=(
        "Storage is the part of the platform where mistakes are permanent. A bad network change causes an "
        "outage; a bad storage decision loses data that nobody can recreate. That is why storage questions "
        "tend to be scored on caution rather than cleverness - interviewers want to hear that you know which "
        "step in the provisioning chain is stuck, that you never assume a snapshot is a backup, and that you "
        "have restored something at least once rather than only configured backups. The chain from claim to "
        "mounted filesystem has five links, and almost every storage incident is one of them."
    ),
    infographics=["pvc_lifecycle"],
    questions=[
        Q(
            q="What are PersistentVolumes and PersistentVolumeClaims?",
            level=FOUNDATION,
            answer=(
                "A PersistentVolume is a piece of storage in the cluster - real capacity on a backend. A "
                "PersistentVolumeClaim is a workload's request for storage of a given size, access mode and "
                "class. The claim binds to a volume, and the pod references the claim rather than the volume, "
                "so applications ask for what they need without knowing anything about the backend. With "
                "dynamic provisioning the volume is created on demand by a CSI driver when the claim appears."
            ),
            analogy=(
                "The claim is a hotel reservation for a room of a certain type; the volume is the actual "
                "room. The guest holds the reservation, not a key to a specific door number."
            ),
            context=(
                "The separation is what makes manifests portable between clusters with completely different "
                "storage backends, and it is also where the most common confusion lives: the PVC is "
                "namespaced and belongs to the application, while the PV is cluster-scoped and belongs to the "
                "platform. Deleting a namespace deletes the claims, and what happens to the underlying data "
                "then depends entirely on the reclaim policy - which is why that setting deserves more "
                "attention than it usually gets."
            ),
            steps=[
                "Define the claim as the request and the volume as the resource, and say which is namespaced.",
                "Explain binding and dynamic provisioning through the StorageClass.",
                "Point out that the pod references the claim, which is what makes manifests portable.",
                "Flag that deletion behaviour depends on reclaim policy, not on intuition.",
            ],
            evidence=[
                "oc get pvc -n <ns> ; oc get pv | grep <ns>",
                "oc get pvc <pvc> -o jsonpath='{.status.phase} {.spec.storageClassName}{\"\\n\"}'",
                "oc describe pvc <pvc> | sed -n '/Events/,$p'",
            ],
            redflag=(
                "Do not say a PVC \"is\" storage. The binding relationship is exactly what fails when a "
                "claim stays Pending."
            ),
            followup="What happens to the data when the namespace holding the PVC is deleted?",
        ),
        Q(
            q="What is a StorageClass?",
            level=FOUNDATION,
            answer=(
                "A StorageClass names a kind of storage the platform offers and tells the provisioner how to "
                "create it - which CSI driver, what parameters such as disk type or replication, the reclaim "
                "policy, whether volumes can be expanded, and the binding mode. A claim asks for a class by "
                "name and gets storage with those properties. One class is usually marked default, which is "
                "what claims get when they do not specify."
            ),
            analogy=(
                "It is the room types on the booking page. Standard, sea view, accessible - each with its own "
                "price, size and cancellation policy, all bookable by name."
            ),
            context=(
                "The default class is quietly one of the most consequential settings in a cluster: every "
                "team that omits storageClassName inherits it, including its reclaim policy and its "
                "performance tier. If the default is a Delete-policy class on expensive fast disks, you get "
                "surprising bills and surprising data loss. Setting the default deliberately - and naming "
                "classes for their guarantees rather than their backend - is a small decision with a long "
                "tail."
            ),
            steps=[
                "Define it as a named storage offering plus the provisioner parameters behind it.",
                "List what it controls: provisioner, parameters, reclaim policy, expansion, binding mode.",
                "Explain the default class and why its choice matters more than people expect.",
                "Recommend naming by guarantee - fast-retain, standard-delete - so intent is visible in the "
                "manifest.",
            ],
            evidence=[
                "oc get sc -o wide",
                "oc get sc <class> -o jsonpath='{.reclaimPolicy} {.allowVolumeExpansion} {.volumeBindingMode}{\"\\n\"}'",
                "oc get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\\.kubernetes\\.io/is-default-class==\"true\")].metadata.name}{\"\\n\"}'",
            ],
            redflag=(
                "Do not leave the default StorageClass unexamined. Every team that forgets to specify one "
                "inherits whatever it happens to be."
            ),
            followup="What would you name your storage classes, and why does the name matter?",
        ),
        Q(
            q="What is a CSI driver?",
            level=FOUNDATION,
            answer=(
                "CSI is the standard interface between Kubernetes and a storage system, and a CSI driver "
                "implements it for one backend. It has two halves: a controller component that creates, "
                "deletes, attaches and snapshots volumes by talking to the storage API, and a node component "
                "running as a DaemonSet that stages and mounts volumes into pods. Splitting them that way is "
                "why some failures are cluster-wide and others affect only one node."
            ),
            analogy=(
                "The controller is the warehouse office that allocates a pallet; the node component is the "
                "forklift at the loading bay that actually brings it to your door."
            ),
            context=(
                "That split is the fastest diagnostic in storage. If new volumes are not being created at "
                "all, look at the controller and its credentials to the storage backend. If volumes provision "
                "fine but pods on one node cannot mount them, look at the node plugin on that node. Getting "
                "this right saves you from restarting the whole storage operator because of a single sick "
                "node."
            ),
            steps=[
                "Define CSI as the standard interface and the driver as the backend-specific implementation.",
                "Describe the controller and node split, and where each runs.",
                "Map symptoms to halves: provisioning failures versus mount failures.",
                "Check driver pod health and backend credentials before suspecting Kubernetes itself.",
            ],
            evidence=[
                "oc get csidrivers ; oc get csinode",
                "oc -n openshift-cluster-csi-drivers get pods -o wide",
                "oc get volumeattachment | grep <node>",
            ],
            redflag=(
                "Do not treat all storage failures as one category. Provisioning and mounting are different "
                "components with different logs."
            ),
            followup="Volumes provision but will not mount on one node. Which component and which log?",
        ),
        Q(
            q="Compare the access modes RWO, RWX and RWOP.",
            level=FOUNDATION,
            answer=(
                "ReadWriteOnce means the volume can be mounted read-write by pods on a single node - note "
                "node, not pod, so several pods on the same node can share it. ReadWriteMany allows "
                "read-write mounts from many nodes at once and requires a backend that supports shared "
                "access, typically file or object based rather than block. ReadWriteOncePod is the strict "
                "one: exactly one pod, cluster-wide, which is what you want for a database that must never "
                "have two writers."
            ),
            analogy=(
                "RWO is a meeting room booked by one department - several of their people can be inside. RWX "
                "is a shared kitchen. RWOP is a single-occupancy office with one key that exists."
            ),
            context=(
                "The subtlety that catches people is that RWO is per node, so it does not protect against two "
                "replicas of the same Deployment both writing, as long as they land on the same node. For "
                "data integrity that matters, RWOP is the correct mode. The other trap is assuming RWX is "
                "available: most block-based cloud storage cannot do it, so a workload designed around shared "
                "filesystems needs a different backend entirely, and that is an architecture decision rather "
                "than a manifest change."
            ),
            steps=[
                "Define each mode precisely, and stress that RWO is node-scoped, not pod-scoped.",
                "Say which backends can realistically offer RWX and which cannot.",
                "Recommend RWOP where a second writer would corrupt data.",
                "Check the driver's supported modes before designing around one.",
            ],
            evidence=[
                "oc get pvc <pvc> -o jsonpath='{.spec.accessModes}{\"\\n\"}'",
                "oc get pv <pv> -o jsonpath='{.spec.accessModes} {.spec.csi.driver}{\"\\n\"}'",
                "oc get csidriver <driver> -o yaml | head -30",
            ],
            redflag=(
                "Do not assume RWO prevents two pods from writing. Two pods on the same node can both mount "
                "it."
            ),
            followup="A database has two replicas writing to one RWO volume. How did that happen?",
        ),
        Q(
            q="What is volumeMode, and when would you use Block?",
            level=FOUNDATION,
            answer=(
                "volumeMode decides whether the volume is presented as a formatted filesystem mounted into "
                "the container, which is the default, or as a raw block device exposed at a device path. "
                "Filesystem is right for almost everything. Block is for workloads that manage their own "
                "storage layout and want to skip the filesystem layer - some databases and storage systems "
                "achieve better and more predictable performance that way."
            ),
            analogy=(
                "Filesystem mode is a furnished flat. Block mode is an empty shell handed over with the keys "
                "- more work, but you control every wall."
            ),
            context=(
                "The practical consequences of Block are worth stating because they surprise people: there is "
                "no filesystem for the platform to resize or inspect, standard file-level backup tools cannot "
                "read it, and the application is entirely responsible for what is on the device. So choosing "
                "Block is also choosing a different backup strategy - snapshots or application-native dumps "
                "rather than file-level copies."
            ),
            steps=[
                "Define the two modes and what the container actually sees in each.",
                "Give the legitimate reasons to pick Block - performance and applications that manage layout.",
                "State the consequences: no filesystem-level tooling, different backup approach, application "
                "owns the format.",
                "Confirm the driver supports Block before designing around it.",
            ],
            evidence=[
                "oc get pvc <pvc> -o jsonpath='{.spec.volumeMode}{\"\\n\"}'",
                "oc get pod <pod> -o jsonpath='{.spec.containers[0].volumeDevices}' | python3 -m json.tool",
                "oc get sc <class> -o yaml | grep -i volumemode",
            ],
            redflag=(
                "Do not choose Block for general workloads. You are giving up tooling for a benefit you "
                "probably cannot measure."
            ),
            followup="How would you back up a Block-mode volume?",
        ),
        Q(
            q="What does reclaimPolicy control?",
            level=FOUNDATION,
            answer=(
                "It decides what happens to the underlying storage when the claim is deleted. Delete removes "
                "the backend volume and the data with it. Retain keeps the volume and its data, leaving the "
                "PV in Released state for an administrator to handle deliberately. Dynamic provisioning "
                "usually defaults to Delete, which is convenient for ephemeral environments and dangerous for "
                "anything you would miss."
            ),
            analogy=(
                "It is what the storage company does when you cancel the unit. Delete means they empty it "
                "immediately; Retain means they keep the contents until someone signs for them."
            ),
            context=(
                "This is one of the few settings where the wrong choice loses data with no recovery path. The "
                "realistic scenario is a namespace cleanup script, or a GitOps prune, removing PVCs whose "
                "class is Delete - and the volumes are gone before anyone notices. Retain on production "
                "classes, plus a documented process for reclaiming Released volumes, converts that from a "
                "data-loss event into an administrative chore."
            ),
            steps=[
                "Define the two policies and what each does to the backend volume.",
                "State the typical default for dynamic provisioning and why that is risky in production.",
                "Recommend Retain for production data classes, with a documented reclaim process.",
                "Note that the policy is set on the class at provisioning time, and check it before you rely "
                "on it.",
            ],
            evidence=[
                "oc get pv -o custom-columns=NAME:.metadata.name,POLICY:.spec.persistentVolumeReclaimPolicy,CLAIM:.spec.claimRef.name",
                "oc get sc <class> -o jsonpath='{.reclaimPolicy}{\"\\n\"}'",
                "oc get pv --field-selector status.phase=Released",
            ],
            redflag=(
                "Do not use a Delete-policy class for production data because it is the default. That is how "
                "irreversible data loss happens quietly."
            ),
            followup="Someone deleted a production PVC an hour ago. What are your options?",
        ),
        Q(
            q="What problem does WaitForFirstConsumer solve?",
            level=INTERMEDIATE,
            answer=(
                "With immediate binding, the volume is provisioned as soon as the claim is created - before "
                "anyone knows where the pod will run. In a zoned cluster that volume might land in zone A "
                "while the scheduler wanted to place the pod in zone B, and the pod then cannot be scheduled "
                "at all. WaitForFirstConsumer delays provisioning until a pod is scheduled, so the volume is "
                "created in the right topology."
            ),
            analogy=(
                "It is waiting until you know which office someone will sit in before installing their desk. "
                "Otherwise you end up with a desk on the wrong floor and a person who cannot use it."
            ),
            context=(
                "The failure this prevents shows up as a FailedScheduling event mentioning volume node "
                "affinity conflict, and it is genuinely confusing the first time because the cluster has "
                "plenty of capacity - just not in the zone the volume was born in. The side effect to expect "
                "is that PVCs now sit Pending until a pod references them, which looks broken to someone who "
                "does not know the binding mode. Saying that out loud avoids a false alarm."
            ),
            steps=[
                "Explain the ordering problem between provisioning and scheduling in a zoned cluster.",
                "Describe how delayed binding fixes it by letting the scheduler decide first.",
                "Name the symptom it prevents: volume node affinity conflict.",
                "Warn that a Pending PVC with no consumer is expected behaviour, not a fault.",
            ],
            evidence=[
                "oc get sc <class> -o jsonpath='{.volumeBindingMode}{\"\\n\"}'",
                "oc describe pvc <pvc> | grep -i 'waiting for first consumer'",
                "oc get pv <pv> -o jsonpath='{.spec.nodeAffinity}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not use immediate binding on a multi-zone cluster. You are creating scheduling deadlocks "
                "for no benefit."
            ),
            followup="A pod is Pending with 'volume node affinity conflict'. Explain the sequence that caused it.",
        ),
        Q(
            q="How do CSI volume snapshots work, and are they a backup?",
            level=INTERMEDIATE,
            answer=(
                "A VolumeSnapshot asks the CSI driver to take a point-in-time snapshot of a volume, governed "
                "by a VolumeSnapshotClass, and you can then create a new PVC from it. They are fast and cheap "
                "because they are usually copy-on-write on the same storage system. That is exactly why they "
                "are not a backup: if the array fails or is destroyed, the snapshots go with it, and a "
                "crash-consistent snapshot of a running database may not restore cleanly."
            ),
            analogy=(
                "A snapshot is a bookmark in the book you are holding. A backup is a photocopy stored in "
                "another building. Losing the book loses every bookmark in it."
            ),
            context=(
                "Snapshots are excellent for what they actually are: a fast rollback before a risky change, a "
                "way to clone production data into a test namespace, the storage half of a backup tool's "
                "workflow. The interview point is being explicit about the two independent limitations - same "
                "failure domain, and crash consistency - and then describing how you get application "
                "consistency by quiescing the application or using its native dump before snapshotting."
            ),
            steps=[
                "Describe the objects: VolumeSnapshotClass, VolumeSnapshot, VolumeSnapshotContent, and "
                "restore by creating a PVC from the snapshot.",
                "State the two limits clearly: same failure domain, and crash-consistent by default.",
                "Explain how to reach application consistency - quiesce, hook, or native dump.",
                "Give the legitimate uses and pair them with a real off-array backup for durability.",
            ],
            evidence=[
                "oc get volumesnapshotclass ; oc get volumesnapshot -n <ns>",
                "oc get volumesnapshot <snap> -o jsonpath='{.status.readyToUse}{\"\\n\"}'",
                "oc get volumesnapshotcontent | head",
            ],
            redflag=(
                "Do not call snapshots a backup strategy. It is the answer that ends senior interviews early."
            ),
            followup="How would you take an application-consistent snapshot of a running database?",
        ),
        Q(
            q="How do you expand a persistent volume?",
            level=INTERMEDIATE,
            answer=(
                "If the StorageClass allows expansion, you edit the claim's requested size upward and the CSI "
                "driver grows the backend volume. Whether the filesystem is grown online or needs the pod to "
                "restart depends on the driver. Shrinking is not supported at all - the only route to a "
                "smaller volume is to create a new one and copy the data. So the operational rule is to plan "
                "for growth and monitor usage rather than treating expansion as a routine dial."
            ),
            analogy=(
                "You can knock through into the next room, but you cannot un-knock it. Extensions are one "
                "way."
            ),
            context=(
                "Expansion becomes an incident when nobody is watching usage, because a full volume usually "
                "means the application has already failed - a database that cannot write, or a log volume "
                "that filled and took the pod with it. The right posture is alerting on percentage used with "
                "enough lead time to expand calmly, plus knowing in advance whether your driver needs a "
                "restart, because that changes expansion from a background task into a change window."
            ),
            steps=[
                "Verify allowVolumeExpansion on the class before promising anything.",
                "Patch the claim's requested size and watch the PVC conditions for resize progress.",
                "Confirm whether the filesystem resize is online or requires a pod restart for your driver.",
                "Alert on volume usage with enough headroom that expansion is planned, not emergency work.",
            ],
            evidence=[
                "oc get sc <class> -o jsonpath='{.allowVolumeExpansion}{\"\\n\"}'",
                "oc patch pvc <pvc> -p '{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"200Gi\"}}}}'",
                "oc get pvc <pvc> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not promise you can shrink a volume later. You cannot, and someone will plan around your "
                "answer."
            ),
            followup="A volume is 95% full and expansion needs a restart. How do you sequence it?",
        ),
        Q(
            q="When is ephemeral or node-local storage the right choice?",
            level=INTERMEDIATE,
            answer=(
                "emptyDir is right for scratch space that dies with the pod - caches, temporary files, a "
                "shared directory between containers in the same pod. Local persistent volumes are right when "
                "the workload needs the performance of a directly attached disk and handles its own "
                "replication, such as a distributed database. hostPath is almost never right for "
                "applications; it is for node-level system components and it breaks isolation."
            ),
            analogy=(
                "emptyDir is a notepad on the desk that gets binned each evening. A local volume is a safe "
                "bolted to that specific floor - fast to reach, useless if you move offices."
            ),
            context=(
                "The trade-off with local volumes is that the data is pinned to one node, so the pod is "
                "pinned too. Losing that node means losing that replica's data, which is fine for a "
                "distributed database that replicates across nodes and unacceptable for a single-instance "
                "one. It also blocks the cluster autoscaler from removing the node and complicates upgrades, "
                "because draining is no longer free."
            ),
            steps=[
                "Distinguish emptyDir, local persistent volumes and hostPath by purpose and lifetime.",
                "State the pinning consequence of local storage for scheduling, drains and autoscaling.",
                "Require application-level replication before accepting local storage for stateful work.",
                "Set size limits on emptyDir so a runaway process cannot fill the node and trigger "
                "DiskPressure.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.volumes}' | python3 -m json.tool",
                "oc get pv -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]",
                "oc describe node <node> | grep -i diskpressure",
            ],
            redflag=(
                "Do not use hostPath for application storage. It bypasses isolation and ties the workload to "
                "a machine in a way nothing else will respect."
            ),
            followup="A local-volume workload blocks node drain during upgrades. What do you do?",
        ),
        Q(
            q="A PVC has been Pending for twenty minutes. Walk me through it.",
            level=SENIOR,
            answer=(
                "I read the PVC's events first, because they usually name the stage that is stuck. Then I "
                "work the chain: does the requested StorageClass exist and is it spelled correctly, is the "
                "binding mode WaitForFirstConsumer with no pod yet - which is normal - is the CSI controller "
                "healthy and authenticated to the backend, does the backend have capacity and quota, and does "
                "the requested access mode exist on this driver at all."
            ),
            analogy=(
                "It is a delivery that has not arrived. You check the order was placed, the address was "
                "valid, the warehouse has stock, and the courier is actually operating - in that order."
            ),
            context=(
                "The two answers that surprise people are the harmless one and the invisible one. Harmless: "
                "with delayed binding, a claim with no consuming pod is supposed to stay Pending, so the "
                "\"problem\" is a missing or unschedulable pod. Invisible: the backend is out of capacity or "
                "the driver's credentials expired, and the only place that is stated is the CSI controller "
                "log, not the Kubernetes objects."
            ),
            steps=[
                "Read PVC events and conditions and take the message literally.",
                "Confirm the StorageClass name resolves, and check the binding mode before assuming failure.",
                "Check CSI controller pod health and its logs for backend errors, quota or authentication.",
                "Validate the requested access mode and size against what the driver and backend actually "
                "support.",
            ],
            evidence=[
                "oc describe pvc <pvc> | sed -n '/Events/,$p'",
                "oc -n openshift-cluster-csi-drivers logs deploy/<driver>-controller -c csi-provisioner --tail=100",
                "oc get sc ; oc get pvc <pvc> -o jsonpath='{.spec.storageClassName}{\"\\n\"}'",
            ],
            redflag=(
                "Do not delete and recreate the PVC as a first move. If provisioning succeeded partially you "
                "may orphan backend capacity nobody is tracking."
            ),
            followup="The events say nothing at all. Where do you look next?",
        ),
        Q(
            q="A volume is stuck attached to a failed node. What do you do?",
            level=SENIOR,
            answer=(
                "This is a safety problem before it is an availability problem. The volume is attached to a "
                "node that is unreachable, and the replacement pod cannot start until it is detached. The "
                "critical question is whether the old node is genuinely dead or merely unreachable - if it is "
                "alive and still writing, force-detaching an RWO volume and mounting it elsewhere risks "
                "corruption. So I confirm the node is fenced or powered off, then let the controller detach, "
                "and force it only with that confirmation."
            ),
            analogy=(
                "It is a safe deposit box still signed out to someone you cannot reach. You do not drill it "
                "open until you are certain they are not in the vault."
            ),
            context=(
                "This is exactly what MachineHealthCheck automates when it is configured with proper "
                "remediation: an unhealthy node is deleted and, on infrastructure that supports it, the "
                "machine is destroyed, which guarantees it is not writing. Without that, a network partition "
                "produces a node that looks dead from the cluster and is happily running - the classic "
                "split-brain that turns an outage into data corruption."
            ),
            steps=[
                "Establish whether the node is dead or partitioned - those need different actions.",
                "Confirm fencing: the machine is deleted, powered off, or otherwise proven not to be writing.",
                "Let the attach-detach controller complete the detach; delete the VolumeAttachment only after "
                "fencing is confirmed.",
                "Verify the pod starts and the filesystem is clean, then fix the underlying cause and "
                "consider MachineHealthCheck for automated fencing.",
            ],
            evidence=[
                "oc get volumeattachment | grep <node>",
                "oc get node <node> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get machine -A -o wide | grep <node>",
            ],
            redflag=(
                "Do not force-delete the VolumeAttachment to speed things up. If the old node is alive you "
                "have just created two writers."
            ),
            followup="How does MachineHealthCheck change this scenario, and what does it require?",
        ),
        Q(
            q="How do you achieve application-consistent backup?",
            level=SENIOR,
            answer=(
                "Crash-consistent means the copy looks like the power was pulled; the application may recover "
                "or may not. Application-consistent means the application was told to quiesce - flush "
                "buffers, freeze writes - at the moment of the copy. In practice I use the backup tool's pre "
                "and post hooks to run the application's own quiesce or dump command around the snapshot, and "
                "then I prove it by restoring into a scratch namespace and starting the application."
            ),
            analogy=(
                "Crash-consistent is photographing a kitchen mid-service. Application-consistent is asking "
                "the chef to put the knives down for three seconds first."
            ),
            context=(
                "The proof step is the part that separates a real answer from a plausible one. Plenty of "
                "teams have hooks configured that silently fail - the command name changed, the container "
                "does not have the binary, the hook timed out - and nobody notices until a restore is needed. "
                "A scheduled restore test into a scratch namespace, with the application actually started and "
                "queried, is the only evidence that counts."
            ),
            steps=[
                "Define the difference and say which one your current setup actually produces.",
                "Use pre and post hooks to quiesce the application around the snapshot or copy.",
                "Prefer the application's native backup mechanism where one exists, and back that up.",
                "Restore into a scratch namespace on a schedule, start the application, and record the "
                "result as evidence.",
            ],
            evidence=[
                "oc get backup,restore -n openshift-adp",
                "oc get backup <name> -n openshift-adp -o jsonpath='{.status.phase} {.status.errors}{\"\\n\"}'",
                "Documented restore test: date, dataset, measured restore time, verification query",
            ],
            redflag=(
                "Do not claim backups work because the job reports success. Until you have restored one, you "
                "have a backup job, not a backup."
            ),
            followup="Your restore test fails on one of five applications. What do you do about the other four?",
        ),
        Q(
            q="How do you troubleshoot storage performance complaints?",
            level=SENIOR,
            answer=(
                "I turn the complaint into numbers before doing anything else: which operation is slow, what "
                "latency is being observed, at what IOPS and block size, and compared with what baseline. "
                "Then I separate the layers - application, filesystem, node, and backend - by measuring at "
                "each. Very often the limit is the class of storage that was requested rather than a fault, "
                "and that is a capacity conversation, not a troubleshooting one."
            ),
            analogy=(
                "\"The tap is slow\" could be the tap, the pipe, or the water pressure into the street. You "
                "measure at each point rather than replacing the tap and hoping."
            ),
            context=(
                "The most common real causes are noisy neighbours on shared backend capacity, a workload "
                "using a general-purpose class when it needs a provisioned-IOPS one, and small random IO "
                "against storage optimised for sequential throughput. Node-level contention matters too - a "
                "log-heavy pod saturating the same path. Having a baseline from cluster build makes this a "
                "ten-minute comparison instead of a week of theories."
            ),
            steps=[
                "Quantify the complaint: operation, latency, IOPS, block size, and when it started.",
                "Measure at each layer - inside the pod, on the node, and from the backend's own metrics.",
                "Compare against the class's expected performance and your recorded baseline.",
                "Decide between a fix, a class change, or a capacity purchase, and record the new expected "
                "numbers.",
            ],
            evidence=[
                "oc exec <pod> -- dd if=/dev/zero of=/data/test bs=1M count=1024 oflag=direct",
                "node_disk_io_time_seconds_total ; node_disk_read_time_seconds_total by device",
                "Backend array metrics: queue depth, latency, throughput for the volume in question",
            ],
            redflag=(
                "Do not accept \"storage is slow\" without numbers. Half of these tickets end with the "
                "workload being on the class it asked for."
            ),
            followup="The backend reports 2ms latency and the application sees 40ms. Where is the time going?",
        ),
        Q(
            q="How would you design the storage class catalogue for a platform?",
            level=ARCHITECT,
            answer=(
                "I would offer a small number of classes that describe guarantees rather than products - "
                "something like standard, fast, shared and retained-critical - each with a documented "
                "performance envelope, reclaim policy, expansion support, snapshot support and cost. The "
                "default would be the safe, general-purpose one. Anything outside the catalogue needs a "
                "conversation, because every extra class is another thing to test, monitor and migrate later."
            ),
            analogy=(
                "It is a menu, not a warehouse inventory. Four dishes people understand beat forty they have "
                "to ask about."
            ),
            context=(
                "A small catalogue is an operational decision as much as a user-experience one. Each class "
                "carries a testing burden - expansion, snapshot, restore, failure behaviour - and a migration "
                "burden when the backend changes. Teams also make better choices when the names describe "
                "guarantees, because a developer can reason about \"fast-retained\" without knowing anything "
                "about the array underneath. Publishing cost per gigabyte alongside is what actually changes "
                "behaviour."
            ),
            steps=[
                "Gather the real requirements: latency, throughput, sharing, durability, retention, cost "
                "sensitivity.",
                "Define a small set of classes by guarantee, and document the envelope and cost of each.",
                "Set a safe default and make retention policy explicit in the name where it matters.",
                "Test each class for expansion, snapshot and restore before publishing it, and review the "
                "catalogue as usage data arrives.",
            ],
            evidence=[
                "oc get sc -o wide ; usage and cost per class per namespace",
                "Documented performance envelope and test results per class",
                "oc get pvc -A -o custom-columns=NS:.metadata.namespace,CLASS:.spec.storageClassName,SIZE:.spec.resources.requests.storage | sort -k2",
            ],
            redflag=(
                "Do not expose one class per backend feature. You will end up supporting a dozen "
                "combinations nobody chose deliberately."
            ),
            followup="A team wants a class with guaranteed IOPS. What do you need to know before saying yes?",
        ),
        Q(
            q="How would you plan a migration from one storage backend to another?",
            level=ARCHITECT,
            answer=(
                "I treat it as a data migration project rather than a storage change. First an inventory - "
                "every claim, its size, class, access mode, owning application and criticality. Then a "
                "per-application method: snapshot-and-restore, a backup tool's migration workflow, or "
                "application-native replication for databases, which is usually the safest. Then a pilot on "
                "something low-risk, measured cutover windows, and a documented rollback while the old "
                "backend still holds the data."
            ),
            analogy=(
                "It is moving house one room at a time, with the old keys still in your pocket until the "
                "last box is unpacked and checked."
            ),
            context=(
                "The two things that derail these projects are discovered late: applications that cannot "
                "tolerate the downtime the chosen method requires, and access modes that do not exist on the "
                "new backend. Both are found in the inventory phase if you actually do it. Keeping the old "
                "backend live until every application has been verified is what makes rollback real rather "
                "than theoretical, and that has a cost you should surface early."
            ),
            steps=[
                "Inventory every volume with owner, size, class, access mode, criticality and downtime "
                "tolerance.",
                "Choose a migration method per application, preferring native replication for databases.",
                "Pilot on low-risk workloads, measure the actual cutover time, and refine the runbook.",
                "Migrate in waves with verification after each, keeping the old backend as rollback until "
                "sign-off.",
            ],
            evidence=[
                "oc get pvc -A -o wide   # full inventory with class and size",
                "Per-application migration runbook with measured cutover and verification steps",
                "Post-migration verification: application checks, performance comparison against baseline",
            ],
            redflag=(
                "Do not decommission the old backend before every application has been verified. Rollback "
                "that depends on data you deleted is not rollback."
            ),
            followup="One application cannot tolerate any downtime. What is your approach for that one?",
        ),
    ],
)
