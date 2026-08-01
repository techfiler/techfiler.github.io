"""Part 1 - Senior Linux administration for platform and SRE roles."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=1,
    title="Senior Linux administration",
    subtitle="systemd, storage, SELinux, and the failure modes that show up before Kubernetes ever gets blamed",
    intro=(
        "Platform interviews still open on Linux because every abstraction leaks. A pod that will not mount a volume "
        "is often an SELinux label problem. A node that goes NotReady is frequently disk, OOM, or a systemd unit in "
        "a restart loop. Senior candidates are expected to work from symptoms to evidence without guessing — "
        "journalctl before reboot, ss before tcpdump, and an AVC denial before chmod 777. This part covers the "
        "administration depth that separates someone who knows kubectl from someone who can own the node underneath."
    ),
    infographics=["container_stack"],
    questions=[
        Q(
            q="What are the main Linux process states, and which ones should worry you in production?",
            level=FOUNDATION,
            answer=(
                "Running means on CPU or runnable. Sleeping in an interruptible wait is normal for I/O. Uninterruptible "
                "sleep — state D — means the process is stuck in a kernel call, usually blocked disk or NFS, and cannot "
                "be killed until the kernel returns. Zombie means the process exited but the parent has not reaped it; "
                "one zombie is harmless, thousands mean a broken parent. Stopped is a job-control pause. In interviews "
                "and incidents, D-state processes and zombie storms are the ones that escalate because they do not "
                "respond to SIGKILL and they often point at storage or a buggy supervisor."
            ),
            analogy=(
                "Think of process states as people in a queue. Running is at the counter. Sleeping is waiting politely "
                "and can leave if called. D-state is glued to the counter mid-transaction — security cannot move them. "
                "Zombies are receipts nobody filed away."
            ),
            context=(
                "On OpenShift nodes you see D-state during hung NFS or a failing SAN LUN; kubelet and container "
                "processes pile up and the node looks busy while nothing completes. Zombie leaks from a wrapper script "
                "that never wait on children can exhaust the PID table even when free memory looks fine. Interviewers "
                "use this question to see whether you reach for kill -9 or read /proc and the parent chain."
            ),
            steps=[
                "Name the states interviewers expect: R, S, D, Z, T — and what each means in one line.",
                "Highlight D-state as unkillable and almost always storage or kernel I/O.",
                "Explain zombies as a parent bug, not a child problem — find who is not reaping.",
                "Close with the operational move: ps, /proc/<pid>/stack or wchan, and fix storage or the parent.",
            ],
            evidence=[
                "ps aux | awk '$8 ~ /D/ {print}'",
                "cat /proc/<pid>/wchan ; cat /proc/<pid>/stack",
                "ps -eo pid,ppid,stat,cmd | awk '$3 ~ /Z/' | head -20",
            ],
            redflag=(
                "Do not say you would SIGKILL a D-state process. It does not work and tells the interviewer you "
                "have not lived through a storage outage."
            ),
            followup="You see fifty D-state processes on one node. What do you check before draining the node?",
        ),
        Q(
            q="How do you use journalctl to troubleshoot a failed systemd service?",
            level=FOUNDATION,
            answer=(
                "journalctl is the unified log for systemd and anything that logs to the journal. I start with the unit "
                "since boot — journalctl -u nginx.service -b — then widen the window if needed. -f follows live, "
                "--since narrows time, -p err filters priority, and -o json-pretty helps when I need structured fields. "
                "If the service fails on start I also check systemctl status for the exit code and the last few log lines "
                "inline. On RHEL the journal persists under /var/log/journal unless someone disabled it, so reboot does "
                "not automatically erase the evidence you need for the interview story."
            ),
            analogy=(
                "journalctl is the building's CCTV system with timestamps and camera IDs. systemctl status is the "
                "alarm panel summary; the journal is where you actually see who opened the door."
            ),
            context=(
                "This comes up constantly for kubelet, crio, chronyd, and node-exporter on platform nodes. Candidates "
                "who only tail /var/log/messages miss stdout from Type=simple units and lose the ordering systemd "
                "already captured. In a 2025/2026 SRE loop, correlating journal timestamps with Prometheus alerts is "
                "the expected workflow — not grepping random flat files."
            ),
            steps=[
                "State that systemd aggregates service, kernel, and structured logs in one place.",
                "Give the first command: journalctl -u <unit> -b and systemctl status <unit>.",
                "Add filters: --since, -p err, -n, and -o json-pretty for automation.",
                "Mention persistence and rotation — verify Storage= and not assuming logs vanish on restart.",
            ],
            evidence=[
                "systemctl status kubelet --no-pager -l",
                "journalctl -u kubelet -b --since '30 min ago' -p err --no-pager",
                "journalctl -u crio -n 100 -o json-pretty | head -40",
            ],
            redflag=(
                "Do not say you always edit rsyslog.conf first. On modern RHEL, systemd journal is the primary "
                "source and rsyslog is optional forwarding."
            ),
            followup="Logs show the service started cleanly but clients still fail. Where do you look next?",
        ),
        Q(
            q="What is systemd responsible for, and how do you manage a service day to day?",
            level=FOUNDATION,
            answer=(
                "systemd is PID 1: it starts the boot target, brings up units in dependency order, supervises daemons, "
                "mounts filesystems, and applies cgroups to service processes. A unit file describes what to run — "
                "Service section — when — Install and WantedBy — and how to restart. Day to day I use systemctl start, "
                "stop, enable, and daemon-reload after unit edits. status shows Active state and the last logs; "
                "show tells me the effective unit after drop-ins. The interview point is that systemd is not just "
                "init — it is the process supervisor and dependency graph the whole node relies on."
            ),
            analogy=(
                "systemd is an air-traffic controller, not a single runway worker. It decides which planes take off "
                "in what order, watches them in flight, and clears a gate when one crashes."
            ),
            context=(
                "On RHCOS many changes go through MachineConfig rather than hand-edited units, but debug pods still "
                "use systemctl and journalctl on the host. Platform candidates confuse systemd with Kubernetes "
                "controllers; the parallel is real — desired state in unit files, observed state in systemctl — but "
                "the failure modes are local: a bad After= dependency, a missing EnvironmentFile, Restart= always "
                "masking a config error."
            ),
            steps=[
                "Define systemd as PID 1 plus unit supervision, dependencies, mounts, and cgroups.",
                "Explain unit file sections: Unit, Service, Install — and drop-in overrides.",
                "List daily commands: enable, start, status, daemon-reload, cat/show.",
                "Connect to troubleshooting: failed state, restart loops, and ordering with After/Wants/Requires.",
            ],
            evidence=[
                "systemctl list-units --failed --no-pager",
                "systemctl cat kubelet.service",
                "systemctl show kubelet -p ActiveState,SubState,RestartCount,FragmentPath",
            ],
            redflag=(
                "Do not describe systemd as \"just replacing init scripts\". Miss the dependency graph and "
                "supervision story and senior follow-ups will expose it immediately."
            ),
            followup="A unit is in a restart loop with exit code 1. How do you stop the loop without losing logs?",
        ),
        Q(
            q="How do you read and fix an SELinux AVC denial on RHEL?",
            level=INTERMEDIATE,
            answer=(
                "An AVC denial means SELinux blocked an action that UNIX permissions allowed — different domain, "
                "wrong file context, or a capability the policy denies. I reproduce or wait for the failure, then "
                "search audit logs: ausearch -m avc -ts recent or journalctl with SETroubleshoot hints. The denial "
                "names source context, target context, object class, and permission. The fix hierarchy is: apply the "
                "correct file context with semanage fcontext plus restorecon, use a supported boolean if it is a "
                "known pattern, or adjust the service domain through policy modules — never setenforce 0 in "
                "production. On OpenShift, pod MCS labels and volume contexts are the same problem wearing a "
                "different hat."
            ),
            analogy=(
                "UNIX permissions are a door lock. SELinux is the badge reader next to it. You can have the key and "
                "still be denied because your badge is not cleared for that room."
            ),
            context=(
                "This is still a top-ten real interview question for RHEL and OpenShift roles in 2025/2026. Classic "
                "cases: a custom app writing to /var/log, NFS mounts without the right context, a backup agent reading "
                "container volumes. Candidates who reach for chmod 777 fail the security bar; candidates who grep AVC "
                "and fix labels pass."
            ),
            steps=[
                "Define AVC as mandatory access control denying despite chmod being open.",
                "Collect evidence: ausearch, sealert, or journalctl AVC lines with timestamp correlation.",
                "Read the denial fields: scontext, tcontext, tclass, permission.",
                "Apply the fix ladder: fcontext/restorecon, boolean, policy module — and verify with a test run.",
            ],
            evidence=[
                "ausearch -m avc -ts recent | tail -20",
                "sealert -a /var/log/audit/audit.log 2>/dev/null | less",
                "ls -Z /path/to/file ; semanage fcontext -l | grep myapp",
            ],
            redflag=(
                "Do not recommend setenforce 0 or disabling SELinux as a normal fix. That is an instant fail in "
                "regulated and platform interviews."
            ),
            followup="The denial mentions container_file_t but the app needs a host log directory. What are your options?",
        ),
        Q(
            q="How does the Linux OOM killer work, and how do you tell it from a cgroup memory limit?",
            level=INTERMEDIATE,
            answer=(
                "When the kernel cannot satisfy a memory allocation and reclaim is exhausted, the OOM killer selects "
                "a process using an oom_score derived from RSS, age, and tunables like oom_score_adj. Containers and "
                "systemd services often set oom_score_adj so critical daemons survive longer. Exit code 137 in a "
                "container usually means cgroup memory.max was hit — the killer ran inside that cgroup. Host-level OOM "
                "shows in dmesg as \"Out of memory: Killed process\" and can take down sshd or kubelet if the node is "
                "truly exhausted. The interview skill is splitting those two stories with evidence before blaming the "
                "application."
            ),
            analogy=(
                "Host OOM is the building manager evicting someone when the whole block is out of space. Cgroup OOM is "
                "your flat's smart meter cutting power because you exceeded your prepaid cap — the building still "
                "has electricity."
            ),
            context=(
                "Platform engineers see both daily. A pod OOMKilled with node memory free is almost always limits. "
                "A node flapping NotReady with ssh hangs is often host OOM or memory pressure evictions. In 2026 "
                "interviews expect a follow-up on overcommit, swap absence on RHCOS, and why requests matter for "
                "scheduling but limits enforce death."
            ),
            steps=[
                "Explain the trigger: allocation failure after reclaim, then oom_score selection.",
                "Differentiate cgroup limit enforcement from global host OOM via dmesg versus pod status.",
                "Mention oom_score_adj — kubelet and systemd adjust who dies first.",
                "Land on mitigation: right-size limits, fix leaks, protect critical daemons, alert on memory pressure.",
            ],
            evidence=[
                "dmesg -T | grep -i 'out of memory'",
                "oc describe pod <pod> | grep -A5 'Last State'   # or crictl inspect for OOM",
                "cat /proc/<pid>/oom_score_adj ; systemctl show kubelet -p OOMScoreAdjust",
            ],
            redflag=(
                "Do not say \"Kubernetes killed the pod for using too much memory\" without mentioning the kernel "
                "OOM killer and cgroup limits — the distinction is the whole question."
            ),
            followup="Node memory looks 40% free but the OOM killer still ran. What mechanisms could explain that?",
        ),
        Q(
            q="df reports 100% full but du shows plenty of free space. How do you troubleshoot?",
            level=INTERMEDIATE,
            answer=(
                "I work through the usual suspects in order. Deleted-but-open files: lsof +L1 or lsof | grep deleted — "
                "space returns only when the process closes the descriptor. Inodes exhausted: df -i shows 100% while "
                "blocks remain; find tiny files or runaway socket files. Reserved blocks on ext4: tune2fs -l shows "
                "five percent root-only reserve — df counts it as used. A mount overlay: df on the wrong mountpoint "
                "hides that /var/log is on a full partition. Sparse or deleted snapshots can confuse if you mix LVM "
                "and bind mounts. Each hypothesis has a thirty-second test; the interview win is a ordered method, "
                "not guessing reboot."
            ),
            analogy=(
                "It is like a warehouse that looks empty on paper but every pallet is still booked because someone "
                "forgot to close the shipping manifest — the space exists but the ledger says full."
            ),
            context=(
                "This is a classic senior Linux phone-screen question and a real kubelet failure mode: /var fills "
                "because container logs were deleted but still held open by a long-running process, image layers "
                "cannot unpack, and the node enters DiskPressure. Candidates who only run du on / and give up lose "
                "credibility fast."
            ),
            steps=[
                "Confirm which filesystem with df -h and df -i on the exact mountpoint.",
                "Check deleted open files with lsof +L1 sorted by size.",
                "Inspect reserved blocks and mount topology with tune2fs -l and findmnt.",
                "Fix the holder process or inode consumer, then verify with df before closing the incident.",
            ],
            evidence=[
                "df -h /var ; df -i /var",
                "lsof +L1 2>/dev/null | sort -k7 -n | tail -20",
                "findmnt /var ; tune2fs -l /dev/sda2 | grep -i block",
            ],
            redflag=(
                "Do not answer \"just reboot the server\" as step one. You lose the chance to name the process "
                "holding deleted files and you destroy evidence."
            ),
            followup="lsof shows a multi-gigabyte deleted log held by journald. What safe cleanup path do you take?",
        ),
        Q(
            q="How do you debug basic network connectivity from a Linux host?",
            level=INTERMEDIATE,
            answer=(
                "I split \"cannot connect\" into layers. DNS: getent hosts or dig shows name resolution. Routing: "
                "ip route get tells me which interface and source IP the kernel would use. Local listen state: ss "
                "-tlnp shows whether anything is bound on the port. Path and firewall: ping or tracepath for L3, "
                "curl -v for application handshake, tcpdump on the interface for silent drops. \"Connection refused\" "
                "means I reached a host that actively rejected the port — nothing listening or firewall REJECT. "
                "\"Timed out\" means packets vanished — wrong route, ACL, or asymmetric return path. That "
                "distinction is what interviewers listen for."
            ),
            analogy=(
                "Debugging the network is like delivering a letter: first check the address book, then the route on "
                "the map, then whether anyone is home to sign for it, then whether the post office threw it away "
                "without telling you."
            ),
            context=(
                "SRE interviews use this to filter out candidates who only know kubectl exec curl. On nodes you "
                "debug CNI, DNS CoreDNS upstream, MTU mismatches on overlay networks, and conntrack exhaustion — "
                "all of which start with ip, ss, and tcpdump on the host. In 2025/2026 expect IPv6 and nftables "
                "to appear in follow-ups."
            ),
            steps=[
                "Clarify the failure string: refused versus timeout versus name resolution failure.",
                "Test DNS and routing before the application — getent, ip route get.",
                "Verify local sockets with ss -tlnp and remote reachability with curl -v or nc -vz.",
                "Capture packets with tcpdump when the syscalls lie — counters increment but clients hang.",
            ],
            evidence=[
                "getent hosts api.example.com ; dig +short api.example.com",
                "ip route get 10.0.0.5 ; ss -tlnp | grep :8443",
                "curl -v --connect-timeout 3 https://api.example.com:8443/health",
            ],
            redflag=(
                "Do not skip straight to tcpdump without stating what refused versus timeout implies. That "
                "misdiagnosis wastes minutes in real incidents."
            ),
            followup="curl times out but tcpdump shows SYN leaving and SYN-ACK returning. What do you check next?",
        ),
        Q(
            q="Explain LVM building blocks and how you extend a filesystem online.",
            level=INTERMEDIATE,
            answer=(
                "Physical volumes are disk partitions or LUNs. Volume groups pool PV capacity. Logical volumes are "
                "sliced from the VG and presented as block devices like /dev/mapper/rhel-root. To grow online I extend "
                "the LV with lvextend -r if the filesystem supports it, or lvextend then xfs_growfs or resize2fs "
                "separately. I always verify pvdisplay, vgdisplay, and lvdisplay before typing — extending the wrong "
                "LV on a shared VG is a resume event. Snapshots and thin pools are advanced topics but the interview "
                "baseline is PV/VG/LV vocabulary and a safe grow workflow."
            ),
            analogy=(
                "LVM is a flexible wallet system: PVs are cash in your pocket, the VG is the wallet, LVs are "
                "labelled envelopes inside it — you can move space between envelopes without buying a new wallet."
            ),
            context=(
                "Bare-metal and VM platform roles still manage root and data volumes outside Kubernetes. Satellite "
                "hosts, registry nodes, and database VMs on the cluster edge all hit \"disk eighty-five percent\" "
                "tickets. Interviewers want to hear that XFS grow is online on RHEL, that you check VG free space "
                "first, and that you update kickstart or Terraform after the manual fix so the next rebuild matches."
            ),
            steps=[
                "Define PV, VG, LV and how device mapper names map to mounts.",
                "Check free space: vgs, lvs, df on the mountpoint.",
                "Extend: lvextend -L +50G /dev/vg/lv then xfs_growfs or resize2fs.",
                "Verify df, update infrastructure-as-code or kickstart so the change is not a one-off snowflake.",
            ],
            evidence=[
                "pvs ; vgs ; lvs -o lv_name,vg_name,lv_size,data_percent",
                "df -h /var/lib ; lsblk -f",
                "lvextend -r -L +20G /dev/rhel/var && xfs_growfs /dev/rhel/var",
            ],
            redflag=(
                "Do not run lvextend without confirming filesystem type and VG free space. Growing is easy; "
                "shrinking XFS is not, and interviewers will ask."
            ),
            followup="The VG is out of free extents but the SAN LUN has unused space. What are your next steps?",
        ),
        Q(
            q="How do you write a production-grade systemd unit with dependencies and restart policy?",
            level=SENIOR,
            answer=(
                "I start from a vendor unit or systemd-analyze cat systemd-example.service and override with drop-ins "
                "under /etc/systemd/system/foo.service.d/ rather than editing vendor files. After= and Wants= express "
                "ordering versus hard requirement — Requires= fails the unit if the dependency fails. Type=notify "
                "for daemons that signal readiness; Restart=on-failure with RestartSec= avoids tight loops. "
                "LimitNOFILE= and MemoryMax= belong in the unit for services I own. ExecStartPre= runs validation "
                "before the main process. I always systemctl daemon-reload, systemctl start, then systemd-analyze "
                "verify and systemd-analyze critical-chain to prove ordering. On fleet-managed nodes the same content "
                "becomes a MachineConfig fragment."
            ),
            analogy=(
                "A unit file is a recipe card with prep steps, oven temperature, and what must finish before this "
                "dish goes in — skip the prep line and the whole kitchen backs up."
            ),
            context=(
                "Senior platform roles wrap agents, exporters, and bootstrap scripts in systemd. The interview tests "
                "whether you understand that Restart=always hides misconfiguration, that ordering races cause "
                "\"works on reboot sometimes\", and that Type=simple marks started before the daemon is actually ready."
            ),
            steps=[
                "Prefer drop-in overrides; list Unit, Service, Install sections you actually set.",
                "Explain After versus Requires — ordering versus hard dependency.",
                "Choose Type and Restart policy deliberately; add resource limits where needed.",
                "Validate with daemon-reload, critical-chain, journal on failure, and document in IaC or MachineConfig.",
            ],
            evidence=[
                "systemd-analyze verify /etc/systemd/system/myapp.service",
                "systemd-analyze critical-chain myapp.service",
                "systemctl cat myapp.service ; journalctl -u myapp -b --no-pager",
            ],
            redflag=(
                "Do not set Restart=always on a service that fails its config check every time — you get a "
                "log flood and a missed root cause."
            ),
            followup="The service must start only after an NFS mount and a specific TLS file exist. How do you model that?",
        ),
        Q(
            q="How do you diagnose and fix file descriptor exhaustion?",
            level=SENIOR,
            answer=(
                "Symptoms include \"too many open files\", accept failures on busy sockets, and mysterious 502s under "
                "load. I compare the process soft limit from /proc/<pid>/limits with how many descriptors it holds — "
                "ls /proc/<pid>/fd | wc -l. System-wide, fs.file-nr in /proc/sys/fs/file-nr shows allocated versus "
                "maximum. lsof -p or lsof -c names the leak — often log pipelines, database pools, or forgotten "
                "sockets in long-lived workers. Fix is raise LimitNOFILE in systemd or /etc/security/limits.d, tune "
                "fs.file-max at the kernel, and fix the application leak. For Kubernetes nodes, kubelet and CRI-O "
                "defaults matter when pod density is high."
            ),
            analogy=(
                "File descriptors are coat-check tickets. You can enlarge the cloakroom — ulimit — but if one guest "
                "hoards tickets and never returns them, expanding the room only delays the same collapse."
            ),
            context=(
                "This appears in 2025/2026 SRE loops for API gateways, log aggregators, and etcd-adjacent proxies. "
                "Interviewers want both the sysctl and systemd knobs and the insistence on finding the leak. Saying "
                "only \"increase ulimit\" without /proc/<pid>/fd is junior."
            ),
            steps=[
                "Confirm the error — application log, errno 24, or ss showing listen drops.",
                "Compare per-process fd count to limits via /proc/<pid>/limits and fd count.",
                "Check system totals with fs.file-nr and lsof summaries.",
                "Raise limits appropriately and fix the leak; add alerting on fd usage percentage.",
            ],
            evidence=[
                "cat /proc/<pid>/limits | grep 'open files'",
                "ls /proc/<pid>/fd | wc -l ; lsof -p <pid> | wc -l",
                "cat /proc/sys/fs/file-nr ; sysctl fs.file-max",
            ],
            redflag=(
                "Do not crank fs.file-max to millions without finding which process consumes them. You mask a leak "
                "until the node runs out of memory tracking metadata."
            ),
            followup="Only one pod on the node hits the limit while others are fine. Where is the boundary?",
        ),
        Q(
            q="When would you use an LVM snapshot, and what are the risks?",
            level=SENIOR,
            answer=(
                "An LVM snapshot is a copy-on-write view of a logical volume at a point in time — useful for "
                "consistent backups before a risky migration or for short-lived rollback windows. I create it with "
                "lvcreate -L size -s -n snap /dev/vg/lv, mount read-only if possible, back up with xfsdump or pg_dump "
                "from the snapshot not the live LV, then lvremove the snapshot promptly. Risks: the snapshot COW "
                "table fills if the source LV changes heavily while the snapshot exists — writes fail or the snapshot "
                "becomes invalid. Size snapshots generously or keep them minutes not days. They are not a replacement "
                "for replicas; they are a crash-consistent or application-quiesced backup aid."
            ),
            analogy=(
                "A snapshot is a photocopy of your ledger at noon. Every edit after noon is tracked on a sticky note "
                "stack — if the stack overflows, the copy is useless and the books may lock."
            ),
            context=(
                "Database and registry interview loops still mention LVM snapshots alongside pg_start_backup and "
                "Restic. Platform candidates managing StatefulSets on bare metal need to articulate why snapshots "
                "without quiesce are crash-consistent only, and why full thin pools differ from classic snapshots."
            ),
            steps=[
                "Define COW snapshot behaviour and the point-in-time use case.",
                "Describe create, mount read-only, backup, remove — short lifetime.",
                "Warn about snapshot fill under write churn and sizing the COW pool.",
                "Contrast with application-consistent backup and storage replication for DR.",
            ],
            evidence=[
                "lvcreate -L 10G -s -n db_snap /dev/vg/db",
                "lvs -o lv_name,origin,data_percent,snap_percent",
                "mount -o ro /dev/vg/db_snap /mnt && xfsdump -l 0 - /mnt",
            ],
            redflag=(
                "Do not treat LVM snapshots as free infinite backups. An filled snapshot pool takes down writes "
                "on the origin LV."
            ),
            followup="You need application-consistent backup for PostgreSQL on LVM. Walk through the sequence.",
        ),
        Q(
            q="Which kernel tunables do you adjust for a high-connection Linux server, and how do you persist them on RHEL?",
            level=SENIOR,
            answer=(
                "For connection-heavy workloads I review net.core.somaxconn and the application backlog, "
                "net.ipv4.ip_local_port_range for ephemeral ports, net.ipv4.tcp_tw_reuse carefully on modern kernels, "
                "fs.file-max and per-service LimitNOFILE, vm.swappiness on databases often tuned toward 1 or 10, "
                "and vm.overcommit_memory when the workload justifies it — for example Redis documentation. Conntrack "
                "nf_conntrack_max matters on nodes doing NAT. I set values in /etc/sysctl.d/99-app.conf, apply with "
                "sysctl --system, and verify with sysctl -a and /proc. On OpenShift fleet nodes the same keys belong "
                "in MachineConfig kubeletConfig or tuned profiles — not manual sysctl on one box."
            ),
            analogy=(
                "Kernel tunables are city traffic rules — speed limits, lane counts, and parking spaces. You can "
                "widen the road, but if every driver triple-parks you still gridlock unless the rules match reality."
            ),
            context=(
                "2025/2026 platform interviews tie this to ingress controllers, service meshes, and etcd latency. "
                "Candidates should mention tuned-adm profile for throughput versus latency, and that blind copy-paste "
                "from blog posts without measuring ss -s and conntrack -S is how you break TCP behaviour."
            ),
            steps=[
                "Start from the symptom: port exhaustion, accept queue drops, conntrack full, swap thrash.",
                "Name relevant sysctl keys and what each actually controls — not magic numbers.",
                "Persist via /etc/sysctl.d and sysctl --system; on OpenShift via MachineConfig.",
                "Validate under load and document rollback — tunables are changes with blast radius.",
            ],
            evidence=[
                "sysctl net.core.somaxconn net.ipv4.ip_local_port_range fs.file-max",
                "ss -s ; cat /proc/sys/net/netfilter/nf_conntrack_count",
                "sysctl --system ; tuned-adm active",
            ],
            redflag=(
                "Do not recite deprecated tunables like raising tcp_fin_timeout without context. Interviewers "
                "flag cargo-cult sysctl lists from 2012 blog posts."
            ),
            followup="After raising somaxconn, clients still see connection timeouts under load. What do you measure next?",
        ),
        Q(
            q="How would you design disk layout and LVM strategy for a stateful database node?",
            level=ARCHITECT,
            answer=(
                "I separate concerns onto different LVs or disks: OS root small and boring, data LV for the database "
                "on the fastest durable tier, WAL or redo on separate low-latency devices when the engine benefits, "
                "logs on their own mount so a log storm cannot fill data, and backups landing on a different VG or "
                "object storage — not the same full VG. I align filesystem choice with workload — XFS default on "
                "RHEL for most data volumes — size LVs with headroom but snapshot COW in mind, and document extent "
                "growth in Terraform or kickstart. RAID level, multipath, and LUKS for data-at-rest sit underneath "
                "LVM; the interview is about blast-radius isolation and operational headroom, not one giant /."
            ),
            analogy=(
                "Designing disk layout is zoning a factory: raw materials, assembly line, and shipping docks are "
                "separate bays so a spill in shipping does not shut production."
            ),
            context=(
                "Architect-level loops ask this for PostgreSQL on bare metal, OpenShift Data Foundation edge cases, "
                "and migration from \"one volume\" VMs. They listen for separating logs from data, monitoring inode "
                "and block usage independently, and having a grow path that does not require downtime."
            ),
            steps=[
                "List workloads and I/O patterns — random versus sequential, latency sensitivity for WAL.",
                "Map mounts to LVs with failure isolation: data, logs, temp, backup target.",
                "Choose RAID/multipath/encryption under the PVs; leave VG free space for growth and snapshots.",
                "Encode in IaC, define alerts at seventy and eighty-five percent, and test restore not just backup.",
            ],
            evidence=[
                "lsblk -f ; lvs -o+devices ; df -h",
                "iostat -xz 1 5   # validate device separation under load",
                "cat /etc/fstab ; grep -r lvcreate kickstart/ or terraform/",
            ],
            redflag=(
                "Do not put database data, logs, and backups on one LV because \"LVM can grow later\". One full "
                "mount stops the database even if another area has space."
            ),
            followup="You inherit a monolithic /var with PostgreSQL and logs. How do you split without a full rebuild?",
        ),
        Q(
            q="How do you manage kernel and sysctl configuration across a fleet without creating snowflakes?",
            level=ARCHITECT,
            answer=(
                "Single source of truth wins: tuned profiles plus /etc/sysctl.d fragments rendered from Git, applied "
                "by Ansible or MachineConfig on OpenShift, with node labels selecting which profile applies — GPU "
                "nodes versus ingress versus generic workers. I avoid ssh sysctl on individual hosts; drift shows up "
                "in compliance scans and surprise reboot behaviour. Changes go through PR, canary nodes, before fleet "
                "rollout, with sysctl --system idempotency and automated validation comparing sysctl -a to expected "
                "JSON. Document why each tunable exists — owner, rollback, blast radius — because sysctl debt is "
                "harder to audit than package debt. On immutable OSes, if it is not in the rendered config, it did "
                "not happen."
            ),
            analogy=(
                "Fleet sysctl management is air-traffic rules for a country, not each pilot choosing their own altitude. "
                "Local exceptions need a filed flight plan and an expiry date."
            ),
            context=(
                "This separates staff SRE from consultants who fix one node. 2026 interviews connect it to MCO "
                "pool semantics, PerformanceProfile for low latency, and compliance tools flagging unexpected "
                "/proc/sys values. The architect answer mentions observability — track conntrack usage and OOM events "
                "after fleet-wide changes."
            ),
            steps=[
                "Declare principle: declarative, versioned, node-class scoped configuration.",
                "Pick mechanisms: tuned, sysctl.d, MachineConfig kubeletConfig or custom MC.",
                "Describe change flow: PR, canary pool, metrics watch, fleet promote, rollback path.",
                "Add drift detection and documentation — no unnamed magic numbers in production.",
            ],
            evidence=[
                "oc get mc,pp -o wide   # OpenShift path",
                "ansible-playbook sysctl.yml --check --diff",
                "sysctl -a | sha256sum   # compare canary versus baseline",
            ],
            redflag=(
                "Do not describe \"we have a wiki page of sysctl settings\" as fleet management. Wikis do not "
                "survive the first hire-and-forget emergency ssh session."
            ),
            followup="One node class needs a vendor-required kernel module and tunable the others must not have. How do you model that?",
        ),
    ],
)
