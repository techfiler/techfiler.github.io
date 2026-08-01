"""Part 8 - Identity, authorisation, workload security and compliance."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=8,
    title="Security, identity and compliance",
    subtitle="Six independent gates, and why collapsing any two of them costs you the offer",
    intro=(
        "Security is the topic where confident vagueness is punished hardest. Interviewers ask about RBAC "
        "and SCC in the same breath specifically to see whether you know they answer different questions - "
        "one is about API calls, the other is about what a pod may be on the node. The same applies to "
        "secrets versus encryption, certificates versus trust, and policy versus enforcement. This part "
        "keeps those gates separate, and it consistently prefers the answer that fixes the workload over the "
        "answer that grants a privilege, because that preference is exactly what is being measured."
    ),
    infographics=["security_layers"],
    questions=[
        Q(
            q="How do users authenticate to OpenShift?",
            level=FOUNDATION,
            answer=(
                "OpenShift runs an integrated OAuth server that issues tokens after delegating the actual "
                "identity check to a configured identity provider - LDAP, OIDC, an enterprise SSO, or "
                "htpasswd for bootstrap. The oc client presents that token on every request, and the API "
                "server maps it to a user and their groups. Group membership from the provider is what "
                "should drive RBAC, so that access follows the corporate directory rather than a local list."
            ),
            analogy=(
                "OAuth is the security desk that issues a visitor badge. It does not decide who you are - it "
                "checks with your employer - and the badge is what every door reads afterwards."
            ),
            context=(
                "The operational point is that authentication and authorisation are separate, and both can "
                "fail independently. A user who can log in but sees nothing has an RBAC problem; a user who "
                "cannot log in at all has an identity provider problem, and the authentication Cluster "
                "Operator will usually say so. The other thing to say is that the kubeadmin bootstrap "
                "credential should be removed once a real provider is configured, because it is an "
                "unattributable cluster-admin account."
            ),
            steps=[
                "Separate the two steps: the identity provider proves who you are, OAuth issues the token.",
                "Bind RBAC to groups from the provider so joiners and leavers are handled by the directory.",
                "Read the authentication Cluster Operator's conditions when logins fail - it names the cause.",
                "Remove the bootstrap kubeadmin account once a real provider is live, and audit who has "
                "cluster-admin.",
            ],
            evidence=[
                "oc get oauth cluster -o yaml | sed -n '/identityProviders/,$p'",
                "oc get co authentication -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get users ; oc get identities ; oc get clusterrolebinding | grep cluster-admin",
            ],
            redflag=(
                "Do not leave kubeadmin in place on a production cluster. It is an anonymous administrator "
                "and it will be found in the first audit."
            ),
            followup="A user can log in but sees no projects. Where do you look?",
        ),
        Q(
            q="Explain RBAC: Role versus ClusterRole, RoleBinding versus ClusterRoleBinding.",
            level=FOUNDATION,
            answer=(
                "A Role is a namespaced set of permissions - verbs on resources within one namespace. A "
                "ClusterRole is the same idea but cluster-scoped, and it is also the only way to grant access "
                "to cluster-scoped resources such as nodes or PersistentVolumes. A RoleBinding grants a role "
                "within one namespace, and importantly it can reference a ClusterRole, which is how you reuse "
                "a standard permission set namespace by namespace. A ClusterRoleBinding grants it everywhere."
            ),
            analogy=(
                "A ClusterRole is a job description; a binding is the employment contract that says where "
                "you do that job. The same job description can apply to one branch or to the whole company."
            ),
            context=(
                "The mistake that shows up in real clusters is using a ClusterRoleBinding when a RoleBinding "
                "would do. Someone needs edit access in one namespace, gets a ClusterRoleBinding to edit, and "
                "now has write access to every namespace in the cluster including platform ones. Because "
                "nothing breaks, nobody notices until an audit. Reviewing ClusterRoleBindings periodically "
                "is one of the highest-value security chores available."
            ),
            steps=[
                "Define the four objects and which of them are namespaced.",
                "Highlight the useful pattern: RoleBinding referencing a ClusterRole for reusable "
                "permission sets.",
                "Explain why cluster-scoped resources require a ClusterRole.",
                "Audit ClusterRoleBindings regularly and bind to groups rather than individual users.",
            ],
            evidence=[
                "oc auth can-i --list --as=<user> -n <ns>",
                "oc get clusterrolebinding -o wide | grep -v 'system:'",
                "oc describe clusterrole <role> | head -30",
            ],
            redflag=(
                "Do not grant cluster-admin to solve a namespace-scoped permission problem. It is fast, it "
                "works, and it is the finding that ends up in the report."
            ),
            followup="Someone needs to read pods in every namespace. Which objects do you create?",
        ),
        Q(
            q="How do RBAC and Security Context Constraints solve different problems?",
            level=FOUNDATION,
            answer=(
                "RBAC answers \"what API calls may this identity make?\" - can you create a pod, read a "
                "secret, delete a deployment. SCC answers \"what may this pod actually be on the node?\" - "
                "which UID it runs as, whether it can escalate privileges, which capabilities and volume "
                "types it may use, whether it can touch host namespaces. You can have permission to create a "
                "pod and still have that pod rejected because it asked to run as root."
            ),
            analogy=(
                "RBAC is whether you are allowed to book the meeting room. SCC is what you are allowed to do "
                "once you are inside it - and no amount of booking permission lets you drill into the wall."
            ),
            context=(
                "This distinction is asked in almost every OpenShift interview, and the tell is a candidate "
                "who tries to solve an SCC rejection with RBAC or vice versa. When a pod is rejected because "
                "it requests a UID or privilege the SCC does not allow, the right response is to fix the "
                "workload so it runs under restricted-v2 - and only if that is truly impossible, create a "
                "narrowly scoped custom SCC bound to one ServiceAccount, never a broad grant of privileged."
            ),
            steps=[
                "State the two questions each control answers, in one sentence each.",
                "Give the concrete case: permission to create a pod, rejection because of its security "
                "context.",
                "Explain how SCC selection works - it is matched against the pod's ServiceAccount.",
                "Give the escalation ladder: fix the image, then a narrow custom SCC, never blanket "
                "privileged.",
            ],
            evidence=[
                "oc get scc ; oc describe scc restricted-v2 | head -30",
                "oc get pod <pod> -o jsonpath='{.metadata.annotations.openshift\\.io/scc}{\"\\n\"}'",
                "oc adm policy who-can use scc privileged",
            ],
            redflag=(
                "Do not describe SCC as \"RBAC for pods\". They are orthogonal, and the interviewer is "
                "listening for exactly that word."
            ),
            followup="A pod is rejected with a UID range error. Walk me through your options in order.",
        ),
        Q(
            q="What is a Secret, and how is it different from a ConfigMap?",
            level=FOUNDATION,
            answer=(
                "Both hold key-value configuration data and both can be mounted as files or exposed as "
                "environment variables. A Secret is intended for sensitive data: it is base64-encoded in the "
                "API, can be encrypted at rest in etcd, is not shown by default in some tooling, and has its "
                "own RBAC surface so you can grant access to config without granting access to credentials. "
                "Base64 is encoding, not encryption, and that distinction matters."
            ),
            analogy=(
                "A ConfigMap is a note on the noticeboard. A Secret is a note in a locked drawer - but the "
                "drawer is only locked if someone actually turned the key."
            ),
            context=(
                "The practical guidance is about handling rather than the object. Secrets mounted as files "
                "are safer than environment variables, because environment variables leak into crash dumps, "
                "process listings and logs. Secrets should never be committed to Git, which is why external "
                "secret operators and sealed secrets exist. And etcd encryption at rest needs to be enabled "
                "deliberately - it is not on by default."
            ),
            steps=[
                "State what is genuinely different: RBAC surface, encryption-at-rest option, tooling "
                "treatment.",
                "Be explicit that base64 is encoding and provides no protection.",
                "Prefer file mounts over environment variables, and explain why.",
                "Describe how secrets get into the cluster safely - external secret manager or sealed "
                "secrets, never plaintext in Git.",
            ],
            evidence=[
                "oc get secret <name> -o jsonpath='{.data}' | python3 -m json.tool",
                "oc get apiserver cluster -o jsonpath='{.spec.encryption.type}{\"\\n\"}'",
                "oc get rolebinding -n <ns> -o wide | grep secret",
            ],
            redflag=(
                "Do not say Secrets are encrypted. They are base64-encoded, and encryption at rest is a "
                "separate setting you must enable."
            ),
            followup="How do secrets reach the cluster in your GitOps workflow?",
        ),
        Q(
            q="What does the restricted-v2 SCC enforce?",
            level=FOUNDATION,
            answer=(
                "restricted-v2 is the default SCC for most workloads and it enforces the baseline that a "
                "well-behaved container should already meet: run as a non-root, arbitrarily assigned UID from "
                "the namespace's range, no privilege escalation, all Linux capabilities dropped, the default "
                "seccomp profile applied, no host namespaces, host network or host paths, and only safe "
                "volume types. It is deliberately strict so that the safe option is the automatic one."
            ),
            analogy=(
                "It is the standard building fire code. Nobody argues about it per room - the constraints "
                "are the same for everyone, and exceptions require a documented case."
            ),
            context=(
                "The reason this matters in interviews is that it is where most vendor images fail, and the "
                "response distinguishes candidates. An image that hardcodes a UID or writes to a directory "
                "owned by a fixed user will be rejected, and the correct sequence is to make the image "
                "arbitrary-UID friendly - group-writable paths owned by the root group - rather than to "
                "escalate the pod's privileges. Every escalation is permanent in practice, because nobody "
                "ever comes back to remove it."
            ),
            steps=[
                "List what it enforces, grouping into identity, privilege, capabilities and host access.",
                "Explain the arbitrary UID model and why images must be written for it.",
                "Give the correct remediation order when a workload fails admission.",
                "Note that exceptions should be narrow, bound to one ServiceAccount, documented and "
                "reviewed.",
            ],
            evidence=[
                "oc describe scc restricted-v2",
                "oc get ns <ns> -o jsonpath='{.metadata.annotations.openshift\\.io/sa\\.scc\\.uid-range}{\"\\n\"}'",
                "oc get pod <pod> -o jsonpath='{.spec.securityContext}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not reach for anyuid as the standard fix. It is a five-minute shortcut that becomes a "
                "permanent exception."
            ),
            followup="A vendor image writes to /var/lib/app as UID 1001. What do you do?",
        ),
        Q(
            q="What do allowPrivilegeEscalation: false and dropping capabilities actually achieve?",
            level=INTERMEDIATE,
            answer=(
                "allowPrivilegeEscalation false sets the no-new-privileges flag on the process, so it cannot "
                "gain more privileges than it started with - setuid binaries and file capabilities stop "
                "working as an escalation path. Dropping capabilities removes specific kernel privileges from "
                "the process, such as changing network configuration or loading modules. Together they mean "
                "that even a compromised process inside the container has very little to work with."
            ),
            analogy=(
                "It is confiscating the master key and the ladder before letting a contractor into the "
                "building. They can still do their job; they just cannot reach the roof."
            ),
            context=(
                "The practical value is in reducing what an exploited application can do next. Most container "
                "escapes in the wild depend on either a capability that was never needed or a setuid path "
                "that was never removed. Dropping ALL and adding back only what is demonstrably required is "
                "the standard, and the exercise of finding out what is required usually reveals that the "
                "answer is nothing."
            ),
            steps=[
                "Explain no-new-privileges and what escalation paths it closes.",
                "Explain capabilities as fine-grained slices of root, and the drop-ALL-then-add-back "
                "practice.",
                "Give a legitimate example that needs a capability, such as binding a low port, and the "
                "alternative.",
                "Enforce it through the SCC rather than trusting each manifest to get it right.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.containers[0].securityContext}' | python3 -m json.tool",
                "oc describe scc restricted-v2 | grep -i -A3 capabilities",
                "oc debug node/<node> -- chroot /host grep CapEff /proc/<pid>/status",
            ],
            redflag=(
                "Do not add NET_ADMIN or SYS_ADMIN because an application \"needs networking\". Almost "
                "nothing legitimately needs those."
            ),
            followup="An application needs to bind port 80. What are your options besides a capability?",
        ),
        Q(
            q="What is the seccomp RuntimeDefault profile?",
            level=INTERMEDIATE,
            answer=(
                "seccomp filters which system calls a process may make. RuntimeDefault applies the container "
                "runtime's curated profile, which blocks the syscalls that normal application workloads never "
                "use but that exploits frequently rely on. It is a cheap, broad reduction in kernel attack "
                "surface, it is part of the restricted-v2 baseline, and it very rarely breaks anything "
                "because the blocked calls are genuinely unusual."
            ),
            analogy=(
                "It is a menu rather than an open kitchen. You can order anything a normal customer would "
                "want; you cannot walk in and use the gas line."
            ),
            context=(
                "When seccomp does break something the failure is distinctive - the process dies with a "
                "signal or gets EPERM on an unusual syscall, and the node's audit log records the blocked "
                "call. The correct response is a custom profile that permits that specific syscall, not "
                "Unconfined, which removes the entire filter. Being able to describe that debugging path is "
                "what makes this more than a definition."
            ),
            steps=[
                "Define seccomp as syscall filtering and RuntimeDefault as the runtime's curated profile.",
                "Say why it is low risk - the blocked calls are rare in application code.",
                "Describe the failure signature and how to identify the blocked syscall from audit logs.",
                "Fix with a narrow custom profile; never fall back to Unconfined as the default.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.securityContext.seccompProfile}{\"\\n\"}'",
                "oc debug node/<node> -- chroot /host ausearch -m seccomp -ts recent",
                "oc describe scc restricted-v2 | grep -i seccomp",
            ],
            redflag=(
                "Do not set seccompProfile to Unconfined to make a problem go away. You have removed the "
                "control rather than adjusted it."
            ),
            followup="A workload dies with a signal after enabling RuntimeDefault. How do you find out why?",
        ),
        Q(
            q="What is etcd encryption at rest, and what does it protect?",
            level=INTERMEDIATE,
            answer=(
                "It encrypts sensitive API resources - Secrets, ConfigMaps and a few others - before they are "
                "written to etcd, so the data on disk and in etcd backups is not readable in plaintext. It "
                "protects against someone obtaining the disk, a snapshot or a backup file. It does not "
                "protect against anyone with API access and RBAC permission to read the Secret, because the "
                "API server decrypts on read."
            ),
            analogy=(
                "It is a safe in the records room. It stops someone who steals the filing cabinet; it does "
                "nothing about the person who is legitimately allowed to open it."
            ),
            context=(
                "Being precise about that boundary is the whole point of the question. Teams sometimes enable "
                "encryption at rest and consider secret management solved, when the far more likely exposure "
                "is over-broad RBAC or a secret printed into application logs. It is worth enabling - it is a "
                "simple, supported setting and it materially improves backup safety - but it belongs "
                "alongside least-privilege RBAC and external secret management, not instead of them."
            ),
            steps=[
                "Explain what is encrypted and at what point in the write path.",
                "State the threat model it addresses: stolen disks, snapshots and backups.",
                "State what it does not address: authorised API reads and leaked secrets in logs.",
                "Enable it, then verify the migration completed and re-check backup handling procedures.",
            ],
            evidence=[
                "oc get apiserver cluster -o jsonpath='{.spec.encryption.type}{\"\\n\"}'",
                "oc get co kube-apiserver -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get secret -A | wc -l   # scope of the migration",
            ],
            redflag=(
                "Do not claim encryption at rest protects secrets from users. It protects them from disks."
            ),
            followup="Where would you store the credentials that the cluster itself needs to bootstrap?",
        ),
        Q(
            q="How do ServiceAccount tokens work securely?",
            level=INTERMEDIATE,
            answer=(
                "Modern tokens are projected into the pod by the kubelet: they are short-lived, bound to a "
                "specific audience, and bound to the pod's lifetime, so they are automatically rotated and "
                "become useless once the pod is gone. That replaces the old model of a permanent token stored "
                "in a Secret, which never expired and which anyone with read access to that Secret could use "
                "indefinitely."
            ),
            analogy=(
                "It is a day pass that expires at 5pm and only opens the doors on your floor, instead of a "
                "master key that works forever and can be copied."
            ),
            context=(
                "Two operational habits follow. First, disable automounting for workloads that never call "
                "the API - most applications do not need a token at all, and mounting one is free attack "
                "surface. Second, when integrating an external system, use a dedicated ServiceAccount with a "
                "narrow role and a bound token rather than creating a long-lived token Secret, because those "
                "are exactly what turns up in a repository six months later."
            ),
            steps=[
                "Describe the projected token model: short-lived, audience-bound, rotated automatically.",
                "Contrast it with legacy long-lived token Secrets and the risk they carry.",
                "Set automountServiceAccountToken false for workloads that do not call the API.",
                "For external integrations, use a dedicated ServiceAccount with least privilege and audit "
                "its use.",
            ],
            evidence=[
                "oc get pod <pod> -o jsonpath='{.spec.volumes[?(@.projected)]}' | python3 -m json.tool",
                "oc get sa <sa> -o jsonpath='{.secrets}{\"\\n\"}'   # legacy tokens if any remain",
                "oc auth can-i --list --as=system:serviceaccount:<ns>:<sa>",
            ],
            redflag=(
                "Do not create long-lived ServiceAccount token Secrets for convenience. They are permanent "
                "credentials with no expiry and no rotation."
            ),
            followup="An external CI system needs to deploy into one namespace. How do you set that up?",
        ),
        Q(
            q="How do service serving certificates work?",
            level=INTERMEDIATE,
            answer=(
                "You annotate a Service, and the service CA operator issues a certificate for that Service's "
                "internal DNS name and puts it in a Secret, which the workload mounts. Clients trust it by "
                "mounting the service CA bundle, which is injected into a ConfigMap by another annotation. "
                "The operator rotates the certificates automatically. It is the simple way to get internal "
                "TLS between cluster services without running your own PKI."
            ),
            analogy=(
                "It is an in-house pass office. Staff get their own passes issued and renewed automatically, "
                "and everyone in the building already trusts the office that issues them."
            ),
            context=(
                "The value is that it removes the most common excuse for unencrypted internal traffic, which "
                "is that certificate management is painful. The thing to know operationally is that these "
                "certificates are only trusted inside the cluster - they are not for external clients, who "
                "need a certificate from a public or corporate CA. Mixing those two up produces trust errors "
                "that look like application bugs."
            ),
            steps=[
                "Describe the annotation on the Service and the Secret it produces.",
                "Describe the CA bundle injection annotation on the client side.",
                "Note that rotation is automatic, and that workloads must reload certificates or be "
                "restarted.",
                "State the boundary: internal trust only; external clients need a corporate or public CA.",
            ],
            evidence=[
                "oc annotate svc <svc> service.beta.openshift.io/serving-cert-secret-name=<secret>",
                "oc get secret <secret> -o jsonpath='{.data.tls\\.crt}' | base64 -d | openssl x509 -noout -dates",
                "oc get cm <bundle-cm> -o jsonpath='{.data.service-ca\\.crt}' | head -5",
            ],
            redflag=(
                "Do not offer service serving certificates to external clients. Nothing outside the cluster "
                "trusts that CA."
            ),
            followup="An internal client gets a certificate trust error after rotation. What happened?",
        ),
        Q(
            q="What are admission webhooks and how do they affect reliability?",
            level=INTERMEDIATE,
            answer=(
                "Admission webhooks are external services the API server calls during admission - mutating "
                "ones can modify an object, validating ones can reject it. They are how policy engines, "
                "service meshes and many operators enforce rules. The reliability catch is failurePolicy: "
                "with Fail, if the webhook is unavailable the API server rejects the affected requests, so an "
                "unhealthy webhook can block object creation cluster-wide."
            ),
            analogy=(
                "It is a compulsory inspection step on the production line. If the inspector does not turn "
                "up and the rule says nothing ships uninspected, the whole line stops."
            ),
            context=(
                "This produces one of the most alarming failure modes in Kubernetes: a webhook whose pods are "
                "down, with failurePolicy Fail and a broad rule scope, means nobody can create pods - "
                "including the pods that would restore the webhook. Mitigations are namespace exclusions for "
                "system namespaces, tight timeouts, narrow scoping so the webhook only sees what it needs, "
                "and running the webhook itself with high availability."
            ),
            steps=[
                "Define mutating and validating webhooks and where they sit in the admission chain.",
                "Explain failurePolicy and the deadlock it can create when set to Fail.",
                "Scope narrowly by namespace, resource and operation, and set short timeouts.",
                "Exclude platform namespaces so a broken webhook cannot block cluster recovery.",
            ],
            evidence=[
                "oc get validatingwebhookconfiguration,mutatingwebhookconfiguration",
                "oc get validatingwebhookconfiguration <name> -o jsonpath='{.webhooks[*].failurePolicy}{\"\\n\"}'",
                "oc get events -A --field-selector reason=FailedCreate | grep -i webhook",
            ],
            redflag=(
                "Do not deploy a cluster-wide webhook with failurePolicy Fail and no namespace exclusions. "
                "You have built a single point of failure into object creation."
            ),
            followup="No pods can be created cluster-wide and a webhook is suspected. What do you do?",
        ),
        Q(
            q="A vendor asks for the privileged SCC. How do you respond?",
            level=SENIOR,
            answer=(
                "I ask what specifically fails, because \"needs privileged\" is almost always a guess. Then I "
                "work up the ladder: fix the image so it runs as an arbitrary UID, then grant only the "
                "specific capability, host path or volume type it genuinely needs through a narrow custom SCC "
                "bound to one ServiceAccount in one namespace. Privileged is a last resort with a documented "
                "risk acceptance, an expiry date and compensating controls such as a dedicated node pool."
            ),
            analogy=(
                "Somebody asking for the master key to every door usually needs one cupboard opened. You find "
                "out which cupboard first."
            ),
            context=(
                "This question is really a test of how you handle pressure from a delivery deadline. The "
                "answer that scores is the one that offers a path forward rather than a flat refusal - a "
                "temporary, narrowly scoped exception on a dedicated node pool, with a ticket to fix the "
                "image, keeps the project moving without permanently weakening the cluster. Refusing "
                "outright and granting immediately are both wrong for the same reason: neither engages with "
                "the actual requirement."
            ),
            steps=[
                "Get the evidence: the exact admission error, the syscall, the path or the port involved.",
                "Try the image fix first - arbitrary UID, group-writable paths, no root requirement.",
                "If a genuine privilege is needed, write a custom SCC granting only that, bound to one "
                "ServiceAccount.",
                "If privileged is unavoidable, isolate on dedicated nodes, document risk acceptance with an "
                "owner and expiry, and monitor its use.",
            ],
            evidence=[
                "oc get events -n <ns> | grep -i 'unable to validate against any security context constraint'",
                "oc adm policy who-can use scc privileged",
                "oc get pod <pod> -o jsonpath='{.metadata.annotations.openshift\\.io/scc}{\"\\n\"}'",
            ],
            redflag=(
                "Do not grant privileged to unblock a deadline. It never gets removed, and it will be "
                "attributed to you in the audit."
            ),
            followup="They say the vendor will not change the image and go live is Friday. Now what?",
        ),
        Q(
            q="How do you manage and rotate secrets across the platform?",
            level=SENIOR,
            answer=(
                "I keep the source of truth outside the cluster in a secret manager, and sync into Kubernetes "
                "Secrets through an operator so nothing sensitive is ever in Git. Rotation is driven by the "
                "manager on a schedule, and workloads either reload the mounted file or are restarted "
                "deliberately by the sync controller. Access is least-privilege per namespace, etcd "
                "encryption is on, and I audit who reads secrets rather than assuming RBAC is correct."
            ),
            analogy=(
                "It is a key cabinet with a sign-out log, not a bowl of keys by the door. Keys are reissued "
                "on a schedule, and you can tell who took which one."
            ),
            context=(
                "Rotation is where most designs quietly fail, because rotating the secret is easy and getting "
                "the application to pick it up is not. Applications that read a secret once at startup keep "
                "using the old value until they restart, so rotation without a restart strategy produces a "
                "false sense of security - and rotation with an unplanned restart produces an outage. "
                "Deciding that behaviour per workload, in advance, is the real work."
            ),
            steps=[
                "Keep the authoritative secret outside the cluster; sync in, never commit to Git.",
                "Define rotation cadence per secret class and the propagation mechanism for each workload.",
                "Decide per application whether it reloads or needs a controlled restart, and automate that.",
                "Enable encryption at rest, restrict read access per namespace, and audit secret reads.",
            ],
            evidence=[
                "oc get externalsecret,secretstore -A   # or the equivalent operator objects",
                "oc get secret <name> -o jsonpath='{.metadata.annotations}' | python3 -m json.tool",
                "Audit log query for get and list on secrets, grouped by identity",
            ],
            redflag=(
                "Do not put secrets in Git, even encrypted, without a clear key management story. \"It is "
                "encrypted\" is not an answer if the key is in the same repository."
            ),
            followup="You rotate a database password. Walk me through what happens to the running pods.",
        ),
        Q(
            q="How do you manage certificates, and how do you troubleshoot a certificate problem?",
            level=SENIOR,
            answer=(
                "I separate the three families: internal platform certificates that OpenShift rotates itself, "
                "service serving certificates issued by the service CA operator, and external certificates "
                "for routes and APIs that come from a corporate or public CA. For troubleshooting I check "
                "what the server actually presents, its dates and chain, whether the client trusts the "
                "issuer, and whether the name matches - and I always test from the same network position as "
                "the failing client."
            ),
            analogy=(
                "A certificate problem is a passport problem: it is either expired, issued by an authority "
                "the officer does not recognise, or it has the wrong name on it. Three checks, in that "
                "order."
            ),
            context=(
                "Expiry is the one that causes real incidents, because it is silent until the moment it is "
                "not, and it tends to hit at the worst time - a cluster that has been powered off past its "
                "certificate rotation window, or a route certificate nobody owned after a team reorganised. "
                "The prevention is boring and effective: an inventory of every externally managed "
                "certificate with owner and expiry, plus alerts at thirty and seven days."
            ),
            steps=[
                "Classify the certificate: platform-managed, service CA, or externally issued.",
                "Inspect what the server presents - subject, SAN, issuer, validity dates - from the client's "
                "position.",
                "Check the client's trust store and whether the full chain is being served.",
                "Renew through the owning mechanism, then verify; maintain an inventory with expiry alerts "
                "for anything external.",
            ],
            evidence=[
                "openssl s_client -connect <host>:443 -servername <host> </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates",
                "oc get csr | grep -i pending   # node certificates awaiting approval",
                "oc get secret -A -o json | jq -r '.items[]|select(.type==\"kubernetes.io/tls\")|.metadata.namespace+\"/\"+.metadata.name'",
            ],
            redflag=(
                "Do not tell clients to skip verification to get past a certificate error. You have turned a "
                "known problem into an invisible one."
            ),
            followup="The cluster was powered off for six weeks. What certificate problems do you expect?",
        ),
        Q(
            q="How do you secure the container image supply chain?",
            level=SENIOR,
            answer=(
                "End to end: build from approved base images in a controlled pipeline, scan for "
                "vulnerabilities and fail the build on policy, generate an SBOM, sign the image, push to a "
                "trusted registry, and enforce at admission that only signed images from allowed registries "
                "may run, referenced by digest. Then promote the same digest through environments rather than "
                "rebuilding, so what was tested is what runs."
            ),
            analogy=(
                "It is food safety in a restaurant: approved suppliers, inspection on arrival, a label on "
                "every batch, and a rule that nothing unlabelled goes on a plate."
            ),
            context=(
                "The step teams skip is enforcement. Scanning and signing produce reports and signatures that "
                "nobody checks at runtime, so an unsigned image from a random registry still runs. Admission "
                "policy is what turns the pipeline's work into an actual control. The other frequently "
                "missing piece is the response process - a scan result is only useful if there is an agreed "
                "path from finding to rebuild to redeploy, with a deadline."
            ),
            steps=[
                "Control the inputs: approved, pinned base images and a controlled build environment.",
                "Scan and generate an SBOM in the pipeline, with policy that fails the build.",
                "Sign the image and promote the identical digest across environments.",
                "Enforce at admission - allowed registries, signature required, digest references - and "
                "define the remediation process with deadlines.",
            ],
            evidence=[
                "oc get image.config.openshift.io cluster -o jsonpath='{.spec.registrySources}' | python3 -m json.tool",
                "cosign verify <registry>/<image>@sha256:<digest>",
                "oc get pods -A -o jsonpath='{range .items[*]}{.spec.containers[*].image}{\"\\n\"}{end}' | grep -v '@sha256' | head",
            ],
            redflag=(
                "Do not describe scanning as your supply chain security. Without admission enforcement it is "
                "a report, not a control."
            ),
            followup="A critical CVE lands in your base image. Walk me through the next four hours.",
        ),
        Q(
            q="How do audit logs support security and operations?",
            level=SENIOR,
            answer=(
                "The API server audit log records who did what, to which object, when, and what the outcome "
                "was. It is how you answer questions that nothing else can: who deleted this namespace, who "
                "read this secret, which ServiceAccount is generating the request storm. The policy is "
                "tunable, because logging every request at full fidelity is expensive, and logs should be "
                "forwarded off-cluster so they survive the incident they describe."
            ),
            analogy=(
                "It is the building's access log. Nobody reads it on a normal day, and it is the only thing "
                "that answers the question after something goes missing."
            ),
            context=(
                "The operational uses are broader than security. Audit logs are how you find the client "
                "hammering the API server, how you attribute a surprise configuration change during an "
                "incident, and how you prove a control was in force during an audit. The two design decisions "
                "that matter are the audit profile - default, write-request bodies, or all-request bodies - "
                "and forwarding, because logs stored only on the control plane are lost in exactly the "
                "scenarios you care about."
            ),
            steps=[
                "Explain what an audit event contains and the levels available.",
                "Set an audit profile that balances fidelity against volume, and document the choice.",
                "Forward off-cluster with retention that matches your compliance requirement.",
                "Practise the queries you will need under pressure: who deleted X, who read secret Y, which "
                "identity is generating this load.",
            ],
            evidence=[
                "oc get apiserver cluster -o jsonpath='{.spec.audit.profile}{\"\\n\"}'",
                "oc adm node-logs <master> --path=kube-apiserver/audit.log | tail -5",
                "Query: verb=delete, resource=namespaces, sorted by timestamp with user attribution",
            ],
            redflag=(
                "Do not rely on audit logs that are only stored on the control plane. If you lose the "
                "cluster you lose the evidence."
            ),
            followup="A production namespace vanished overnight. How do you find out who and when?",
        ),
        Q(
            q="How does the Compliance Operator fit into a governance programme?",
            level=ARCHITECT,
            answer=(
                "It runs benchmark-based scans against the cluster and its nodes - CIS, PCI and similar "
                "profiles - and reports each rule as pass, fail or not applicable, with remediation content "
                "for many findings. The value is that compliance becomes continuous and evidence-based "
                "rather than an annual spreadsheet exercise. The judgement it requires is deciding which "
                "findings to remediate, which to accept with justification, and which are false positives "
                "for your architecture."
            ),
            analogy=(
                "It is a standing health inspection rather than a once-a-year visit. The point is not the "
                "certificate on the wall; it is that problems are found in days rather than months."
            ),
            context=(
                "The trap is auto-applying every remediation. Some benchmark rules conflict with how a "
                "platform is legitimately operated, and blind remediation can break authentication, "
                "monitoring or node configuration. The mature pattern is to scan continuously, triage into "
                "remediate, accept-with-justification and not-applicable, apply remediations through the "
                "normal change process, and track the exception register as a living document with owners "
                "and review dates."
            ),
            steps=[
                "Select the profiles that match the actual regulatory obligation, not every available one.",
                "Scan on a schedule and triage findings into remediate, accept or not-applicable.",
                "Apply remediations through change control, in a non-production cluster first.",
                "Maintain an exception register with owner, justification and review date, and report trend "
                "rather than raw counts.",
            ],
            evidence=[
                "oc get compliancescan,compliancecheckresult -n openshift-compliance | head -20",
                "oc get compliancecheckresult -n openshift-compliance -l compliance.openshift.io/check-status=FAIL",
                "Exception register with owner, justification and next review date",
            ],
            redflag=(
                "Do not auto-remediate everything a scanner reports. Some rules will break your cluster, and "
                "the scanner does not know your architecture."
            ),
            followup="A benchmark rule conflicts with how your monitoring works. How do you handle it?",
        ),
        Q(
            q="How would you design the security model for a multi-tenant cluster?",
            level=ARCHITECT,
            answer=(
                "In layers, with each one independently defensible. Identity from the corporate directory "
                "with RBAC bound to groups. Namespaces as the tenancy unit with quota, LimitRange and "
                "default-deny NetworkPolicy applied automatically. restricted-v2 as the baseline with "
                "exceptions narrow, owned and time-boxed. Supply chain enforcement at admission. Egress "
                "control and audit logging forwarded off-cluster. And a clear, written line where soft "
                "tenancy stops and a separate cluster starts."
            ),
            analogy=(
                "It is a shared office building with real security: one directory of who works here, locks "
                "on each floor, rules about what tenants may install, deliveries checked at the door, and "
                "cameras that record."
            ),
            context=(
                "The architectural judgement being tested is knowing the limit of the model. Namespaces plus "
                "policy is genuinely strong for teams within one organisation who are not adversarial. It is "
                "not sufficient for untrusted code or for tenants with incompatible regulatory obligations, "
                "and pretending otherwise is how organisations end up with a security incident that was "
                "predictable from the architecture diagram. Saying where the line is - and what you would do "
                "on the other side of it - is the answer."
            ),
            steps=[
                "Layer the controls: identity, authorisation, workload constraints, network, supply chain, "
                "audit.",
                "Automate the per-namespace baseline so no tenant can exist without it.",
                "Define exception handling: narrow scope, named owner, expiry, compensating control.",
                "State the escalation criteria to dedicated nodes or a separate cluster, and price both "
                "options honestly.",
            ],
            evidence=[
                "Namespace conformance report: quota, LimitRange, NetworkPolicy, SCC exceptions",
                "oc get clusterrolebinding -o wide | grep -v 'system:'   # standing privilege review",
                "Exception register and audit log forwarding status",
            ],
            redflag=(
                "Do not claim namespaces give you hard multi-tenancy. The follow-up question is always about "
                "untrusted workloads, and there is only one honest answer."
            ),
            followup="A tenant runs untrusted customer-supplied code. Does your model still hold?",
        ),
    ],
)
