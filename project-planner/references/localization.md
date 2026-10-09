# Fixed-message localization

Use this workflow when the resolved plan language has no current, verified message bundle, or when a bundle's source or message hash no longer matches. Plan text is authored for the selected language by the planning agent; this workflow covers only fixed interface and chart messages. A translation bundle is not a saved user language preference.

## Sources and language tags

The English and Simplified Chinese JSON files in `scripts/locales/` are the source pair. Read the complete files and this document before preparing or reviewing a language. The context fingerprint covers this document. The source set is the actual complete key set returned by the helper; the current count of 59 keys is not a permanent schema limit.

Use the localization helper for canonical language tags and fingerprints. A syntactically valid tag does not prove that a verified bundle exists. Never turn an untrusted language string directly into a file path. The English source and Chinese comparison may reveal a semantic conflict; resolve the source conflict before translating or publishing anything. Source fingerprints are SHA-256 over raw source/context file bytes. Message hashes use the helper's canonical JSON representation; obtain them from the helper rather than calculating them independently.

Tag normalization checks ordinary BCP 47 syntax, applies standard casing, and accepts all 26 fixed grandfathered tags. It uses their IANA Preferred-Value when present, for example `i-klingon` becomes `tlh`, `en-GB-oed` becomes `en-GB-oxendict`, and `art-lojban` becomes `jbo`; tags without a replacement, such as `i-default`, retain their registered spelling. This local helper does not query the registry, validate registration of every ordinary subtag or extension, or perform all registry-based alias transformations (for example `iw` remains `iw`). New preferences and bundles use the normalized tag. Existing plan snapshots with a recognized old tag remain valid offline if their embedded message and review proof is valid; they are not rewritten by reading. To reuse a shared package under a newly preferred tag, publish a currently reviewed bundle at the normalized path; preserve the old package rather than renaming it or inventing fresh proof. See [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html) and the [IANA registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry).

Inspect the authoritative sources and their fingerprints:

```text
python -X utf8 "<skill-dir>/scripts/localization.py" sources
```

The command reports the English and Chinese messages and source/message fingerprints. Hashes bind a translation review to the exact English source, Chinese comparison, localization context, and candidate messages.

## Prepare a candidate

For a language without a valid current bundle, read every source key and its usage context. Produce a UTF-8 JSON candidate containing only a complete `messages` object: every actual key exactly once, with a non-empty string value. Translate full sentences naturally, preserve every placeholder name and purpose, and allow placeholder position to follow the target language. Do not translate protocol keys or change scheduling, workload, dependency, resource-lock, or blocked-state meaning. Include keys that the current plan will not display.

Keep the candidate outside the official locale sources and outside generated plan artifacts. A candidate is not a published bundle. Validate its structure, language, key set, placeholders, and formatting before semantic review:

```text
python -X utf8 "<skill-dir>/scripts/localization.py" validate --language <language-tag> --messages "<candidate-messages.json>"
```

The helper exits `0` on success and `2` on error. Structural validation cannot establish translation quality and cannot create a semantic `PASS`.

The validator freezes formatting placeholders from the English source. Keep this mapping in sync with the implementation when the source templates change; any such change invalidates the prior locale verification and requires full revalidation and semantic review:

| Message key | Required placeholder |
| --- | --- |
| `blocked_reason` | `{items}` |
| `chart_desc` | `{title}` |
| `chart_caption` | `{unit}` |
| `blocked_label` | `{items}` |
| `blocked_count` | `{count}` |
| `schedule_span` | `{finish}` |
| `completion_blocked` | `{finish}` |
| `completion` | `{finish}` |

All eight templates use plain named fields with no format specifier or conversion. Every other current message key has no formatting placeholder. Validation exercises these templates with representative arguments using Python formatting; translation may move a placeholder but must preserve its exact name and purpose.

## Independent full semantic review

Review the complete English source, Chinese comparison, candidate, and this document as a read-only assignment. Use a fresh independent subagent with no parent conversation context for each round. Before dispatch, obtain source/context hashes with `sources` and the candidate's canonical message hash with `validate`; give the reviewer stable file paths and these fingerprints. The reviewer compares every actual key, including unused strings, returns a result for each key with specific evidence, and uses the same helper to report the hashes of the files it actually read. It must check:

- preserved meaning, conditions, negation, limits, and uncertainty, without omissions or new promises;
- consistent terms and accurate distinctions among tasks, milestones, external events, dependencies, and resource locks;
- the distinction among rough workload, relative position, and real elapsed duration, including blocked unknown readiness;
- human-readable labels for fixed states such as `scheduled` and `blocked`, while the protocol values remain unchanged;
- quantities, units, and placeholder purpose, with grammar and word order appropriate to the language;
- natural wording and clear meaning in each button, heading, legend, explanation, and detail-panel context.

The review JSON passed to `publish` must have this structure:

```json
{
  "status": "PASS",
  "per_key": {
    "<every actual message key>": {
      "status": "PASS",
      "evidence": "Specific comparison evidence for this key"
    }
  },
  "reviewer": {
    "identity": "Actual independent reviewer identity",
    "fork_turns": "none"
  },
  "hashes": {
    "before": {
      "source_hashes": {
        "en": "<sha256>",
        "zh-CN": "<sha256>",
        "context": "<sha256>"
      },
      "messages_sha256": "<candidate message hash>"
    },
    "read": {
      "source_hashes": {
        "en": "<sha256>",
        "zh-CN": "<sha256>",
        "context": "<sha256>"
      },
      "messages_sha256": "<candidate message hash>"
    },
    "after": {
      "source_hashes": {
        "en": "<sha256>",
        "zh-CN": "<sha256>",
        "context": "<sha256>"
      },
      "messages_sha256": "<candidate message hash>"
    }
  }
}
```

Replace the illustrative keys and hashes with the complete actual key set and measured values. Do not fabricate reviewer identities or `PASS`. The before, read, and after fingerprints must match exactly. A failed or unfinished check is not publishable.

The Primary checks the review evidence against the actual English, Chinese, and candidate files. For each issue, record accepted, partly accepted, or rejected with specific evidence. Correct every confirmed issue in the candidate, rerun automatic validation, and send the corrected full key set to a new independent reviewer for a complete semantic review. Allow one initial review plus at most two full revision-and-review cycles for a locale. This locale limit is separate from `max_review_revisions` for a plan. If an issue remains after the limit, preserve the candidate and evidence, stop locale preparation, and report that the requested language is not ready.

## Publish a verified bundle and create a plan snapshot

Publish only after automatic validation, complete per-key semantic `PASS`, and matching before/read/after fingerprints:

```text
python -X utf8 "<skill-dir>/scripts/localization.py" publish --language <language-tag> --messages "<candidate-messages.json>" --review "<semantic-review.json>"
```

The helper writes a versioned bundle under `user-locales/<language-tag>.json`. A bundle contains `generator: "project-planner/localization"`, `version: 1`, the canonical `language`, all `messages`, `source_hashes` for `en`, `zh-CN`, and `context`, `messages_sha256`, and the verified `semantic_review`. A valid bundle requires current source hashes, a matching message hash, and the complete passing per-key review. Presence of a file, a `PASS` string, or a structurally valid JSON object alone is insufficient.

Create a plan-local snapshot for every new skill-flow plan. It stores the selected language, complete fixed messages, source fingerprints, message hash, and verification evidence. Set `plan-input.json`'s `localization` to the snapshot's relative path and message hash. The generator reads this fixed snapshot so later changes to shared locales cannot alter a plan under review.

```text
python -X utf8 "<skill-dir>/scripts/localization.py" snapshot --language <language-tag> --output "<output-dir>/locale-snapshot.json"
```

When the user explicitly requests a different language for an existing plan in the same directory, add `--replace-language` to this command. Update the plan input's language, authored text, and snapshot message hash, regenerate all four artifacts, and complete the full independent plan review. The flag permits replacing only a valid snapshot owned by this helper with a known version and recognized language; without it, a cross-language replacement is refused. It does not change the saved skill preference or allow overwriting persistent `user-locales/` packages.

If publishing the long-term bundle fails after the candidate has passed full review, create the plan-local snapshot directly from the same candidate and review:

```text
python -X utf8 "<skill-dir>/scripts/localization.py" snapshot --language <language-tag> --output "<output-dir>/locale-snapshot.json" --messages "<candidate-messages.json>" --review "<semantic-review.json>"
```

The candidate and review arguments must be supplied together; the same `--replace-language` option applies when changing an existing plan's language with a reviewed candidate. This recovery permits the current plan to proceed from the verified snapshot when the output directory is writable; report that long-term locale publication failed. Do not claim the language was saved for later plans. The helper preserves files it does not own. It may repair a damaged or hash-mismatched target only when it carries this helper's exact generator marker, version `1`, and the same canonical language. Persistent bundles always require matching language ownership. Snapshots permit a different language only with the explicit flag and valid existing proof; unknown versions, unrecognized ownership, symbolic links, and source or persistent-package targets remain protected.

When creating a new plan, the `snapshot` command checks the current source hashes and bilingual baseline whether it reads a published bundle or a candidate. A changed source, context, or catalog hash makes an old shared bundle ineligible for reuse. Candidate-based snapshot creation also verifies the candidate against current sources and its full matching review before saving. After the plan-local snapshot exists, the generator validates its embedded proof and exact message hash offline without reading mutable skill configuration or source catalogs. This keeps the reviewed plan reproducible if shared locale files change afterward.

An existing verified bundle with unchanged source, context, and message hashes can be reused without retranslating or repeating locale semantic review. Any changed source, localization context, or target message invalidates the prior review. Even when only a few entries were translated again, validate and semantically review the complete updated message set before publishing.

Built-in `en` and `zh-CN` bundles also require a current `scripts/locales/baseline-review.json`. The Primary creates this file only after an actual independent full comparison of both complete message sets. It contains `generator: "project-planner/localization"`, `version: 1`, the current three source hashes, message hashes for both languages, and a passing per-key review with evidence and matching before/read/after hashes. The nested review's before/read/after message hashes use the same `{ "en": "<hash>", "zh-CN": "<hash>" }` map. The loader does not treat the built-ins as semantically verified merely because they are included in the skill.

Keep `user-locales/` as runtime data shared by projects using this skill installation. Skill upgrades preserve it, but it is user-generated local data and must not be published with the public skill source. Preserve `config.json` and its custom fields independently. A saved locale does not save or change the user's default language preference.
