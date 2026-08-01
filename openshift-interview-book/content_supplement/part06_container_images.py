"""Part 6 - Podman, Buildah, Skopeo and container images."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=6,
    title="Podman, Buildah, Skopeo and container images",
    subtitle="Building and moving images without Docker — the toolchain RHEL and OpenShift CI actually standardise on",
    intro=(
        "Red Hat's container stack is daemonless: Podman runs containers, Buildah builds them, Skopeo "
        "copies and inspects them, and UBI gives you a supportable base. Platform engineers meet this "
        "toolchain in CI pipelines, disconnected registries, rootless build hosts and the shift from "
        "Docker-in-Docker to Buildah-in-Kubernetes. Interviewers want practical answers — how subuid "
        "mapping works, why multi-arch manifests matter on heterogeneous clusters, and what you would "
        "check before trusting an image in production beyond the tag name."
    ),
    infographics=["container_stack"],
    questions=[
        Q(
            q="Why is Podman daemonless, and what changes for platform engineers?",
            level=FOUNDATION,
            answer=(
                "Podman talks directly to the OCI runtime — crun or runc — and the storage library "
                "containers/storage. There is no long-lived root daemon holding sockets and state. Each "
                "podman command is a process that forks the runtime, which means no single point of "
                "compromise, simpler systemd integration via podman generate systemd and Quadlet, and "
                "straightforward rootless operation mapped to the calling UID. For platform engineers the "
                "shift is operational: CI no longer needs a privileged Docker socket mounted into the "
                "builder; OpenShift builds can use Buildah strategies; and node troubleshooting uses "
                "crictl and podman interchangeably on RHCOS for debugging, not docker ps."
            ),
            analogy=(
                "Docker with a daemon is a restaurant with one head chef who must approve every order. "
                "Podman is a food truck — you order, it cooks, nobody waits on a central kitchen phone."
            ),
            context=(
                "This is the default on RHEL 9 and OpenShift 4.x nodes run CRI-O, which shares the same "
                "storage and runtime ecosystem. Teams still saying \"install Docker on the build server\" "
                "raise eyebrows in 2025/2026 interviews because it reintroduces a root daemon and socket "
                "permissions problem Podman was designed to remove."
            ),
            steps=[
                "Contrast architecture: Podman CLI → conmon + runtime + graph driver, no dockerd.",
                "List platform wins: rootless, pod semantics compatible with kube, systemd units, no socket.",
                "Mention compatibility: docker-compatible CLI flags, podman-docker package for alias.",
                "Note boundaries: Podman builds images via Buildah under the hood; it is not a registry.",
            ],
            evidence=[
                "podman info | head -30",
                "systemctl --user status podman.socket   # rootless API socket if enabled",
                "oc debug node/<node> -- chroot /host crictl ps ; chroot /host podman ps",
            ],
            redflag=(
                "Do not say \"Podman is just Docker with a different name\". The missing daemon changes "
                "security, CI design and how you run builds on shared infrastructure."
            ),
            followup="How would you migrate a Jenkins pipeline from Docker socket to Buildah?",
        ),
        Q(
            q="What is Buildah, and when do you use it instead of Podman build?",
            level=FOUNDATION,
            answer=(
                "Buildah constructs OCI images by committing container layers — from scratch, from an "
                "existing image, or via a Containerfile — without requiring a running container engine "
                "daemon. buildah bud builds from a Containerfile; buildah from starts an empty or base "
                "working container you mutate with run, copy, config, then commit. Use Buildah in CI when "
                "you want fine-grained scripting, multi-stage builds without extra privileges, or to build "
                "inside a locked-down namespace where podman build is too heavy. Podman build is Buildah "
                "under a convenience wrapper; in pipelines that only need docker build behaviour, either "
                "works, but Buildah is the lower-level tool operators embed in OpenShift S2I and custom "
                "build strategies."
            ),
            analogy=(
                "Buildah is a pottery wheel — you shape each layer by hand. Podman build is the same "
                "wheel with a recipe card clipped to it."
            ),
            context=(
                "OpenShift's built-in builds and many Tekton tasks use Buildah with chroot isolation and "
                "vfs or overlay mounts. Interviewers ask this to see if you know why Dockerfile RUN "
                "instructions become buildah run plus commit, and why --isolation chroot matters in "
                "unprivileged CI."
            ),
            steps=[
                "Define Buildah as OCI image construction without dockerd.",
                "Contrast bud (Containerfile) vs from/run/commit (scripted layer assembly).",
                "Explain typical CI invocation: buildah bud --layers --isolation chroot -t ... .",
                "State relationship to Podman and OpenShift BuildConfig strategies.",
            ],
            evidence=[
                "buildah --version ; buildah info",
                "buildah bud -t localhost/test:latest .",
                "oc get buildconfig -n <ns> -o yaml | grep -A5 strategy",
            ],
            redflag=(
                "Do not assume Buildah requires root. Rootless builds are supported with user namespace "
                "mapping — that is usually the whole point in CI."
            ),
            followup="Build fails with permission denied on RUN yum install. What isolation settings do you check?",
        ),
        Q(
            q="What is Skopeo used for in a platform pipeline?",
            level=INTERMEDIATE,
            answer=(
                "Skopeo performs image and repository operations without building or running containers. "
                "skopeo copy moves images between registries, directories and docker-archive tarballs, "
                "preserving or converting formats. skopeo inspect reads manifest metadata without a full "
                "pull. skopeo sync bulk-replicates repositories — essential for disconnected OpenShift "
                "mirrors. skopeo list-tags and signverify support promotion gates. Platform teams use it "
                "in mirroring jobs, air-gapped installs, and pre-flight checks before deploying a digest "
                "to production. It shares containers/image and containers/storage with Podman and Buildah "
                "so transport and auth configuration is consistent."
            ),
            analogy=(
                "If Buildah manufactures the product and Podman uses it, Skopeo is the shipping department "
                "— it moves boxes between warehouses without opening them."
            ),
            context=(
                "Disconnected OpenShift installs depend on oc mirror plus skopeo copy to populate "
                "registry.redhat.io content on a local registry. Interviewers connect Skopeo to supply "
                "chain: copy by digest, verify signatures on inspect, and never rely on a tag that moved "
                "between staging and production."
            ),
            steps=[
                "List core commands: copy, inspect, sync, delete, signverify.",
                "Explain transports: docker://, containers-storage:, dir:, oci-archive:.",
                "Describe disconnected mirroring: sync catalog → internal registry, preserve digests.",
                "Mention auth: registries.conf, auth.json, pull secrets same as Podman.",
            ],
            evidence=[
                "skopeo inspect docker://registry.redhat.io/ubi9/ubi-minimal:latest | head -20",
                "skopeo copy docker://src/image@sha256:... docker://dest/image@sha256:...",
                "oc adm release mirror --help | head -5",
            ],
            redflag=(
                "Do not use skopeo copy with a floating tag in production promotion. Copy the digest you "
                "tested or you have not promoted anything."
            ),
            followup="How do you mirror a multi-arch catalog for a disconnected cluster?",
        ),
        Q(
            q="What is Red Hat UBI, and why do platform teams standardise on it?",
            level=FOUNDATION,
            answer=(
                "Universal Base Image is Red Hat's freely redistributable container base built from RHEL "
                "content. UBI images — standard, minimal, micro, init — can be pulled, rebuilt and "
                "republished without extra licensing for your applications, while still receiving updates "
                "through registry.redhat.io or mirrored registries. Platform teams standardise on UBI "
                "because support boundaries are clear, SELinux and OpenShift compatibility are tested, "
                "and security scanners have consistent CVE data. Micro and minimal reduce attack surface "
                "for Go operators and static binaries; standard suits apps needing yum and common tools. "
                "The interview point is contractual: UBI is not \"CentOS renamed\"; it is the supported "
                "path for customer workloads on OpenShift."
            ),
            analogy=(
                "UBI is a certified foundation slab. You can build any house on it and ship the house "
                "anywhere; the slab supplier still stands behind the concrete formula."
            ),
            context=(
                "Enterprises mandate UBI in Dockerfile/Containerfile policy to avoid unlicensed RHEL "
                "layers or unmaintained alpine variants in regulated environments. Pair with image "
                "mirroring in disconnected sites and RHSA notifications tied to image streams."
            ),
            steps=[
                "Define UBI tiers: ubi9/ubi, ubi-minimal, ubi-micro, init helpers.",
                "State redistribution rights and update path via registry.redhat.io or mirror.",
                "Contrast with alpine/busybox — glibc, RPM ecosystem, OpenShift support matrix.",
                "Mention tooling: podman pull registry.redhat.io/ubi9/ubi-minimal, rpm -q in builds.",
            ],
            evidence=[
                "podman pull registry.redhat.io/ubi9/ubi-minimal:latest",
                "skopeo inspect docker://registry.redhat.io/ubi9/ubi-minimal:latest | grep -i arch",
                "oc get istag -n openshift | grep ubi",
            ],
            redflag=(
                "Do not ship arbitrary yum repos into UBI in production images without a CVE review "
                "process. \"Latest packages\" and \"reproducible builds\" pull in opposite directions."
            ),
            followup="When would you choose ubi-micro over ubi-minimal for an operator image?",
        ),
        Q(
            q="How do rootless container builds work on RHEL?",
            level=INTERMEDIATE,
            answer=(
                "Rootless Podman and Buildah run as an unprivileged user mapped into a user namespace "
                "where your UID appears as 0 inside the build container. Image layers land in "
                "~/.local/share/containers/storage instead of /var/lib/containers. Network uses slirp4netns "
                "or pasta unless you have delegated capabilities. Builds that need package installs work "
                "because the inner root is fake; binds to host paths you cannot read still fail, which is "
                "the point. Platform teams run rootless builders on shared CI workers so a compromised "
                "pipeline cannot own the host. Limitations to know: some storage drivers behave poorly "
                "rootless, privileged RUN instructions are impossible, and subuid range size caps the "
                "number of nested IDs available."
            ),
            analogy=(
                "Rootless build is a simulator cockpit. The controls feel real inside, but you are not "
                "actually flying the airline's plane."
            ),
            context=(
                "OpenShift namespaces default to restricted-v2 SCC; builders there are non-root. "
                "Interviewers ask how you install RPMs in a Containerfile without docker build --privileged "
                "and whether you trust rootless images to run on OpenShift without random UID assignment."
            ),
            steps=[
                "Explain user namespaces: outer UID mapped to inner 0 for build steps.",
                "Point to storage location and graph root under the user's home.",
                "List constraints: no true privileged ops, network namespace overhead, fuse-overlayfs on "
                "some setups.",
                "Describe CI pattern: run buildah bud as CI user, push with skopeo copy and registry auth.",
            ],
            evidence=[
                "podman info --format '{{.Store.Root}}' ; id ; cat /etc/subuid",
                "buildah bud --isolation chroot -t localhost/app:rootless .",
                "grep user /etc/containers/containers.conf",
            ],
            redflag=(
                "Do not disable user namespaces cluster-wide to \"make builds work\". Fix subuid allocation "
                "and storage driver choice instead."
            ),
            followup="Rootless build cannot bind-mount /var/run/docker.sock. Why is that a feature?",
        ),
        Q(
            q="What are subuid and subgid, and what breaks when they are missing?",
            level=INTERMEDIATE,
            answer=(
                "/etc/subuid and /etc/subgid allocate ranges of subordinate IDs to a user. Rootless "
                "Podman maps UIDs inside the container to this range on the host so file ownership in "
                "layers is consistent and multiple containers do not collide. A typical entry is "
                "build:100000:65536 — start at 100000, length 65536. Without it, rootless podman fails "
                "at setup with cannot find UID/GID for user. Platform teams provisioning build hosts must "
                "automate subuid assignment in Ansible or cloud-init alongside disk quotas for "
                "~/.local/share/containers. Nested ID exhaustion shows up as cannot allocate user namespace "
                "when ranges are too small or shared across too many users."
            ),
            analogy=(
                "subuid is a block of parking spaces reserved for your badge. Without a reserved block "
                "you cannot park — you certainly cannot park fifty guest cars."
            ),
            context=(
                "Shared CI runners are where this breaks in production. One golden image with wrong "
                "numeric ownership often traces back to building as root on a laptop and running rootless "
                "on OpenShift with arbitrary UID 1000680000. Interviewers want you to connect subuid to "
                "OpenShift's runAsUser strategy and fsGroup."
            ),
            steps=[
                "Define subuid/subgid files and the three-field format: name, start, count.",
                "Explain mapping: container UID 0 → host start+offset, keeping layer tar ownership sane.",
                "List failure symptoms: podman info warnings, permission denied on volume mounts.",
                "Describe provisioning: usermod --add-subuids, loginctl enable-linger for long-running "
                "rootless services.",
            ],
            evidence=[
                "cat /etc/subuid /etc/subgid",
                "podman unshare cat /proc/self/uid_map",
                "grep subid /etc/nsswitch.conf",
            ],
            redflag=(
                "Do not hand-edit subuid ranges without checking for overlaps. Duplicate ranges corrupt "
                "ownership silently across users."
            ),
            followup="An image built rootless shows wrong ownership on OpenShift volumes. How do you fix the Dockerfile?",
        ),
        Q(
            q="Containerfile versus Dockerfile — does the difference matter?",
            level=FOUNDATION,
            answer=(
                "Syntax is identical for practical purposes: FROM, RUN, COPY, ENTRYPOINT, multi-stage AS "
                "blocks all work in a Containerfile. Red Hat documentation prefers Containerfile to signal "
                "OCI-native tooling without implying a Docker daemon dependency. Buildah and Podman accept "
                "either filename; -f points to whichever you use. Platform standards often mandate "
                "Containerfile in repos for clarity and lint rules. Interview nuance: some Docker-specific "
                "directives — HEALTHCHECK with certain forms, legacy builder-only flags — may differ; test "
                "with buildah bud. For OpenShift builds, the strategy dockerfile path in BuildConfig "
                "accepts Containerfile when you set contextDir and dockerfile keys accordingly."
            ),
            analogy=(
                "Containerfile is the same recipe card with the word \"kitchen\" crossed out and \"food "
                "prep area\" written in — the dish does not change."
            ),
            context=(
                "Policy-as-code in CI sometimes fails builds named Dockerfile to push teams toward the "
                "Red Hat toolchain. The substantive interview topic is not the filename but whether the "
                "instructions are compatible with rootless Buildah and produce arbitrary-UID-safe images."
            ),
            steps=[
                "State syntax parity and tooling acceptance: bud -f Containerfile .",
                "Explain naming convention: Red Hat docs, OCI emphasis, enterprise policy.",
                "Note BuildConfig/Tekton: reference path explicitly in task parameters.",
                "Mention validation: buildah bud --layers, dive or syft for review, not the extension.",
            ],
            evidence=[
                "buildah bud -f Containerfile -t localhost/app:test .",
                "ls -la Containerfile Dockerfile 2>/dev/null ; head Containerfile",
                "oc set build-hook --help ; grep -i dockerfile oc/new-build --help",
            ],
            redflag=(
                "Do not treat renaming Dockerfile to Containerfile as \"migration to Podman\". You still "
                "need rootless-safe instructions and a non-Docker CI executor."
            ),
            followup="Which Dockerfile patterns break under rootless Buildah?",
        ),
        Q(
            q="How do you build and publish multi-architecture images in 2025?",
            level=SENIOR,
            answer=(
                "Multi-arch images are manifest lists: one tag points to per-architecture manifests "
                "— amd64, arm64, s390x, ppc64le — each with its own digest. buildah manifest create "
                "starts a list; buildah manifest add builds or adds each arch; buildah manifest push "
                "publishes to the registry. Podman manifest commands mirror this. In CI, either native "
                "builders per arch fan-in with skopeo or buildah manifest, or cross-build with QEMU "
                "binfmt_misc registration — slower but one pipeline. OpenShift heterogeneous clusters "
                "— IBM Z, ARM edge, mixed worker pools — require manifest lists or pods fail ImagePullBackOff "
                "with no matching manifest. Always push the list, not individual arch tags, to production "
                "tags."
            ),
            analogy=(
                "A multi-arch manifest is a menu in three languages. The dish name is the same; the "
                "kitchen prepares the version each guest can actually eat."
            ),
            context=(
                "Apple Silicon laptops building amd64-only images that work locally but fail in CI is a "
                "classic gotcha. Platform interviews in 2025/2026 expect cosign sign on the manifest "
                "list index digest so signature covers all architectures."
            ),
            steps=[
                "Explain manifest list vs single-arch manifest and registry resolution.",
                "Walk buildah manifest workflow: create, add per arch, annotate, push --all.",
                "Compare native multi-node CI vs QEMU cross-build trade-offs.",
                "Verify with skopeo inspect --raw and oc adm release info for platform support.",
            ],
            evidence=[
                "buildah manifest create localhost/app:multi ; buildah manifest add ... ; buildah manifest push --all",
                "skopeo inspect docker://quay.io/<org>/<image>:latest | jq '.Manifests'",
                "podman run --rm mplatform/mquery quay.io/<org>/<image>:latest",
            ],
            redflag=(
                "Do not docker push from a single-arch laptop and call it multi-arch. You have built one "
                "flavour and mislabelled the menu."
            ),
            followup="How do you sign a manifest list so all architectures are covered?",
        ),
        Q(
            q="How should platform teams implement container image signing?",
            level=SENIOR,
            answer=(
                "Signing binds a cryptographic identity to an image digest. Cosign from Sigstore is the "
                "common choice: cosign generate-key-pair or keyless with OIDC in CI, cosign sign "
                "registry.example.com/app@sha256:..., cosign verify with public key or Fulcio certificate "
                "chain. Red Hat and Quay support signing integration; OpenShift can enforce signature "
                "policy via ClusterImagePolicy or admission configuration referencing sigstore policy "
                "documents. Platform pattern: CI builds image, pushes by digest, signs the digest, "
                "promotion copies only signed digests to production registry. Tags are signed only if "
                "you accept race conditions; digest signing is the durable approach. Rotate keys, audit "
                "verify failures, and mirror signatures with skopeo copy when air-gapped."
            ),
            analogy=(
                "Signing is a wax seal on a specific letter, not on the word \"letter\" in general. Anyone "
                "can reuse the word; they cannot reuse the seal on different paper."
            ),
            context=(
                "Supply chain interviews post-SLSA and EO 14028 expect digest-pinning plus verify before "
                "deploy. OpenShift 4.14+ image policy APIs connect to this; know the difference between "
                "Red Hat signed catalog images and your own app images signed in Tekton."
            ),
            steps=[
                "State object of signing: digest, not mutable tag.",
                "Outline cosign sign/verify flow in CI and at admission.",
                "Mention keyless OIDC for short-lived certificates vs long-lived KMS keys.",
                "Describe air-gap: copy signatures with skopeo, distribute public keys or CA roots.",
            ],
            evidence=[
                "cosign sign --key cosign.key registry.example.com/app@sha256:abc...",
                "cosign verify --key cosign.pub registry.example.com/app@sha256:abc...",
                "oc get clusterimagepolicy ; oc adm policy images --help",
            ],
            redflag=(
                "Do not verify tags in production policy. Tags move; signatures on tags lie the moment "
                "someone retags."
            ),
            followup="Admission rejects a Red Hat catalog image that worked yesterday. What changed?",
        ),
        Q(
            q="What role do SBOMs play in container supply chain security?",
            level=SENIOR,
            answer=(
                "A Software Bill of Materials lists packages and libraries inside an image — RPMs, pip "
                "modules, Go modules — tied to a specific digest. Tools like syft generate SPDX or CycloneDX "
                "SBOMs; grype or Trivy scan them for CVEs. Platform teams attach SBOMs as build artifacts, "
                "store them in OCI referrers or alongside releases, and feed VEX statements when "
                "vulnerabilities are not exploitable. Red Hat provides SBOM metadata for UBI and certified "
                "operators; your application images need their own. In interviews connect SBOM to policy: "
                "block critical CVEs at deploy, waivers with expiry, and reproducible builds so SBOM "
                "matches what ran."
            ),
            analogy=(
                "An SBOM is the ingredients list on packaged food. The health inspection does not eat "
                "the meal — it checks whether a known allergen is listed."
            ),
            context=(
                "Enterprise customers request SBOM exports for every release. OpenShift compliance "
                "operator and Konflux supply chain pipelines automate generation in Red Hat's ecosystem. "
                "Know the limit: an SBOM is only as honest as the build that produced it — hermetic builds "
                "matter."
            ),
            steps=[
                "Define SBOM purpose: inventory for vulnerability and license management.",
                "Name generators and formats: syft → SPDX/CycloneDX; scan with grype/trivy.",
                "Explain storage: CI artifact, OCI attachment/ referrer, release portal.",
                "Link to policy: CVE gates, VEX, UBI RHSA correlation, not checkbox compliance.",
            ],
            evidence=[
                "syft registry.example.com/app@sha256:abc... -o spdx-json",
                "grype sbom:./app.spdx.json",
                "skopeo inspect docker://registry.example.com/app@sha256:abc... | jq '.Labels'",
            ],
            redflag=(
                "Do not treat SBOM generation as security by itself. Without scanning, policy enforcement "
                "and signed digests, it is paperwork."
            ),
            followup="A CVE hits a base image package. Walk through patch, rebuild and redeploy with SBOM update.",
        ),
        Q(
            q="How do you run Buildah safely in CI and OpenShift pipelines?",
            level=INTERMEDIATE,
            answer=(
                "Avoid Docker-in-Docker and privileged daemon sockets. Preferred pattern: an unprivileged "
                "Tekton task or GitLab/Konflux job running buildah bud with --isolation chroot or "
                "oci, storage driver vfs or overlay in a writable emptyDir, and push via buildah push or "
                "skopeo copy using workspace registry credentials. Mount /tmp and HOME for layer cache if "
                "allowed. In OpenShift, use non-root SCC-compatible builders — custom pipeline namespace "
                "with anyuid only if policy demands and you understand the risk. Cache images with "
                "--layers and registry mirror. Set STORAGE_DRIVER explicitly when nodes lack fuse-overlayfs "
                "for rootless. Resource limits must cover peak layer extraction — OOM during yum is common."
            ),
            analogy=(
                "Safe CI build is cooking in your own booth at the fair, with your own gas line — not "
                "borrowing the central kitchen's master key."
            ),
            context=(
                "Many breaches traced to privileged CI containers with docker.sock mounted. Interviewers "
                "want Tekton/Konflux specifics: buildah task from Red Hat catalogs, workload identity for "
                "registry push, and separating build from deploy signing stages."
            ),
            steps=[
                "Reject privileged DinD; choose rootless buildah in isolated namespace.",
                "Configure storage: emptyDir graph root, vfs if overlay unavailable, layer cache policy.",
                "Wire auth: dockercfg or imagePullSecret mounted for push.",
                "Split pipeline: build → scan → sign → promote, each stage pinned by digest.",
            ],
            evidence=[
                "grep -R buildah .tekton/ .gitlab-ci.yml",
                "oc get task buildah -n openshift-pipelines -o yaml | head -40",
                "buildah bud --isolation chroot --storage-driver vfs -t $IMAGE .",
            ],
            redflag=(
                "Do not mount /var/run/docker.sock \"because it is easier\". You have given the pipeline "
                "root on the host."
            ),
            followup="Buildah task OOMKills on RUN dnf install. What do you tune?",
        ),
        Q(
            q="What storage drivers matter for Podman and Buildah, and how do crun and runc differ on RHEL?",
            level=ARCHITECT,
            answer=(
                "Storage drivers control how image layers map to disk: overlay or overlayfs is default on "
                "RHEL with kernel support; vfs is slow but works everywhere including rootless without "
                "fuse-overlayfs; zfs and btrfs exist but are rare in enterprise. containers-storage picks "
                "driver via storage.conf — graphroot, runroot, mountopt for metacopy and force_mask. "
                "Wrong driver choice causes \"cannot mount overlay\" in CI or excessive inode use with vfs. "
                "For runtime, crun is the default low-level OCI runtime on RHEL 9 and RHCOS: written in C, "
                "fast startup, cgroup v2 aware, better for dense pods. runc remains available and is the "
                "reference implementation. CRI-O on OpenShift selects crun; podman --runtime crun matches "
                "node behaviour. Differences matter for seccomp, systemd cgroup delegation, and KPIs like "
                "pod start latency — not day-to-day Dockerfile authoring."
            ),
            analogy=(
                "Storage drivers are filing systems for stacked transparencies; crun versus runc is choosing "
                "which motor spins the projector — same film, different startup time and fuel use."
            ),
            context=(
                "Node incidents with \"no space left on device\" often trace to overlay whiteouts and "
                "abandoned images in /var/lib/containers, not Kubernetes itself. Architects compare crun "
                "vs runc when vendors ask for runc-specific workarounds or when debugging systemd unit "
                "pods on RHEL 9."
            ),
            steps=[
                "Name drivers: overlay preferred, vfs fallback, read storage.conf graphroot.",
                "Explain rootless overlay needs fuse-overlayfs or native overlay mount options.",
                "Contrast crun vs runc: performance, cgroup v2, default on RHEL 9/RHCOS/CRI-O.",
                "Tie to operations: podman system prune, crictl pull failures, monitor /var/lib/containers.",
            ],
            evidence=[
                "grep -E 'driver|graphroot' /etc/containers/storage.conf",
                "crun --version ; runc --version",
                "oc debug node/<node> -- chroot /host crictl info | grep runtime",
            ],
            redflag=(
                "Do not switch an entire CI fleet to vfs without sizing disk and IOPS. It fixes mounts "
                "and melts performance."
            ),
            followup="Nodes fill /var/lib/containers despite image garbage collection. What is your cleanup order?",
        ),
    ],
)
