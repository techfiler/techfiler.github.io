"""Part 5 - Service networking, DNS and ingress."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=5,
    title="Services, DNS and ingress",
    subtitle="Following one request from the browser to the container, and back",
    intro=(
        "Networking questions are the fastest way for an interviewer to find out whether you have actually "
        "operated a cluster. Anyone can define a Service. Far fewer people can say, without hesitating, "
        "which seven things stand between a browser and a container and what each one looks like when it "
        "breaks. That path - DNS, load balancer, router, Service, EndpointSlice, network policy, container - "
        "is the backbone of this part. Learn it in order and you will diagnose most outages faster than the "
        "person asking the question."
    ),
    infographics=["request_path"],
    questions=[
        Q(
            q="What is a Service, and what does ClusterIP give you?",
            level=FOUNDATION,
            answer=(
                "A Service is a stable virtual address in front of a changing set of pods. Pods come and go "
                "with new IPs on every restart, so the Service gives you one name and one ClusterIP that "
                "stays put, plus a label selector that decides which pods are behind it. The ClusterIP is "
                "virtual - nothing listens on it - and traffic sent to it is rewritten to a real pod IP by "
                "the node's datapath."
            ),
            analogy=(
                "It is a company's main phone number. Staff change, desks move, extensions get reassigned - "
                "the number on the letterhead does not."
            ),
            context=(
                "Two things follow that matter in incidents. First, because the ClusterIP is virtual, you "
                "cannot ping your way to a diagnosis - a Service with no matching pods answers nothing at all "
                "while looking perfectly healthy in oc get svc. Second, the selector is the whole "
                "relationship: change a pod label or a Service selector by one character and traffic stops, "
                "with no error anywhere except an empty EndpointSlice."
            ),
            steps=[
                "Define the problem it solves: stable identity in front of ephemeral pods.",
                "Explain the selector-to-endpoint relationship, because that is where failures live.",
                "Note that the ClusterIP is virtual and implemented in the datapath, not by a process.",
                "Give the first check when a Service seems dead: does its EndpointSlice have any addresses?",
            ],
            evidence=[
                "oc get svc <svc> -o jsonpath='{.spec.selector}{\"\\n\"}'",
                "oc get endpointslice -n <ns> -l kubernetes.io/service-name=<svc> -o yaml | head -40",
                "oc get pods -n <ns> --show-labels",
            ],
            redflag=(
                "Do not say a Service \"load balances between pods\" and stop there. The selector and "
                "readiness relationship is the part that fails."
            ),
            followup="A Service has no endpoints but the pods are Running. Give me two causes.",
        ),
        Q(
            q="What are the Service types and when do you use each?",
            level=FOUNDATION,
            answer=(
                "ClusterIP is internal-only and the default. NodePort exposes the Service on a port on every "
                "node, which is mostly a building block rather than something you expose to users. "
                "LoadBalancer asks the infrastructure for an external load balancer and is how you expose "
                "non-HTTP traffic. ExternalName is just a DNS CNAME to something outside the cluster. On "
                "OpenShift, HTTP and HTTPS normally go through a Route rather than any of these."
            ),
            analogy=(
                "ClusterIP is an internal extension, NodePort is a side door with a number on it, "
                "LoadBalancer is a public reception desk, and ExternalName is a sign that says the office you "
                "want is in another building."
            ),
            context=(
                "The design point interviewers listen for is that LoadBalancer Services cost real money and "
                "real IP addresses - one per Service on most clouds - which is exactly why HTTP traffic is "
                "consolidated behind an ingress layer. Reaching for LoadBalancer per application is a common "
                "and expensive pattern in teams migrating from a per-service load balancer world."
            ),
            steps=[
                "List the four types with one sentence of purpose each.",
                "State the OpenShift default for HTTP: Route through the shared ingress layer.",
                "Explain when LoadBalancer is genuinely right - non-HTTP protocols, or dedicated ingress.",
                "Mention the cost and IP consumption trade-off, because that is the design conversation.",
            ],
            evidence=[
                "oc get svc -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,TYPE:.spec.type",
                "oc get svc <svc> -o jsonpath='{.status.loadBalancer}' | python3 -m json.tool",
                "oc get route -A | head",
            ],
            redflag=(
                "Do not propose a LoadBalancer Service per application for HTTP. It is what the router layer "
                "exists to avoid."
            ),
            followup="A team needs to expose a TCP database port externally. What do you recommend?",
        ),
        Q(
            q="What is an EndpointSlice and why did it replace Endpoints?",
            level=FOUNDATION,
            answer=(
                "An EndpointSlice lists the actual pod IPs and ports currently behind a Service, along with "
                "readiness and topology information. It replaced the older Endpoints object because a single "
                "Endpoints object had to contain every backend, so any change rewrote the whole thing and "
                "every node received the full update. Slices chunk that into pieces, which scales far better "
                "on large Services."
            ),
            analogy=(
                "It is the difference between reprinting the entire phone book because one person moved, and "
                "reprinting only the page they were on."
            ),
            context=(
                "For troubleshooting, EndpointSlice is the single most useful object in the request path. "
                "Only pods that pass their readiness probe appear as ready addresses, so an empty or all-"
                "unready slice immediately tells you whether the problem is routing or the application. That "
                "one check separates a router or DNS problem from a workload problem in about five seconds."
            ),
            steps=[
                "Define it as the live backend list for a Service, including readiness.",
                "Explain the scaling motivation versus the old Endpoints object.",
                "Show the diagnostic use: empty slice means selector or readiness, not networking.",
                "Mention topology hints, which allow zone-aware routing on supported setups.",
            ],
            evidence=[
                "oc get endpointslice -n <ns> -l kubernetes.io/service-name=<svc>",
                "oc get endpointslice <slice> -o jsonpath='{.endpoints[*].conditions.ready}{\"\\n\"}'",
                "oc get pods -n <ns> -o wide --show-labels",
            ],
            redflag=(
                "Do not troubleshoot a Service without looking at its EndpointSlice. You will spend an hour "
                "on the network for a readiness problem."
            ),
            followup="The slice lists three addresses, all with ready false. What does that tell you?",
        ),
        Q(
            q="What is a Route, and how does it differ from an Ingress?",
            level=FOUNDATION,
            answer=(
                "A Route is OpenShift's native ingress object. It maps a hostname and path to a Service, and "
                "the OpenShift router - HAProxy, managed by the Ingress Operator - implements it. Ingress is "
                "the portable Kubernetes object that does a similar job; on OpenShift an Ingress is converted "
                "into a Route behind the scenes. Routes expose OpenShift-specific capabilities directly, such "
                "as re-encrypt termination and weighted backends for canary traffic."
            ),
            analogy=(
                "Ingress is the international standard plug; a Route is the local socket that has been "
                "wired in for years and has a few extra pins."
            ),
            context=(
                "In practice you use whichever fits the portability requirement. A team that deploys to both "
                "OpenShift and vanilla Kubernetes should write Ingress and accept the smaller feature set. A "
                "team that lives on OpenShift gets more from Routes - especially weighted backends, which "
                "give you canary releases without installing a service mesh. Knowing that Ingress is "
                "translated into Routes explains why you sometimes see Routes nobody created."
            ),
            steps=[
                "Define Route as the OpenShift-native ingress object implemented by HAProxy.",
                "State the translation: Ingress objects become Routes on OpenShift.",
                "Name what Routes add - termination modes, weighted backends, per-route annotations.",
                "Choose based on portability requirements and say so explicitly.",
            ],
            evidence=[
                "oc get route -n <ns> -o wide",
                "oc get ingress -n <ns> ; oc get route -n <ns> -o jsonpath='{.items[*].metadata.ownerReferences[*].kind}{\"\\n\"}'",
                "oc get route <route> -o jsonpath='{.status.ingress[*].conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not say Routes and Ingress are interchangeable. The differences show up exactly when you "
                "need re-encrypt or weighting."
            ),
            followup="How would you do a 10% canary release using only Route features?",
        ),
        Q(
            q="How does DNS work inside an OpenShift cluster?",
            level=FOUNDATION,
            answer=(
                "CoreDNS runs as the cluster DNS service, managed by the DNS Operator, and every pod's "
                "resolv.conf points at it. Services get records of the form service.namespace.svc.cluster."
                "local, and the search path in resolv.conf lets pods use short names inside their own "
                "namespace. Anything not matching the cluster domain is forwarded upstream to the resolvers "
                "the cluster is configured with."
            ),
            analogy=(
                "It is an internal switchboard with a local directory. Ask for a colleague by first name and "
                "it works; ask for an outside number and the call is forwarded to the public network."
            ),
            context=(
                "DNS causes an unfair share of outages because everything depends on it and its failures are "
                "indirect - applications report connection timeouts, not resolution failures. The two "
                "classics are an upstream forwarder that is slow or unreachable, which makes every external "
                "lookup take five seconds, and ndots search-path behaviour turning one external lookup into "
                "several queries. Knowing to test resolution from inside a pod rather than from your laptop "
                "is the practical skill."
            ),
            steps=[
                "Name the components: CoreDNS pods, the DNS Operator, per-pod resolv.conf.",
                "Explain the record format and the search path behaviour for short names.",
                "Describe upstream forwarding and why a slow forwarder looks like an application problem.",
                "Always test from inside an affected pod, then from the node, to localise it.",
            ],
            evidence=[
                "oc exec <pod> -- cat /etc/resolv.conf",
                "oc exec <pod> -- getent hosts <svc>.<ns>.svc.cluster.local",
                "oc get dns.operator/default -o yaml | sed -n '/servers:/,$p'",
            ],
            redflag=(
                "Do not test DNS from your workstation and conclude the cluster is fine. The only view that "
                "matters is from inside the pod."
            ),
            followup="External lookups take five seconds from every pod. What do you suspect?",
        ),
        Q(
            q="What is an IngressController?",
            level=FOUNDATION,
            answer=(
                "An IngressController is the OpenShift object that defines a router deployment: which "
                "namespaces and routes it admits, its wildcard domain, replica count, node placement, TLS "
                "profile and how it is exposed. The Ingress Operator reconciles it into a router deployment "
                "and the corresponding Service. The default one serves the cluster's apps wildcard domain; "
                "you can create additional ones for isolation."
            ),
            analogy=(
                "It is the specification for a reception desk: which visitors it accepts, which building "
                "entrance it sits at, how many staff it has, and what identification it checks."
            ),
            context=(
                "The reason this matters is that everything about ingress behaviour is configured here rather "
                "than on individual Routes - TLS minimum version and cipher profile, HTTP/2, proxy protocol, "
                "logging, and the placement that decides which nodes handle external traffic. When someone "
                "asks how you would enforce TLS 1.2 minimum for all external traffic, this object is the "
                "answer, not a per-route annotation."
            ),
            steps=[
                "Define it as the declarative spec for a router, reconciled by the Ingress Operator.",
                "List the properties it controls - domain, admission scope, replicas, placement, TLS profile.",
                "Explain the relationship to the router pods and the exposing Service.",
                "Give the use case for additional controllers: separating internal from external traffic.",
            ],
            evidence=[
                "oc -n openshift-ingress-operator get ingresscontroller default -o yaml | head -40",
                "oc -n openshift-ingress get pods -o wide",
                "oc -n openshift-ingress-operator get ingresscontroller default -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not describe router configuration as something you set per Route. Most of it is "
                "controller-level and cluster-wide."
            ),
            followup="How would you enforce a minimum TLS version for all external traffic?",
        ),
        Q(
            q="What is SNI and why does it matter for routing?",
            level=FOUNDATION,
            answer=(
                "Server Name Indication is a TLS extension where the client sends the hostname it wants "
                "during the handshake, before any encrypted data. That lets one IP address and one port serve "
                "many different certificates - the router reads the SNI value and presents the right one. "
                "Without it, a single listener could only serve one certificate, and shared ingress would not "
                "work."
            ),
            analogy=(
                "It is telling reception who you are visiting before they let you through the door, rather "
                "than after. That is the only way one desk can serve fifty companies in the building."
            ),
            context=(
                "SNI is why passthrough routes work at all: the router cannot decrypt the traffic, so the "
                "only thing it can route on is the hostname in the handshake. It is also the cause of a "
                "specific class of failure - an old client that does not send SNI gets the router's default "
                "certificate, and the user sees a certificate name mismatch that looks like a certificate "
                "problem but is actually a client capability problem."
            ),
            steps=[
                "Define SNI as the hostname sent in the TLS ClientHello, before encryption.",
                "Explain how it allows one IP and port to serve many certificates.",
                "Connect it to passthrough routes, where SNI is the only routing information available.",
                "Name the failure signature: no SNI means the default certificate and a name mismatch error.",
            ],
            evidence=[
                "openssl s_client -connect <host>:443 -servername <host> </dev/null 2>/dev/null | head -20",
                "oc get route <route> -o jsonpath='{.spec.tls.termination}{\"\\n\"}'",
                "oc -n openshift-ingress logs deploy/router-default --tail=50",
            ],
            redflag=(
                "Do not claim passthrough routes can do path-based routing. Without decryption there is no "
                "path to route on."
            ),
            followup="A legacy client gets a certificate mismatch that browsers do not. What is happening?",
        ),
        Q(
            q="Explain edge, re-encrypt and passthrough termination.",
            level=INTERMEDIATE,
            answer=(
                "Edge terminates TLS at the router and talks plain HTTP to the pod - simplest, and the "
                "internal hop is unencrypted. Re-encrypt terminates at the router, then opens a new TLS "
                "connection to the pod, validating the backend certificate against a destination CA - so "
                "traffic is encrypted end to end and the router can still see and route on paths and "
                "headers. Passthrough does not terminate at all; the TLS connection goes straight to the pod, "
                "so the pod owns the certificate and the router routes only on SNI."
            ),
            analogy=(
                "Edge is opening the envelope at the post room and hand-delivering the letter. Re-encrypt is "
                "opening it, reading the address, and sealing it in a new envelope. Passthrough is delivering "
                "the sealed envelope untouched."
            ),
            context=(
                "In regulated environments re-encrypt is usually the default, because it satisfies "
                "encryption-in-transit requirements while keeping the operational benefits of a router that "
                "can see the request. Passthrough is chosen when the application must terminate TLS itself - "
                "mutual TLS or client certificate authentication - and the cost is that you lose path "
                "routing, header injection and centralised certificate management. Saying that trade-off "
                "out loud is what gets the mark."
            ),
            steps=[
                "Describe where TLS terminates in each mode and what the internal hop looks like.",
                "State what the router can and cannot do in each mode - paths, headers, SNI only.",
                "Give the compliance angle: internal encryption requirements usually point at re-encrypt.",
                "Name the certificate ownership consequence for passthrough - the app manages rotation.",
            ],
            evidence=[
                "oc get route <route> -o jsonpath='{.spec.tls}' | python3 -m json.tool",
                "openssl s_client -connect <host>:443 -servername <host> </dev/null 2>/dev/null | openssl x509 -noout -subject -dates",
                "oc get route <route> -o jsonpath='{.spec.tls.destinationCACertificate}' | head -c 100",
            ],
            redflag=(
                "Do not default to edge in a regulated environment without saying that the router-to-pod hop "
                "is unencrypted. That is a finding waiting to happen."
            ),
            followup="An application needs client certificate authentication. Which mode, and what do you lose?",
        ),
        Q(
            q="What does route admission policy control?",
            level=INTERMEDIATE,
            answer=(
                "It controls which Routes a given IngressController will serve. The two main levers are "
                "namespace selection - which namespaces this controller admits routes from - and the policy "
                "for claims across namespaces, which decides whether two namespaces may both claim the same "
                "hostname. The default is strict, so the first claim wins and later ones are rejected, which "
                "prevents one tenant from hijacking another's hostname."
            ),
            analogy=(
                "It is the rule that stops a second shop putting up the same street address. First "
                "registration keeps the address; everyone else is told to pick another."
            ),
            context=(
                "This is the mechanism behind a genuinely confusing symptom: a Route that exists, looks "
                "correct, and simply is not served. The status on the Route says it was not admitted and "
                "usually why - a hostname already claimed elsewhere, or a namespace this controller does not "
                "select. It is also how you build tenant isolation with separate internal and external "
                "routers, each admitting a different set of namespaces by label."
            ),
            steps=[
                "Explain the two controls: namespace selection and cross-namespace hostname claims.",
                "Describe the default strict behaviour and why it exists.",
                "Show where the rejection is visible - the Route's status ingress conditions.",
                "Give the design use: label-based routing of namespaces to internal or external controllers.",
            ],
            evidence=[
                "oc get route <route> -o jsonpath='{.status.ingress[*].conditions}' | python3 -m json.tool",
                "oc -n openshift-ingress-operator get ingresscontroller <name> -o jsonpath='{.spec.routeAdmission}{\"\\n\"}'",
                "oc get route -A -o custom-columns=NS:.metadata.namespace,HOST:.spec.host | sort -k2 | uniq -d -f1",
            ],
            redflag=(
                "Do not loosen the cross-namespace claim policy to fix a conflict. You are removing a "
                "tenant-isolation control to solve a naming problem."
            ),
            followup="A Route exists but is not being served. Walk me through it.",
        ),
        Q(
            q="How does traffic actually get from a Service IP to a pod?",
            level=INTERMEDIATE,
            answer=(
                "The Service ClusterIP is virtual, so something on the node has to rewrite it. With "
                "OVN-Kubernetes, the endpoint list is programmed into OVN load balancers and implemented as "
                "OpenFlow rules in the node's integration bridge, so the destination is rewritten to a real "
                "pod IP and the reply is translated back through conntrack. Traffic to a pod on another node "
                "is then encapsulated with Geneve and sent over the node network."
            ),
            analogy=(
                "It is a mailroom that rewrites the internal address on the envelope before it leaves the "
                "building, and rewrites the sender on the reply so the conversation still makes sense."
            ),
            context=(
                "Knowing that the datapath is per-node explains a symptom that otherwise looks impossible: "
                "the Service works from most pods and fails from one node. That is a node-local datapath or "
                "OVS problem, not a Service problem, and it points you at ovnkube pods and OVS flows on that "
                "specific node rather than at the object definitions. It also explains why conntrack "
                "exhaustion on a busy node causes intermittent connection failures across unrelated "
                "services."
            ),
            steps=[
                "State that the ClusterIP is virtual and translated in the node datapath.",
                "Name the components: OVN load balancer entries, OpenFlow rules on br-int, conntrack.",
                "Explain cross-node traffic and Geneve encapsulation, which is where MTU issues come from.",
                "Use the per-node nature diagnostically: test from several nodes to localise the failure.",
            ],
            evidence=[
                "oc -n openshift-ovn-kubernetes get pods -o wide | grep <node>",
                "oc debug node/<node> -- chroot /host ovs-vsctl show | head -20",
                "oc exec <pod> -- curl -sS -m 3 http://<svc>.<ns>.svc:8080/healthz",
            ],
            redflag=(
                "Do not say \"kube-proxy iptables rules\" for an OVN-Kubernetes cluster without qualifying "
                "it. The implementation matters when you are asked where to look."
            ),
            followup="The Service works from every node except one. What is your next step?",
        ),
        Q(
            q="What is a NetworkPolicy, and how do you roll out default-deny safely?",
            level=INTERMEDIATE,
            answer=(
                "A NetworkPolicy is namespace-scoped, pod-selected, allow-only firewalling for pod traffic. "
                "The important rule is that a pod is unrestricted until some policy selects it, and from that "
                "moment only what policies explicitly allow is permitted. To roll out default-deny safely I "
                "first observe real traffic, write the allow rules from that evidence, apply the policies to "
                "a non-critical namespace, verify, then apply default-deny - never the other way around."
            ),
            analogy=(
                "It is fitting door locks in an occupied building. You first find out who genuinely needs "
                "which door, hand out those keys, and only then change the locks."
            ),
            context=(
                "The dependencies people forget are the ones that break everything: DNS to the cluster DNS "
                "service, the monitoring stack scraping metrics endpoints, the ingress router reaching "
                "application pods, and health probes. Blocking any of those turns a security improvement "
                "into an outage. Network Observability or flow logs give you the real dependency map instead "
                "of the one on the architecture diagram, which is usually out of date."
            ),
            steps=[
                "Explain the selection model: unrestricted until selected, then allow-list only.",
                "Gather evidence of real flows before writing rules - observability first, policy second.",
                "Write explicit allows including DNS, monitoring, ingress and probes.",
                "Apply to one namespace, verify service behaviour, then extend; keep a documented rollback.",
            ],
            evidence=[
                "oc get networkpolicy -n <ns> -o yaml",
                "oc exec <pod> -- curl -sS -m 3 <target>:<port>   # before and after",
                "Network Observability flow data filtered by namespace and dropped verdict",
            ],
            redflag=(
                "Do not apply default-deny across the cluster in one change. The DNS and monitoring "
                "breakages alone will make it memorable for the wrong reasons."
            ),
            followup="After applying default-deny, metrics stopped being collected. What rule is missing?",
        ),
        Q(
            q="Why would you run multiple IngressControllers?",
            level=INTERMEDIATE,
            answer=(
                "To separate traffic that should not share a path. The common split is internal versus "
                "external: one controller on an internal load balancer serving internal namespaces, another "
                "facing the internet with stricter TLS settings and rate limiting. Other reasons are "
                "dedicating router capacity to a high-volume tenant, giving a business unit its own wildcard "
                "domain and certificate, or isolating a controller with different TLS or logging "
                "requirements."
            ),
            analogy=(
                "It is having a staff entrance and a public entrance. Same building, different security "
                "checks, and a queue at one does not block the other."
            ),
            context=(
                "The operational benefit that is easiest to defend is blast radius. With a single shared "
                "router, one tenant's traffic spike or a bad route annotation affects everyone, and router "
                "upgrades are a single change window for the whole cluster. With separate controllers, "
                "capacity and risk are partitioned, and you can roll out a TLS profile change to internal "
                "traffic first. The cost is more DNS, more certificates and more to keep consistent."
            ),
            steps=[
                "Start from the requirement - isolation, capacity, different security posture, or domains.",
                "Configure namespace selection and route admission so each controller owns a clear scope.",
                "Give each its own domain, certificate and load balancer, and place router pods "
                "deliberately.",
                "State the cost honestly: more moving parts, more certificates, more consistency to "
                "maintain.",
            ],
            evidence=[
                "oc -n openshift-ingress-operator get ingresscontroller",
                "oc -n openshift-ingress get pods -l ingresscontroller.operator.openshift.io/deployment-ingresscontroller=<name> -o wide",
                "oc get route -A -o custom-columns=NS:.metadata.namespace,HOST:.spec.host,STATUS:.status.ingress[0].routerName",
            ],
            redflag=(
                "Do not create a separate controller per application. You are rebuilding the per-service "
                "load balancer problem with extra steps."
            ),
            followup="How do you make sure a namespace's routes land on the internal controller only?",
        ),
        Q(
            q="A Route is returning 503. Walk me through it.",
            level=SENIOR,
            answer=(
                "503 from the router means it accepted the connection and had no healthy backend to send it "
                "to, so I work the path from the pod outwards. First, are there ready endpoints for the "
                "Service - if not, this is a readiness or selector problem and the network is irrelevant. If "
                "there are, I check that the Route points at the right Service and port, that it was "
                "admitted, and that the router can actually reach the pods, which is where NetworkPolicy and "
                "OVN come in. Then I check the router pods themselves."
            ),
            analogy=(
                "The receptionist answered the phone and said nobody is available. That is not a phone fault "
                "- it is a staffing fault, and you go and look at the rota."
            ),
            context=(
                "The reason to start at endpoints is that it is the highest-yield check by a wide margin. In "
                "most real 503 incidents the pods are running but not ready, because a probe is failing "
                "against a dependency. Starting at the router instead means restarting router pods, which "
                "briefly affects every application in the cluster and does not fix anything. Working inward "
                "to outward keeps blast radius at zero until you have evidence."
            ),
            steps=[
                "State impact: one route, one namespace, or every route - that alone splits the diagnosis.",
                "Check the EndpointSlice for ready addresses; if empty, investigate readiness and selectors.",
                "Verify the Route's target Service and port, and that it was admitted by a controller.",
                "Test connectivity from a router pod to a backend pod, check NetworkPolicy, and only then "
                "look at router pod health and logs.",
            ],
            evidence=[
                "oc get endpointslice -n <ns> -l kubernetes.io/service-name=<svc>",
                "oc get route <route> -o jsonpath='{.spec.to} {.spec.port}{\"\\n\"}'",
                "oc -n openshift-ingress rsh deploy/router-default curl -sS -m 3 <podIP>:<port>/healthz",
            ],
            redflag=(
                "Do not restart the router first. It affects every application in the cluster and almost "
                "never addresses the cause."
            ),
            followup="Every route in the cluster returns 503. How does that change your approach?",
        ),
        Q(
            q="How do you troubleshoot cluster DNS?",
            level=SENIOR,
            answer=(
                "I establish scope first: is it one pod, one namespace, one node, or everything, and is it "
                "cluster names, external names or both. Then I test resolution from inside an affected pod, "
                "check the CoreDNS pods and the DNS Operator status, and look at whether a NetworkPolicy is "
                "blocking port 53 to the DNS service. If only external names fail, the upstream forwarders "
                "are the suspect. If only one node is affected, it is a node datapath problem, not a DNS "
                "problem."
            ),
            analogy=(
                "It is a phone that cannot get through. Before blaming the network, you find out whether it "
                "is one handset, one floor, or every phone - and whether internal extensions still work."
            ),
            context=(
                "Scoping first is what makes this fast, because each scope points at a different component. "
                "The most common real causes are a default-deny NetworkPolicy that forgot to allow DNS "
                "egress, a slow or unreachable upstream forwarder producing five-second timeouts, and "
                "CoreDNS being resource-starved on a busy node. Note also that a pod's DNS config is set at "
                "creation, so a DNS configuration change does not reach existing pods until they restart."
            ),
            steps=[
                "Scope it: one pod, one node, one namespace, or cluster-wide; cluster names or external.",
                "Test from inside the pod, then from the node, then directly against a CoreDNS pod IP.",
                "Check DNS Operator and CoreDNS pod health, plus NetworkPolicy allowing UDP and TCP 53.",
                "If only external resolution fails, test the upstream forwarders directly from a node.",
            ],
            evidence=[
                "oc exec <pod> -- getent hosts <name> ; oc exec <pod> -- cat /etc/resolv.conf",
                "oc -n openshift-dns get pods -o wide ; oc get co dns",
                "oc debug node/<node> -- chroot /host dig @<upstream> <external-name> +short",
            ],
            redflag=(
                "Do not restart CoreDNS as a first move. If a NetworkPolicy is blocking port 53, restarting "
                "it proves nothing and delays the fix."
            ),
            followup="Only newly created pods resolve correctly. What does that tell you?",
        ),
        Q(
            q="How do you tune the ingress layer for scale?",
            level=SENIOR,
            answer=(
                "I start by measuring where the limit actually is: router CPU, connection counts, TLS "
                "handshake rate, or backend latency being blamed on the router. Then the levers are router "
                "replica count and placement on dedicated infrastructure nodes, connection and timeout "
                "tuning, HTTP/2 and keepalive settings, and reducing the reload cost by limiting how often "
                "route objects change. For very large clusters, sharding routes across multiple "
                "IngressControllers is the structural answer."
            ),
            analogy=(
                "A single reception desk can only process so many visitors. You add desks, put them in the "
                "right lobbies, and stop reprinting the visitor list every time one name changes."
            ),
            context=(
                "The failure mode people miss is configuration churn. Every route change causes a router "
                "reload, and in a cluster where controllers create and delete routes frequently, the routers "
                "spend their time reloading rather than serving, producing latency spikes that look like "
                "backend problems. Placing routers on dedicated nodes also matters more than it sounds: "
                "routers competing with application workloads for CPU produce exactly the intermittent "
                "latency that is hardest to diagnose."
            ),
            steps=[
                "Measure first - router CPU and memory, connection rate, TLS handshakes, reload frequency.",
                "Scale replicas and place routers on dedicated infrastructure nodes with enough headroom.",
                "Tune timeouts, keepalives and HTTP/2 deliberately, changing one thing at a time.",
                "Reduce churn, and shard routes across controllers when a single router set is the limit.",
            ],
            evidence=[
                "haproxy_process_current_connections ; haproxy_backend_http_average_response_time_seconds",
                "oc -n openshift-ingress adm top pod",
                "oc -n openshift-ingress logs deploy/router-default | grep -c 'reload'",
            ],
            redflag=(
                "Do not scale router replicas without measuring first. If the bottleneck is reload churn or "
                "backend latency, more routers change nothing."
            ),
            followup="Router latency spikes every few minutes with no traffic change. What do you suspect?",
        ),
        Q(
            q="How would you design ingress for a multi-tenant cluster?",
            level=ARCHITECT,
            answer=(
                "I would separate by exposure and blast radius rather than by team. One internal controller "
                "and one external controller as the baseline, each with its own domain, certificate and load "
                "balancer, with namespace selection deciding which tenants land where. Tenants with genuinely "
                "different security requirements or very high volume get a dedicated controller on dedicated "
                "nodes. Hostname claims stay strict, certificates are issued automatically, and every route "
                "gets standard rate limiting and TLS policy from the controller rather than per route."
            ),
            analogy=(
                "It is designing entrances for a mixed-use building. Residents, offices and the public do not "
                "share one door - but you also do not build one door per tenant."
            ),
            context=(
                "The pressure in this design is always between isolation and operational load. Every extra "
                "controller means another certificate to rotate, another DNS entry, another thing to upgrade "
                "and to keep consistent. So the rule I use is that a new controller needs a stated reason - "
                "different exposure, different compliance boundary, or measured capacity contention - and "
                "anything else stays on the shared pair. That gives you a policy you can apply consistently "
                "instead of negotiating each request."
            ),
            steps=[
                "Classify traffic by exposure and compliance requirement, not by organisational chart.",
                "Baseline on an internal and an external controller with namespace-label admission.",
                "Define the criteria that justify a dedicated controller, and hold the line on them.",
                "Automate certificates, DNS and the standard TLS and rate-limit policy so consistency is "
                "free.",
            ],
            evidence=[
                "oc -n openshift-ingress-operator get ingresscontroller -o wide",
                "oc get ns -L ingress-class ; oc get route -A --show-labels | head",
                "Certificate inventory with expiry dates and issuing automation status",
            ],
            redflag=(
                "Do not give every tenant their own IngressController by default. The consistency debt will "
                "outlive the isolation benefit."
            ),
            followup="A tenant demands a dedicated router for performance. How do you validate the claim?",
        ),
    ],
)
