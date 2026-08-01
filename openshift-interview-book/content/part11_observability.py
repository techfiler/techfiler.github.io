"""Part 11 - Monitoring, logging and SRE practice."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=11,
    title="Observability and reliability engineering",
    subtitle="Knowing what is happening, proving it, and being woken up only when it matters",
    intro=(
        "Observability questions separate people who install monitoring from people who use it. The first "
        "group can name the components; the second can tell you which signal answers which question, why "
        "their alert count went down after they improved reliability, and what they deleted from the "
        "dashboard because nobody ever acted on it. Interviewers are listening for a connection between "
        "technical measurement and user impact - if every answer stops at CPU graphs, the conversation "
        "never reaches the senior half of the scorecard."
    ),
    infographics=["observability_signals"],
    questions=[
        Q(
            q="Explain the OpenShift monitoring architecture.",
            level=FOUNDATION,
            answer=(
                "The platform monitoring stack is managed by the Cluster Monitoring Operator. Prometheus "
                "instances scrape metrics from the control plane, nodes through node-exporter, and cluster "
                "components; kube-state-metrics turns API objects into metrics; Alertmanager handles routing, "
                "grouping and silencing of alerts; and Thanos provides query aggregation and, where "
                "configured, longer retention. There is a separate stack for user workload monitoring so "
                "application metrics do not interfere with platform ones."
            ),
            analogy=(
                "It is a building management system. Sensors everywhere, one place that collects readings, "
                "another that decides who gets phoned, and a records room for the history."
            ),
            context=(
                "The separation between platform and user-workload monitoring is the detail worth knowing, "
                "because it is the answer to a very common question: how do application teams get their own "
                "metrics and alerts without being given access to the platform stack. It also explains why "
                "the platform Prometheus is not configurable in arbitrary ways - it is operator-managed, and "
                "changes go through the CMO's configuration rather than by editing its objects."
            ),
            steps=[
                "Name the components and what each is responsible for.",
                "Explain the platform versus user-workload split and why it exists.",
                "Say that the stack is operator-managed, so configuration goes through the CMO ConfigMap.",
                "Point out retention as the design decision: local Prometheus retention is short by default.",
            ],
            evidence=[
                "oc -n openshift-monitoring get pods",
                "oc -n openshift-monitoring get cm cluster-monitoring-config -o yaml",
                "oc get co monitoring -o jsonpath='{.status.conditions}' | python3 -m json.tool",
            ],
            redflag=(
                "Do not offer to edit the Prometheus object directly. It is operator-managed and your change "
                "will be reverted."
            ),
            followup="How do application teams get their own alerts without access to platform monitoring?",
        ),
        Q(
            q="What is a ServiceMonitor, and when would you use a PodMonitor instead?",
            level=FOUNDATION,
            answer=(
                "A ServiceMonitor tells Prometheus to scrape the endpoints behind a Service, selected by "
                "labels, on a named port and path. It is the normal choice because it follows the Service "
                "abstraction and picks up new pods automatically. A PodMonitor scrapes pods directly by "
                "label, which you need when the pods are not behind a Service at all, or when you need to "
                "scrape a port the Service does not expose."
            ),
            analogy=(
                "A ServiceMonitor is delivering to the department; a PodMonitor is delivering to named "
                "individuals. The first is usually right, and occasionally the person is not in a "
                "department."
            ),
            context=(
                "The overwhelmingly common failure with both is that nothing gets scraped and no error "
                "appears anywhere. The causes are always the same short list: label selector does not match, "
                "the port is referenced by the wrong name, the namespace is not in the monitor's scope, or "
                "user-workload monitoring is not enabled. Checking Prometheus's target list directly is the "
                "fastest way to see which of those it is."
            ),
            steps=[
                "Define both and state the default preference for ServiceMonitor.",
                "Give the cases that require a PodMonitor - no Service, or a port not exposed by one.",
                "Name the four usual causes of silent scrape failure.",
                "Verify in Prometheus's targets view rather than assuming the object is enough.",
            ],
            evidence=[
                "oc get servicemonitor,podmonitor -A",
                "oc -n openshift-user-workload-monitoring get pods",
                "Prometheus UI: Status, Targets - filter by job and read the last scrape error",
            ],
            redflag=(
                "Do not assume creating a ServiceMonitor means metrics are being collected. Check the target "
                "list; silent failure is the norm."
            ),
            followup="Your ServiceMonitor exists and no metrics appear. What are your four checks?",
        ),
        Q(
            q="What is a PrometheusRule?",
            level=FOUNDATION,
            answer=(
                "A PrometheusRule holds two kinds of rules. Alerting rules define a PromQL expression, a "
                "duration it must hold true for, labels such as severity, and annotations carrying the "
                "summary and runbook link. Recording rules precompute expensive expressions into new time "
                "series. Both are namespaced objects, so application teams can manage their own alerts "
                "declaratively in Git alongside the workload."
            ),
            analogy=(
                "It is the standing instruction to the night porter: if this condition holds for this long, "
                "phone this person, and here is what to tell them."
            ),
            context=(
                "The annotations are the part that determines whether the alert is useful at 3am. An alert "
                "that says \"HighMemoryUsage\" with no summary, no impact statement and no runbook link "
                "produces a phone call and then twenty minutes of orientation. The same alert with a "
                "one-line description of user impact and a link to the runbook produces action. Treating "
                "annotations as required fields rather than optional decoration is a small policy with a "
                "large effect."
            ),
            steps=[
                "Define alerting and recording rules and the fields each needs.",
                "Insist on severity, a summary describing user impact, and a runbook link as mandatory.",
                "Explain the for duration as the noise filter it is.",
                "Keep rules in Git with the workload so they are reviewed like code.",
            ],
            evidence=[
                "oc get prometheusrule -A",
                "oc get prometheusrule <name> -n <ns> -o yaml | head -40",
                "Prometheus UI: Alerts - check for rules firing without annotations",
            ],
            redflag=(
                "Do not ship alerts without a runbook link. You are scheduling somebody else's confusion "
                "for the middle of the night."
            ),
            followup="What fields would you make mandatory on every alert in your organisation?",
        ),
        Q(
            q="What does Alertmanager do?",
            level=FOUNDATION,
            answer=(
                "Alertmanager takes alerts that Prometheus has fired and decides what happens to them: "
                "grouping related alerts into one notification, routing by label to the right team and "
                "channel, inhibiting lower-priority alerts when a higher-priority one covers the same "
                "problem, silencing during maintenance, and deduplicating across replicas. Prometheus "
                "decides what is true; Alertmanager decides who finds out and how."
            ),
            analogy=(
                "It is the switchboard. The smoke detector decides there is smoke; the switchboard decides "
                "whether that means one phone call to the duty manager or fifty calls to everybody."
            ),
            context=(
                "Inhibition and grouping are what make a large cluster survivable during an incident. When a "
                "node fails, dozens of alerts fire - pods down, endpoints missing, probes failing - and "
                "without inhibition rules the on-call engineer gets buried in symptoms while the one alert "
                "that names the cause scrolls past. Configuring inhibition so a node-level alert suppresses "
                "its downstream symptoms is a high-value, low-effort improvement."
            ),
            steps=[
                "Separate the roles: Prometheus evaluates, Alertmanager routes.",
                "Name the five behaviours - group, route, inhibit, silence, deduplicate.",
                "Explain inhibition with a concrete cause-and-symptom example.",
                "Route by label to owning teams, and use silences for planned maintenance rather than "
                "disabling rules.",
            ],
            evidence=[
                "oc -n openshift-monitoring get secret alertmanager-main -o jsonpath='{.data.alertmanager\\.yaml}' | base64 -d | head -40",
                "oc -n openshift-monitoring get pods -l alertmanager=main",
                "Alertmanager UI: active alerts, grouped, with silences listed",
            ],
            redflag=(
                "Do not disable an alert rule to stop noise during maintenance. Use a silence, so the rule "
                "comes back automatically."
            ),
            followup="A node fails and forty alerts fire. How do you make that one notification?",
        ),
        Q(
            q="What are the four golden signals, and what does saturation mean?",
            level=FOUNDATION,
            answer=(
                "Latency, traffic, errors and saturation. Latency is how long requests take, and it should "
                "be measured at percentiles rather than averages. Traffic is demand - requests per second. "
                "Errors is the failure rate, including requests that succeed but too slowly to be useful. "
                "Saturation is how full the constrained resource is - the queue depth, the connection pool, "
                "the disk throughput - which is what tells you how close to falling over you are."
            ),
            analogy=(
                "It is a motorway. Journey time, number of cars, crashes, and how close to capacity the "
                "lanes are. The last one is the only one that predicts the others."
            ),
            context=(
                "Saturation is the signal most teams neglect and the only leading indicator among the four. "
                "Latency, traffic and errors tell you what is happening now; saturation tells you what will "
                "happen in twenty minutes. It is also the hardest to instrument because the constrained "
                "resource is application-specific - a thread pool, a connection limit, an IO queue - and "
                "generic CPU dashboards do not capture it."
            ),
            steps=[
                "Name the four signals and what each answers.",
                "Insist on percentiles for latency and explain why averages hide the problem.",
                "Define saturation as the fill level of the actual constraint, and call it the leading "
                "indicator.",
                "Identify the real constraint per service rather than defaulting to CPU.",
            ],
            evidence=[
                "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
                "sum(rate(http_requests_total{code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
                "Queue depth, connection pool utilisation or IO wait for the specific service",
            ],
            redflag=(
                "Do not present average latency as your reliability metric. The average is fine while the "
                "worst 1% of users are having an outage."
            ),
            followup="What is the saturation signal for a service backed by a connection pool?",
        ),
        Q(
            q="How do you set up monitoring for application workloads?",
            level=INTERMEDIATE,
            answer=(
                "I enable user-workload monitoring in the cluster monitoring configuration, which starts a "
                "separate Prometheus stack for application namespaces. Teams then create ServiceMonitors and "
                "PrometheusRules in their own namespaces, and they can query and alert on their own metrics "
                "without any access to platform monitoring. The platform team provides the dashboards, the "
                "alert routing and the guardrails on cardinality and retention."
            ),
            analogy=(
                "It is giving each department its own filing cabinet in a shared records room. Their "
                "documents, their keys, the building's fire rules."
            ),
            context=(
                "The guardrails matter as much as the enablement. Without limits, one team's high-cardinality "
                "metric can consume the memory of the shared user-workload Prometheus and take monitoring "
                "down for everyone. So the platform offer should include a documented cardinality budget, "
                "retention limits, and a review of new metrics as part of the golden path - not just a "
                "feature flag and good luck."
            ),
            steps=[
                "Enable user-workload monitoring through the cluster monitoring ConfigMap.",
                "Publish how teams create ServiceMonitors and PrometheusRules in their namespaces.",
                "Set resource limits, retention and a documented cardinality budget for the stack.",
                "Provide default dashboards and alert routing so teams start from something that works.",
            ],
            evidence=[
                "oc -n openshift-monitoring get cm cluster-monitoring-config -o jsonpath='{.data.config\\.yaml}'",
                "oc -n openshift-user-workload-monitoring get pods",
                "prometheus_tsdb_head_series   # in the user-workload stack",
            ],
            redflag=(
                "Do not enable user-workload monitoring without limits. One team's label choice can take "
                "down monitoring for the whole cluster."
            ),
            followup="One namespace's metrics are consuming most of the stack's memory. What do you do?",
        ),
        Q(
            q="Why is metrics cardinality dangerous?",
            level=INTERMEDIATE,
            answer=(
                "Every unique combination of label values creates a separate time series, and Prometheus "
                "holds those series in memory. Put a high-cardinality value in a label - a user ID, a "
                "request ID, a full URL path, a pod name on a workload that restarts constantly - and one "
                "metric becomes millions of series. The monitoring stack then consumes enormous memory, "
                "queries slow to a crawl, and eventually the thing that was supposed to warn you is the "
                "thing that is down."
            ),
            analogy=(
                "It is filing one document per customer interaction instead of one per customer. The "
                "cabinet is technically correct and nobody can find anything, including the fire "
                "inspector."
            ),
            context=(
                "The bitter irony is the failure mode: monitoring dies during the incident it was meant to "
                "observe, because the incident generated the churn that exploded the cardinality. Prevention "
                "is a review habit - challenge every new label, aggregate high-cardinality dimensions into "
                "buckets, and watch the head series count as a first-class metric with an alert on its "
                "growth rate rather than just its absolute value."
            ),
            steps=[
                "Explain the series-per-label-combination model and where the memory goes.",
                "Name the usual offenders: IDs, full paths, timestamps, unbounded user-supplied values.",
                "Monitor head series count and alert on growth rate, not just a threshold.",
                "Review new metrics before they ship, and bucket high-cardinality dimensions instead of "
                "labelling them.",
            ],
            evidence=[
                "prometheus_tsdb_head_series ; topk(10, count by (__name__)({__name__=~\".+\"}))",
                "oc -n openshift-monitoring adm top pod",
                "Prometheus UI: Status, TSDB Status - top series by metric name",
            ],
            redflag=(
                "Do not put a request ID or a raw URL in a metric label. It is the single most reliable way "
                "to destroy a monitoring stack."
            ),
            followup="Head series doubled overnight. How do you find the cause in five minutes?",
        ),
        Q(
            q="What is a recording rule and when do you need one?",
            level=INTERMEDIATE,
            answer=(
                "A recording rule evaluates an expression on a schedule and stores the result as a new time "
                "series. You need one when an expression is expensive and used repeatedly - a dashboard "
                "panel that aggregates across thousands of series, or an alert that would otherwise "
                "recompute a heavy query every evaluation cycle. It trades a small amount of storage for a "
                "large reduction in query cost and much more predictable dashboard load times."
            ),
            analogy=(
                "It is doing the monthly totals once and writing them down, rather than adding up every "
                "receipt each time somebody asks."
            ),
            context=(
                "The practical trigger is dashboards that take ten seconds to load or alerts that time out "
                "during evaluation, which is exactly when you need them most. Naming matters too - the "
                "convention of level:metric:operation makes recorded series discoverable, whereas "
                "arbitrarily named rules become a set of series nobody understands and nobody dares delete."
            ),
            steps=[
                "Define the mechanism: scheduled evaluation stored as a new series.",
                "Identify candidates - expensive expressions used by multiple dashboards or alerts.",
                "Follow a naming convention so recorded series are discoverable.",
                "Measure the improvement in query duration, and remove rules nothing consumes.",
            ],
            evidence=[
                "prometheus_rule_evaluation_duration_seconds by rule group",
                "oc get prometheusrule -A -o yaml | grep -c 'record:'",
                "Dashboard load time before and after",
            ],
            redflag=(
                "Do not create recording rules for every query. Each one is a permanent cost, and most "
                "queries are not run often enough to justify it."
            ),
            followup="An alert times out during evaluation. Is a recording rule the right fix?",
        ),
        Q(
            q="How do you design cluster logging?",
            level=INTERMEDIATE,
            answer=(
                "I start from the questions logs need to answer and the retention the organisation is "
                "legally required to keep, then work backwards. Collection is a per-node agent gathering "
                "container and node logs; forwarding sends them to an external store, because keeping long "
                "retention on cluster storage is expensive and couples log availability to cluster health. "
                "Applications should log structured JSON to stdout with a correlation ID, and never write "
                "logs to a persistent volume."
            ),
            analogy=(
                "It is CCTV footage. Recording it is easy, storing years of it is the expensive part, and "
                "the value depends entirely on whether you can find the right three minutes."
            ),
            context=(
                "The design decision with the biggest cost impact is retention tiering: short retention "
                "hot and searchable, longer retention in cheap object storage. The decision with the "
                "biggest usefulness impact is structure - unstructured multi-line stack traces are almost "
                "unsearchable, whereas structured logs with a correlation ID let you follow one request "
                "across services. Both are conventions you set in the golden path rather than negotiating "
                "per team."
            ),
            steps=[
                "Define the questions and the compliance retention requirement first.",
                "Collect at the node, forward off-cluster, and tier retention by cost and search need.",
                "Standardise structured JSON to stdout with correlation IDs in the golden path.",
                "Budget for volume, alert on ingestion rate, and review what is actually being queried.",
            ],
            evidence=[
                "oc get clusterlogforwarder,clusterlogging -n openshift-logging",
                "oc -n openshift-logging get pods -o wide",
                "Log ingestion rate and storage growth per namespace",
            ],
            redflag=(
                "Do not keep long log retention on cluster storage. It is expensive and it disappears in "
                "exactly the incident where you need it."
            ),
            followup="Log volume tripled after a release. How do you find out which service and why?",
        ),
        Q(
            q="What makes an alert actionable?",
            level=INTERMEDIATE,
            answer=(
                "It fires on user-visible impact or on a genuine leading indicator, not on a raw resource "
                "number. It has a clear owner and routes to them. It says what is broken and for whom in "
                "the summary. It links to a runbook with steps that work. And there is something the "
                "responder can actually do at the moment it fires. If an alert fails any of those, it is "
                "noise, and noise trains people to ignore the alerts that matter."
            ),
            analogy=(
                "A smoke alarm that goes off when you make toast is not a safety device any more. It is "
                "the thing people take the battery out of."
            ),
            context=(
                "The measurable version of this is alert-to-action ratio: what fraction of pages resulted in "
                "somebody doing something. Most organisations that measure it for the first time find "
                "numbers well under half, and the fix is deletion rather than tuning - remove the alerts "
                "nobody acts on, and convert the informational ones into dashboards or tickets. That single "
                "exercise usually improves on-call more than any tooling change."
            ),
            steps=[
                "Alert on symptoms and impact; leave causes to dashboards unless they are leading "
                "indicators.",
                "Require owner, severity, impact summary and runbook link on every alert.",
                "Measure alert-to-action ratio and delete alerts that nobody acts on.",
                "Review firing alerts after every incident and after every quiet week, in both directions.",
            ],
            evidence=[
                "ALERTS{alertstate=\"firing\"} counts by alertname over 30 days",
                "Paging history with disposition - actioned, acknowledged only, or auto-resolved",
                "Alert definitions missing runbook_url annotations",
            ],
            redflag=(
                "Do not defend an alert that has never been acted on because it \"might matter one day\". "
                "It is actively degrading the alerts that do."
            ),
            followup="Your team gets 200 pages a month and acts on 30. Where do you start?",
        ),
        Q(
            q="Explain SLOs and error budgets.",
            level=SENIOR,
            answer=(
                "An SLI is a measurement of user experience - the proportion of requests served "
                "successfully and fast enough. An SLO is the target for that measurement over a window, say "
                "99.9% over thirty days. The error budget is what is left over: 0.1% of requests may fail "
                "without breaking the promise. That budget turns reliability from an argument into "
                "arithmetic - if it is being consumed quickly, you pause risky changes; if it is barely "
                "touched, you can afford to move faster."
            ),
            analogy=(
                "It is a monthly allowance for failure. Spend it slowly and you can take risks at the end "
                "of the month; blow it in week one and you are on a strict budget until it resets."
            ),
            context=(
                "The reason this appears in senior interviews is that it changes conversations rather than "
                "dashboards. Without an SLO, \"is this reliable enough?\" is a matter of opinion and the "
                "loudest voice wins. With one, it is a number both sides can look at. The failure mode is "
                "setting SLOs from aspiration rather than measurement - a 99.99% target on a service whose "
                "dependencies cannot support it produces a permanently exhausted budget that everyone "
                "learns to ignore."
            ),
            steps=[
                "Define SLI, SLO and error budget precisely, with a concrete example.",
                "Derive the target from measured behaviour and user need, not from a round number.",
                "Agree the policy in advance: what happens when the budget burns fast, and who decides.",
                "Alert on burn rate rather than on instantaneous breaches, and review targets quarterly.",
            ],
            evidence=[
                "SLI query: successful and fast requests over total requests, over the SLO window",
                "Error budget remaining and burn rate over 1h and 6h windows",
                "Change freeze policy tied to budget exhaustion, agreed with the product owner",
            ],
            redflag=(
                "Do not propose 99.99% because it sounds good. If the dependencies cannot deliver it, the "
                "SLO is decoration."
            ),
            followup="Your error budget is exhausted in week one. What actually changes?",
        ),
        Q(
            q="How do you handle monitoring stack storage pressure?",
            level=SENIOR,
            answer=(
                "First I find out whether the growth is legitimate or a cardinality accident, because the "
                "responses are completely different. If a metric exploded, I fix the label at source. If "
                "growth is genuine, the levers are retention, scrape interval, dropping metrics nobody "
                "queries through relabelling, and moving long-term data into object storage through Thanos "
                "rather than expanding local volumes indefinitely."
            ),
            analogy=(
                "The archive room is full. You could rent more space, or you could notice that half of it is "
                "duplicate paperwork nobody has ever asked for."
            ),
            context=(
                "The urgent part is that Prometheus running out of disk means losing observability, and it "
                "usually happens during a period of high churn - which is to say, during an incident. So the "
                "real answer includes prevention: alerting on storage growth rate with enough lead time, and "
                "reviewing the top metrics by series count on a schedule so a bad label is caught in days "
                "rather than at capacity."
            ),
            steps=[
                "Determine whether growth is cardinality-driven or volume-driven before acting.",
                "Fix bad labels at source; use relabelling to drop metrics nothing queries.",
                "Tune retention and scrape interval deliberately, and document the trade-off.",
                "Move long-term retention to object storage, and alert on growth rate with lead time.",
            ],
            evidence=[
                "prometheus_tsdb_storage_blocks_bytes ; rate(prometheus_tsdb_head_series[1d])",
                "topk(20, count by (__name__)({__name__=~\".+\"}))",
                "oc -n openshift-monitoring get pvc",
            ],
            redflag=(
                "Do not just expand the volume. If a bad label caused it, you have bought a week and the "
                "same incident."
            ),
            followup="Prometheus has two days of disk left. What do you do in the next hour?",
        ),
        Q(
            q="When does distributed tracing earn its cost?",
            level=SENIOR,
            answer=(
                "When a request crosses enough services that latency cannot be attributed from metrics "
                "alone. Metrics tell you the service is slow; traces tell you which of the eleven downstream "
                "calls consumed the time and whether it was one slow dependency or a fan-out of many. In a "
                "monolith or a two-service system the cost of instrumenting and sampling is rarely worth it; "
                "past five or six services in a request path it becomes the only practical answer."
            ),
            analogy=(
                "Metrics tell you the parcel arrived late. Tracing is the scan history showing it sat in "
                "one depot for nine hours."
            ),
            context=(
                "The practical constraints are sampling and propagation. Sample too low and the rare slow "
                "request - the one you actually care about - is never captured, which is why tail-based "
                "sampling that keeps slow and errored traces is worth the extra complexity. Propagation is "
                "the harder organisational problem: a single service that does not forward trace headers "
                "breaks the chain for everyone downstream, so it has to be a platform-wide convention rather "
                "than a per-team choice."
            ),
            steps=[
                "State the threshold: request paths deep enough that attribution from metrics fails.",
                "Standardise context propagation across every service, as a platform convention.",
                "Choose a sampling strategy that retains slow and errored traces rather than a flat "
                "percentage.",
                "Connect traces to metrics and logs through shared identifiers so you can move between "
                "them.",
            ],
            evidence=[
                "Trace showing per-span duration across the request path",
                "Sampling configuration and retained trace volume",
                "Correlation ID present in logs, metrics exemplars and traces for the same request",
            ],
            redflag=(
                "Do not sample at a flat 1% and expect to debug rare latency. The slow requests are exactly "
                "the ones you will miss."
            ),
            followup="A service is slow at p99 only. How do traces help where metrics did not?",
        ),
        Q(
            q="How do you build an on-call practice people can sustain?",
            level=SENIOR,
            answer=(
                "Page only on user impact, and route everything else to tickets or dashboards. Give every "
                "page a runbook that has been tested by someone who did not write it. Track pages per shift "
                "and treat a rising number as a defect, not as a fact of life. Run blameless reviews for "
                "anything that woke someone, and make the follow-up action a real backlog item with an "
                "owner. And rotate fairly, with enough people that nobody is permanently on call."
            ),
            analogy=(
                "It is a night shift rota. Sustainable if the workload is real and predictable; a "
                "resignation letter if it is constant false alarms."
            ),
            context=(
                "The metric that changes behaviour is pages per shift, because it is visible and "
                "uncomfortable. Once it is tracked, alert quality improvements get prioritised the same way "
                "features do. The other habit that matters is treating the runbook as a product: after every "
                "incident, the responder updates the runbook while it is fresh, which is what stops the same "
                "twenty minutes of orientation happening every time."
            ),
            steps=[
                "Define the paging bar - user impact or imminent user impact only.",
                "Require a tested runbook per page, and update it immediately after each use.",
                "Track pages per shift and time-to-acknowledge as reliability metrics of the alerting "
                "system.",
                "Review every page in a blameless forum, and convert findings into owned backlog items.",
            ],
            evidence=[
                "Pages per shift, trended over months",
                "Percentage of alerts with a tested runbook link",
                "Follow-up action completion rate from incident reviews",
            ],
            redflag=(
                "Do not treat alert fatigue as an individual resilience problem. It is a defect in the "
                "alerting system and it should be tracked as one."
            ),
            followup="On-call is burning people out. What do you change in the first month?",
        ),
        Q(
            q="How would you design observability across a fleet of clusters?",
            level=ARCHITECT,
            answer=(
                "Local Prometheus in every cluster for short retention and fast local queries, with metrics "
                "shipped to a central long-term store for cross-cluster querying and history. Alerting stays "
                "local so a network partition does not blind a cluster, but alerts route to central "
                "handling. Dashboards are templated per cluster from one source. And I would decide the "
                "metric allow-list deliberately, because shipping everything from fifty clusters is a cost "
                "problem before it is a technical one."
            ),
            analogy=(
                "It is regional offices with local records and a central archive. Each office works if the "
                "line to head office drops, and head office can still see the whole picture."
            ),
            context=(
                "Keeping alert evaluation local is the design decision that gets tested during a real "
                "incident. Central evaluation means a network partition produces silence rather than alerts, "
                "which is the worst possible failure mode for a monitoring system. The cost decision is "
                "equally consequential: an unfiltered federation of fifty clusters can easily cost more than "
                "the clusters, and an allow-list of metrics that dashboards and alerts actually use is "
                "usually a fraction of what gets scraped."
            ),
            steps=[
                "Keep scraping and alert evaluation local so a partition degrades gracefully.",
                "Ship a deliberately filtered metric set to central long-term storage.",
                "Template dashboards and alert rules from one source, deployed by GitOps to every cluster.",
                "Track observability cost per cluster and review the allow-list against what is actually "
                "queried.",
            ],
            evidence=[
                "Central store ingestion rate and cost per cluster",
                "oc get prometheusrule -A per cluster, compared against the templated source",
                "Query patterns: which metrics are actually used by dashboards and alerts",
            ],
            redflag=(
                "Do not centralise alert evaluation. A network problem then produces silence instead of "
                "alarms."
            ),
            followup="Observability cost is now 20% of the platform budget. What do you cut first?",
        ),
        Q(
            q="How do you measure whether the platform is actually getting more reliable?",
            level=ARCHITECT,
            answer=(
                "With a small set of outcome metrics rather than activity metrics. SLO attainment per "
                "critical service. Incident count and severity trend. Time to detect and time to restore. "
                "Change failure rate. Percentage of incidents with a completed follow-up action. And a "
                "leading indicator or two, such as the proportion of workloads meeting the production "
                "readiness standard. Then I review them monthly and let them drive where engineering effort "
                "goes."
            ),
            analogy=(
                "It is a patient's vital signs rather than a list of treatments administered. What matters "
                "is whether they are getting better, not how busy the ward was."
            ),
            context=(
                "The trap is measuring activity - alerts configured, dashboards built, tickets closed - "
                "which rewards motion rather than outcomes. Time to detect and time to restore are the pair "
                "that most reliably expose whether observability and runbooks are improving, and change "
                "failure rate is the one that keeps delivery honest. Publishing the numbers, including the "
                "ones going the wrong way, is what makes the exercise credible internally."
            ),
            steps=[
                "Choose outcome metrics: SLO attainment, incident trend, detect and restore times, change "
                "failure rate.",
                "Add one or two leading indicators tied to the production readiness standard.",
                "Review monthly with the teams, and let the numbers set the improvement backlog.",
                "Publish the trend openly, including regressions, and revisit the metric set annually.",
            ],
            evidence=[
                "SLO attainment per service over rolling 90 days",
                "MTTD and MTTR distributions, not averages, per severity",
                "Change failure rate and follow-up action completion rate",
            ],
            redflag=(
                "Do not report activity metrics as reliability progress. Nobody cares how many dashboards "
                "exist if restore time is getting worse."
            ),
            followup="Incident count is flat but restore time halved. Is that success? Argue it.",
        ),
    ],
)
