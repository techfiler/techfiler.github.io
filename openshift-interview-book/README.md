# The OpenShift Platform Engineer's Interview Book (V5)

A restructured, expanded rewrite of the earlier UHG-CF1 250 Q&A interview books. Same 250-question
scope, completely reorganised: topics run in a dependency-safe sequence from first principles to
architecture, and inside every part the questions climb from Foundation to Architect.

Both output formats are generated from one source of truth, so the PDF and the Word document never
drift apart.

Two editions are produced from the same content:

**Clean copy** — for reading properly.

- `output/OpenShift_Platform_Engineer_Interview_Book_V5_250QA.pdf` — print-ready A4
- `output/OpenShift_Platform_Engineer_Interview_Book_V5_250QA.docx` — editable Word document

**Quick-learning copy** — same book with the load-bearing sentences highlighted in yellow, for a fast
revision pass.

- `output/OpenShift_Platform_Engineer_Interview_Book_V5_250QA_Highlighted.pdf`
- `output/OpenShift_Platform_Engineer_Interview_Book_V5_250QA_Highlighted.docx`

## What changed from the earlier editions

The previous edition ordered questions by how they had accumulated: questions 1–40 were
Intermediate/Senior, 41–80 dropped back to Basic, and topics reappeared several times under
different headings. Around fifteen questions were near-duplicates of each other (Route 503 appeared
twice, RBAC versus SCC twice, Multus twice, CPU Manager twice). The "explanation" field was, for
most questions, the answer text repeated verbatim with one generic sentence appended.

This edition fixes all of that:

- **Sequenced topic-wise, basics → intermediate → senior.** Seventeen parts ordered so nothing
  depends on a concept you have not met yet, and every part sorted Foundation → Intermediate →
  Senior → Architect.
- **Duplicates removed and replaced.** The freed slots went to genuinely missing subjects —
  admission webhooks, API Priority and Fairness, VPA, dual-stack, NMState, cardinality, incident
  communication, exception governance, and more.
- **Six layers per question instead of two.** Every question now carries a spoken answer, an
  analogy, production context, a step-by-step procedure, the evidence you would quote, the red flag
  that costs you the offer, and the follow-up question the interviewer is already holding.
- **Written to be spoken.** Answers are in plain first-person language at interview length, not
  encyclopedia prose.
- **23 vector infographics.** Answer ladder, six-layer method, reading route, evidence-first loop,
  scorecard, control-plane ownership map, `oc apply` flow, workload chooser, scheduling funnel, QoS
  matrix, request path, OVN layers, PVC lifecycle, security layers, OLM chain, upgrade flow,
  observability signals, recovery matrix, HPC alignment, GitOps flow, ACM hub and spoke, STAR-R, and
  the container stack.

## What gets highlighted, and why

Highlighting is generated, not hand-marked, so it stays consistent across all 250 questions and
survives edits to the content. Selection lives in `bookgen/highlight.py` and follows how the content
is written:

- **The opening claim of each answer.** Every answer was written to lead with its point, so the first
  sentence is the one worth skimming. A short opener pulls in the sentence after it.
- **The closing consequence of each production-context paragraph.** Those paragraphs build to their
  punchline, so the highlight goes at the end. A short closer extends backwards.
- **The closing sentence of each part introduction.**

That gives roughly 517 highlighted passages — about two per question — averaging 174 characters.
Both renderers share the same selection code: `highlight.pick()` returns character spans, the PDF
builder turns them into `<span backColor>` markup and the DOCX builder turns them into runs with a
yellow highlight, so the two formats can never disagree about what is marked.

## Structure

| Part | Topic | Questions |
|-----:|-------|----------:|
| 1 | Linux, containers and the Kubernetes idea | Q1–Q14 |
| 2 | The control plane and who owns what | Q15–Q31 |
| 3 | Workloads, controllers and the application contract | Q32–Q47 |
| 4 | Scheduling, resources and capacity | Q48–Q63 |
| 5 | Services, DNS and ingress | Q64–Q79 |
| 6 | OVN-Kubernetes, egress and secondary networks | Q80–Q94 |
| 7 | Storage that survives the pod | Q95–Q110 |
| 8 | Security, identity and compliance | Q111–Q128 |
| 9 | Operators and lifecycle management | Q129–Q140 |
| 10 | Installation, machines and updates | Q141–Q156 |
| 11 | Observability and reliability engineering | Q157–Q172 |
| 12 | Troubleshooting and incident response | Q173–Q188 |
| 13 | High availability, backup and disaster recovery | Q189–Q200 |
| 14 | HPC and performance engineering | Q201–Q212 |
| 15 | Automation, GitOps and change control | Q213–Q226 |
| 16 | Fleet operations with Advanced Cluster Management | Q227–Q238 |
| 17 | Architecture, influence and the behavioural round | Q239–Q250 |

## Rebuilding

```bash
cd openshift-interview-book
pip install -r requirements.txt
python3 build.py
```

This writes all four files — both editions in both formats. The build validates before rendering: it
fails if the total is not exactly 250, if any question is missing a field, if any question has fewer
than three steps or no evidence commands, or if two questions have the same text.

## Editing the content

Content lives in `content/partNN_*.py`, one module per part, each exporting a `PART` object. A
question looks like this:

```python
Q(
    q="What is a PodDisruptionBudget, and what does it not protect against?",
    level=INTERMEDIATE,
    answer="...",      # the spoken 45-90 second answer
    analogy="...",     # one line that makes the mechanism obvious
    context="...",     # why it matters in production
    steps=[...],       # the ordered procedure or reasoning path
    evidence=[...],    # commands and signals you would quote
    redflag="...",     # the answer that loses the offer
    followup="...",    # what the interviewer asks next
)
```

Questions are numbered automatically at build time, sorted by level within their part, so inserting
a question anywhere renumbers everything correctly.

Infographics are vector drawings defined in `bookgen/infographics.py` on top of the primitives in
`bookgen/graphics.py` (`flow`, `stack`, `compare`, `ladder`, `matrix`, `cycle`). Reference one from
a part by adding its registry name to that part's `infographics` list. The PDF embeds the drawing
directly; the DOCX builder rasterises the same drawing through PyMuPDF, so both stay in sync.

## Scope note

The enterprise and healthcare examples are illustrative and do not describe any specific customer
environment. Product behaviour is written against current OpenShift 4.x and ACM 2.x documentation; a
given project may run an earlier supported or EUS release, so version-sensitive details are worth
spot-checking against Red Hat documentation before an interview.

## V6 supplement — topics beyond OpenShift/Kubernetes

The V5 book focuses on OpenShift and Kubernetes. Many senior platform roles also test Linux
administration, Ansible, Python, Go, container image engineering, bare metal provisioning and
HPC/AI workloads. The V6 supplement adds **100 additional questions** in those areas, researched
from current interview guides and Red Hat documentation.

```bash
cd openshift-interview-book
python3 build_v6.py
```

Output files:

- `output/Platform_Engineer_Supplement_Interview_Book_V6_100QA.pdf`
- `output/Platform_Engineer_Supplement_Interview_Book_V6_100QA.docx`
- `output/Platform_Engineer_Supplement_Interview_Book_V6_100QA_Highlighted.pdf`
- `output/Platform_Engineer_Supplement_Interview_Book_V6_100QA_Highlighted.docx`

| Part | Topic | Questions |
|-----:|-------|----------:|
| 1 | Senior Linux administration | Q1–Q14 |
| 2 | Bash and shell scripting for SRE | Q15–Q24 |
| 3 | Python for SRE and platform engineers | Q25–Q36 |
| 4 | Advanced Ansible for senior platform engineers | Q37–Q50 |
| 5 | Go for platform engineers | Q51–Q64 |
| 6 | Podman, Buildah, Skopeo and container images | Q65–Q76 |
| 7 | Bare metal provisioning | Q77–Q88 |
| 8 | HPC and AI on OpenShift | Q89–Q100 |

Content lives in `content_supplement/partNN_*.py`. Use V5 and V6 together for full platform-role
coverage.
