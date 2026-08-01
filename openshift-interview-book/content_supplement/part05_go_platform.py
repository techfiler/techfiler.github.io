"""Part 5 - Go for platform engineers."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=5,
    title="Go for platform engineers",
    subtitle="The language behind client-go, operators and most of the control plane — and what interviewers actually probe",
    intro=(
        "Go is not optional on a senior platform team anymore. The Kubernetes API machinery, client-go, "
        "controller-runtime, the Operator SDK and a large fraction of the cluster components you operate "
        "are written in it. Interviewers rarely ask you to implement a red-black tree; they ask whether you "
        "can reason about goroutine lifetimes, whether you know why a controller requeues, and whether you "
        "would trust your own operator in production. This part covers the Go idioms and Kubernetes "
        "framework pieces that show up in those conversations."
    ),
    infographics=["control_plane_map"],
    questions=[
        Q(
            q="What is a goroutine, and when would you not spawn one?",
            level=FOUNDATION,
            answer=(
                "A goroutine is a lightweight concurrent function started with the go keyword. The Go runtime "
                "multiplexes thousands of them onto a small pool of OS threads, so they are cheap to create "
                "and cheap to block on I/O. You use them when work can proceed independently — serving HTTP "
                "requests, watching an API stream, fanning out health checks. You do not spawn one for "
                "every tiny task: unbounded goroutines on a hot path are a memory leak with a polite name, "
                "and anything that needs strict ordering is usually clearer with a channel or a worker pool "
                "than with goroutines firing at random."
            ),
            analogy=(
                "Goroutines are extra staff on a shift, not extra buildings. Hiring is fast, but if you "
                "hire everyone who walks past the door you will run out of desks."
            ),
            context=(
                "This shows up constantly in operators. A reconcile function that launches a goroutine per "
                "object without a wait group or context cancellation will leak work on shutdown and can "
                "double-apply changes during leader election flaps. Interviewers use this question to see "
                "whether you understand concurrency as a resource decision, not a syntax trick."
            ),
            steps=[
                "Define a goroutine as a concurrent function scheduled by the Go runtime, not an OS thread.",
                "Explain why they are cheap: small stacks, M:N scheduling, blocking does not pin a thread.",
                "Give a good use case — HTTP handler, watch loop, parallel I/O with a bounded fan-out.",
                "Name the failure mode — unbounded creation, work that outlives process shutdown, races on "
                "shared state — and point to channels, errgroup or a worker pool as the fix.",
            ],
            evidence=[
                "go tool pprof http://localhost:6060/debug/pprof/goroutine   # count stacks in a controller",
                "GODEBUG=gctrace=1 ./operator --zap-devel   # correlate goroutine growth with GC pressure",
                "grep -R 'go func' internal/controller/ | wc -l   # audit unbounded spawns in your codebase",
            ],
            redflag=(
                "Do not say \"just use a goroutine, they are free\". They are cheap, not free, and the "
                "runtime will not save you from spawning one per reconcile forever."
            ),
            followup="Your operator's goroutine count climbs during a thundering herd. How do you cap it?",
        ),
        Q(
            q="How do channels work, and what is the difference between buffered and unbuffered?",
            level=FOUNDATION,
            answer=(
                "A channel is a typed conduit for sending values between goroutines. An unbuffered channel "
                "synchronises: the sender blocks until a receiver is ready, which gives you a hand-off "
                "point. A buffered channel decouples sender and receiver up to its capacity — useful for "
                "worker pools and rate smoothing, dangerous if nobody drains it. Send and receive directions "
                "are part of the type. Closing a channel signals no more values; receivers should range or "
                "use the comma-ok form to detect close. The idiomatic rule is \"do not communicate by sharing "
                "memory; share memory by communicating\" — but only when a channel actually models the "
                "problem."
            ),
            analogy=(
                "Unbuffered is a direct hand-off at the door. Buffered is a tray on the counter — fine until "
                "the tray fills and the kitchen stops cooking."
            ),
            context=(
                "In platform code you see channels in rate limiters, shutdown signals and test harnesses. "
                "Controllers in client-go rarely expose channels to you directly — they use workqueues "
                "instead — but understanding blocking and back-pressure explains why a saturated queue "
                "stalls reconciliation. Senior interviews often pivot from channels to \"why doesn't "
                "controller-runtime use a channel for the informer cache?\""
            ),
            steps=[
                "State the purpose: safe communication and synchronisation between goroutines.",
                "Contrast unbuffered (rendezvous, enforces pairing) with buffered (decouples up to N).",
                "Explain close semantics — only the sender closes; receivers must handle zero values.",
                "Land on when not to use one — shared mutable state with a Mutex is sometimes clearer.",
            ],
            evidence=[
                "go test -race ./...   # channel misuse often surfaces as a data race first",
                "dlv debug ./cmd/manager --headless   # break on send/receive in a worker pool",
                "grep -n 'make(chan' internal/worker/pool.go   # review buffer sizes in your code",
            ],
            redflag=(
                "Do not pick buffer size 1000 because it \"feels safe\". Every buffer is a latency and "
                "memory trade-off you should be able to justify."
            ),
            followup="When would you reach for a sync.Mutex instead of a channel?",
        ),
        Q(
            q="What does select do, and how do you avoid starving a case?",
            level=INTERMEDIATE,
            answer=(
                "select waits on multiple channel operations and executes whichever case is ready first. If "
                "several are ready, Go chooses one at random — there is no priority. A default case makes "
                "the select non-blocking, which is useful for polling but easy to abuse into a busy loop. "
                "The classic pattern combines a work channel, a done channel from context cancellation, and "
                "sometimes a timer. Starvation happens when one case always wins — for example, a tight loop "
                "on default while a shutdown signal never runs — and the fix is to remove default, use "
                "context, or split responsibilities across goroutines."
            ),
            analogy=(
                "select is a receptionist with several ringing lines. If one caller never hangs up, everyone "
                "else waits — unless you have a rule for when to pick up which phone."
            ),
            context=(
                "You will write select in health checks, graceful shutdown and any custom controller "
                "machinery outside controller-runtime. In interviews the follow-up is almost always "
                "context.Context integration: select on ctx.Done() alongside your work channel so SIGTERM "
                "during a rolling update actually stops the goroutine."
            ),
            steps=[
                "Define select as multiplexing channel operations with random tie-breaking among ready cases.",
                "Show the three common cases: work, cancellation, timeout via time.After or context.",
                "Explain default — non-blocking receive/send — and why busy loops are a smell.",
                "Describe starvation and the fix: no default on hot paths, dedicated shutdown goroutine, or "
                "priority via separate selects.",
            ],
            evidence=[
                "grep -R 'select {' internal/ | head   # locate shutdown and worker loops",
                "go test -timeout 30s -run TestGracefulShutdown ./...",
                "kill -TERM $(pidof manager) ; sleep 2 ; ps aux | grep manager   # verify clean exit",
            ],
            redflag=(
                "Do not put heavy work inside the select body. select chooses; goroutines should do the work."
            ),
            followup="How does context cancellation replace a manual done channel in a worker loop?",
        ),
        Q(
            q="How should platform code use context.Context?",
            level=INTERMEDIATE,
            answer=(
                "context carries deadlines, cancellation signals and request-scoped values down a call chain. "
                "The rule for libraries and controllers is: accept Context as the first parameter, never "
                "store it in a struct. context.WithCancel, WithTimeout and WithDeadline create child "
                "contexts; cancelling the parent cancels all children. In Kubernetes code you pass "
                "ctx into client-go calls so watches and API requests stop promptly when reconcile ends or "
                "the process shuts down. Values in context are for request metadata — trace IDs, user "
                "identity — not for passing optional function parameters you were too lazy to thread."
            ),
            analogy=(
                "Context is the fire alarm for a building wing. Pull one lever and every room on that branch "
                "knows to stop and leave — but only if people actually listened when they moved in."
            ),
            context=(
                "This is non-negotiable in operator interviews. A Reconcile that ignores context will keep "
                "calling the API during leader loss, prolong shutdown past the kubelet's grace period, and "
                "fight the next leader's work. OpenShift and upstream controllers propagate context from "
                "manager.SetupWithManager through to client calls — breaking that chain is a production bug."
            ),
            steps=[
                "State the contract: first parameter, never stored, propagates cancellation and deadlines.",
                "Name WithCancel, WithTimeout, WithDeadline and what cancelling a parent does.",
                "Map it to reconcile: ctx from controller-runtime, pass to client.Get/List/Patch/Delete.",
                "Warn against context.Value abuse — only cross-cutting metadata, not business config.",
            ],
            evidence=[
                "grep -n 'context.Background()' controllers/   # Background in hot paths is a review flag",
                "oc logs -n <ns> deploy/<operator> | grep 'context canceled'",
                "dlv break reconcile.go:42   # inspect ctx.Err() on shutdown path",
            ],
            redflag=(
                "Do not say \"I use context.Background() everywhere in the controller\". That tells the "
                "interviewer your operator ignores SIGTERM semantics."
            ),
            followup="Reconcile runs past the 30-second timeout every time. Where do you enforce the deadline?",
        ),
        Q(
            q="When do you use sync.Mutex, and what is wrong with a global lock in a controller?",
            level=INTERMEDIATE,
            answer=(
                "A Mutex serialises access to shared mutable state — a cache map, a metrics counter, an "
                "in-memory index the controller maintains alongside the API. Lock before read/write, unlock "
                "with defer in the same function, and keep the critical section small. sync.RWMutex helps "
                "when reads dominate. In controllers the smell is a global Mutex around reconcile: it "
                "defeats parallelism, hides races you should fix with the API server's optimistic "
                "concurrency, and becomes a bottleneck under load. Prefer the apiserver as source of truth "
                "and patch with resourceVersion; use Mutex only for process-local bookkeeping."
            ),
            analogy=(
                "A Mutex is a toilet key for one stall. Fine for that stall; ridiculous if the whole "
                "building shares one key."
            ),
            context=(
                "client-go's informer cache is already thread-safe. Interviewers ask this to see if you "
                "reach for locks before understanding what the framework gives you. Real bugs show up when "
                "operators cache derived state — last applied checksum, external API tokens — without "
                "sync, or when tests pass because -race was never run in CI."
            ),
            steps=[
                "Define Mutex as mutual exclusion for shared memory, with defer unlock as the idiomatic pattern.",
                "Mention RWMutex when many readers and rare writers justify the complexity.",
                "Contrast with channels — Mutex for protecting state, channels for orchestration.",
                "Call out the controller anti-pattern: global lock serialising every reconcile.",
            ],
            evidence=[
                "go test -race ./controllers/...",
                "grep -R 'sync.Mutex' internal/ controllers/",
                "go tool trace trace.out   # look for lock contention in load tests",
            ],
            redflag=(
                "Do not say \"I add a Mutex whenever I have concurrency\". That usually means the design "
                "needs channels, the API server, or fewer shared variables."
            ),
            followup="How does resourceVersion give you lock-free concurrency against the API server?",
        ),
        Q(
            q="What does the race detector do, and when must you run it?",
            level=INTERMEDIATE,
            answer=(
                "Go's race detector instruments memory accesses at runtime and reports when two goroutines "
                "access the same variable and at least one is a write without synchronisation. Enable it with "
                "go test -race or go run -race. It slows execution and increases memory use — typically "
                "five to ten times — so you run it on unit and integration tests in CI, not on every local "
                "edit. It catches bugs that pass review: map writes from reconcile goroutines, lazy-init "
                "singletons, closed-over loop variables before Go 1.22. It does not catch every logic bug "
                "and it does not help with distributed races across the cluster — only your process."
            ),
            analogy=(
                "It is CCTV for shared desks. It will not stop someone taking your stapler, but it will "
                "prove two people reached for it at once."
            ),
            context=(
                "Platform teams shipping operators should treat -race in CI as seriously as go vet. A data "
                "race in a controller can corrupt an in-memory cache and write garbage back to the API "
                "server under load — intermittent, evil, and exactly the class of bug senior interviews "
                "ask you to prevent. OpenShift CI runs race-enabled tests on core components for this reason."
            ),
            steps=[
                "Explain what it detects: unsynchronised concurrent access, at least one write.",
                "Show how to enable it: -race on test and selective integration runs.",
                "State the cost: slower, more RAM — CI gate, not default dev loop.",
                "Note limits: in-process only; does not replace proper API-level concurrency design.",
            ],
            evidence=[
                "go test -race ./...",
                "grep -i race .github/workflows/*.yml .gitlab-ci.yml",
                "go test -race -count=50 ./controllers/   # flake hunt on suspicious tests",
            ],
            redflag=(
                "Do not say \"we will catch races in production\". Production is the wrong place to learn "
                "your operator has a data race."
            ),
            followup="Tests pass without -race but fail with it. What is your triage order?",
        ),
        Q(
            q="How does golang.org/x/sync/errgroup help in platform tooling?",
            level=SENIOR,
            answer=(
                "errgroup.Group wraps a set of goroutines and returns the first error from any of them, "
                "cancelling sibling work when tied to a context. g, ctx := errgroup.WithContext(parent) "
                "then g.Go(func() error { ... }) for each task; g.Wait() blocks for completion or failure. "
                "It is the right tool for parallel cluster checks — hit every node API, pull metrics from "
                "several endpoints, migrate objects in shards — where you want all-or-nothing semantics and "
                "clean cancellation. It replaces ad-hoc WaitGroups plus error channels plus manual cancel "
                "wiring that everyone gets slightly wrong."
            ),
            analogy=(
                "errgroup is a project manager who stops the whole job when one subcontractor walks off — "
                "and tells everyone else to down tools the same day."
            ),
            context=(
                "CLI tools and admission webhooks use errgroup heavily; controllers less so because "
                "reconcile is already serialised per object. Interviewers pair this with worker pools: "
                "errgroup for a fixed fan-out job, bounded channel workers for sustained throughput. "
                "Knowing both keeps you from using errgroup to launch ten thousand goroutines against "
                "the API server during a migration script."
            ),
            steps=[
                "Define errgroup: WaitGroup plus first-error propagation, optional context cancellation.",
                "Show WithContext pattern: one failed goroutine cancels ctx for the rest.",
                "Contrast with sync.WaitGroup — no built-in error return or cancel propagation.",
                "Give a platform example: parallel node validation with a concurrency cap via semaphore.",
            ],
            evidence=[
                "grep -R 'errgroup' cmd/ hack/ | head",
                "go doc golang.org/x/sync/errgroup",
                "time ./migrate --workers=20   # compare with and without cancel on first 500 error",
            ],
            redflag=(
                "Do not use errgroup to fire unbounded API calls. Pair it with a semaphore or a worker "
                "count you can defend."
            ),
            followup="One shard returns a retryable error. Do you fail the whole errgroup or wrap retry logic?",
        ),
        Q(
            q="How would you design a worker pool in Go for sustained API work?",
            level=SENIOR,
            answer=(
                "A worker pool fixes the number of goroutines consuming jobs from a channel. Producers send "
                "work items — object keys, node names, file paths — into a jobs channel; N worker goroutines "
                "range over it and call a handler; a WaitGroup or done channel signals completion. Size the "
                "pool from downstream limits: API server QPS, etcd latency, registry rate limits. Use "
                "context cancellation so workers exit when the parent shuts down. For error handling, either "
                "send results on a separate channel, use errgroup with a bounded semaphore, or collect "
                "errors in a sync-safe slice. The anti-pattern is one goroutine per item on a million-object "
                "backlog."
            ),
            analogy=(
                "It is a bank with four counters, not four thousand. Customers queue; the building does not "
                "hire a new teller for every person who walks in."
            ),
            context=(
                "Bulk adoption tools, custom pruners and migration controllers hit this in production. "
                "client-go's own rate limiting is per-client; your pool is the second line of defence. "
                "Interviewers want to hear you connect pool size to APF priority levels and 429 responses, "
                "not just recite channel syntax."
            ),
            steps=[
                "Sketch the components: jobs channel, fixed worker count, handler func, shutdown via context.",
                "Explain sizing: start from API limits and p99 latency, load-test, tune.",
                "Cover error aggregation — fail fast vs best-effort with a summary report.",
                "Mention alternatives: workqueue rate limiting in controllers, errgroup for bounded batches.",
            ],
            evidence=[
                "grep -R 'worker' cmd/ | grep -E 'chan|pool'",
                "oc adm top api-resources   # watch request rates during a bulk job",
                "curl -s localhost:9090/metrics | grep apiserver_request_total",
            ],
            redflag=(
                "Do not hard-code ten workers because it is a round number. Tie the number to a limit you "
                "measured or the API server will throttle you anyway."
            ),
            followup="Workers start getting 429 Too Many Requests. What do you change first — pool size or client QPS?",
        ),
        Q(
            q="How do Go interfaces work, and why does Kubernetes code use small ones?",
            level=FOUNDATION,
            answer=(
                "An interface is a set of method signatures. A type satisfies an interface implicitly by "
                "implementing those methods — no implements keyword. The empty interface any holds anything "
                "but costs a type assertion at use. Kubernetes and controller-runtime favour small interfaces "
                "— io.Reader, client.Reader, client.Writer — so mocks and fakes are easy in tests. "
                "client.Client is deliberately narrow compared to the raw clientset. Accept interfaces, "
                "return concrete types is the local idiomatic rule, though controllers often depend on "
                "client.Client injected by the manager."
            ),
            analogy=(
                "An interface is a job description. Anyone who can do the listed tasks gets hired; you do "
                "not care which university they attended."
            ),
            context=(
                "Interviewers use interfaces to probe testability. If you cannot explain why "
                "reconcile.Recorder is an interface but your database handle is a concrete struct, you "
                "will struggle on \"how do you unit test without a cluster\". Fake client from "
                "controller-runtime's fake package exists because Client is an interface."
            ),
            steps=[
                "Define implicit satisfaction and contrast with Java-style explicit implementation.",
                "Explain small interfaces — one or two methods — and the mocking benefit.",
                "Map to client-go: Client, Reader, StatusClient, the recorder pattern.",
                "Warn on interface{} / any soup in API types — use generics or concrete structs where clear.",
            ],
            evidence=[
                "go doc sigs.k8s.io/controller-runtime/pkg/client Client",
                "grep -R 'client.Client' controllers/ | head",
                "go test ./controllers/ -run TestReconcile -v   # fake client in unit tests",
            ],
            redflag=(
                "Do not create a fifteen-method interface \"for flexibility\". Large interfaces are harder "
                "to mock and usually mean the abstraction is wrong."
            ),
            followup="How does the fake client differ from envtest for controller tests?",
        ),
        Q(
            q="What is idiomatic error handling in Go for controllers and CLI tools?",
            level=INTERMEDIATE,
            answer=(
                "Go uses explicit error returns, not exceptions. Check err immediately; wrap with fmt.Errorf "
                "\"...: %w\", err to preserve the chain; inspect with errors.Is and errors.As. In controllers "
                "return (ctrl.Result{}, err) to requeue with exponential backoff, or (ctrl.Result{RequeueAfter: "
                "t}, nil) for known transient conditions. User-facing CLI messages belong at the top of "
                "main; libraries return errors without printing. Sentinel errors like ErrNotFound are fine "
                "for control flow if documented. panic is for programmer bugs, not failed API calls."
            ),
            analogy=(
                "Errors are receipts, not alarms. You pass the receipt up the chain until someone who can "
                "refund the customer — log, metric, requeue — is holding it."
            ),
            context=(
                "Operators that swallow errors or always return nil hide outages until CR status stops "
                "updating. Interviewers listen for wrap vs print, and for knowing when client.IgnoreNotFound "
                "is correct. Go 1.20+ errors.Join helps aggregate parallel failures in migration tools."
            ),
            steps=[
                "State the rule: check every error, wrap with context at boundaries.",
                "Show errors.Is/As for typed inspection — NotFound, Conflict, TooManyRequests.",
                "Map to reconcile returns: error for retry, RequeueAfter for timed retry, nil for done.",
                "Separate CLI: cobra RunE returns error to main; controller logs with log.FromContext(ctx).",
            ],
            evidence=[
                "grep -R 'fmt.Errorf.*%w' controllers/",
                "oc get <crd> <name> -o jsonpath='{.status.conditions}' | python3 -m json.tool",
                "controller-runtime metrics: workqueue_retries_total",
            ],
            redflag=(
                "Do not log an error and return nil in Reconcile. You have hidden the failure from the "
                "workqueue and the object will never retry."
            ),
            followup="When do you surface a terminal error in status.conditions instead of retrying forever?",
        ),
        Q(
            q="What are the moving parts of client-go for someone writing an operator?",
            level=INTERMEDIATE,
            answer=(
                "client-go is the Go client for the Kubernetes API. The pieces you actually touch are: "
                "rest.Config from kubeconfig or in-cluster service account; typed clientsets for built-in "
                "resources; the dynamic client for arbitrary GVRs; the informer/reflector pair that lists "
                "and watches, maintaining a local cache; the workqueue that deduplicates events into "
                "reconcile keys; and listers for cache reads without hitting the API. controller-runtime "
                "wraps these with a cleaner manager, shared informers, and a delegating client that reads "
                "from cache and writes through the API. You still need to know what happens when the cache "
                "is stale or when a direct API read is required."
            ),
            analogy=(
                "client-go is the postal system: trucks on schedules (informers), a local sorting office "
                "(cache), and registered mail (writes) when the copy on your desk might be out of date."
            ),
            context=(
                "Senior platform roles expect you to debug without controller-runtime magic. If watches "
                "disconnect, the reflector relists; if relist is too heavy, you see APF throttling. "
                "Knowing client-go explains operator memory use — one cache entry per watched object — and "
                "why cluster-scoped watches on ConfigMaps are a bad idea."
            ),
            steps=[
                "Name rest.Config and auth — in-cluster vs kubeconfig, QPS/Burst tuning.",
                "Explain informer: ListWatch, DeltaFIFO, indexer, resync period.",
                "Describe workqueue: Add, rate limiting, forget after success.",
                "State what controller-runtime adds: Manager, cached client, scheme registration.",
            ],
            evidence=[
                "oc whoami ; oc auth can-i list pods --all-namespaces",
                "grep -R 'NewForConfig' vendor/sigs.k8s.io | head",
                "curl -k -H \"Authorization: Bearer $(cat /var/run/secrets/.../token)\" https://kubernetes.default.svc/api/v1/namespaces",
            ],
            redflag=(
                "Do not say \"controller-runtime replaces client-go so I do not need to know it\". When "
                "the cache lies, you will need the raw client."
            ),
            followup="When must you use the uncached API reader instead of the default client?",
        ),
        Q(
            q="Walk through the controller-runtime reconciliation loop.",
            level=SENIOR,
            answer=(
                "You register a Reconciler with SetupWithManager: For(&YourCR{}), Owns(&Deployment{}), "
                "WithOptions. The manager starts shared informers; when an object changes, the controller "
                "enqueues a Request — namespace/name, not the event object. Reconcile(ctx, req) runs; you "
                "fetch the latest object, compare spec to reality, create/update/delete dependents, update "
                "status, return Result. On error the item requeues with backoff; on success it is forgotten "
                "until the next watch event. Resync period periodically requeues everything for drift "
                "detection. Leader election ensures only one manager instance mutates at a time. The loop "
                "is level-triggered — state, not edge — so missed events do not matter if the next resync "
                "or update catches up."
            ),
            analogy=(
                "Reconciliation is a hotel housekeeper with a room list, not a guest who only reacts when "
                "someone shouts. They enter, compare the room to the standard, fix what is wrong, leave."
            ),
            context=(
                "This is the core operator interview question. They want idempotency, status subresource "
                "updates, owner references, and knowing that deleting the CR should trigger cleanup via "
                "finalizers — not orphan Deployments. OpenShift platform operators all follow this shape; "
                "debugging is log.FromContext, events, and workqueue depth metrics."
            ),
            steps=[
                "Register: For primary CR, Owns/ Watches secondary types, predicates if needed.",
                "Describe enqueue: name-keyed, deduplicated, not one reconcile per field change storm.",
                "Inside Reconcile: Get latest, handle NotFound, apply spec, patch status, return Result.",
                "Close with level-triggered semantics, leader election, and resync as a safety net.",
            ],
            evidence=[
                "oc logs -n <ns> deploy/<operator> --tail=100 | grep reconcile",
                "curl localhost:8080/metrics | grep workqueue_depth",
                "oc describe <crd> <name> | sed -n '/Events/,$p'",
            ],
            redflag=(
                "Do not describe reconciliation as \"watch events and react\". Events are hints; desired "
                "state in etcd is the source of truth."
            ),
            followup="Spec matches reality but status is wrong. Where do you look first?",
        ),
        Q(
            q="What does the Operator SDK give you on top of controller-runtime?",
            level=SENIOR,
            answer=(
                "Operator SDK is scaffolding and tooling: init/generate for project layout, CSV and bundle "
                "generation for OLM, scorecard integration tests, and helpers for Ansible/Helm hybrid "
                "operators. For Go operators the core is still controller-runtime and kubebuilder-style "
                "markers — +kubebuilder:rbac, webhook, printcolumn. SDK CLI creates Dockerfile, Makefile, "
                "and bundle manifests so you can run operator-sdk run bundle and test OLM install locally "
                "on kind or OpenShift Local. It does not replace understanding reconciliation; it removes "
                "boilerplate and standardises packaging for Red Hat catalogues and community operators."
            ),
            analogy=(
                "controller-runtime is the engine; Operator SDK is the factory tooling and the compliance "
                "paperwork to ship the car."
            ),
            context=(
                "Platform teams evaluating build vs buy ask whether SDK's OLM integration is worth the "
                "CRD lifecycle opinion. In 2025/2026 interviews expect scorecard, bundle validation, and "
                "multitenancy annotations — run operator-sdk bundle validate and know what warn vs error "
                "means before publishing to a catalog."
            ),
            steps=[
                "Separate layers: client-go → controller-runtime → kubebuilder markers → Operator SDK CLI.",
                "Name deliverables: bundle/, CSV, scorecard, kustomize overlays, run bundle workflow.",
                "Explain when to use Helm/Ansys plugins vs pure Go — team skills and CR complexity.",
                "Mention CI: make docker-build docker-push bundle-build bundle-validate bundle-push.",
            ],
            evidence=[
                "operator-sdk init --domain example.com --repo github.com/example/operator",
                "operator-sdk bundle validate ./bundle",
                "oc get csv -n <ns> -o jsonpath='{.items[0].status.phase}'",
            ],
            redflag=(
                "Do not claim Operator SDK \"runs the operator in the cluster\". It builds and packages; "
                "OLM and your Deployment run it."
            ),
            followup="Bundle validation fails on untested bundle upgrade paths. What do you fix?",
        ),
        Q(
            q="How do finalizers and the workqueue interact during deletion?",
            level=SENIOR,
            answer=(
                "A finalizer is a string in metadata.finalizers that blocks object removal until cleared. "
                "When a user deletes a CR with a finalizer, the object stays with deletionTimestamp set and "
                "phase Terminating. Your reconcile sees the delete, runs cleanup — tear down cloud resources, "
                "revoke certificates, remove external DNS — then removes the finalizer with a patch and the "
                "garbage collector deletes the object. The workqueue receives a delete event like any other "
                "change; reconcile must handle deletionTimestamp != nil before create logic. If cleanup "
                "fails, return error and the workqueue retries with backoff; the object stays Terminating "
                "until you succeed or an admin removes the finalizer. Never orphan external state by "
                "stripping finalizers without finishing cleanup."
            ),
            analogy=(
                "Finalizers are the checklist on a hotel room door during checkout. The guest cannot leave "
                "until housekeeping signs off — unless someone breaks the process and eats the minibar charge."
            ),
            context=(
                "Stuck Terminating namespaces and CRs are daily platform tickets. The fix is almost always "
                "find the controller that owns example.com/cleanup, read its logs, fix the external "
                "dependency, or acknowledge manual intervention. Interviewers test whether you know forced "
                "removal is a break-glass action with audit consequences."
            ),
            steps=[
                "Explain deletionTimestamp: object visible, finalizers block removal from etcd.",
                "Reconcile branch: if deleting, run cleanup, patch finalizers minus yours, return.",
                "Connect workqueue: delete triggers reconcile same as update; errors mean retry.",
                "Describe failure modes: external API down, RBAC missing on status/finalizer patch.",
            ],
            evidence=[
                "oc get <crd> <name> -o jsonpath='{.metadata.deletionTimestamp}{\"\\n\"}{.metadata.finalizers}'",
                "oc patch <crd> <name> --type=merge -p '{\"metadata\":{\"finalizers\":[]}}'   # break-glass only",
                "grep -R 'Finalizer' controllers/ ; oc logs deploy/<operator> | grep -i finalizer",
            ],
            redflag=(
                "Do not teach \"remove the finalizer with a patch\" as the normal fix. That is how "
                "orphaned load balancers and leaked volumes happen."
            ),
            followup="Namespace stuck Terminating with dozens of resources. What is your ordered triage?",
        ),
    ],
)
