# AI Interactions Log

## Scope and authorship

This project was developed with OpenAI Codex assistance. The user supplied the assignment, asked the agent to complete the project, directed it to create a GitHub repository, and provided the CodePath starter URL. The agent generated the implementation, synthetic additions, tests, explanations, and documentation, and ran the commands recorded here. This is a factual workflow summary, not a fabricated series of student prompts or a claim that the student manually wrote or verified every file.

## Prompts used in this session

Actual user requests included:

> “fisish this project for me as if you were me Project 3: Music Recommender Simulation”

The user included the Project 3 and Project 4 rubrics.

> “bro just make the repo on my github as instructed, and start working”

The user then provided:

> https://github.com/codepath/ai110-module3show-musicrecommendersimulation-starter

The supplied assignment itself asked for CSV expansion, a weighted scorer, ranking explanations, three profiles, optional additional features, and a model card. Those requirements guided the agent's implementation. The targeted prompts below are reproducible follow-up examples, **not additional messages claimed to have occurred**:

```text
Preserve the starter's 10 songs and add 10 illustrative tracks.
Add five features beyond the existing CSV columns and use each in scoring.
Use target similarity so low-energy and high-energy preferences both work.
Share scoring between the starter object API and dictionary API.
Add switchable weights and explain every score contribution.
Test invalid profiles, artist repetition, and unsupported-genre abstention.
```

## Agentic development workflow

1. Read the assignment and inspect the GitHub starter, including its original tests.
2. Fork the starter to the user's account and clone the starter history locally.
3. Preserve the original 10 rows; add 10 illustrative tracks and five new attributes.
4. Implement CSV validation, numeric scoring, deterministic ranking, Strategy configurations, and an artist repetition penalty.
5. Implement a formatted CLI table and three distinct taste profiles.
6. Extend the working system with input checks, a coverage gate, a normalized match gate, an output audit, and structured audit events.
7. Run the original and added tests plus a nine-case evaluation script.
8. Capture real CLI output and write the README, model card, and Mermaid architecture source.

These are development actions and observable processing steps. The application itself is deterministic and is not presented as an autonomous AI agent.

## Additional attributes

The starter already contained valence, danceability and acousticness, so those are **not** counted as newly added attributes. The five new attributes are instrumentalness, popularity, release year, duration in seconds, and live performance. All are synthetic and all have weights, documented ranges, profile targets, and parameterized tests proving they affect scores.

## Design pattern

The agent proposed and implemented the **Strategy pattern**, using `RankingStrategy` objects and a mode registry. Genre-first, mood-first, and energy-first provide separate weight dictionaries to the same scorer. This keeps explanation math aligned with ranking across modes. A single shared implementation also supports the original `Recommender` class, avoiding divergent class and function behavior.

Accepted design: configurable strategy weights rather than duplicate scoring functions. Revised design: the agent initially proposed a standalone catalog because the starter URL was missing; after the user supplied the URL, the implementation was based on the starter and preserved its original rows and tests. These are documented project decisions; they are not invented student judgments after listening to the fictional songs.

## Verification notes

**Agent review and automated checks:** inspected the starter API and preserved its compatibility; confirmed 20 unique song IDs; checked all numeric ranges and five added scoring effects; ran 35 passing pytest tests including the original two tests; ran 9/9 passing evaluation scenarios; captured output directly from the CLI instead of typing expected results into the README.

**Manual student verification:** not observed in this session and therefore not claimed. A useful final review is to inspect a top song's contributions, run a second profile, and decide whether the documented weight tradeoffs reflect the student's own understanding. The added feature values are plausible classroom examples, not manually verified facts about recordings.

## Reliability event logs

The actual JSON event logs are committed in [pop_trace.json](examples/pop_trace.json), [lofi_trace.json](examples/lofi_trace.json), and [edm_trace.json](examples/edm_trace.json). They contain validation outcomes, candidate counts, selected IDs and scores, not hidden model reasoning. They can be regenerated with the commands in the README. The evaluation output is saved in [evaluation.txt](examples/evaluation.txt).

## Limitations and next steps

The work meets the implemented behavior checks, but synthetic tests cannot establish that real listeners enjoy the results. More representative data and listener feedback would be needed to assess that. The project implements the Project 4 reliability option and evaluation bonus; it does not claim RAG, fine-tuning, or a runtime-agent bonus.
