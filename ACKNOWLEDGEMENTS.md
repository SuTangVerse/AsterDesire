# Sources and acknowledgements

AsterDesire is an independently written Python implementation assembled from
several design references and the project's own engineering work. This
repository does not vendor third-party source files, private datasets, prompt
material, or example state from the references below.

The distinction matters: the links and document named here are credited as
design references. Their code, prose, media, and licenses are not incorporated
into AsterDesire unless explicitly stated.

## Pulse System Tutorial — dankefox

- Source: [dankefox/pulse-system-tutorial](https://github.com/dankefox/pulse-system-tutorial/tree/eb255d8fff44b416ca2455235bb50dbec7be700b)
- Referenced ideas: a causal physiology chain; heart rate, temperature,
  breathing, and chord as related signals; decaying sensory and emotional
  traces; and the conceptual separation of environment, body state, bedside,
  and solo state.
- Use in AsterDesire: the public `PulseEngine` is a smaller, independently
  written implementation with its own data model, formulas, interfaces, and
  tests. No upstream implementation code was available in the referenced
  revision, and no tutorial prose or private companion assets are reproduced.

The referenced revision contained documentation and a PDF, but no published
implementation source or license file. The upstream repository later adopted
AGPL-3.0 on 2026-08-16. AsterDesire does not copy or vendor material from that
later revision.

## CcCompanion Heartbeat HOWTO — CyberSealNull

- Source: [CcCompanion `HEARTBEAT_HOWTO.md`](https://github.com/CyberSealNull/CcCompanion/blob/efb61d643a24448448af9b3d6f652497148b743a/docs/HEARTBEAT_HOWTO.md)
- Upstream license: MIT.
- Referenced ideas: periodic model wake-ups, allowing the model to choose
  between speaking and remaining silent, and separating wake-up decisions from
  message delivery.
- Use in AsterDesire: `HeartbeatController` and `HeartbeatLoop` are independent,
  platform-neutral implementations. They do not include CcCompanion services,
  APNs integration, its application code, or a Claude-specific runtime.

## Ren — *年轮系统：分享和实现教程*

- Source: a PDF supplied to the project owner under the filename
  `Ren-年轮系统-分享和实现教程.pdf`.
- Referenced ideas: a long-lived desire ledger, actions or footprints, evidence
  cards, lifecycle state, and identity-growth snapshots.
- Use in AsterDesire: `GrowthRingLedger` is a lightweight, independently written
  JSONL ledger. It does not reproduce the tutorial, its wording, visual assets,
  or any unpublished implementation.

No public canonical URL or license accompanied the supplied PDF. It is not
redistributed here. If the author publishes a preferred citation or canonical
link, the project welcomes a correction.

## Original integration work in this repository

The following parts are project-specific engineering rather than copied
upstream implementations:

- the eight-drive deterministic engine and its signal-only privacy boundary;
- the current separation of slow libido from event-driven arousal;
- satisfaction plateaus, idempotent receipts, retry backoff, and circuit
  breaking;
- the model- and chat-platform-neutral callback API;
- atomic local persistence, state migration, configuration, examples, and the
  test suite; and
- the particular way Desire, Pulse, Solo, Reverie, Heartbeat, and Growth Rings
  are composed into one runtime.

## Licensing boundary

The original code in this repository is released under the repository's MIT
License. That license applies only to AsterDesire's own code and documentation;
it does not relicense any referenced third-party work. Consult each upstream
source before copying material from it directly.
