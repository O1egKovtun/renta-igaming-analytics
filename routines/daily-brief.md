# Daily briefing as a cloud routine

A routine (claude.ai/code/routines, or `/schedule` in the CLI) runs the briefing on a schedule without anyone asking. Create it by hand; this plugin never creates routines.

## Before you create it

- A routine runs in the cloud with the repositories and connectors you pick. The plugin installed on your machine is not there: select this plugin's repository, and the prompt below reads the command from the clone.
- The unpublished pack (`private/`) is not in the repository, so the run discovers models with `list_models` and `describe_model`. It has no golden numbers and no unit notes: that is slower and less certain than a local run.
- **Write access.** All connectors you include are fully usable without approval, including write tools. The Renta connector has write tools (models, pipelines, destinations). The read-only rule below is text, not a technical limit. Include only the Renta connector and the one chat connector the result goes to, and check every run's transcript at first.
- Results (company numbers) go to the chat channel you name. Choose a channel with the right audience.
- Minimum interval is one hour; schedule a few minutes past the hour (for example 07:07) so the start is not delayed. Times are entered in your local zone.
- A green run only means the session ended. Open the run and read what it did.

## Prompt to paste

```
Read commands/renta-brief.md and references/rules.md in the cloned repository and carry out the briefing exactly as that command describes, for the last full UTC day, all regions. Run the scripts from the clone's scripts/ directory with `python3 -I` (the command text says ${CLAUDE_PLUGIN_ROOT}; here that is the repository root).

Use only the Renta context_layer tool, and only to read (list_models, describe_model, sample_field, run_query). Never call any write action, and never print contact data of players.

Do not invent a cause for any change. If a step fails (session expired, no data, a model is stale), say so in the output instead of filling it in.

Output: publish the dashboard as a private artifact, reusing the same artifact on every run, and post to <CHANNEL> at most five lines: the flagged metrics first (or "no anomalies"), stale models, the artifact link. Write in Ukrainian. If no artifact tool is available in this session, put the full briefing text in the final message instead.
```

Replace `<CHANNEL>` with the chat channel, or delete the part "and post to <CHANNEL> at most five lines: ..." from the Output paragraph if the result should only be an artifact.

## Why this saves effort

Anomaly detection runs in `scripts/anomalies.py`, so the same numbers come out each day and the model does not recompute them. The queries are the thirty-five-day series the command lists, a handful per day, instead of ad-hoc exploring.
