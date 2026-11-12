# 聚义厅 Realtime 语音适配合同（2026-09-30；2026-10-01 原生转写修订）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 现行设计边界（2026-11-07）

**本专题：实时语音传输与会话生命周期。**

### 最小责任链
Realtime适配器处理音频会话/网络事件；业务权限与请求事实保持API职责。

授权建立实时通道→音频分块→事件/文本显示→用户停止/断线释放与明确恢复。

### 实施约束
PCM分块大小不是总音频限制；不把传输分片当业务请求逐块入库/鉴权；不臆造Provider能力或自动启用付费服务。

通用开发/验证约束：[统一开发约束](../architecture-convergence/development-principles.md)。

只在本专题实际改变协议或数据语义时同步生产者/消费者/必要迁移；接口不变的内部修复不默认修改Web、API、Runtime全链。表/索引修改须说明其查询或一致性职责，不新建CHECK/触发器代替业务规则。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


## Scope and architecture

Keep the existing Hall voice workflow: record → transcription review/edit → explicit frozen Hall target/context → existing text chat/Agent relay → one correlated final reply → optional speech playback. Do not replace the chosen Agent with a generic realtime model conversation. Keep provider credentials entirely on the backend. No direct browser access to CLIProxyAPI. No new DB schema, no production DML or paid integration test beyond separately authorized calls.

Existing authenticated CYF `/chat/speech/transcriptions` and `/chat/speech/synthesis` remain the product API; upstream becomes `wss://<configured same-origin gateway>/v1/realtime?model=gpt-realtime`, provider alias `cliproxy-realtime`. No fallback/retry to `/v1/audio/speech` or `/v1/audio/transcriptions`. Original `openai-compatible` implementation may remain for other explicitly configured gateways; it is not used for the new mode.

## Formats

- New browser capture: PCM signed 16-bit little-endian, mono, 24000 Hz, RIFF/WAVE (`audio/wav`), normal bounded recording. Use a reusable AudioWorklet recorder with injectable factory for deterministic unit tests; cleanup on cancellation, late permissions, identity/context changes, unmount and recording failures. Honor existing 45s/5MiB audio-input limits; those are media limits, not performance SLOs. Stateful resampling must handle device rate different from 24k.
- API multipart transcription adds strict WAV support while retaining previous explicitly supported media for legacy provider. Reject RIFF/container length mismatch, wrong PCM/channels/rate/width, empty/truncated/alignment/invalid headers, and overlong audio using actual samples, not client-declared duration.
- Realtime transcription (2026-10-01): keep the normal `gpt-realtime` session but configure `audio.input.transcription.model=gpt-transcribe`. Commit audio and consume only correlated native `conversation.item.input_audio_transcription.*` events; no STT `response.create` or assistant-generated answer is accepted. Commit is the possibly paid dispatch boundary. Require the acknowledged input item, content index, complete transcript, bounds and terminal/error consistency; empty native transcript -> NO_SPEECH. This is not a transcription-only session. The earlier model-assisted route lost questions and followed spoken instructions in actual probes; historical failures and the three native diagnostic passes are in `docs/implementation/VOICE_SEMANTIC_FIX_20261001.md`.
- New synthesis request: `{requestId,text,voice:"juyiting-default",format:"wav"}`; response `audio/wav`, PCM16 mono 24k RIFF/WAVE, Cache-Control=no-store, X-Voice-Request-Id, actual Content-Length. The existing `mp3` request/response is retained only for the explicitly selected legacy provider. Provider/format mismatches reject before paid calls.
- Realtime synthesis: an explicit literal-speech task plus JSON-escaped `text` in one <=32-character-ID user item; require its exact ACK before response.create(audio) with conversation:none and only its item_reference. Require the correctly correlated complete audio transcript to equal the original text, except the evidence-backed decimal spoken-glyph equivalence below, as well as audio deltas and completed terminal response. Never expose gateway diagnostic bodies/credentials to clients or logs. Validate PCM alignment/nonempty and existing 8MiB output bound including WAV header. Do not silently play partial audio or hallucinate success.

### Bounded decimal pronunciation (2026-10-01)

Only independent ASCII decimals with one integer digit (for example `-3.14` and `2.5`) enable the tested Chinese numerical pronunciation instruction. Compare source/caption through a deterministic spoken canonical form: negative sign → 负, decimal point → 点, each digit → 零…九; caption may use 负 with ASCII digits or the identical spoken form. Every surrounding character, whitespace, punctuation and unit remains exact. Missing sign/point, changed value, shortened text, chat answers and changed units still fail. Token boundaries exclude partial matches in identifiers, IP addresses, scientific notation and multi-digit integer parts; unsupported syntax keeps the original literal path rather than a new rejection gate. This is not general-purpose number parsing. Native STT stays verbatim; acceptance evidence must retain original transcripts and distinguish numerical equivalence from character-exact PASS.

## Security / concurrency / cancellation

Retain exact JWT jiacn/client_id/sub identity; original Redis admission, HMAC digest, encrypted result cache, idempotency and reservation ownership. Replay is format-bound; adjust synthesis MIME validation/cache replay to exact format/provider without allowing mixed cache content. JWT and identity changes still cancel browser work. Backend provider waits for actual terminal events; keep configured transport/inactivity timeout and InterruptedException handling; no new total SLO deadline and no automatic provider retry. Close/abort owned WebSocket on success, error, interruption, transport timeout. Distinguish known pre-dispatch rejection from unknown accepted-request transport failure, preserving RESULT_UNKNOWN semantics. Lease ownership is never bypassed for slow calls.

New mode uses explicit provider=cliproxy-realtime and session/route model=gpt-realtime, with fixed native STT model=gpt-transcribe; same configured Spring AI gateway/key with audio overrides and current allowed HTTPS gateway policy. Native STT keeps its own native-transcription-v1 digest plus existing STT semantics-v2 domain; only TTS moves to semantics-v3 and legacy digests remain byte-identical, without cache flush or migration. Do not place key in browser/config artifacts. Production enabling and device acceptance are separate from code/tests; paid acceptance calls require an explicit live budget (the user authorized up to 500 cumulative attempts on 2026-10-01; failures and handshakes count, and the budget does not reset on continuation).

## Regression tests

API: offline fake WebSocket/session transport, protocol order, no STT response.create and one TTS response.create, native ASR and text/audio terminals, fragmented messages/deltas, terminal failure, bad audio/base64/oversize, cleanup, known/unknown errors, strict WAV parsing, activation model/provider/format validation, identity/admission/cache existing tests. No live provider calls in tests.
Web: PCM/WAV bytes and stateful resampling, recorder resources/late callbacks, old voice context/CAS/cancellation/reply-correlation coverage, format-specific request/response MIME and bounded binary playback; text remains usable on unsupported browsers/errors. Preserve opt-in auto-send.
