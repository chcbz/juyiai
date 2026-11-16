# PAGE-RETURN-20261116

Owner: current Codex task. Status: IMPLEMENTED / LOCAL_VALIDATED; not pushed, not deployed, no platform acceptance claim.

## Scope and fixed source

- Authority: detailed-design.md `cross-page-return-design-20261116`, A–Q. No share links, new runtime environment, database/API/Runtime/native wire changes.
- Interface: `api/docs/interface-standard.md` at API `377132f786c6a38b1cb9d2cb90bda7dc3a96ff0b`.
- Root base `513a725605775ce925aa07780cb8eabc42c80a6e`; Web base `a28b0c1b65143b74963df3f91c0446d47726ccc2`. Existing workspace and original design edits retained. Root/Web branch `codex/page-return`.
- Web implementation `c7df3fceb5ec662a8d4ac95f338ee6deaaaf1a7d`; final candidate `d52f808e5897b2b5f9ae82a937822c685f3535fa`, tree `d6c23a24a0c19f1d75f45778613bafec3247d0fd`.
- Read-only remote-develop check on 2026-11-16: Root `513a725`, Web `a28b0c1`, API `377132f`; Runtime remote `4fd0951`, local detached `978d442` (not involved). API remains develop and unchanged. Native sources unchanged.
- Root develop is checked out separately at `D:/workspace/chaoyoufan/project/juyiai`, local `aa5525b`; do not overwrite that independent worktree. No integration/push into that checkout or develop is claimed by this handoff.

## Implementation

1. `JuyiHall` owns a return-first startup branch after identity hydration. Exact public/private/task-private/bounty targets are resolved before panel mount; no home, map stage, latest-conversation read or substitute conversation. Missing/revoked original context is an explicit retry/exit state. Home return mounts the form before home lists. Closing a cold chat activates home once.
2. `pageReturnState.js` owns v1 local records, v0 migration, target keys, revisions, fixed-version references, source checkpoints, expiry and explicit correlation. No newest-pending fallback. A new chooser supersedes only the same target after durable source assignment. Accepted receipts prevent re-appending removed references or resurrecting sent text. Readback detects observed races, not cross-tab CAS.
3. `useHallPageReturn` provides the Hall-scoped coordinator; pages register scene owners and pickers receive only their scoped receiver. Provide/inject is confined to this component subtree, avoiding repeated coordinator props across the three wrappers; no module-global active request or global URL listener remains. Conflict/readonly/failure paths keep recovery possible.
4. Home and chat own text; real chat edits/clearing notify synchronously through `useHallConversation.onDraftChange`, while scope initialization does not count as editing. Typed send captures revision so late acceptance does not clear new text. Discussion metadata stores only consumed fields; revoked mentions cannot silently become public broadcast.
5. Picker keeps baseline and tentative selection separate, ACL-reads exact versions and retains removable unreadable placeholders. Complete awaits association confirmation. Cancelling unresolved writes does not erase them; explicit “暂存离开” pauses without abandonment. Returning to the chooser preserves staged references.
6. Existing conversation/task adapters opt into pure-data write intentions. Original key, fixed input, relation ID and If-Match survive refresh; no writes happen merely on restore. Completion uses S−B / B−S and does not remove concurrent additions. Unknown writes require explicit original-operation recovery.
7. Roster/catalog callbacks are identity/request fenced. Automatic onboarding waits for return handling; explicit help remains available. The native query/message protocol and existing HTTPS/upload-domain contract remain unchanged: this increment needs H5 deployment, not a new native Mini Program release.

## Prototype and verification

- Existing prototype only: `web/prototypes/juyiting/material-wechat.js/css`, `specs/prototype-spec.md`. Covers neutral return, conflict, unavailable target, unknown result/paused exit, manual pending recovery. The actual browser observed the conflict controls at workspace preview port 18796; old workspace port 18786 was not used. This was an offline prototype check, not an authenticated product or device acceptance.
- Final fixed-source batch: `.evidence/page-return-20261116-final/`. `build-receipt.json` contains exact commit/tree/toolchain/selectors; `tests.json`, `onboarding.log`, `build.log`, `artifact-manifest.json` retain outputs. Evidence is local/ignored, not published into this open-source repo.
- Mocha: 517 defined entries, 515 passed, 2 opt-in paired-checkout entries initially skipped; onboarding: 25/25. The paired entries are separately invoked with `MINIPROGRAM_PROJECT` pointing at the unchanged checked-in native project; both passed (2/2), with the distinct result in `paired-native-entry.json`.
- Coverage includes both orientations and all four chat scopes; auth delay, slow exact history, missing/revoked target, identity changes, ordinary startup, drafts/conflicts/empty post-send state, stale repeated callbacks, selection removal during reads, paused selector, differential reconciliation, fixed-original DELETE replay, storage failure before network and typed-send edits.
- Final tests + production-mode compilation: 53.365 seconds (600-second attempt limit); manifest and source-clean readback finalized at 157.464 seconds. 613 output files, 113582485 bytes; manifest SHA-256 `05c363f7f88cd29c8ccb3ec3d65a3a05e25e06521ab5593bbe3aaff59c933300`. Generated declaration changes saved as a patch and only those build-generated changes restored.
- This is compile validation, NOT an installable production release package: deployment-specific API/OAuth configuration is absent locally. No package was installed, no pipeline invoked, no production request sent. User deployment must use their existing real configuration. No new environment was introduced.
- New/common return modules pass scoped ESLint. Existing Vue files have historical lint debt; baseline comparison is preserved, not represented as all-project lint passing. Production build retains existing chunk-size/Browserslist warnings.
- Earlier diagnostics and failures are retained at `.evidence/page-return-20261116/diagnostics/`, with the previous fixed-source compile in its parent. Expanded default-2s diagnostic timeouts were rerun using the repository runner's existing 10s test timeout. Interface-fixture checksum failure was traced to Windows CRLF checkout conversion: restored the exact Git-blob bytes only, verified manifest SHA, no fixture content or expected digest change.
- No claim of global 119-case business acceptance, real WeChat SDK/device/network/storage acceptance, or current production health. The local proof does not guarantee defect-free behavior on every platform.

## Delivery boundary

Local feature commits and coordinated root gitlink/docs only; not pushed or deployed. No API/Runtime/native changes, migrations or new subscriptions. The existing user-managed deployment flow remains authoritative. Keep build success, source publication, installation and real business acceptance separate.
