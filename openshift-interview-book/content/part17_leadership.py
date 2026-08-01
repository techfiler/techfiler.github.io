"""Part 17 - Architecture, communication and the behavioural round."""

from bookgen.model import ARCHITECT, FOUNDATION, INTERMEDIATE, SENIOR, Part, Question as Q

PART = Part(
    number=17,
    title="Architecture, influence and the behavioural round",
    subtitle="The half of the interview that is not about OpenShift, and often decides the outcome",
    intro=(
        "Technical rounds decide whether you could do the job. This part decides whether people want to "
        "work with you while you do it. Senior platform roles are unusual in that most of the work is "
        "influence: persuading a team to adopt a standard, telling an executive that the date is at risk, "
        "explaining a trade-off to someone who will pay for it, and running an incident without making "
        "anyone defensive. Interviewers assess this through stories, so the practical skill is having three "
        "or four real ones ready, structured, honest, and with a number in them."
    ),
    infographics=["star_r"],
    questions=[
        Q(
            q="How do you structure an answer to a behavioural question?",
            level=FOUNDATION,
            answer=(
                "Situation, Task, Action, Result, Reflection. One sentence of context and blast radius. "
                "What I specifically owned - not what the team did. What I actually did, including the "
                "evidence I gathered and the decision I made. A measured result with a number. And what I "
                "changed afterwards so it could not happen again. Ninety seconds, no rambling, and the "
                "reflection is the part that makes it sound senior."
            ),
            analogy=(
                "It is a news report rather than a diary entry. What happened, what was done, what the "
                "outcome was, what it means - in that order, and finite."
            ),
            context=(
                "Most candidates lose points here not through weak stories but through unstructured ones "
                "that take four minutes and never reach the outcome. Having three or four stories prepared "
                "and rehearsed - an incident, a difficult trade-off, a disagreement handled well, a "
                "failure you learned from - covers the majority of behavioural questions, because most of "
                "them are variations on those themes."
            ),
            steps=[
                "Set the scene in one sentence, including who was affected.",
                "State your specific ownership, using I rather than we.",
                "Describe the actions and the evidence behind the key decision.",
                "Give a measured result and finish with the change you made so it could not recur.",
            ],
            evidence=[
                "Three or four prepared stories, each timed at 90 seconds",
                "A concrete metric in each: minutes saved, incidents avoided, percentage improvement",
                "The prevention action for each, stated as something that actually shipped",
            ],
            redflag=(
                "Do not tell a story with no measured outcome. \"It went well\" is not a result and the "
                "interviewer will not ask twice."
            ),
            followup="Tell me about a time your fix did not work. What did you do next?",
        ),
        Q(
            q="What would you ask the interviewer about the environment?",
            level=FOUNDATION,
            answer=(
                "Which OpenShift version and infrastructure provider, and how many clusters. Who owns "
                "upgrades and how often they happen. What the current incident volume looks like and the "
                "biggest recurring cause. How much is in Git today. What the on-call rota is and how often "
                "it fires. And what the biggest platform problem is that they would want solved in the "
                "first six months. Those answers tell you what the job actually is."
            ),
            analogy=(
                "It is asking to see the kitchen before accepting the head chef job. The menu tells you the "
                "ambition; the kitchen tells you the reality."
            ),
            context=(
                "Asking good questions is genuinely part of the assessment, because it shows what you "
                "consider important. Questions about upgrade cadence, GitOps coverage and incident themes "
                "signal that you think about the operational reality rather than the technology stack. They "
                "also protect you: a role where nothing is in Git, upgrades have not happened in eighteen "
                "months and on-call fires nightly is a specific kind of job, and you should know that before "
                "you accept it."
            ),
            steps=[
                "Ask about scale and versions to calibrate everything else.",
                "Ask about change and upgrade practice - cadence, ownership, automation coverage.",
                "Ask about incident volume, themes and the on-call experience.",
                "Ask what success looks like in six months, and listen for whether they have an answer.",
            ],
            evidence=[
                "Their answers on cluster count, version spread and upgrade cadence",
                "Their answer on GitOps and automation coverage",
                "Their answer on the biggest current platform problem",
            ],
            redflag=(
                "Do not say you have no questions. It reads as either disinterest or a lack of experience "
                "in judging environments."
            ),
            followup="Which of those answers would most change how you approached the first month?",
        ),
        Q(
            q="How do you conduct an architecture review?",
            level=INTERMEDIATE,
            answer=(
                "I start with requirements and constraints rather than the proposed solution, because half "
                "the disagreements in a review come from unstated assumptions. Then I look for the failure "
                "modes - what happens when each dependency is unavailable - the operational cost of running "
                "it, the security and data boundaries, and the recovery story. I ask what alternatives were "
                "considered and why they were rejected, and I make sure the decision and its reasoning are "
                "written down."
            ),
            analogy=(
                "It is a building inspection before the concrete is poured. Cheap now, extremely expensive "
                "after the fact, and the questions are always the same ones."
            ),
            context=(
                "The most valuable question in the room is usually \"what happens when this dependency is "
                "down?\", because it exposes the difference between a design that has been thought through "
                "and one that only describes the happy path. The second most valuable is \"who operates "
                "this at 3am and what do they do?\", which surfaces operational cost that architecture "
                "diagrams hide entirely."
            ),
            steps=[
                "Establish requirements, constraints and non-functional targets before discussing the "
                "solution.",
                "Walk the failure modes dependency by dependency, including partial failures.",
                "Assess operational cost, security boundaries and the recovery story explicitly.",
                "Ask what alternatives were rejected and why, and record the decision as an ADR.",
            ],
            evidence=[
                "Architecture decision records with alternatives and rejection reasoning",
                "Failure mode analysis per dependency",
                "Operational cost assessment: who runs it, what they do when it breaks",
            ],
            redflag=(
                "Do not review a design by critiquing technology choices. The questions that matter are "
                "about failure, cost and recovery."
            ),
            followup="A design has no answer for what happens when its database is unavailable. What do you do?",
        ),
        Q(
            q="What is an architecture decision record and why keep them?",
            level=INTERMEDIATE,
            answer=(
                "An ADR is a short document capturing one decision: the context and constraints at the time, "
                "the options considered, the decision taken, and the consequences accepted. They are kept "
                "because eighteen months later somebody will ask why the platform works this way, and "
                "without an ADR the answer is either speculation or an argument. They also make it possible "
                "to revisit a decision honestly when the constraints change."
            ),
            analogy=(
                "It is the minutes of the meeting where the decision was made. Nobody reads them until "
                "somebody disputes what was agreed, and then they are worth everything."
            ),
            context=(
                "The property that makes ADRs useful is that they are immutable and superseded rather than "
                "edited. A decision that was correct given 2023's constraints is not wrong just because the "
                "constraints changed, and recording it that way removes the blame from revisiting it. Kept "
                "in the same repository as the code they describe, they also get reviewed like code."
            ),
            steps=[
                "Keep them short - context, options, decision, consequences - and dated.",
                "Store them in the repository they relate to, reviewed through pull requests.",
                "Supersede rather than edit, so the history of thinking is preserved.",
                "Reference them in design reviews and revisit when constraints materially change.",
            ],
            evidence=[
                "ADR directory with numbered, dated records",
                "Superseded records linked to their replacements",
                "Design review references to existing ADRs",
            ],
            redflag=(
                "Do not edit an old ADR to match current thinking. You have destroyed the record of why the "
                "original decision made sense."
            ),
            followup="A decision from two years ago is now wrong. How do you handle it?",
        ),
        Q(
            q="How do you work with application teams to improve reliability?",
            level=INTERMEDIATE,
            answer=(
                "By making the reliable option the easy one rather than by writing standards and hoping. "
                "That means templates that already contain probes, requests, PDBs and spread constraints; "
                "dashboards and alerts provided by default; and shared review of their SLOs and incidents so "
                "the conversation is about their service rather than about platform rules. Where a team "
                "resists, I show them their own incident data rather than arguing from principle."
            ),
            analogy=(
                "It is designing the path where people already walk. Fencing the grass makes enemies; paving "
                "the desire line makes converts."
            ),
            context=(
                "The dynamic to avoid is the platform team as compliance function, which produces "
                "adversarial relationships and workarounds. Teams adopt standards when the standard "
                "obviously saves them work or prevents an incident they remember. That is why incident data "
                "is the most persuasive artefact available - a team that was paged three times last quarter "
                "for something a readiness probe would have prevented needs no further argument."
            ),
            steps=[
                "Provide working defaults in templates rather than requirements in documents.",
                "Give teams their own dashboards, alerts and SLOs so reliability is visible to them.",
                "Review incidents jointly and let the data make the argument.",
                "Track adoption and off-path incident rate to prioritise where to help next.",
            ],
            evidence=[
                "Golden path adoption rate across services",
                "Incidents traced to missing platform practices, per team",
                "Joint incident reviews held and actions completed",
            ],
            redflag=(
                "Do not position the platform team as the team that says no. You will be routed around, and "
                "then you will own the consequences anyway."
            ),
            followup="A team refuses to add probes because they are 'confident in their code'. What do you do?",
        ),
        Q(
            q="Tell me about a production incident you handled.",
            level=SENIOR,
            answer=(
                "Use the structure and be specific. One sentence on impact and scale. What you owned. The "
                "evidence you gathered and how you narrowed it down - naming the signal that turned the "
                "corner. The mitigation you chose and why it was the smallest safe one. The measured "
                "outcome: how long, how many users, what recovered. And the prevention that shipped "
                "afterwards, with evidence it worked."
            ),
            analogy=(
                "It is a flight incident report, not a war story. Facts, decisions, outcome, and what "
                "changed in the procedure afterwards."
            ),
            context=(
                "What distinguishes a strong answer is the moment of narrowing - the specific piece of "
                "evidence that took you from three hypotheses to one. Candidates who tell this well sound "
                "like they were there; candidates who describe a sequence of actions without saying what "
                "each one ruled out sound like they are reciting a runbook. Mentioning something you got "
                "wrong along the way makes the whole story more credible, not less."
            ),
            steps=[
                "Open with impact and scale in one sentence, including duration.",
                "Describe the evidence path and name the signal that narrowed it to one cause.",
                "Explain the mitigation choice in terms of blast radius, and the validation you did.",
                "Close with the measured outcome and the prevention that shipped afterwards.",
            ],
            evidence=[
                "Incident timeline with timestamps and decisions",
                "The specific metric, log line or condition that narrowed the diagnosis",
                "Post-incident action and the measured effect since",
            ],
            redflag=(
                "Do not tell an incident story where everything you tried worked first time. It is not "
                "believable and it wastes the chance to show judgement."
            ),
            followup="What would you do differently if the same incident happened tomorrow?",
        ),
        Q(
            q="How do you handle disagreeing with a senior stakeholder?",
            level=SENIOR,
            answer=(
                "I separate the decision from the evidence. I make sure I understand their constraint - "
                "often the disagreement is about a requirement I did not know existed - then present the "
                "risk in terms of impact rather than technology, propose an alternative that meets their "
                "actual constraint, and if the decision still goes the other way, I document the risk, "
                "accept the decision and support it properly. Escalating past someone should be rare and "
                "reserved for genuine safety or compliance issues."
            ),
            analogy=(
                "It is a second opinion, not a mutiny. You give your professional assessment clearly, in "
                "writing, and then you help with the plan that was chosen."
            ),
            context=(
                "The behaviour interviewers are checking for is whether you can disagree without becoming a "
                "problem. Someone who cannot let a decision go is expensive to work with; someone who never "
                "pushes back is not doing the job. The written record is the mature middle - it protects "
                "the organisation, gives the decision-maker the information, and lets everyone move on "
                "without the disagreement resurfacing every week."
            ),
            steps=[
                "Understand their constraint before arguing the technical position.",
                "Frame the risk in business impact terms, with a probability and a consequence.",
                "Offer an alternative that satisfies their constraint, not just your preference.",
                "Document the accepted risk, support the decision, and revisit it when evidence changes.",
            ],
            evidence=[
                "Written risk assessment with impact, likelihood and mitigation options",
                "Decision record noting the accepted risk and its owner",
                "Follow-up when evidence changed the picture",
            ],
            redflag=(
                "Do not describe going over someone's head as your normal approach. It answers a different "
                "question than the one being asked."
            ),
            followup="They accepted the risk and it materialised. How do you handle that conversation?",
        ),
        Q(
            q="How do you explain technical risk to a non-technical audience?",
            level=SENIOR,
            answer=(
                "In their terms, not mine. What could happen, to whom, how likely it is, what it would cost, "
                "and what it would take to reduce it - with numbers where I have them and honest uncertainty "
                "where I do not. I avoid component names entirely and talk about service impact, customers "
                "affected and recovery time. Then I offer options with costs so the decision is theirs to "
                "make rather than mine to justify."
            ),
            analogy=(
                "It is a doctor explaining a procedure. Not the biochemistry - the odds, the recovery time, "
                "and what happens if you do nothing."
            ),
            context=(
                "The mistake that undermines otherwise strong engineers is explaining the mechanism instead "
                "of the consequence. An executive does not need to know what etcd quorum is; they need to "
                "know that a particular design means a data centre failure takes the service down for four "
                "hours, and that a different design costs a certain amount and reduces that to ten minutes. "
                "Presented that way, the decision is straightforward and it is theirs."
            ),
            steps=[
                "Describe impact in customer and business terms, with duration and scope.",
                "Give likelihood honestly, including your uncertainty about it.",
                "Present two or three costed options rather than a single recommendation.",
                "Record the decision and who made it, and revisit it when circumstances change.",
            ],
            evidence=[
                "Risk register entries written in business impact language",
                "Costed options presented, with the decision recorded",
                "Post-decision review when the situation changed",
            ],
            redflag=(
                "Do not explain the technology to justify the risk. The audience will remember confusion, "
                "not concern."
            ),
            followup="They ask for a percentage likelihood you do not have. What do you say?",
        ),
        Q(
            q="How do you grow the capability of a platform team?",
            level=SENIOR,
            answer=(
                "By spreading knowledge deliberately rather than hoping it diffuses. That means pairing on "
                "incidents so the same person is not always the one who knows, runbooks written by whoever "
                "learned the thing most recently, game days where someone unfamiliar runs the recovery, and "
                "rotating ownership of areas so there is no single point of human failure. I also make "
                "space for people to do the boring reliability work, because that is where most learning "
                "actually happens."
            ),
            analogy=(
                "It is cross-training a kitchen brigade. If only one person can work the grill, the "
                "restaurant closes when they are ill - and they never get a holiday."
            ),
            context=(
                "The measurable version is bus factor per critical system, and it is uncomfortable to look "
                "at honestly in most teams. Game days are the most effective intervention because they "
                "surface the gap immediately: the person who did not write the runbook discovers what is "
                "missing from it in twenty minutes, and the runbook improves in a way that no review "
                "process achieves."
            ),
            steps=[
                "Measure bus factor per critical system and make it visible to the team.",
                "Pair on incidents and rotate ownership so knowledge does not concentrate.",
                "Run game days where an unfamiliar person executes the recovery, and fix what they hit.",
                "Protect time for reliability work, and treat runbook improvement as real output.",
            ],
            evidence=[
                "Bus factor assessment per critical system",
                "Game day schedule, participants and gaps found",
                "Runbook update frequency and who authored the changes",
            ],
            redflag=(
                "Do not let one person own the recovery procedure for a critical system. It is a risk to "
                "the business and unfair to them."
            ),
            followup="One engineer is the only person who understands your storage layer. What do you do?",
        ),
        Q(
            q="How would you approach modernising a legacy platform?",
            level=ARCHITECT,
            answer=(
                "Incrementally, and starting with the thing that hurts most. First an honest assessment - "
                "what runs where, what the actual pain is, and what constraints are real versus assumed. "
                "Then pick a target state and a migration path that delivers value in stages, with a "
                "reference workload proving each stage before it becomes policy. Big-bang migrations fail "
                "because they defer all the learning to the end, when the cost of being wrong is highest."
            ),
            analogy=(
                "It is renovating an occupied building. One floor at a time, tenants stay housed, and you "
                "learn how the plumbing actually works before you commit to the whole block."
            ),
            context=(
                "The organisational half matters as much as the technical. Modernisation projects stall "
                "when application teams are asked to change without getting anything in return, so "
                "sequencing matters: deliver a paved path that is genuinely better - faster builds, better "
                "visibility, less on-call - and migration becomes something teams want rather than "
                "something imposed. Measuring and publishing progress keeps sponsorship alive."
            ),
            steps=[
                "Assess honestly: inventory, pain points, real constraints, and current cost.",
                "Define a target state and a staged path where each stage delivers standalone value.",
                "Prove each stage with a reference workload before making it policy.",
                "Make the new path clearly better for teams, and publish migration progress and outcomes.",
            ],
            evidence=[
                "Application inventory with migration complexity and business criticality",
                "Reference workload migrated end to end, with measured before and after",
                "Migration progress and benefit metrics published regularly",
            ],
            redflag=(
                "Do not propose a big-bang migration. It concentrates all the risk at the point where you "
                "understand the least."
            ),
            followup="Six months in, three teams have not started. How do you unblock it?",
        ),
        Q(
            q="What would your first 90 days look like?",
            level=ARCHITECT,
            answer=(
                "First thirty days, learn: architecture, versions, ownership, incident history, change "
                "process, and who the platform's customers actually are - while delivering a couple of small "
                "visible wins so I am useful rather than just observing. By sixty days, baseline: cluster "
                "health, risk register, capacity, upgrade posture, backup and recovery status, tested. By "
                "ninety, a prioritised roadmap with measurable outcomes, agreed with the people who will "
                "have to live with it."
            ),
            analogy=(
                "It is a new head chef learning the kitchen before changing the menu - but still cooking "
                "service every night while they learn."
            ),
            context=(
                "The balance being assessed is between listening and delivering. Someone who proposes a "
                "rewrite in week two has not understood the constraints; someone who delivers nothing for "
                "three months has not built any credibility to spend later. Small early wins - a recurring "
                "alert silenced properly, a manual task automated, a stale runbook fixed - buy the goodwill "
                "you need for the larger changes."
            ),
            steps=[
                "Days 1-30: learn the environment and the people, and ship two or three small visible wins.",
                "Days 31-60: baseline health, risk, capacity and recovery, and actually test the recovery.",
                "Days 61-90: propose a prioritised roadmap with measurable outcomes and named owners.",
                "Throughout: write down what you learn, because the newcomer's view is only available "
                "once.",
            ],
            evidence=[
                "Stakeholder map and platform inventory produced in the first month",
                "Risk register and tested recovery results by day sixty",
                "Roadmap with measurable outcomes agreed by day ninety",
            ],
            redflag=(
                "Do not promise a platform rewrite before understanding the constraints. It signals "
                "confidence rather than judgement, and interviewers can tell the difference."
            ),
            followup="What would be your first small win, based on what you know about this role?",
        ),
        Q(
            q="How do you prioritise platform work against competing demands?",
            level=ARCHITECT,
            answer=(
                "Against a small number of stated outcomes rather than by who asks loudest. Reliability "
                "risk, security exposure, toil reduction and enablement value are the four lenses I use, "
                "with anything that is currently causing incidents taking precedence. I keep a visible "
                "backlog with the reasoning attached, reserve capacity for unplanned work and for reducing "
                "toil, and review priorities with stakeholders on a fixed cadence so trade-offs are "
                "explicit."
            ),
            analogy=(
                "It is a hospital waiting list. Triage by severity, not by who is most insistent - and "
                "keep some capacity free for emergencies, because there will be emergencies."
            ),
            context=(
                "The reserved capacity is the part that keeps platform teams from being permanently "
                "reactive. A team that plans to be one hundred percent allocated has no room for the "
                "incident that will certainly arrive, so every incident pushes planned work later and the "
                "toil that caused the incident never gets fixed. Explicitly reserving a proportion for "
                "unplanned work and improvement breaks that cycle, and it is defensible with data once you "
                "measure where time actually goes."
            ),
            steps=[
                "Publish the prioritisation lenses and apply them consistently and visibly.",
                "Give anything currently causing incidents precedence over new capability.",
                "Reserve explicit capacity for unplanned work and for toil reduction.",
                "Review with stakeholders on a fixed cadence, showing what was traded off and why.",
            ],
            evidence=[
                "Visible backlog with priority reasoning per item",
                "Time allocation: planned, unplanned, toil reduction, measured over quarters",
                "Stakeholder review cadence and recorded trade-off decisions",
            ],
            redflag=(
                "Do not plan for full allocation. Incidents are not exceptional events and a plan that "
                "assumes none is a plan that always slips."
            ),
            followup="Two directors both want their work first and neither will yield. What do you do?",
        ),
    ],
)
