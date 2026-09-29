# Decisions

## What I deliberately did not do, and why

For this submission, I am keeping the scope to the required planning loop and trace UI, preserving the supplied prompts and result shapes.
I considered letting users edit the proposed plan, request changes through chat, and require particular tools, but deferred those extensions because they introduce new approval, validation, and execution guarantees beyond A1-A3.
During review, I found that the supplied observer sees only the current step goal and up to 1,200 characters of executor output, without the full remaining plan, while the replay fixture labels a fixed rain phrase as a surprise even when rain was already part of the user's request.
I left that observer unchanged for this exercise, accepting that it can trigger unnecessary replanning or miss a necessary change, and that a `thin` observation currently continues without a recovery step.
Before a customer pilot, I would revisit it with labeled examples such as a rain-related closure affecting a planned outdoor visit versus rain that does not affect an indoor plan, and add context or recovery behavior where those examples expose failures.

## How I would know this works

The local replay check passed all 29 tests and completed the Lisbon demo with a recorded replan, but the canned final answer still described one day despite the two-day request, so this demonstrates control flow rather than itinerary quality.
I would require zero failures for approval-before-execution, execution of the approved starting plan, preservation of completed steps, and configured step, revision, and tool-call limits, adding targeted tests where the current suite does not cover them.
For model evaluation, I would use 20 fixed, human-labeled scenarios covering known rain, unexpected closures, empty results, and budget or duration constraints, run each five times with a fixed model version, prompts, settings, and tool responses, and save the traces for regression replay.
My proposed pilot gates would be zero missed must-replan cases, no more than 10% unnecessary replans on cases labeled keep-plan, and at least 90% of final answers accepted by a coordinator against a checklist of user constraints, feasibility, and source support; these are proposed thresholds, not measured results.
During a pilot, I would review a fixed weekly sample of 20 runs with the same checklist and compare median coordinator editing time against the roughly 40-minute manual baseline, pausing expansion if acceptance fell below 90% or editing time did not improve.

---

**AI assistance:** AI generated the Part A implementation and added UI tests, explained the code and its limitations, ran the local checks, and drafted this document; my confidence is limited to the observed checks, and I have not independently validated live-model quality.

**Time spent:** About 3 hours on implementation and verification, and over 5 hours in total including background reading to understand agent fundamentals such as tool schemas and execution loops.
