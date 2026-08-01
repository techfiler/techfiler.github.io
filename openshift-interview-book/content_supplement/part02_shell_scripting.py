"""Part 2 - Bash and shell scripting for SRE automation."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=2,
    title="Bash and shell scripting for SRE",
    subtitle="set -euo pipefail, traps, and the glue code that outlives every dashboard",
    intro=(
        "Every platform team owns a graveyard of bash scripts — backup wrappers, release helpers, on-call runbooks "
        "frozen as code. Interviews test whether yours are safe under failure or whether they double-charge customers "
        "at 3 a.m. because pipefail was missing. Senior SRE scripting is not clever one-liners; it is strict mode, "
        "explicit error handling, structured logging, and choosing systemd timers over cron when ordering and "
        "journal integration matter. This part covers the bash depth hiring managers still probe because Ansible "
        "and Python do not replace the five-line fix at the shell."
    ),
    infographics=["evidence_first_loop"],
    questions=[
        Q(
            q="What does set -euo pipefail do, and why should production scripts use it?",
            level=FOUNDATION,
            answer=(
                "set -e exits when a command returns non-zero — no silent fall-through. set -u treats unset variables "
                "as errors, catching typos like $SERVR instead of $SERVER. set -o pipefail makes a pipeline fail if any "
                "stage fails, not just the last one — so curl ... | jq ... fails when curl fails. Together they turn "
                "bash from permissive glue into something that stops on the first lie. I put them at the top of every "
                "script after the shebang, sometimes with a short comment so the next editor does not remove them. "
                "Interviewers know most outages from shell scripts come from one missing flag."
            ),
            analogy=(
                "Without strict mode, bash is a car with the check-engine light taped over. With it, the car pulls "
                "over at the first odd noise instead of driving until the engine falls out."
            ),
            context=(
                "This is the most common bash screening question for SRE roles in 2025/2026. Real incidents: a "
                "migration script continued after rsync failed and deleted the wrong tree; a deploy helper with "
                "unset VERSION pushed latest everywhere. Pipelines without pipefail hide curl 404s when jq happily "
                "parses an error HTML page."
            ),
            steps=[
                "Define each flag: -e command failure, -u unset vars, pipefail pipeline failure.",
                "Explain why pipelines without pipefail lie — only the last exit status counts by default.",
                "Show placement: #!/usr/bin/env bash then set -euo pipefail near the top.",
                "Mention sensible exceptions — some commands expect non-zero and need || true or if ! cmd.",
            ],
            evidence=[
                "bash -c 'set -e; false; echo unreachable'",
                "bash -c 'set -u; echo $UNDEFINED'",
                "bash -c 'set -o pipefail; false | true; echo exit:$?'",
            ],
            redflag=(
                "Do not say \"I never use set -e because it breaks my script\". That signals you have not learned "
                "the conditional patterns to handle expected failures safely."
            ),
            followup="You need a command that may legitimately fail. How do you handle it without disabling -e globally?",
        ),
        Q(
            q="Explain useful bash parameter expansion for defensive scripting.",
            level=FOUNDATION,
            answer=(
                "Parameter expansion lets scripts handle missing or messy input without sprawling if blocks. "
                "${VAR:-default} uses default when unset or empty; ${VAR:?message} aborts with an error — great after "
                "set -u. ${VAR#pattern} and ${VAR##pattern} strip prefixes; ${VAR%/} removes a trailing slash safely. "
                "${#VAR} is length. For paths I use ${VAR%/} before joining so I do not double slashes. In production "
                "I combine ${VAR:?} for required env vars with :- for optional knobs. Interviewers listen for whether "
                "you know the difference between :- and := — the latter assigns the default."
            ),
            analogy=(
                "Parameter expansion is form validation on a web field — default placeholders for optional boxes, "
                "hard stops on required ones — before the data reaches the database."
            ),
            context=(
                "SRE scripts consume environment variables from CI, Vault exports, and Kubernetes downward API. "
                "Typos in NAMESPACE or ENDPOINT_URL cause wide blast radius. Defensive expansion is cheaper than "
                "debugging a loop that ran against production because $ENV was empty and :- prod was wrong."
            ),
            steps=[
                "Cover defaults and required vars: :- versus :? with a concrete env var example.",
                "Show string cleanup: # ## % %% for paths and suffixes.",
                "Mention := when you want to assign a default once and reuse it.",
                "Tie to set -u — expansion patterns complement strict mode rather than fight it.",
            ],
            evidence=[
                "NAMESPACE=${NAMESPACE:?set NAMESPACE}; echo $NAMESPACE",
                "BASE=${BASE:-https://localhost:8080}; echo ${BASE%/}/health",
                "FILE=/var/log/app.log; echo ${FILE##*/}",
            ],
            redflag=(
                "Do not use unquoted $VAR everywhere. Expansion does not fix word-splitting; \"${VAR}\" still "
                "matters."
            ),
            followup="How do you validate that ENDPOINT_URL is HTTPS and non-empty before curl uses it?",
        ),
        Q(
            q="How do you write and use bash functions in maintainable scripts?",
            level=FOUNDATION,
            answer=(
                "Functions group reusable logic with local variables and explicit return codes. I declare locals with "
                "local inside the function so I do not clobber globals. Return 0 or 1 for success checks — or echo "
                "structured output and capture with \"$()\" when the caller needs data. Naming is verb-noun: "
                "log_info, require_root, wait_for_port. For SRE scripts I keep functions small enough to test in "
                "isolation by sourcing the file with bash -c 'source lib.sh; wait_for_port localhost 8080'. Passing "
                "arrays to functions needs nameref — declare -n — in bash 4.4 plus. The interview point is structure: "
                "main at the bottom, library functions above, no three-hundred-line flat scripts."
            ),
            analogy=(
                "Functions are tools on a pegboard — each one does one job, returns to the same place, and does not "
                "leave shavings all over the workbench."
            ),
            context=(
                "Platform repos mix shell and Python; bash functions wrap kubectl, oc, and aws with consistent logging "
                "and retry. Interviewers dislike copy-pasted blocks; they like a log() function that timestamps to "
                "stderr while results go to stdout for piping."
            ),
            steps=[
                "Show basic shape: myfunc() { local x=$1; ...; return 0; }.",
                "Explain local, return codes, and capturing output with \"$()\".",
                "Separate logging on stderr from machine-readable stdout.",
                "Mention sourcing a shared lib.sh and guarding with if [[ ${BASH_SOURCE[0]} != \"$0\" ]].",
            ],
            evidence=[
                "log() { printf '[%s] %s\\n' \"$(date -Is)\" \"$*\" >&2; }",
                "wait_for_port() { local host=$1 port=$2; ...; }",
                "bash -c 'source ./lib.sh; wait_for_port 127.0.0.1 22'",
            ],
            redflag=(
                "Do not use the function keyword unless you need it for historical compatibility — myfunc() is "
                "portable and idiomatic in modern bash."
            ),
            followup="How do you pass an array of hostnames into a function and iterate safely?",
        ),
        Q(
            q="How do traps help you write scripts that clean up on exit or signals?",
            level=INTERMEDIATE,
            answer=(
                "trap registers a handler for signals or EXIT. I almost always trap cleanup on EXIT so temp dirs "
                "vanish whether the script succeeds or set -e aborts — trap 'rm -rf \"$tmpdir\"' EXIT. For INT and "
                "TERM I trap to a function that logs, kills child processes, and exits 130 so orchestrators know "
                "it was interrupted. Quote the handler carefully — expand variables at trap time versus execution "
                "time trips people up; use single quotes on EXIT with variables defined before trap, or a function. "
                "In long-running SRE jobs, trap prevents leaving stale lock files or half-finished database exports "
                "when someone hits Ctrl-C."
            ),
            analogy=(
                "A trap is the \"close the door behind you\" sign — whether you leave happily or the fire alarm "
                "goes off, the door still gets closed."
            ),
            context=(
                "Cron and CI jobs that create /tmp/work.$$ directories without traps fill disks. Kubernetes "
                "preStop hooks are different, but host-level backup scripts that trap TERM behave correctly under "
                "systemd stop timeout. This is a favourite live-coding prompt: add a trap to an existing messy script."
            ),
            steps=[
                "Explain trap COMMAND SIGNAL and that EXIT fires on any shell exit path.",
                "Show tempdir pattern: tmpdir=$(mktemp -d); trap 'rm -rf \"$tmpdir\"' EXIT.",
                "Handle INT/TERM with a cleanup function that reaps children.",
                "Warn about quoting and overwriting traps — use trap - EXIT to remove when done.",
            ],
            evidence=[
                "tmpdir=$(mktemp -d); trap 'rm -rf \"$tmpdir\"' EXIT",
                "cleanup() { kill \"$(jobs -p)\" 2>/dev/null; rm -f /var/lock/myjob.lock; }; trap cleanup EXIT INT TERM",
                "bash -x ./script.sh   # verify trap runs on failure path",
            ],
            redflag=(
                "Do not trap without quoting paths — rm -rf $tmpdir without quotes is how you rm -rf / when tmpdir "
                "is empty."
            ),
            followup="Your script acquires a flock lock file. How do traps interact with the lock on failure?",
        ),
        Q(
            q="How do you debug a bash script that fails only in production?",
            level=INTERMEDIATE,
            answer=(
                "I reproduce locally with the same env vars and bash version — bash --version matters on RHEL 8 versus "
                "9. bash -n checks syntax without running. set -x enables trace to stderr; I wrap it with "
                "PS4='+${BASH_SOURCE}:${LINENO}: ' for readable lines. shellcheck catches quoting and portability "
                "issues in CI. For prod-only failures I log set -x output to a file temporarily, compare PATH, umask, "
                "and cwd, and check whether cron or systemd runs a minimal environment without variables CI sets. "
                "strace -f -e trace=file,process on a canary host shows missing files or permission denials bash "
                "errors swallow. The interview arc is systematic narrowing, not sprinkling echo debug forever."
            ),
            analogy=(
                "Debugging bash is diagnosing a car that only stalls on cold mornings — you need the same temperature "
                "and fuel, not just a test drive on a sunny afternoon."
            ),
            context=(
                "2025/2026 SRE interviews often give a broken deploy.sh. Production-only bugs usually mean "
                "environment differences, race conditions, or parallel execution — flock and set -e interactions. "
                "Candidates who mention shellcheck and PS4 stand out from those who only say \"add echo statements\"."
            ),
            steps=[
                "Reproduce: match bash version, env, cwd, and invoking user or unit file.",
                "Static check: bash -n and shellcheck in CI.",
                "Dynamic trace: PS4 and set -x scoped to the failing section.",
                "System-level: strace or auditd when the script insists the file does not exist.",
            ],
            evidence=[
                "shellcheck -x deploy.sh",
                "PS4='+${BASH_SOURCE}:${LINENO}: '; bash -x deploy.sh 2>trace.log",
                "bash -n deploy.sh ; strace -f -e trace=openat,execve ./deploy.sh 2>&1 | tail -30",
            ],
            redflag=(
                "Do not leave set -x enabled in production logs long term — credentials in arguments leak into "
                "journald and Splunk."
            ),
            followup="The script succeeds when run manually but fails under systemd. What differs in the environment?",
        ),
        Q(
            q="When do you choose cron versus a systemd timer for scheduled work?",
            level=INTERMEDIATE,
            answer=(
                "cron is fine for simple fixed schedules on a single host — log rotation reminders, weekly reports. "
                "systemd timers win when I need dependency ordering — After=network-online.target — persistent "
                "catch-up if the host was down, journal integration, resource limits, and RandomizedDelaySec to "
                "desynchronize fleet thundering herds. Timers pair with a service unit so TimeoutStartSec, User=, "
                "and EnvironmentFile are first-class. On RHEL 9 I default new platform automation to timer plus "
                "service unless the job is trivial. In interviews I also mention that cron's minimal environment "
                "causes half of \"works manually, fails at night\" tickets."
            ),
            analogy=(
                "cron is an alarm clock — it rings at seven whether or not you have power. A systemd timer is a "
                "smart alarm tied to the house alarm system — it waits until the network is up and logs why it skipped."
            ),
            context=(
                "Fleet SRE teams replace crontab sprawl with packaged timer units in RPM or Ansible. Kubernetes "
                "CronJob is a separate layer; the question targets nodes and jump hosts. Interviewers want "
                "OnCalendar versus Monotonic, Persistent=true, and why you systemctl list-timers --all to audit."
            ),
            steps=[
                "State cron strength: simple, universal, quick one-liners.",
                "State timer strengths: deps, journaling, limits, missed-run catch-up, fleet jitter.",
                "Show unit pair: foo.timer triggers foo.service with [Timer] settings.",
                "Mention auditing: list-timers, enable timer not just service, avoid duplicate cron and timer.",
            ],
            evidence=[
                "systemctl list-timers --all",
                "systemctl cat backup.timer backup.service",
                "journalctl -u backup.service -b --since today",
            ],
            redflag=(
                "Do not say cron is \"deprecated\". It is not — but pretending cron and systemd timers are identical "
                "shows you have not operated both in production."
            ),
            followup="You need a job to run at most once across three redundant hosts. How would you design that in shell/systemd?",
        ),
        Q(
            q="What patterns make bash error handling production-safe beyond set -e?",
            level=SENIOR,
            answer=(
                "Strict mode is the floor, not the ceiling. I check critical commands explicitly: if ! cp \"$src\" \"$dst\"; "
                "then log and exit 1; fi. For pipelines I use if ! output=$(curl -fsS ... | jq -e .); then ... For "
                "retries I wrap with a small loop and exponential backoff rather than ignoring failure. errexit and "
                "pipefail still allow if cmd; then and cmd || true when intentional. I define a die() function that "
                "logs to stderr and exits with a chosen code. Scripts return distinct exit codes — 2 for usage, 3 "
                "for dependency missing — so CI and on-call playbooks branch correctly. Finally I avoid subshell "
                "surprises: ( set +e; ... ) does not affect parent errexit but can hide failures if mishandled."
            ),
            analogy=(
                "set -e is the seatbelt. Explicit if checks, retries, and die() are airbags and crumple zones — "
                "different failures need different responses."
            ),
            context=(
                "Senior SRE loops ask you to harden a naive script that rsyncs then deletes source. The expected "
                "answer includes verifying destination, dry-run flags, and atomic rename patterns. Financial and "
                "healthcare clients audit exit codes in runbooks."
            ),
            steps=[
                "Combine set -euo pipefail with explicit if ! for high-stakes commands.",
                "Use die/log helpers and meaningful exit codes documented in the script header.",
                "Handle retries without disabling errexit globally.",
                "Watch subshells, pipelines in if, and temporary set +e blocks with comments why.",
            ],
            evidence=[
                "die() { log \"ERROR: $*\" >&2; exit \"${2:-1}\"; }",
                "if ! rsync -a --dry-run \"$src/\" \"$dst/\"; then die \"dry-run failed\"; fi",
                "for i in 1 2 3; do curl -fsS --retry 0 \"$url\" && break; sleep $((i*i)); done",
            ],
            redflag=(
                "Do not wrap entire scripts in set +e ... set -e to \"handle errors\". You end up with a script "
                "that exits zero after partial failure."
            ),
            followup="How do you structure a script that should fail the CI job but still upload logs on failure?",
        ),
        Q(
            q="How do you write bash scripts that are safe for automation and idempotent operations?",
            level=SENIOR,
            answer=(
                "Idempotent scripts produce the same end state when run twice — critical for Ansible-style loops and "
                "retrying CI. I check before mutate: [[ -f \"$marker\" ]] && exit 0, or test whether the user exists "
                "before useradd. mkdir -p, install -d, and rsync --delete-after with care are idempotent primitives. "
                "I use flock or atomic mkdir for lockdir so two cron invocations do not race. Logging includes run "
                "id, hostname, and who invoked it. Dry-run flags — --dry-run, echo before rm — are mandatory for "
                "destructive steps. Secrets come from env or files with0600, never argv. For automation I document "
                "inputs, outputs, side effects, and exit codes in a header comment so the next engineer and the "
                "orchestrator treat it like a small API."
            ),
            analogy=(
                "An idempotent script is a light switch — flipping it twice leaves the room in the same state, not "
                "brighter and brighter until the bulb explodes."
            ),
            context=(
                "Platform teams invoke bash from Tekton, GitHub Actions, and AWX. Non-idempotent scripts cause "
                "double provisioning, duplicate firewall rules, and torn partial state. 2026 interviews connect this "
                "to Terraform apply semantics — scripts should behave the same way."
            ),
            steps=[
                "Define desired end state and check if already true before destructive actions.",
                "Use locking — flock — and temp files with mktemp for safe concurrent runs.",
                "Provide --dry-run or VERBOSE=1 paths for operators to preview changes.",
                "Document contract: env vars, exit codes, idempotency guarantees in script header.",
            ],
            evidence=[
                "flock -n /var/lock/myjob.lock -c './myjob.sh' || exit 0",
                "id myuser &>/dev/null || useradd myuser",
                "install -d -m 0750 /var/lib/myapp",
            ],
            redflag=(
                "Do not append to config files on every run without deduplication — you get seventeen identical "
                "Include lines and a parser failure months later."
            ),
            followup="The script must update a line in /etc/sysctl.d only if the value differs. How do you implement that?",
        ),
        Q(
            q="What advanced parameter expansion and bash features help SRE automation at scale?",
            level=SENIOR,
            answer=(
                "Arrays beat repeated strings: hosts=(web1 web2 web3); for h in \"${hosts[@]}\"; do ... nameref "
                "declare -n ref=$1 passes array names by reference in bash 4.4 plus. ${var/pattern/replacement} "
                "does inline replace; ${!prefix*} lists indirect variable names for config profiles. readarray -t "
                "mapfile reads lines into an array without word-splitting pain. Brace expansion {1..10} and printf "
                "formatting beat seq in subshells. For parallel SSH I use xargs -P or GNU parallel with a quoted "
                "export of helper functions. Process substitution diff <(sort a) <(sort b) helps config drift checks. "
                "The senior bar is knowing when bash should stop and Python or Go should start — bash for glue, not "
                "for fifty-host orchestration logic."
            ),
            analogy=(
                "Advanced bash is power tools in a workshop — faster for the right job, but you still should not "
                "build the whole house with a angle grinder."
            ),
            context=(
                "Interviewers test array quoting because for i in ${arr[@]} without quotes breaks on hostnames "
                "with spaces — rare but fatal. Fleet scripts parsing oc get -o json sometimes belong in jq or Python; "
                "knowing readarray and jq -r @sh shows mature judgment."
            ),
            steps=[
                "Demonstrate arrays: \"${arr[@]}\" quoting and mapfile for line-safe input.",
                "Show nameref or passing arrays to functions without global pollution.",
                "Use parameter expansion for string ops before reaching for sed.",
                "State the ceiling: complex JSON, API clients, and unit tests → Python or Go.",
            ],
            evidence=[
                "readarray -t lines < <(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')",
                "declare -n ref=$1; for item in \"${ref[@]}\"; do echo \"$item\"; done",
                "diff <(sort /etc/hosts) <(sort hosts.golden)",
            ],
            redflag=(
                "Do not parse JSON with grep and awk in new automation — interviewers file that under \"will "
                "maintain poorly\" unless you immediately justify jq."
            ),
            followup="You need to run a function against two hundred hosts in parallel with a concurrency cap. Sketch the approach.",
        ),
        Q(
            q="How would you structure a reusable shell library for a platform team's automation?",
            level=ARCHITECT,
            answer=(
                "I treat it like a tiny SDK: lib/log.sh, lib/http.sh, lib/k8s.sh sourced by thin entrypoint scripts. "
                "Each lib file is idempotent on source — guard with [[ -n ${_LIB_LOG_LOADED:-} ]] && return; export "
                "_LIB_LOG_LOADED=1. Public functions are verb-noun; internals prefixed with underscore. Strict mode "
                "lives in lib/init.sh. Version pin in git tags; consumers source by absolute path from repo root "
                "discovered via git rev-parse --show-toplevel. Tests use bats-core or shunit2 in CI with shellcheck "
                "and bash -n. Documentation lists env contract, exit codes, and examples. Packaging as an RPM or "
                "installing to /opt/platform/lib makes jump hosts consistent. The architect point: bash libraries "
                "scale until they do not — the library boundary is where Python modules or a CLI binary take over "
                "for anything needing structured config and typed errors."
            ),
            analogy=(
                "A shell library is the shared toolbox in a fire truck — every crew grabs the same wrench; nobody "
                "carries a custom one that only fits their hand."
            ),
            context=(
                "Staff-level platform interviews ask how ten engineers avoid ten slightly different oc wrapper "
                "scripts. The answer includes semver, code review, CI tests, and deprecation policy. Teams that "
                "failed this have /usr/local/bin chaos and scripts that source random GitHub gists."
            ),
            steps=[
                "Split by concern: logging, retries, cloud or oc wrappers, lock helpers — thin scripts on top.",
                "Enforce strict mode, shellcheck, bats tests, and semver tags in CI.",
                "Install via RPM, git submodule, or /opt with a single PLATFORM_LIB root env var.",
                "Define when to graduate a module to Python or Go — complexity threshold and testability.",
            ],
            evidence=[
                "shellcheck -x lib/*.sh ; bats tests/",
                "source \"$(git rev-parse --show-toplevel)/lib/init.sh\"",
                "rpm -ql platform-bash-lib | head",
            ],
            redflag=(
                "Do not advocate curl | bash for internal libraries. That pattern is how supply-chain nightmares "
                "and undebuggable drift enter platform teams."
            ),
            followup="Two teams need conflicting behaviour in the same library function. How do you version and migrate safely?",
        ),
    ],
)
