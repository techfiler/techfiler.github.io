"""Part 3 - Python for SRE and platform engineers."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=3,
    title="Python for SRE and platform engineers",
    subtitle="The language platform teams actually write production automation in",
    intro=(
        "Python questions for platform roles are not about memorising syntax. Interviewers want to know "
        "whether you treat automation as production code: how you call APIs safely, handle failures, test "
        "behaviour, manage dependencies and build tools other engineers can run without reading your "
        "laptop's mind. The best answers connect Python patterns to operational concerns - retries, "
        "idempotency, observability and least privilege - rather than listing libraries."
    ),
    infographics=["gitops_flow"],
    questions=[
        Q(
            q="How do you use pathlib instead of os.path for file operations?",
            level=FOUNDATION,
            answer=(
                "pathlib.Path represents filesystem paths as objects with methods for joining, reading, "
                "writing and iterating. Instead of os.path.join and string concatenation, you use the slash "
                "operator or joinpath, which handles separators correctly on every platform. It reads "
                "cleaner, fails less often on edge cases like trailing slashes, and makes recursive "
                "directory walks and globbing explicit rather than buried in nested os calls."
            ),
            analogy=(
                "os.path is giving someone directions as a string of street names. pathlib is handing them "
                "a map with buttons for \"go here\" and \"list what's inside\"."
            ),
            context=(
                "Platform scripts constantly touch config files, certificate paths, inventory directories "
                "and log locations. pathlib reduces the class of bugs where a missing slash or a relative "
                "path resolves differently depending on where the script was launched. It also composes "
                "well with open(), shutil and subprocess when you pass .as_posix() only where a string is "
                "required."
            ),
            steps=[
                "Prefer Path objects from the start rather than converting strings back and forth.",
                "Use / or joinpath for composition; use .exists(), .is_file() and .glob() for inspection.",
                "Read and write with .read_text(), .write_text() or open(path) for large files.",
                "Resolve paths with .resolve() when you need an absolute, canonical location.",
            ],
            evidence=[
                "python3 -c \"from pathlib import Path; p=Path('/etc')/'ansible'/'ansible.cfg'; print(p.exists(), p.resolve())\"",
                "grep -r 'from pathlib import Path' automation/ | head",
                "python3 -m py_compile scripts/check_certs.py",
            ],
            redflag=(
                "Do not build paths with f-strings and hard-coded slashes. It breaks the moment someone "
                "runs the script on Windows or from a different working directory."
            ),
            followup="Your script works when run from /opt/automation but fails from cron. What did pathlib miss?",
        ),
        Q(
            q="How do you manage Python dependencies with virtual environments?",
            level=FOUNDATION,
            answer=(
                "A virtual environment is an isolated directory containing a Python interpreter and its "
                "own site-packages, so project dependencies do not pollute the system Python or conflict "
                "with other projects. I create one per project or per automation repo, activate it for "
                "local development, pin exact versions in a requirements file or lockfile, and install from "
                "that file in CI and production images so every environment gets the same dependency set."
            ),
            analogy=(
                "It is a labelled toolbox for one job site. The tools stay together, nobody borrows your "
                "specialist spanner for another project, and you can hand the whole box to someone else."
            ),
            context=(
                "On RHEL and OpenShift control nodes, system Python is managed by the OS and should not "
                "be modified. Platform engineers who pip install globally create drift that is impossible "
                "to reproduce. Virtual environments are the minimum bar; in production automation the "
                "pattern graduates to container images or execution environments where the venv is baked "
                "in and versioned."
            ),
            steps=[
                "Create an isolated environment with python3 -m venv .venv and activate it for local work.",
                "Install dependencies and freeze exact versions: pip freeze > requirements.txt.",
                "Install from the requirements file in CI and in container builds, never ad hoc.",
                "Document the Python version alongside dependencies so upgrades are deliberate.",
            ],
            evidence=[
                "python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt",
                "pip freeze | diff - requirements.txt",
                "grep -E 'python|requirements' Dockerfile .gitlab-ci.yml",
            ],
            redflag=(
                "Do not pip install packages as root on a shared control node. You have changed "
                "everyone's Python and nobody knows what version anything is."
            ),
            followup="Two engineers get different results from the same script. Where do you look first?",
        ),
        Q(
            q="How should platform automation use the logging module instead of print?",
            level=FOUNDATION,
            answer=(
                "The logging module gives you levels, timestamps, structured context and configurable "
                "destinations without rewriting code. I configure a module-level logger, use DEBUG for "
                "verbose troubleshooting, INFO for normal progress, WARNING for recoverable issues and "
                "ERROR for failures that need attention. Print statements disappear into cron mail nobody "
                "reads; logs go to stdout for container platforms, to files with rotation on VMs, or to "
                "a central collector when integrated with the observability stack."
            ),
            analogy=(
                "Print is shouting in a busy room. Logging is writing in a lab notebook with dated entries "
                "and severity labels that someone can search later."
            ),
            context=(
                "Automation that runs unattended must be diagnosable from its output alone. When a "
                "nightly certificate check fails at 3am, the on-call engineer needs the cluster name, the "
                "API endpoint and the HTTP status - not a traceback with no context. Structured logging "
                "with extra fields, or JSON log format in containerised jobs, makes that correlation "
                "possible in Loki or Elasticsearch."
            ),
            steps=[
                "Use logging.getLogger(__name__) in each module rather than configuring at import time.",
                "Configure handlers and format once in main(), including level from an environment variable.",
                "Log context with every message: cluster, namespace, resource name, correlation ID.",
                "Reserve print for truly interactive CLI output that a human reads directly.",
            ],
            evidence=[
                "grep -r 'logging.getLogger' automation/ | head",
                "oc logs job/cert-check-nightly --tail=50",
                "LOG_LEVEL=DEBUG python3 scripts/sync_inventory.py 2>&1 | head",
            ],
            redflag=(
                "Do not catch an exception and print(e) without logging the traceback. You have hidden "
                "the one line that explains the failure."
            ),
            followup="Your CronJob logs are empty but the script exits 1. What logging mistake did you make?",
        ),
        Q(
            q="How do you build CLI tools with argparse or click?",
            level=FOUNDATION,
            answer=(
                "argparse, in the standard library, turns a script into a tool with named arguments, "
                "defaults, help text and validation - sufficient for most internal tools with a handful "
                "of flags. click adds nested subcommands, shell completion, environment variable fallbacks "
                "and CliRunner for tests, which pays off when multiple teams extend the tool over time. "
                "Both should exit with meaningful codes, expose --help, and validate input before touching "
                "production systems."
            ),
            analogy=(
                "argparse is a control panel with labelled switches. click is the same panel mounted in "
                "a reception desk when strangers need to use it daily without training."
            ),
            context=(
                "Platform teams ship inventory syncs, certificate checks and report generators. Start "
                "with argparse to avoid extra dependencies; migrate to click when subcommands multiply. "
                "Expose the finished tool via console_scripts in pyproject.toml so pip install puts it "
                "on PATH consistently across engineer laptops and execution environments."
            ),
            steps=[
                "Use argparse ArgumentParser or click @group decorators with typed options and --help.",
                "Add subcommands when the tool performs distinct operations like check, sync and report.",
                "Validate inputs early with type=, choices= or click callbacks before side effects.",
                "Return non-zero exit codes on failure and test CLI behaviour with CliRunner or subprocess.",
            ],
            evidence=[
                "python3 scripts/cluster_report.py --help",
                "grep -A5 'console_scripts' pyproject.toml",
                "pytest tests/test_cli.py -v",
            ],
            redflag=(
                "Do not parse sys.argv manually with string splits. The first new flag breaks it and "
                "nobody gets --help."
            ),
            followup="How would you package and distribute this CLI to fifty engineers?",
        ),
        Q(
            q="How do you call HTTP APIs safely with the requests library?",
            level=INTERMEDIATE,
            answer=(
                "I wrap calls in a session for connection reuse, set explicit timeouts on every request, "
                "verify TLS unless there is a documented exception, handle non-2xx responses with "
                "raise_for_status(), and retry transient failures with backoff rather than hammering the "
                "API. Authentication goes in headers or the session, never hard-coded in the URL. For "
                "platform work I also log the method, URL, status and latency so failures are traceable."
            ),
            analogy=(
                "It is placing a phone call with a time limit and a retry policy, not shouting into a "
                "dead line until something breaks."
            ),
            context=(
                "Platform automation talks to Kubernetes APIs, cloud control planes, ticketing systems and "
                "internal REST services. The requests library is fine for synchronous calls; the failure "
                "modes are timeouts, rate limits, certificate issues and ambiguous 5xx responses. "
                "Production code treats every call as unreliable and plans for partial failure when calling "
                "many endpoints in a loop."
            ),
            steps=[
                "Create a requests.Session with default headers, auth and timeout tuple.",
                "Call raise_for_status() and catch requests.HTTPError with useful logging.",
                "Retry idempotent methods on connection errors and 429/503 with exponential backoff.",
                "Never disable TLS verification in production without a named, reviewed exception.",
            ],
            evidence=[
                "python3 -c \"import requests; r=requests.get('https://api.example.com/health', timeout=(3,10)); r.raise_for_status(); print(r.status_code)\"",
                "grep -r 'requests.Session' automation/ | head",
                "pytest tests/test_api_client.py -v -k timeout",
            ],
            redflag=(
                "Do not use requests.get(url) with no timeout. It hangs forever when the API is sick and "
                "blocks your entire pipeline."
            ),
            followup="The API returns 429 with a Retry-After header. How do you handle that?",
        ),
        Q(
            q="How do you run external commands with subprocess safely?",
            level=INTERMEDIATE,
            answer=(
                "subprocess.run with a list of arguments, never shell=True unless you have no alternative, "
                "captures output and return codes explicitly. I check returncode or use check=True for "
                "fail-fast behaviour, pass a timeout to prevent hung processes, and set cwd and env "
                "deliberately rather than inheriting whatever the parent had. For long-running commands I "
                "stream stdout line by line instead of buffering everything into memory."
            ),
            analogy=(
                "shell=True is asking a stranger to interpret your instructions. A list of arguments is "
                "handing them a numbered checklist they execute literally."
            ),
            context=(
                "Platform scripts often wrap oc, kubectl, aws, ansible-playbook or openssl. The classic "
                "incident is shell injection through an unquoted variable, or a subprocess that inherits "
                "the wrong KUBECONFIG and mutates production. Wrapping CLI tools is acceptable when no "
                "API exists, but the wrapper must validate context before calling and parse output "
                "defensively."
            ),
            steps=[
                "Build commands as lists: ['oc', 'get', 'pods', '-n', namespace], not formatted strings.",
                "Use subprocess.run(..., capture_output=True, text=True, timeout=300, check=True).",
                "Validate returncode and stderr; log the exact command at INFO for auditability.",
                "For streaming output, use Popen with line iteration and explicit wait with timeout.",
            ],
            evidence=[
                "python3 -c \"import subprocess; subprocess.run(['oc','whoami','--show-server'], check=True, text=True, capture_output=True)\"",
                "grep -r 'shell=True' automation/   # should be empty or heavily justified",
                "bandit -r automation/ -ll | grep subprocess",
            ],
            redflag=(
                "Do not use shell=True with user-supplied input. You have built a remote code execution "
                "hole in your automation."
            ),
            followup="You need to run oc with a specific kubeconfig. How do you pass that safely?",
        ),
        Q(
            q="How do you parse YAML and JSON configuration in automation scripts?",
            level=INTERMEDIATE,
            answer=(
                "Use the json module for JSON and PyYAML's safe_load for YAML - never yaml.load without "
                "Loader=SafeLoader, which can execute arbitrary code. I validate the parsed structure "
                "against expected keys and types before using it, fail with a clear error naming the file "
                "and field, and treat config as data separate from code so the same script works across "
                "environments by swapping input files or environment-specific paths."
            ),
            analogy=(
                "Parsing config is reading the recipe, not guessing ingredients. Safe loading means the "
                "recipe cannot rewrite the kitchen."
            ),
            context=(
                "Platform automation reads Ansible inventories, Kubernetes manifests, CI variables files "
                "and cloud API responses. YAML's flexibility is a footgun: implicit typing, merge keys "
                "and anchors make two files that look equivalent parse differently. For critical config, "
                "schema validation with pydantic or jsonschema catches mistakes at startup rather than "
                "mid-incident when a missing key becomes a NoneType error deep in the call stack."
            ),
            steps=[
                "Load YAML with yaml.safe_load and JSON with json.load; specify encoding explicitly.",
                "Validate required keys and types immediately after parsing.",
                "Separate config file paths from logic via CLI flags or environment variables.",
                "Round-trip test: dump and reload should preserve semantics for generated config.",
            ],
            evidence=[
                "python3 -c \"import yaml; print(yaml.safe_load(open('inventory/group_vars/all.yml')))\"",
                "python3 -c \"import json; json.load(open('config/clusters.json'))\"",
                "pytest tests/test_config_loader.py -v",
            ],
            redflag=(
                "Do not use yaml.load on files from Git without SafeLoader. A malicious merge request "
                "can execute code when your CI parses it."
            ),
            followup="Your YAML parses but replica_count is the string '3' instead of an integer. How do you catch that?",
        ),
        Q(
            q="How do you test platform automation with pytest?",
            level=INTERMEDIATE,
            answer=(
                "pytest discovers test functions by naming convention, runs them with readable failure "
                "output, and supports fixtures for shared setup like mock API responses or temporary "
                "directories. I unit-test pure functions with parametrised cases, mock external calls with "
                "unittest.mock or pytest-mock so tests do not need a live cluster, and keep integration "
                "tests separate and clearly marked for CI jobs that have credentials. The bar is that a "
                "pull request cannot merge if tests fail."
            ),
            analogy=(
                "It is a rehearsal with stunt doubles for the expensive scenes. You verify the script's "
                "decisions without renting the whole theatre every time."
            ),
            context=(
                "Untested automation is a liability: it runs when you are asleep and breaks in ways "
                "reviews do not catch. pytest's fixture model makes it practical to test error paths - "
                "what happens when the API returns 503, when a file is missing, when JSON is malformed. "
                "For platform code, the highest-value tests are often around parsing, retry logic and "
                "idempotency checks rather than full end-to-end cluster operations."
            ),
            steps=[
                "Structure code so business logic lives in importable functions, not only in main().",
                "Use @pytest.mark.parametrize for table-driven cases covering edge inputs.",
                "Mock requests, subprocess and boto3 clients in unit tests; reserve live calls for integration.",
                "Run pytest in CI on every commit with coverage thresholds on critical modules.",
            ],
            evidence=[
                "pytest tests/ -v --tb=short",
                "pytest tests/ --cov=automation --cov-report=term-missing",
                "grep -r '@pytest.fixture' tests/ | head",
            ],
            redflag=(
                "Do not skip tests because the script is small. Small scripts cause large incidents when "
                "they touch production at 2am."
            ),
            followup="How do you test code that wraps oc without a real cluster?",
        ),
        Q(
            q="How do you use concurrent.futures for parallel platform tasks?",
            level=INTERMEDIATE,
            answer=(
                "concurrent.futures provides ThreadPoolExecutor for I/O-bound work like HTTP calls and "
                "ProcessPoolExecutor for CPU-bound work. I submit tasks with executor.submit or map, set "
                "max_workers based on API rate limits rather than CPU count, collect results with "
                "as_completed and handle exceptions per future so one failure does not silently drop the "
                "rest. For many cluster operations, bounded parallelism dramatically cuts wall-clock time "
                "while staying under API quotas."
            ),
            analogy=(
                "It is opening several checkout lanes instead of one, but only as many as the store "
                "manager allows so the shelves are not emptied at once."
            ),
            context=(
                "Checking certificate expiry across five hundred namespaces, polling health endpoints "
                "for a fleet, or fetching metadata from multiple cloud accounts are natural parallel "
                "problems. The mistakes are unbounded parallelism that triggers rate limiting, sharing "
                "mutable state between threads without locks, and losing error context when futures fail "
                "quietly. asyncio is the alternative for high-concurrency I/O, but ThreadPoolExecutor "
                "is often enough and easier to integrate with synchronous requests code."
            ),
            steps=[
                "Choose ThreadPoolExecutor for I/O-bound API calls; ProcessPoolExecutor for CPU-heavy parsing.",
                "Set max_workers conservatively and respect API rate limits with semaphores if needed.",
                "Use as_completed to process results as they arrive and log failures with context.",
                "Shut down the executor explicitly or use a context manager to avoid dangling threads.",
            ],
            evidence=[
                "python3 scripts/check_all_clusters.py --workers 8 --dry-run",
                "grep -r 'ThreadPoolExecutor' automation/ | head",
                "pytest tests/test_parallel_checks.py -v -k rate_limit",
            ],
            redflag=(
                "Do not fire five hundred threads at an API with no rate limiting. You will DoS your "
                "own control plane and blame the script."
            ),
            followup="When would you choose asyncio over ThreadPoolExecutor?",
        ),
        Q(
            q="How do you handle errors and retries in production Python automation?",
            level=SENIOR,
            answer=(
                "I classify errors: programming bugs get fixed, transient infrastructure errors get retried "
                "with exponential backoff and jitter, and permanent failures fail fast with a clear message "
                "and non-zero exit code. Retries wrap only idempotent operations or use idempotency keys "
                "where the API supports them. I never catch bare Exception and continue silently; each "
                "handler logs context, preserves the traceback, and decides whether to retry, abort or "
                "degrade gracefully."
            ),
            analogy=(
                "Retries are redialling a busy phone line, not repeatedly pressing the wrong number and "
                "hoping it becomes right."
            ),
            context=(
                "Platform automation runs against unreliable networks, throttled APIs and partially "
                "upgraded clusters. A script that retries forever masks an outage; one that fails on the "
                "first timeout creates alert noise. Libraries like tenacity or urllib3's Retry help, but "
                "the design decision is yours: which exceptions retry, how many attempts, what backoff "
                "ceiling, and what happens to already-completed steps in a multi-step workflow."
            ),
            steps=[
                "Distinguish transient errors (timeouts, 503, connection reset) from permanent ones (404, 403).",
                "Apply retry with exponential backoff and jitter only to idempotent operations.",
                "Use context managers and try/finally to release resources even when retries exhaust.",
                "Exit with distinct codes or structured error output so callers and monitors can triage.",
            ],
            evidence=[
                "grep -r 'tenacity\\|Retry\\|backoff' automation/ | head",
                "pytest tests/test_retry_logic.py -v",
                "oc logs job/platform-sync --tail=100 | grep -i 'retry\\|error'",
            ],
            redflag=(
                "Do not wrap everything in except Exception: pass. The script exits 0, the monitor is "
                "green, and production is wrong."
            ),
            followup="Step three of five fails after steps one and two succeeded. How do you make the rerun safe?",
        ),
        Q(
            q="How do you use boto3 and cloud SDK patterns in platform automation?",
            level=SENIOR,
            answer=(
                "boto3 uses a session built from environment variables, instance profiles or named profiles, "
                "and clients or resources for each service. I prefer clients for explicit API control, "
                "paginate list operations instead of assuming a single page, handle ClientError by error "
                "code rather than message text, and use waiters for eventual consistency rather than "
                "sleep loops. Credentials never live in source code; IAM roles with least privilege replace "
                "long-lived keys wherever the job runs in AWS."
            ),
            analogy=(
                "It is using the vendor's official courier with a tracked account, not forging shipping "
                "labels by guessing the form layout."
            ),
            context=(
                "Multi-cloud platform teams use boto3 for AWS, but the patterns transfer: azure-identity "
                "with DefaultAzureCredential, google-cloud with application default credentials. The "
                "interview is really about credential chains, pagination, idempotent resource creation "
                "and tagging for cost allocation. Wrapping SDK calls in small functions with typed "
                "inputs makes them testable with botocore stubbers."
            ),
            steps=[
                "Create a boto3.Session from the appropriate credential chain for the runtime environment.",
                "Use client methods with explicit pagination via get_paginator or manual NextToken loops.",
                "Catch botocore.exceptions.ClientError and branch on response['Error']['Code'].",
                "Tag resources consistently and use idempotent create patterns: describe first, create if missing.",
            ],
            evidence=[
                "python3 -c \"import boto3; print(boto3.Session().client('sts').get_caller_identity())\"",
                "aws sts get-caller-identity",
                "pytest tests/test_aws_cleanup.py -v --mock-aws",
            ],
            redflag=(
                "Do not embed access keys in the repository. If they leak, every resource your role can "
                "touch is exposed, and scanners find them in minutes."
            ),
            followup="How do you test boto3 code without calling real AWS APIs?",
        ),
        Q(
            q="How would you structure a Python automation project for production use?",
            level=ARCHITECT,
            answer=(
                "Separate library code from CLI entry points, pin dependencies in a lockfile or "
                "requirements file, run linting and tests in CI, package as a container image for "
                "anything that runs in-cluster or on shared infrastructure, and document how to configure "
                "credentials per environment. Secrets come from the environment or a vault, never from "
                "the repo. Observability is built in: structured logs, metrics for success and failure "
                "counts, and trace context when calling distributed APIs."
            ),
            analogy=(
                "It is the difference between a script on someone's laptop and a product the platform "
                "team stands behind with a version number and a support channel."
            ),
            context=(
                "The architect question is whether your Python is maintainable when the original author "
                "leaves. That means src layout, typed interfaces for external systems, contract tests for "
                "API responses, semver tagging, and a deliberate decision about what runs as a CronJob "
                "versus what stays on a controller. It also means knowing when Python should not be the "
                "answer - declarative GitOps beats a reconciliation loop written over a weekend."
            ),
            steps=[
                "Lay out src/package with modules by domain, tests/, and pyproject.toml with pinned deps.",
                "Run ruff or flake8, mypy where valuable, and pytest in CI on every pull request.",
                "Build a container image with a non-root user for in-cluster or shared execution.",
                "Document configuration, credentials, exit codes and operational runbooks alongside the code.",
            ],
            evidence=[
                "tree automation/ -L 2",
                "cat .gitlab-ci.yml | grep -E 'pytest|ruff|build'",
                "oc get cronjob,job -n platform-automation -l app=inventory-sync",
            ],
            redflag=(
                "Do not treat production automation as a single 800-line script with no tests because "
                "we will refactor it later. Later is after the incident."
            ),
            followup="At what point should this Python project become a Kubernetes operator instead?",
        ),
    ],
)
