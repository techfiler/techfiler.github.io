"""Part 12 - Troubleshooting and incident response."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=12,
    title="Troubleshooting and incident response",
    subtitle="Working from evidence under pressure, and leaving the system better than you found it",
    intro=(
        "This is the part of the interview where the scoring gets brutal, because troubleshooting answers "
        "expose how you actually think. Two candidates can name the same command and score completely "
        "differently: one says \"I would restart the pod\", the other says \"I would state the impact, read "
        "the events, form one hypothesis, take the smallest safe action, validate against the user-visible "
        "symptom, and then make it impossible to happen again\". The second answer is not more knowledgeable. "
        "It is more disciplined, and discipline is what an interviewer can actually assess in forty minutes."
    ),
    infographics=["evidence_first_loop"],
    questions=[
        Q(
            q="How do you approach a troubleshooting question?",
            level=FOUNDATION,
            answer=(
                "With the same six steps every time. Impact - who is affected, since when, is it getting "
                "worse. Evidence - conditions, events, logs and metrics from the owning controller, not just "
                "the symptom. Hypothesis - one testable explanation that accounts for all the evidence. "
                "Mitigation - the smallest safe action that restores service. Validation - prove the "
                "user-visible symptom is gone. Prevention - the alert, guardrail or automation that stops it "
                "recurring."
            ),
            analogy=(
                "It is triage in an emergency department. Assess, examine, form a diagnosis, treat "
                "conservatively, confirm improvement, then discuss how to avoid the next admission."
            ),
            context=(
                "Having a structure matters most when you do not know the answer. If a question catches you "
                "cold, the loop gives you something correct to say while you think, and it demonstrates the "
                "behaviour being assessed even on an unfamiliar technology. It also protects you in real "
                "incidents from the two most expensive mistakes: acting before understanding, and stopping "
                "once service is restored without fixing the cause."
            ),
            steps=[
                "State impact and scope before touching anything - it also determines urgency.",
                "Gather evidence from the owning controller's conditions, then events, logs and metrics.",
                "Form one hypothesis that explains all the evidence, and say how you would test it.",
                "Apply the smallest safe mitigation, validate against the user symptom, then define "
                "prevention.",
            ],
            evidence=[
                "oc get events -A --sort-by=.lastTimestamp | tail -30",
                "oc get co ; oc get nodes ; oc get pods -A --field-selector status.phase!=Running",
                "oc describe <kind> <name> | sed -n '/Conditions/,$p'",
            ],
            redflag=(
                "Do not open with \"I would restart it\". Even when restarting works, it is the answer that "
                "scores lowest."
            ),
            followup="Which of those six steps do people skip most often, and what does it cost?",
        ),
        Q(
            q="How do you troubleshoot CrashLoopBackOff?",
            level=FOUNDATION,
            answer=(
                "CrashLoopBackOff means the container starts, exits, and Kubernetes is backing off before "
                "retrying - so the container is failing, not the platform. I read the previous container's "
                "logs first, because the current one may not have got far enough to log anything. Then the "
                "exit code: 137 is a memory limit kill, 1 or 2 is usually application error or "
                "misconfiguration, 126 or 127 means the command could not be executed. Then I check whether "
                "a liveness probe is killing it before it becomes healthy."
            ),
            analogy=(
                "It is an engine that keeps stalling on ignition. You do not investigate the road - you look "
                "at what the engine says as it dies."
            ),
            context=(
                "The exit code shortcut saves a lot of time. Exit 137 points at memory and you go straight "
                "to limits and working set. Exit 0 in a crash loop means the process completed and exited, "
                "which usually means the container is running the wrong command or a script that ends. And "
                "if the pod becomes healthy for a few seconds before dying, suspect a liveness probe whose "
                "initial delay is shorter than the application's real startup time - which is what startup "
                "probes exist to solve."
            ),
            steps=[
                "Read logs from the previous instance, not the current one.",
                "Read the exit code and last state, and use it to narrow the class of failure.",
                "Check probe configuration and restart count timing to rule out probe-induced kills.",
                "Verify configuration and dependencies - missing ConfigMap, Secret, or an unreachable "
                "dependency at startup.",
            ],
            evidence=[
                "oc logs <pod> --previous --tail=100",
                "oc describe pod <pod> | grep -A6 'Last State'",
                "oc get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not delete the pod before reading the previous logs. You have just destroyed the only "
                "record of why it died."
            ),
            followup="Exit code 137 but the node has plenty of free memory. Explain that.",
        ),
        Q(
            q="How do you troubleshoot ImagePullBackOff?",
            level=FOUNDATION,
            answer=(
                "The kubelet could not pull the image, and the event message almost always says why. The "
                "usual causes are a wrong image name or tag, a private registry with no pull secret attached "
                "to the ServiceAccount, an expired or wrong credential, the registry being unreachable "
                "because of a proxy or network policy, a certificate the node does not trust, or rate "
                "limiting from a public registry."
            ),
            analogy=(
                "It is a delivery that failed. The card through the door says whether the address was wrong, "
                "nobody was in, or the courier could not get through the gate."
            ),
            context=(
                "The one that surprises people is when it works on some nodes and not others - that is "
                "almost always a node-level trust or proxy difference rather than anything to do with the "
                "pod. Public registry rate limiting is the other modern classic, particularly in clusters "
                "that pull unauthenticated: everything works for weeks and then a busy afternoon produces "
                "pull failures across unrelated namespaces."
            ),
            steps=[
                "Read the exact event message - it distinguishes not-found from unauthorised from "
                "unreachable.",
                "Verify the image reference and confirm it exists in the registry, ideally by digest.",
                "Check the pull secret is attached to the pod's ServiceAccount and that the credential is "
                "valid.",
                "If node-specific, check proxy configuration, registry trust and mirror configuration on "
                "that node.",
            ],
            evidence=[
                "oc describe pod <pod> | sed -n '/Events/,$p'",
                "oc get sa <sa> -n <ns> -o jsonpath='{.imagePullSecrets}{\"\\n\"}'",
                "oc debug node/<node> -- chroot /host crictl pull <image>",
            ],
            redflag=(
                "Do not add a pull secret without reading the error first. If the tag does not exist, the "
                "credential was never the problem."
            ),
            followup="The image pulls on three nodes and fails on the fourth. What is different?",
        ),
        Q(
            q="Events, conditions, logs - which do you read first and why?",
            level=FOUNDATION,
            answer=(
                "Conditions first, because they are the owning controller's own statement of what it thinks "
                "and what is blocking it. Events second, because they are the timeline of what the platform "
                "decided and when - though they expire after a few hours, so capture them early. Logs third, "
                "because they are the most detailed and the least structured, and you want to know where to "
                "look before you start reading them."
            ),
            analogy=(
                "Conditions are the diagnosis on the chart, events are the nursing notes, logs are the raw "
                "monitor trace. You read them in that order for a reason."
            ),
            context=(
                "The default retention on events is short - roughly three hours - which is exactly long "
                "enough to be gone by the time an incident review starts. So part of the discipline is "
                "capturing events into the incident record at the beginning rather than assuming they will "
                "still be there. Conditions, by contrast, persist on the object, which is why they are the "
                "reliable starting point."
            ),
            steps=[
                "Read status conditions on the object and on its owning controller.",
                "Pull events for the namespace sorted by time, and save them to the incident record "
                "immediately.",
                "Then go to logs, targeted by what the conditions and events pointed at.",
                "Correlate all three against metrics for the same window before forming a hypothesis.",
            ],
            evidence=[
                "oc get <kind> <name> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc get events -n <ns> --sort-by=.lastTimestamp > incident-events.txt",
                "oc logs <pod> --since=30m --tail=200",
            ],
            redflag=(
                "Do not start with logs. Without direction you will read the wrong ten thousand lines."
            ),
            followup="The events you need have already expired. What do you do?",
        ),
        Q(
            q="How do you troubleshoot a node that is NotReady?",
            level=INTERMEDIATE,
            answer=(
                "I read the node conditions first, because the kubelet usually states the reason - "
                "MemoryPressure, DiskPressure, PIDPressure, or a plain unreachable status meaning the kubelet "
                "is not reporting at all. Unreachable points at the kubelet or the network path to the API "
                "server; pressure conditions point at node resources. Then I get onto the node and check "
                "kubelet and CRI-O logs, disk usage, and kernel messages before deciding anything."
            ),
            analogy=(
                "It is a member of staff who has stopped answering. Either they are unwell, or the phone "
                "line is down - and those need very different responses."
            ),
            context=(
                "The distinction that matters most is that a NotReady node is often still running its "
                "workloads and serving traffic. The kubelet has lost contact; the containers have not "
                "stopped. So rebooting immediately can turn a management-plane problem into a genuine "
                "outage. The other thing to know is the eviction timer: after the toleration period, pods "
                "will be marked for eviction and rescheduled, so you have a window in which to decide "
                "deliberately."
            ),
            steps=[
                "Read node conditions to classify the failure: pressure versus unreachable.",
                "Establish whether workloads on the node are still serving before considering a reboot.",
                "Get on the node and check kubelet and CRI-O logs, disk, memory and kernel messages.",
                "Fix the identified cause, or cordon and drain deliberately if the node must be replaced.",
            ],
            evidence=[
                "oc get node <node> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc debug node/<node> -- chroot /host sh -c 'df -h /var; journalctl -u kubelet -n 100 --no-pager'",
                "oc get pods -A -o wide --field-selector spec.nodeName=<node>",
            ],
            redflag=(
                "Do not reboot the node first. Its pods may still be serving customers, and you will lose "
                "the evidence either way."
            ),
            followup="The node is unreachable but its pods still answer traffic. What does that mean?",
        ),
        Q(
            q="A namespace is stuck in Terminating. What do you do?",
            level=INTERMEDIATE,
            answer=(
                "Something is blocking deletion, and it is either a resource that will not delete or a "
                "finalizer with no controller left to clear it. I list every resource still present in the "
                "namespace, look at what has finalizers, and identify which controller owns them. If the "
                "controller was uninstalled, the correct fix is to bring it back so it can clean up "
                "properly. Removing finalizers by hand works, but it silently leaks whatever they were "
                "protecting, so it is a documented last resort."
            ),
            analogy=(
                "It is a house sale stuck at completion. Someone has not signed, and forging the signature "
                "gets you the keys and an unresolved liability."
            ),
            context=(
                "The usual sequence that creates this is an operator being removed before its custom "
                "resources were deleted. The custom resources still carry finalizers, the controller that "
                "would clear them no longer exists, and the namespace waits forever. Reinstalling the "
                "operator briefly, letting it clean up, then removing it in the right order is slower and "
                "much safer than patching finalizers out."
            ),
            steps=[
                "List every remaining resource in the namespace across all API groups.",
                "Identify which resources carry finalizers and which controller owns each one.",
                "Restore the missing controller so cleanup can complete properly.",
                "Only if that is impossible, remove the finalizer, document what was leaked, and clean it up "
                "at the backend.",
            ],
            evidence=[
                "oc get ns <ns> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "oc api-resources --verbs=list --namespaced -o name | xargs -n1 oc get -n <ns> --ignore-not-found 2>/dev/null",
                "oc get <kind> <name> -n <ns> -o jsonpath='{.metadata.finalizers}{\"\\n\"}'",
            ],
            redflag=(
                "Do not patch finalizers out as your first move. You are guaranteeing an orphaned cloud "
                "resource nobody will ever find."
            ),
            followup="The finalizer belongs to an operator that was uninstalled last month. Now what?",
        ),
        Q(
            q="A pod is Running but never becomes Ready. How do you diagnose it?",
            level=INTERMEDIATE,
            answer=(
                "Running but not Ready means the container process started and the readiness probe is "
                "failing, so the pod is deliberately kept out of the EndpointSlice. I look at the probe "
                "definition - path, port, scheme, timing - then test that exact endpoint from inside the "
                "pod, then from another pod. If it works from inside and not from outside, it is network "
                "policy or a port mismatch. If it fails from inside, the application is genuinely not ready "
                "and its logs will say why."
            ),
            analogy=(
                "The shop is lit and staffed but the Open sign is off. Either the staff know something you "
                "do not, or the sign is wired wrong."
            ),
            context=(
                "The two causes are roughly equally common and pull in opposite directions. A genuinely "
                "unready application - waiting on a database, still loading a cache - is doing exactly the "
                "right thing and the fix is upstream. A misconfigured probe - wrong port, HTTPS versus HTTP, "
                "a path that requires authentication, a timeout shorter than the endpoint's real response "
                "time under load - is a self-inflicted outage. Testing from inside the pod distinguishes "
                "them in one command."
            ),
            steps=[
                "Read the readiness probe definition and the describe output showing the probe failure.",
                "Curl the exact probe path and port from inside the container.",
                "If that succeeds, test from another pod to check policy and port mapping.",
                "If it fails, read the application logs for what it is waiting on, and fix upstream rather "
                "than loosening the probe.",
            ],
            evidence=[
                "oc describe pod <pod> | grep -A4 Readiness",
                "oc exec <pod> -- curl -sS -m 3 -o /dev/null -w '%{http_code}\\n' http://127.0.0.1:8080/healthz",
                "oc get endpointslice -n <ns> -l kubernetes.io/service-name=<svc>",
            ],
            redflag=(
                "Do not relax the readiness probe to make the pod Ready. You have just told the router to "
                "send users to a broken pod."
            ),
            followup="The probe passes from inside the pod and fails from the kubelet. What is going on?",
        ),
        Q(
            q="How do you investigate an OOMKilled container?",
            level=INTERMEDIATE,
            answer=(
                "The kernel killed the process because the container's cgroup exceeded its memory limit. I "
                "confirm it from the last state and exit code 137, then look at the working set over time to "
                "see whether this was a steady climb, which suggests a leak, or a spike, which suggests a "
                "particular request or job. Then I decide between raising the limit, fixing the application, "
                "or both - and I check whether the limit was ever based on measurement in the first place."
            ),
            analogy=(
                "It is a circuit breaker tripping. The breaker is not the fault; either the appliance is "
                "faulty or the circuit was rated for less than you actually plug in."
            ),
            context=(
                "The detail that catches people is that the node can have plenty of free memory and the "
                "container still be killed, because the limit is per-cgroup rather than per-node. The other "
                "one is the JVM and similar runtimes: a heap size configured larger than the container limit "
                "guarantees an eventual kill, and the fix is to make the runtime container-aware rather than "
                "to keep raising the limit."
            ),
            steps=[
                "Confirm OOMKilled from the container's last state and exit code.",
                "Chart working set over time to distinguish a leak from a spike.",
                "Check whether the runtime is aware of the container limit, especially for JVM workloads.",
                "Set the limit from measured p99 usage with headroom, and fix the leak if that is the "
                "pattern.",
            ],
            evidence=[
                "oc describe pod <pod> | grep -A5 'Last State'",
                "container_memory_working_set_bytes{pod=\"<pod>\"} over 24h",
                "oc debug node/<node> -- chroot /host dmesg -T | grep -i 'killed process'",
            ],
            redflag=(
                "Do not just double the memory limit. If it is a leak you have bought a few hours and "
                "learned nothing."
            ),
            followup="The graph shows a steady climb over four days. What is your recommendation?",
        ),
        Q(
            q="How do you investigate intermittent 5xx errors you cannot reproduce?",
            level=INTERMEDIATE,
            answer=(
                "I start by making the intermittent measurable: what percentage of requests, on which paths, "
                "at what times, from which clients, and does it correlate with deploys, traffic peaks or a "
                "specific backend pod. Then I look for a pattern that turns \"random\" into \"conditional\" "
                "- one unhealthy pod still in rotation, a node with a datapath problem, a dependency timing "
                "out under load, or connection churn during rollouts."
            ),
            analogy=(
                "It is a rattle that only happens above forty miles an hour. It feels random until you "
                "notice the condition, and then it is completely reproducible."
            ),
            context=(
                "The single most common cause in practice is one bad backend among many: a pod that passes "
                "its readiness probe but fails real requests, so a fraction of traffic hits it and the error "
                "rate looks random. Per-pod metrics collapse that immediately. The second most common is "
                "deploy-time connection handling - errors that cluster tightly around rollout windows and "
                "trace back to shutdown behaviour rather than to anything in the request path."
            ),
            steps=[
                "Quantify it: error rate, affected paths, time distribution, and correlation with events.",
                "Break metrics down per pod, per node and per zone to find a non-uniform distribution.",
                "Check whether errors cluster around deployments, scaling events or peak traffic.",
                "Reproduce under load if possible, and use traces or flow data to attribute the failing "
                "hop.",
            ],
            evidence=[
                "sum by (pod) (rate(http_requests_total{code=~\"5..\"}[5m]))",
                "oc get events -n <ns> --sort-by=.lastTimestamp | grep -i -E 'unhealthy|killing|scaled'",
                "Router or ingress logs filtered to 5xx, grouped by backend",
            ],
            redflag=(
                "Do not call it random. Errors that appear random are almost always conditional on "
                "something you have not measured yet."
            ),
            followup="Errors cluster tightly around every deployment. What is your first hypothesis?",
        ),
        Q(
            q="Somebody says \"the application is slow\". How do you triage that?",
            level=SENIOR,
            answer=(
                "I turn it into a measurable statement first: which operation, how slow compared with what, "
                "for which users, since when, and is it all requests or a percentile tail. Then I walk the "
                "request path and measure at each hop - ingress, service, application, dependency, database, "
                "storage - to find where the time is actually spent. Most \"slow application\" reports "
                "resolve to one dependency, one saturated resource, or a change that landed recently."
            ),
            analogy=(
                "\"The journey took ages\" is not a diagnosis. You need to know which leg of it, compared "
                "with what, and whether it was the traffic or the train."
            ),
            context=(
                "Two habits make this fast. First, always ask what changed - a deployment, a configuration "
                "change, a data volume increase, an infrastructure event - because the answer is in that "
                "list far more often than not. Second, check whether it is the tail or the whole "
                "distribution: a p99 regression with a flat p50 points at a specific slow path, contention "
                "or garbage collection, whereas everything shifting points at a shared resource or a "
                "dependency."
            ),
            steps=[
                "Convert the complaint into numbers: operation, percentile, baseline, scope, start time.",
                "Ask what changed - deploys, config, data volume, infrastructure - and check the timeline.",
                "Measure at each hop of the request path rather than assuming where the time goes.",
                "Fix the identified bottleneck, then record the new baseline and add an alert on the "
                "relevant percentile.",
            ],
            evidence=[
                "histogram_quantile(0.99, ...) and (0.50, ...) for the same service, over 7 days",
                "oc rollout history deploy/<name> ; recent config and image changes",
                "Dependency latency: database, cache, downstream service, storage",
            ],
            redflag=(
                "Do not start tuning before measuring. Tuning without a baseline is how people spend a week "
                "making something 3% faster."
            ),
            followup="p99 doubled but p50 is unchanged. What does that pattern suggest?",
        ),
        Q(
            q="Multiple unrelated things are failing at once. How do you triage?",
            level=SENIOR,
            answer=(
                "Simultaneous unrelated symptoms almost always mean one shared dependency, so I stop looking "
                "at the symptoms and look for the common factor. The usual candidates are the API server or "
                "etcd, DNS, the ingress layer, storage, identity, or a whole failure domain such as a zone. "
                "I establish scope and blast radius first, communicate early, and work down the shared "
                "dependency list rather than investigating each symptom in parallel."
            ),
            analogy=(
                "When every appliance in the house stops at once, you check the fuse box - you do not open "
                "up the fridge, the washing machine and the boiler simultaneously."
            ),
            context=(
                "The organisational failure in these incidents is as important as the technical one. Under "
                "pressure, several people start investigating different symptoms and nobody is looking at "
                "the shared layer, while stakeholders receive three contradictory updates. Naming an "
                "incident commander, declaring the working hypothesis explicitly, and communicating on a "
                "fixed cadence is what turns a scramble into a controlled response."
            ),
            steps=[
                "Establish scope: which services, which namespaces, which zones, and since when.",
                "Look for the shared dependency instead of investigating each symptom independently.",
                "Assign a commander and communicate early with a stated hypothesis and next update time.",
                "Mitigate at the shared layer, validate broadly, and capture evidence for the review.",
            ],
            evidence=[
                "oc get co ; oc get nodes ; oc get clusterversion",
                "oc get events -A --sort-by=.lastTimestamp | tail -50",
                "Zone-level view: pods, nodes and dependencies grouped by topology label",
            ],
            redflag=(
                "Do not let three people investigate three symptoms in parallel. You will get three partial "
                "answers and no diagnosis."
            ),
            followup="Every namespace reports DNS failures. Where do you look, in order?",
        ),
        Q(
            q="How do you preserve evidence while restoring service?",
            level=SENIOR,
            answer=(
                "By capturing before mitigating, deliberately and quickly. Events expire, pod logs vanish "
                "when the pod is deleted, and node state changes on reboot - so the first two minutes should "
                "capture events, describe output, previous logs and a must-gather if the cluster is "
                "involved. Where possible I isolate rather than destroy: cordon a node instead of rebooting "
                "it, scale a bad replica to zero instead of deleting it, so the artefact still exists."
            ),
            analogy=(
                "It is photographing the scene before the road is reopened. The traffic has to move, but "
                "the crash investigation still needs to happen."
            ),
            context=(
                "This is the difference between an incident you learn from and one you repeat. The classic "
                "loss is deleting a crashing pod to force a fresh one, which removes the only copy of the "
                "logs that explained the crash. Building capture into the first step of every runbook - "
                "with the commands already written down - means it happens under pressure instead of being "
                "remembered afterwards."
            ),
            steps=[
                "Capture first: events to a file, describe output, previous container logs, relevant "
                "metrics screenshots or queries.",
                "Start a must-gather in the background if the platform is implicated.",
                "Prefer isolation over destruction - cordon, scale to zero, or move traffic away.",
                "Record a timeline as you go, with timestamps, so the review does not rely on memory.",
            ],
            evidence=[
                "oc adm must-gather --dest-dir=./mg-$(date +%s)",
                "oc get events -A --sort-by=.lastTimestamp > events-$(date +%s).txt",
                "oc logs <pod> --previous > pod-previous.log ; oc describe pod <pod> > pod-describe.txt",
            ],
            redflag=(
                "Do not delete the failing pod to get a fresh one before capturing its logs. That evidence "
                "does not come back."
            ),
            followup="You have five minutes before you must restore service. What do you capture?",
        ),
        Q(
            q="When and how do you escalate to vendor support?",
            level=SENIOR,
            answer=(
                "When the problem is in the platform rather than the workload, when a supported procedure "
                "is not behaving as documented, or when resolution needs a code fix or product guidance. I "
                "escalate early with a complete package: must-gather, a clear problem statement with impact "
                "and business severity, a timeline of what changed, what I have already tried and ruled out, "
                "and the specific question I need answered. Vague cases with no data sit in queues."
            ),
            analogy=(
                "It is a referral to a specialist. Sending the notes, the scans and a clear question gets "
                "an answer; sending \"patient feels unwell\" gets a waiting list."
            ),
            context=(
                "Two practical points matter. Escalate in parallel with your own investigation rather than "
                "after exhausting it - the case takes time to move regardless, and you can always close it. "
                "And gather must-gather while the problem is present, because a bundle collected after the "
                "cluster recovered often contains nothing useful. Setting severity honestly matters too: "
                "inflating it burns credibility you will need later."
            ),
            steps=[
                "Decide it is a platform problem rather than a workload one, and say why.",
                "Collect must-gather while the symptom is present, plus targeted component gathers.",
                "Write the case as impact, timeline, what changed, what you ruled out, and the specific "
                "question.",
                "Set severity honestly, escalate in parallel with your own work, and keep the case updated "
                "as you learn more.",
            ],
            evidence=[
                "oc adm must-gather ; oc adm must-gather -- /usr/bin/gather_<component>",
                "oc adm inspect ns/<namespace> --dest-dir=./inspect",
                "oc get clusterversion -o jsonpath='{.status.desired.version}{\"\\n\"}' ; oc get co",
            ],
            redflag=(
                "Do not open a case without must-gather. The first reply will ask for it, and you will have "
                "lost a day."
            ),
            followup="The cluster recovered before you collected must-gather. What do you send instead?",
        ),
        Q(
            q="What does good incident communication look like?",
            level=SENIOR,
            answer=(
                "One person owns communication, updates go out on a fixed cadence even when there is "
                "nothing new, and each update says the same four things: what is affected in user terms, "
                "what we currently believe, what we are doing next, and when the next update will be. "
                "Uncertainty is stated plainly rather than smoothed over. Technical detail goes in the "
                "engineering channel; stakeholders get impact and expectations."
            ),
            analogy=(
                "It is an airline announcing a delay. \"We are waiting on a part, next update in twenty "
                "minutes\" keeps people calm. Silence does not, and neither does a technical explanation of "
                "the part."
            ),
            context=(
                "The cadence is what buys you room to work. Without it, stakeholders interrupt constantly "
                "for status and the responders lose focus, which is a real and measurable cost during an "
                "incident. Separating the commander from the person communicating and from the person "
                "typing commands is not bureaucracy - it is what stops the one person who understands the "
                "problem from spending the incident writing updates."
            ),
            steps=[
                "Assign roles explicitly: commander, communicator, and the people doing the work.",
                "Send updates on a fixed cadence with impact, belief, next action and next update time.",
                "State uncertainty honestly and avoid predicting resolution times you cannot support.",
                "Separate stakeholder communication from the technical channel, and log the timeline as "
                "you go.",
            ],
            evidence=[
                "Incident timeline with timestamped updates and decisions",
                "Stakeholder update log showing cadence adherence",
                "Post-incident survey: did stakeholders feel informed",
            ],
            redflag=(
                "Do not go quiet while you investigate. Silence is read as loss of control and generates "
                "more interruptions than any update would."
            ),
            followup="A stakeholder demands an ETA you cannot give. What do you say?",
        ),
        Q(
            q="What makes a useful blameless postmortem?",
            level=ARCHITECT,
            answer=(
                "A factual timeline, an honest account of what people believed at each point and why those "
                "beliefs were reasonable, contributing factors rather than a single root cause, and "
                "follow-up actions with named owners and dates. Blameless means focusing on why the system "
                "made the mistake easy rather than on who made it - because in a blame culture people stop "
                "reporting near misses, and you lose the information that prevents the next incident."
            ),
            analogy=(
                "It is an air accident investigation. Nobody blames the pilot for the design of a confusing "
                "switch - they redesign the switch, and every other aircraft benefits."
            ),
            context=(
                "The measure of whether postmortems are working is not how well written they are but "
                "whether the actions get done. Most organisations produce good documents and complete a "
                "minority of the follow-ups, which means the same incident recurs and people quietly "
                "conclude the process is theatre. Tracking action completion rate, and reviewing repeat "
                "incidents against previous postmortems, is what makes it real."
            ),
            steps=[
                "Build a factual timeline including detection, decisions and communication, with "
                "timestamps.",
                "Describe contributing factors and what made the wrong action easy or the right one hard.",
                "Write actions that are specific, owned and dated - and reject vague ones like \"be more "
                "careful\".",
                "Track completion rate and check repeat incidents against earlier postmortems.",
            ],
            evidence=[
                "Postmortem documents with completed action items and dates",
                "Action completion rate over the last twelve months",
                "Repeat incident analysis: which recurrences had a prior postmortem",
            ],
            redflag=(
                "Do not produce postmortems whose actions are never completed. It is worse than not writing "
                "them, because it teaches people the process is decoration."
            ),
            followup="The same incident recurred despite a postmortem. What went wrong with the process?",
        ),
        Q(
            q="How do you systematically reduce recurring incidents?",
            level=ARCHITECT,
            answer=(
                "By treating incidents as data rather than as individual events. I categorise them by "
                "contributing factor over a quarter, look for the themes - configuration drift, capacity, a "
                "particular dependency, change process - and attack the theme rather than the instance. That "
                "usually means a platform change that removes a whole class: a guardrail in admission "
                "policy, a default in the golden path, an automated check in the pipeline, or better "
                "capacity headroom."
            ),
            analogy=(
                "It is public health rather than medicine. Treating each patient works; fixing the water "
                "supply stops the queue forming."
            ),
            context=(
                "The distinction that matters is between incident management, which is about restoring "
                "service, and problem management, which is about eliminating causes. Organisations that only "
                "do the first get very good at recovering from the same failure repeatedly. Making the "
                "quarterly theme review a standing commitment - with engineering time reserved for it - is "
                "what converts firefighting capability into reliability."
            ),
            steps=[
                "Categorise incidents by contributing factor and review the distribution quarterly.",
                "Pick the top one or two themes and design a platform-level control that removes the class.",
                "Reserve engineering capacity for that work explicitly, not as spare-time effort.",
                "Measure the effect - incident rate within that category before and after - and publish it.",
            ],
            evidence=[
                "Incident categorisation over the last four quarters, by contributing factor",
                "Guardrails added: admission policies, golden path defaults, pipeline checks",
                "Incident rate per category before and after each intervention",
            ],
            redflag=(
                "Do not measure success by incidents resolved. Getting faster at fixing the same thing is "
                "not reliability improvement."
            ),
            followup="Your top theme is configuration drift. What platform change removes that class?",
        ),
    ],
)
