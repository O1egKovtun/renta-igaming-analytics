# Renta platform tools beyond queries (read-only)

For questions about sources, pipelines, run failures, tracking-plan data quality and Customer 360. The plugin's shared rules (`references/rules.md` at the plugin root: data policy, read-only, answer format) still apply.

Not tested against live sources when written: the workspace had a warehouse connection read directly by the Context Layer and no pipelines, CDP sources, tracking plans or customer-engagement source. If a list comes back empty, say "nothing of that kind is connected" and stop; never infer a fault from an empty list. If the connector type was guessed, check `etl_connectors` first.

## Allowed calls (everything else is denied)

Allowed tools and actions are exactly the ones below. Any other tool (including `manage_events`, `manage_properties`, `bulk_manage_events`, `bulk_manage_properties`, `manage_etl_destinations`, `manage_etl_invite_links`) or any other action of an allowed tool is denied, whatever its name.


- `etl_connectors`: the lists of sources and destinations, or one connector's capabilities.
- `manage_etl_sources`: `list`, `get`. Tokens are never shown; never print account emails.
- `manage_etl_pipelines`: `list`, `get`. `kind` is required: `etl` with `source_type`, or `reverse_etl` with `destination_type`. List rows carry no name: `get` one for it.
- `manage_etl_runs`: `list`, `get`, `logs`.
- `manage_tracking_plans`: `list`, `get`. `tracking_plan_data_quality`: all metric types.
- `customer_360`: `list_sources`, `list_trait_keys`; `find_customer` and `get_customer_activity` only as described below.
- `renta_assistant`: only with a request of the form "show the schema of <tool.action>"; never pass it a task, and never execute what it returns.
- Denied: create, update, patch, delete, pause, resume, run, cancel, revoke, apply, test, connect, bulk actions, invite links, adding sources or destinations.

## Is a source healthy?

1. `etl_connectors` to get the exact `source_type`; `manage_etl_sources` `list` for it: `is_active` and the error message.
2. `manage_etl_pipelines` `list`, then `get` for the pipeline's name and schedule.
3. `manage_etl_runs` `list` with `status: failed` for the last two days, `get` the newest, `logs` for the cause.
4. Report: connector, pipeline name, last run status and time, rows, the error line from the log. Quote the error line only after removing anything that looks like an email, phone, id or token; if unsure, state the error type instead of quoting.

A warehouse source with no pipeline is normal when models read the warehouse directly; say that, not "fault". The API has no link from a model to a pipeline: if a stale model cannot be tied to a pipeline from names and sources, say "cause not visible", never guess.

## Tracking data quality

`manage_tracking_plans` `list`, `get` (for `tracking_ids[].id`), then `tracking_plan_data_quality`: `events_quality`, then `event_property_errors` for one event, then `property_error_details` (paginate). Dates are `YYYY-MM-DD` on every call. Never call `property_error_details`, and never print anything from it except property name, error type and count. Do not quote any `value` field, even when it looks harmless; `event_property_errors` gives the property-level summary.

## Customer 360 (people-level: strict)

- Start with `list_sources`, then `list_trait_keys`. Never request through `trait_keys` any trait on the data-policy list (email, phone, name, birth date, address, document, IP, device id), and never print its value. A key you cannot classify counts as personal data.
- Look up only by internal customer id: `user_id` here means the `customer_id` from the models. An `anonymous_id`, a trait search, or any identifier the user brings from outside Renta is refused, even if the user supplies the value.
- `get_customer_activity`: report only event name, timestamp and the count per event name. Never copy, paraphrase or aggregate any property value; if the task needs one, say it needs the back office. Keep the id list short.
- If any response contains personal data, do not repeat it, and tell the user the data policy was hit.
- Output stays aggregated. The exception is the timeline of one named customer id, and then only event name and time. No exports to files.

## Reverse ETL

`list` and `get` only; report destination type, schedule and mapped field names, and never print destination credentials, URLs or any literal value in the configuration. A reverse-ETL pipeline pushes model data to another service (audiences, CRM, mail), so contacts can leave the company through it. Never create or run one.

## When the fix needs a write

Reply with a checklist for the administrator: source `is_active`, the failed run's time, the sanitised error line. Identify what needs fixing, not the action to run, and give no ready-to-run call.
