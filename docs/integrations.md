# SVM Replay and developer-tool integrations

Status checked October 24, 2026. Submitted PRs are **not merged integrations**.
Compatibility upgrades continue during backend development and funded maintenance;
upstream merge decisions remain with each project's maintainers.

| Project | What is available or proposed | Evidence / status |
|---|---|---|
| SVM Replay 0.2.0 | Historical forks, time controls and tool integration support | [Published release](https://github.com/xternet/svm-replay/releases/tag/v0.2.0) |
| Surfpool | Opt-in historical execution backend | [#883](https://github.com/solana-foundation/surfpool/pull/883), open |
| Surfpool Studio | Historical-fork display and state reconciliation | [#60](https://github.com/solana-foundation/surfpool-web-ui/pull/60), open |
| Anchor | Isolated historical tests and Node/Rust templates | [#5222](https://github.com/otter-sec/anchor/pull/5222), open |
| solana.com documentation | Historical-fork guide and safety limits | [#2366](https://github.com/solana-foundation/solana-com/pull/2366), draft |

## Companion PRs

- **Surfpool:** [#878](https://github.com/solana-foundation/surfpool/pull/878), [#879](https://github.com/solana-foundation/surfpool/pull/879), [#880](https://github.com/solana-foundation/surfpool/pull/880), [#881](https://github.com/solana-foundation/surfpool/pull/881), [#882](https://github.com/solana-foundation/surfpool/pull/882).
- **Surfpool Studio:** [#58](https://github.com/solana-foundation/surfpool-web-ui/pull/58), [#59](https://github.com/solana-foundation/surfpool-web-ui/pull/59).
- **Anchor:** [#5218](https://github.com/otter-sec/anchor/pull/5218), [#5219](https://github.com/otter-sec/anchor/pull/5219), [#5220](https://github.com/otter-sec/anchor/pull/5220), [#5221](https://github.com/otter-sec/anchor/pull/5221).

All companion PRs above were open at the status check. The Anchor feature depends
on a historical-capable Surfpool version; source branches are not a claim that
upstream packaged releases already include the proposed changes.

## Additional tools

Use the [version-pinned integration guide](https://github.com/xternet/svm-replay/blob/v0.2.0/docs/tool-integration.md)
to connect other tools. The new historical-state backend supplies account bytes
and replay inputs to SVM Replay, Txlab and external clients through the same API.
Missing historical inputs must fail explicitly, not silently use present-day state.

## Planned keyless free access

SVM Replay will fetch historical state and replay inputs through the bounded free
API by default. Supported Surfpool/Anchor workflows inherit that integration;
the Txlab replay UI uses the same backend. Basic use requires no developer-supplied
API key. This is planned backend work, not an already deployed free service or a
claim that the open integration PRs have merged.

Published limits cover request rates, scans and transfers; enforce them server-side. Authentication remains for
higher quotas and paid jobs; do not distribute a shared secret in clients.
Verified adoption rewards require identifiable external projects, not anonymous
traffic. Additional tools can integrate through the documented API.

Tools will select and remember the nearer EU/US API endpoint, then retry once at
the other site on timeout, unavailability or overload. Client quotas, verified
coverage and site traffic limits still apply; fallback cannot bypass an exhausted
user quota. See [regional routing](architecture.md#regional-api-routing).

Earlier fixes (**merged**) remain separate: LiteSVM
[#400](https://github.com/LiteSVM/litesvm/pull/400),
[#402](https://github.com/LiteSVM/litesvm/pull/402),
[#403](https://github.com/LiteSVM/litesvm/pull/403); Surfpool
[#762](https://github.com/solana-foundation/surfpool/pull/762),
[#764](https://github.com/solana-foundation/surfpool/pull/764),
[#795](https://github.com/solana-foundation/surfpool/pull/795).

The [usage plan](usage-plan.md) includes aggregate daily keyless traffic and
outgoing bandwidth, separate from verified-project reward accounting. Basic free
use is not conditional on purchasing higher quotas or bulk delivery.

## M2 public release

M2 acceptance requires a tagged public production release with deployment/API
and recovery instructions. Test two-way regional API fallback and return to the
preferred site, including outage, overload, coverage and quota checks.
Include the health alerts and cap tests in the [operations plan](operations.md).
