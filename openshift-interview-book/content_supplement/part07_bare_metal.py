"""Part 7 - Bare metal provisioning for OpenShift."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=7,
    title="Bare metal provisioning",
    subtitle="From BMC power-on to a node joining the cluster — Satellite, PXE, Kickstart and Ironic",
    intro=(
        "Bare metal OpenShift clusters do not appear from an API call. Someone must power the machine on, "
        "deliver a boot image over the network, install RHEL with the right Ignition payload, and only then "
        "let the installer or Bare Metal Operator hand the node to the cluster. Interviewers probe this area "
        "because it separates people who have run OpenShift from people who have run the platform underneath "
        "it. The answers that land well connect Satellite, Capsules, DHCP and TFTP to a node that actually "
        "appears in oc get nodes — and explain what breaks when any hop in that chain is wrong."
    ),
    infographics=["upgrade_flow"],
    questions=[
        Q(
            q="What role does Red Hat Satellite play in bare metal provisioning?",
            level=FOUNDATION,
            answer=(
                "Satellite is the content and lifecycle hub for RHEL in the datacentre. It mirrors Red Hat "
                "repositories, publishes custom content views, manages subscriptions and activation keys, and "
                "hosts Kickstart templates and discovery images that turn a blank server into an installed "
                "host. For OpenShift bare metal you use it to standardise the OS build — same packages, same "
                "kernel, same hardening — before Ignition or the installer takes over."
            ),
            analogy=(
                "It is the central kitchen that prepares identical meal kits. Every server gets the same "
                "recipe and ingredients; the local restaurant only plates and serves."
            ),
            context=(
                "Satellite rarely installs OpenShift itself, but it owns everything up to that point. Teams "
                "that skip it often end up with hand-built Kickstarts, drifting package sets and no audit "
                "trail of which build a node received. For interview purposes, Satellite is the answer to "
                "'how do we make a thousand blades identical before they join the cluster?'"
            ),
            steps=[
                "Explain content mirroring, subscriptions and activation keys.",
                "Describe Kickstart and discovery image hosting as the provisioning entry point.",
                "Connect a finished RHEL host to OpenShift via Ignition or the Bare Metal Operator.",
                "Mention Capsules when provisioning happens in remote sites.",
            ],
            evidence=[
                "hammer content-view list ; hammer activation-key list",
                "hammer host list --search 'name~worker'",
                "On the node: cat /etc/redhat-release ; rpm -qa | wc -l",
            ],
            redflag=(
                "Do not describe Satellite as optional once you are at scale. Ad-hoc installs are how "
                "production clusters acquire silent drift."
            ),
            followup="How would you promote a tested Kickstart from dev to production in Satellite?",
        ),
        Q(
            q="How does PXE network boot work with PXELinux and PXEGrub2?",
            level=FOUNDATION,
            answer=(
                "Preboot eXecution Environment lets a server with no local OS fetch a boot loader over the "
                "network. The firmware requests DHCP option 66/67 or equivalent, learns the TFTP server and "
                "boot file name, downloads the loader via TFTP, and that loader fetches a kernel and "
                "initramfs. PXELinux is the legacy BIOS chain loader; PXEGrub2 is the UEFI-aware Grub2 "
                "image used on modern hardware. Both end at the same place — a Linux kernel running an "
                "installer or discovery image."
            ),
            analogy=(
                "PXE is a courier who delivers the key to the front door. PXELinux or PXEGrub2 is which "
                "locksmith cut the key — different shape, same door."
            ),
            context=(
                "Interviewers care because the boot chain is where provisioning fails most often, and the "
                "failure looks like 'machine hangs at DHCP' rather than an OpenShift error. BIOS versus UEFI "
                "determines which loader you publish, and mixing them up produces a silent hang after TFTP "
                "starts. Capsule servers in remote sites must serve the same boot artifacts as the main "
                "Satellite or nodes there will never match the standard build."
            ),
            steps=[
                "State the sequence: DHCP assignment, TFTP fetch of loader, loader fetches kernel/initramfs.",
                "Distinguish PXELinux for legacy BIOS from PXEGrub2 for UEFI.",
                "Point to the Kickstart or discovery image as the payload the kernel runs.",
                "Verify firmware boot mode matches the published loader before debugging OpenShift.",
            ],
            evidence=[
                "On the provisioning host: ls /var/lib/tftpboot/pxelinux.cfg/ ; ls /var/lib/tftpboot/grub2/",
                "tcpdump -i <iface> port 67 or port 69 during a boot attempt",
                "Journal on Capsule: journalctl -u foreman-proxy-dns -u dhcpd -u tftpd",
            ],
            redflag=(
                "Do not publish a PXELinux layout to a UEFI-only server. It will never chain-load."
            ),
            followup="The server gets an IP but stops after TFTP. What do you check next?",
        ),
        Q(
            q="What do DHCP, TFTP and DNS each contribute to network boot?",
            level=FOUNDATION,
            answer=(
                "DHCP assigns the machine an IP address and, critically, tells it where to boot from — the "
                "next-server address and boot file name via options 66 and 67 or the UEFI DHCP options. TFTP "
                "is the trivial file transfer service that actually delivers the small boot loader and "
                "initial files because nothing else is running yet. DNS provides the names the installed host "
                "and the OpenShift cluster will need — api, api-int, apps wildcard, and forward and reverse "
                "records for each node — so the machine can resolve endpoints after the OS is up."
            ),
            analogy=(
                "DHCP is the reception desk that assigns a desk number and directions. TFTP is the lift "
                "that carries your bags to the floor. DNS is the building directory you need once you are "
                "inside."
            ),
            context=(
                "These three services are owned by different teams in most enterprises, which is why "
                "provisioning runbooks spend pages on hand-offs. A working DHCP scope with no TFTP server "
                "gives you an IP and a hang. TFTP with no DNS leaves you with an installed host that cannot "
                "join OpenShift because api-int does not resolve. Senior answers name the owner of each "
                "service and the record each one needs."
            ),
            steps=[
                "DHCP: IP lease plus next-server and bootfile options matched to BIOS or UEFI.",
                "TFTP: boot loader, kernel and initramfs reachable from the provisioning VLAN.",
                "DNS: api, api-int, apps wildcard and per-node forward and reverse before install completes.",
                "Validate all three from a test NIC on the provisioning network before the first production "
                "boot.",
            ],
            evidence=[
                "dig api.<cluster>.<domain> ; dig api-int.<cluster>.<domain>",
                "dhcpd -t -cf /etc/dhcp/dhcpd.conf   # syntax check before reload",
                "tftp <tftp-server> -c get grub/grubx64.efi /tmp/test.efi",
            ],
            redflag=(
                "Do not assume DNS can wait until after install. The OpenShift bootstrap and node join "
                "process need working records immediately."
            ),
            followup="Which DHCP options differ between legacy BIOS PXE and UEFI HTTP boot?",
        ),
        Q(
            q="What is Kickstart and how does it automate RHEL installation?",
            level=FOUNDATION,
            answer=(
                "Kickstart is an unattended installation answer file. It declares partitioning, packages, "
                "network settings, users, firewall posture and post-install scripts so Anaconda installs "
                "RHEL without human input. Satellite hosts Kickstart templates parameterised with "
                "host-specific values — hostname, IP, activation key — and passes them to the booting "
                "kernel via the ks= URL. For OpenShift the Kickstart usually ends with a first-boot script "
                "or Ignition fetch that prepares the node for the installer or Bare Metal Operator."
            ),
            analogy=(
                "It is a detailed shopping list and assembly instructions left on the counter. The installer "
                "follows it exactly, every time, without asking questions."
            ),
            context=(
                "Kickstart is where OS standardisation lives. Two teams with different %packages sections "
                "produce two different clusters that both claim to run the same OpenShift version. "
                "Interviewers want to hear about idempotency — the same Kickstart with different host "
                "variables — and about %post scripts that hand off to cluster join rather than doing "
                "OpenShift installation inside Kickstart itself."
            ),
            steps=[
                "Define sections: lang, network, bootloader, partitioning, %packages, %post.",
                "Bind the template to an activation key and content view in Satellite.",
                "Pass ks= at boot time so Anaconda pulls the rendered file.",
                "Use %post to fetch Ignition, register subscriptions or trigger discovery.",
            ],
            evidence=[
                "hammer host list --search 'build_status=failed'",
                "On installing host: tail -f /tmp/anaconda.log",
                "Rendered Kickstart: curl -k https://<satellite>/unattended/provision?token=<token>",
            ],
            redflag=(
                "Do not embed secrets in plain-text Kickstarts. Use Satellite parameters or vault "
                "integration."
            ),
            followup="A Kickstart succeeds but the node has the wrong OpenShift kernel. Where do you look?",
        ),
        Q(
            q="What is a BMC and how do IPMI and Redfish differ?",
            level=INTERMEDIATE,
            answer=(
                "The Baseboard Management Controller is an out-of-band management chip on the server that "
                "controls power, reads sensors and exposes virtual media and serial consoles independently "
                "of the main CPU. IPMI is the older binary protocol, usually on a dedicated management NIC, "
                "used by tools such as ipmitool and by Ironic for power and boot-order control. Redfish is "
                "the modern RESTful API over HTTPS with JSON payloads, better suited to automation, "
                "firmware inventory and virtual media uploads on current hardware."
            ),
            analogy=(
                "The BMC is the building manager with keys to every switch. IPMI is the old phone line to "
                "the manager; Redfish is the manager's web portal."
            ),
            context=(
                "Bare metal OpenShift depends on reliable out-of-band control. The Bare Metal Operator "
                "talks to Ironic, which talks to the BMC to power on a server, set one-time PXE boot and "
                "read hardware inventory. Interviewers probe whether you know that management network "
                "isolation is non-negotiable — a BMC on the production LAN is a critical vulnerability — "
                "and that Redfish support varies by vendor even when the logo is on the HCL."
            ),
            steps=[
                "Define BMC role: power, boot order, sensors, virtual media, serial over LAN.",
                "Contrast IPMI CLI tooling with Redfish REST endpoints.",
                "Explain Ironic's use of the BMC for provisioning and deprovisioning cycles.",
                "Isolate management traffic on a dedicated VLAN with strict ACLs.",
            ],
            evidence=[
                "ipmitool -I lanplus -H <bmc-ip> -U admin power status",
                "curl -k -u admin:pass https://<bmc-ip>/redfish/v1/Systems/1",
                "oc get baremetalhost -n openshift-machine-api -o wide",
            ],
            redflag=(
                "Do not put BMC interfaces on an untrusted network. They have full power over the server "
                "below the OS."
            ),
            followup="Ironic cannot power on a registered host. How do you isolate BMC versus Ironic?",
        ),
        Q(
            q="How does the OpenShift bare metal discovery service work?",
            level=INTERMEDIATE,
            answer=(
                "Discovery is an assisted onboarding path for user-provisioned bare metal. You boot unknown "
                "hardware with a discovery ISO — often built from Satellite or the OpenShift assisted "
                "installer image — which collects inventory, tests connectivity and reports hardware "
                "details back to a discovery server or hub. Once validated, that inventory becomes a "
                "BareMetalHost definition Ironic can manage, with MAC addresses, BMC credentials and "
                "firmware notes captured before anyone writes a custom YAML by hand."
            ),
            analogy=(
                "It is a job interview before the first day. You learn what the candidate actually is "
                "before assigning them a desk."
            ),
            context=(
                "Discovery saves weeks when you have heterogeneous hardware or remote hands who cannot "
                "run oc commands. The failure mode is booting the wrong ISO on the wrong VLAN — discovery "
                "registrations appear in the hub but BMC addresses are unreachable from the provisioning "
                "network. Interviewers reward candidates who connect discovery to inventory accuracy for "
                "Ironic rather than treating it as a separate installer gimmick."
            ),
            steps=[
                "Build or download the discovery ISO aligned to the OpenShift version.",
                "Boot target servers from ISO or PXE; agents report inventory to the discovery service.",
                "Review CPU, NIC, disk and firmware data; fix BMC or network gaps.",
                "Approve hosts for provisioning; Ironic registers them as BareMetalHost objects.",
            ],
            evidence=[
                "Discovery hub UI or API: list discovered hosts and validation status",
                "oc get baremetalhost -n openshift-machine-api -o yaml | grep -A5 'hardwareDetails'",
                "On discovery agent host: journalctl -u agent — or equivalent agent log",
            ],
            redflag=(
                "Do not skip validating BMC reachability from the provisioning network. Discovery inventory "
                "without working out-of-band control cannot provision."
            ),
            followup="Discovery shows the wrong NIC for provisioning. How do you fix it before approval?",
        ),
        Q(
            q="What are Capsule servers in Satellite and when do you need them?",
            level=INTERMEDIATE,
            answer=(
                "A Capsule is a Satellite proxy deployed close to the servers it serves — a remote "
                "datacentre, edge site or high-latency network. It runs local DNS, DHCP, TFTP, Puppet or "
                "Ansible callbacks and content caching so machines do not pull boot files or RPMs across "
                "a WAN link. The main Satellite remains the control plane; Capsules sync content views and "
                "report back. You need them when provisioning VLANs cannot reach the central Satellite "
                "directly or when local PXE latency and bandwidth would make boot unreliable."
            ),
            analogy=(
                "Satellite is headquarters. A Capsule is the regional warehouse — same catalogue, shorter "
                "delivery route."
            ),
            context=(
                "OpenShift bare metal at multiple sites almost always implies Capsules. The interview "
                "trap is forgetting that DHCP and TFTP must be authoritative locally — pointing remote "
                "servers at a central TFTP host over a congested link produces intermittent PXE failures "
                "that look like bad hardware. Capsule sizing also matters: hundreds of simultaneous builds "
                "need adequate disk for synced repos and TFTP roots."
            ),
            steps=[
                "Identify sites where servers cannot reach central Satellite services reliably.",
                "Deploy a Capsule with synced content views and local DHCP, DNS and TFTP roles.",
                "Register the Capsule with the main Satellite and promote the same content views.",
                "Point provisioning subnets at the Capsule's next-server and TFTP paths.",
            ],
            evidence=[
                "hammer capsule list ; hammer capsule content list --id <id>",
                "On Capsule: foreman-proxy status ; ls /var/lib/tftpboot/",
                "From remote site: time tftp <capsule-ip> -c get pxelinux.0 /tmp/test",
            ],
            redflag=(
                "Do not sync a Capsule manually and forget content view promotion. Stale boot images are "
                "how remote sites run the wrong OpenShift version."
            ),
            followup="Central Satellite is up but remote PXE fails. Walk me through Capsule troubleshooting.",
        ),
        Q(
            q="How does OpenShift integrate with vSphere for machine provisioning?",
            level=INTERMEDIATE,
            answer=(
                "On vSphere, OpenShift uses the Machine API with a vSphere provider: MachineSets define "
                "template, folder, resource pool, network and disk layout, and the machine controller "
                "clones VMs from an OVA or template with Ignition injected via guestinfo. It is not bare "
                "metal, but it fills the same platform role — automated node lifecycle with the installer "
                "or IPI creating load balancers, DNS records and machines. UPI on vSphere means you create "
                "the VMs yourself but still use the same Ignition and RHCOS/RHEL boot process."
            ),
            analogy=(
                "Bare metal provisioning is hiring craftsmen on site. vSphere integration is ordering "
                "prefabricated modules from a factory — still your cluster, different supply chain."
            ),
            context=(
                "Interviewers ask this in bare metal conversations because many 'on-prem OpenShift' roles "
                "are hybrid: control plane on VMs, workers on metal, or the reverse. The integration points "
                "— templates with the right Ignition, DHCP and DNS for API endpoints, storage classes "
                "backed by vSAN — are the same services bare metal needs, just delivered by the hypervisor "
                "instead of PXE. Knowing when to choose full metal versus vSphere workers is an architect "
                "signal."
            ),
            steps=[
                "Prepare a VM template with guestinfo Ignition support and compatible hardware version.",
                "Configure install-config or MachineSet with vCenter credentials, datacentre and network.",
                "Ensure DNS and load balancers for api and apps resolve before install.",
                "For hybrid clusters, label and taint metal workers separately from VM workers.",
            ],
            evidence=[
                "oc get machineset -n openshift-machine-api -o yaml | grep -i vsphere",
                "oc get machine -A -o wide",
                "vCenter: monitor clone tasks tied to machine names",
            ],
            redflag=(
                "Do not treat vSphere templates like generic Linux images. Missing Ignition guestinfo "
                "support produces nodes that boot but never join."
            ),
            followup="When would you choose bare metal workers over vSphere VMs for OpenShift?",
        ),
        Q(
            q="What does the Bare Metal Operator do with Ironic?",
            level=INTERMEDIATE,
            answer=(
                "The Bare Metal Operator is the Kubernetes controller that manages BareMetalHost custom "
                "resources — registering hardware, validating BMC credentials, driving provisioning states "
                "and handing enrolled nodes to the Machine API. Ironic is the OpenStack bare metal service "
                "that actually talks to BMCs, builds deploy ramdisks, writes disk images and toggles boot "
                "devices. In OpenShift, Ironic runs on the bootstrap or control plane; the operator "
                "translates BareMetalHost specs into Ironic API calls and surfaces status back to oc."
            ),
            analogy=(
                "BareMetalHost is the work order on the clipboard. Ironic is the technician in the datacentre "
                "with the cart of tools."
            ),
            context=(
                "This is the centre of native bare metal IPI on OpenShift 4. Candidates who only know "
                "Satellite Kickstart miss the day-two story: deprovisioning, reprovisioning, firmware "
                "RAID and the inspection phase before a host is trusted. Ironic's provisioning network "
                "must reach the BMC and the host NIC used for PXE, which is a common design review "
                "topic."
            ),
            steps=[
                "Define BareMetalHost with BMC address, credentials, MAC and provisioning flags.",
                "Operator registers the host; Ironic inspects hardware if enabled.",
                "Provisioning state: Ironic powers on, PXE boots deploy ramdisk, writes RHCOS image.",
                "Host becomes a Machine; cluster-operator completes node configuration via MachineConfig.",
            ],
            evidence=[
                "oc get baremetalhost,bmh -n openshift-machine-api",
                "oc describe baremetalhost <name> -n openshift-machine-api | grep -i state",
                "On provisioning node: podman logs -f ironic-conductor   # or equivalent Ironic log",
            ],
            redflag=(
                "Do not register BMC credentials in Git. Use secrets referenced by the BareMetalHost."
            ),
            followup="A BareMetalHost is stuck in provisioning. Which states do you walk through?",
        ),
        Q(
            q="What is UEFI HTTP boot and why is it replacing traditional PXE?",
            level=SENIOR,
            answer=(
                "UEFI HTTP boot lets firmware download boot loaders and kernels over HTTP or HTTPS instead "
                "of TFTP. DHCP still provides the initial network configuration, but options now point to "
                "a URI such as http://capsule/boot/grubx64.efi rather than a TFTP path. HTTPS adds integrity "
                "and works better across routed networks and firewalls than TFTP's small-packet UDP model. "
                "Large initramfs images and modern security expectations make HTTP boot the default on "
                "current servers; Satellite and Capsules publish both TFTP and HTTP endpoints during the "
                "transition."
            ),
            analogy=(
                "TFTP is a bicycle courier with a small bag. HTTP boot is a van that can carry the whole "
                "stage set and confirm delivery with a signature."
            ),
            context=(
                "Enterprises refreshing hardware hit this during OpenShift upgrades: new UEFI-only boxes "
                "that never successfully TFTP a full RHCOS ramdisk. Interviewers want you to mention "
                "certificate trust in firmware, proxy settings and the need to update DHCP snippets — not "
                "just 'turn on HTTP boot'. Mixed fleets often run HTTP for UEFI and TFTP for legacy BIOS "
                "until the last old server retires."
            ),
            steps=[
                "Enable HTTP boot in firmware; confirm firmware trusts the serving certificate or use HTTP "
                "on an isolated provisioning VLAN.",
                "Publish Grub2 and kernel artifacts on Capsule or Satellite HTTP endpoints.",
                "Update DHCP to supply the HTTP URI via vendor-specific UEFI options.",
                "Validate boot alongside existing TFTP paths during a hardware refresh migration.",
            ],
            evidence=[
                "curl -I http://<capsule>/pub/grubx64.efi   # artifact reachable",
                "tcpdump -i <vlan> port 67 or port 80 during boot",
                "UEFI firmware boot log — screenshot or IPMI serial capture of HTTP fetch status",
            ],
            redflag=(
                "Do not disable TFTP on day one when legacy BIOS servers still exist. Run both chains until "
                "inventory confirms otherwise."
            ),
            followup="HTTP boot fails with certificate errors in firmware. What are your options?",
        ),
        Q(
            q="A bare metal node fails to join the cluster after provisioning. How do you troubleshoot?",
            level=SENIOR,
            answer=(
                "I work backwards through the chain. First confirm the OS is actually the expected build — "
                "correct kernel, ignition applied, subscription valid. Then DNS: api-int must resolve from "
                "the node. Then network: can the node reach the API on 6443 and the machine config server? "
                "Then certificates: pending CSRs for kubelet and node client. Only after those pass do I "
                "look at Ironic/BareMetalHost state, Machine object conditions and finally kubelet logs on "
                "the node itself."
            ),
            analogy=(
                "The patient is in the building but not at the meeting. Check they have the right badge, "
                "know the room number and the lift works — before questioning their presentation skills."
            ),
            context=(
                "The classic mistake is jumping to OpenShift logs when the node still has the wrong IP or "
                "no reverse DNS. Another is provisioning success in Ironic while Ignition never ran, "
                "leaving ssh keys and hostname wrong. Senior candidates narrate a ordered checklist and "
                "say which team owns each failure — DNS team, network team, platform team — because bare "
                "metal incidents are almost always cross-functional."
            ),
            steps=[
                "Verify OS build, Ignition completion and subscription on the node console or SSH.",
                "From the node: dig api-int.<cluster>.<domain> ; curl -k https://api-int:6443/healthz",
                "Check oc get csr and oc get machine <name> -o yaml for failure conditions.",
                "Review BareMetalHost provisioning state and Ironic logs if the node never reached OS.",
            ],
            evidence=[
                "oc get nodes ; oc get csr | grep Pending",
                "On node: journalctl -u kubelet --no-pager | tail -50",
                "oc describe machine <name> -n openshift-machine-api",
            ],
            redflag=(
                "Do not re-provision immediately. You may destroy evidence and repeat the same misconfigured "
                "Kickstart or DNS gap."
            ),
            followup="Ironic says provisioned but oc get nodes never shows the host. Where is it stuck?",
        ),
        Q(
            q="How would you design bare metal provisioning for OpenShift at enterprise scale?",
            level=ARCHITECT,
            answer=(
                "I separate concerns into layers: Satellite and Capsules for OS standardisation and content "
                "promotion; isolated provisioning and BMC networks with local DHCP, TFTP and HTTP; discovery "
                "for inventory; Ironic and the Bare Metal Operator for cluster-native lifecycle; and GitOps "
                "for BareMetalHost and MachinePool definitions. Each site gets a Capsule, shared activation "
                "keys and content views, and a tested promotion path from lab to production. Rollouts are "
                "canaried — one rack, one row, one site — with automated validation that DNS, pull secret "
                "and Ignition match before the next wave."
            ),
            analogy=(
                "It is an airport hub system: central timetable, regional gates, identical boarding process, "
                "local ground crew — not one overwhelmed check-in desk for every flight worldwide."
            ),
            context=(
                "Architect answers acknowledge organisational reality: networking owns DHCP, security owns "
                "BMC VLANs, Linux owns Kickstart, platform owns OpenShift. The design artefact interviewers "
                "want is a reference architecture diagram with trust boundaries, not a list of tools. Scale "
                "also means decommissioning and firmware lifecycle — provisioning is not a one-way door."
            ),
            steps=[
                "Map sites, Capsule placement and network VLANs for provisioning, BMC and production.",
                "Standardise content views, Kickstart and discovery ISO promotion across environments.",
                "Automate BareMetalHost registration from discovery with sealed BMC secrets.",
                "Define validation gates — DNS, API reachability, node Ready — before fleet expansion.",
            ],
            evidence=[
                "Reference architecture doc: VLANs, Capsule map, promotion workflow",
                "hammer content-view version list --content-view Production-RHEL",
                "Metrics: provisioning success rate, time-to-Ready, failed BMC percentage by site",
            ],
            redflag=(
                "Do not centralise all TFTP and DHCP on one Satellite without redundancy. A single outage "
                "freezes every rack."
            ),
            followup="How do you handle firmware upgrades across thousands of BMCs without breaking Ironic?",
        ),
    ],
)
