# GMI Serving incident log: 2026-11-05 (Pacific)

**Org ID:** `7402d47c-b207-4b23-8899-6b8bc65bd37e`
**API key ID:** `5e5da58e-55a3-4a6a-b814-10f1b1ea3252` (owner `446de144-cdb0-4528-81f6-0dc74255c541`)
**Endpoint:** `POST https://api.gmi-serving.com/v1/chat/completions`
**Client location:** Cloudflare edge SJC
**Log written:** 2026-11-05 23:45 PST (2026-11-06 07:45 UTC)

## Summary

Three models in the catalog (all listed on `GET /v1/models`) fail every request.
Other models on the same key work (control: `google/gemma-4-26b-a4b-it` returned 200).
We first saw the failures at **2026-11-05 22:54 PST** in our benchmark logs. They were still failing at **23:41 PST**.

| Model | HTTP | Error | Failed runs in our logs |
|---|---|---|---|
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16` | 523 | Cloudflare "Origin is unreachable" | 71 |
| `nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16` | 429 | `No available endpoints` (no `Retry-After`) | 8 + many 429 waits |
| `openai/gpt-oss-120b` | 503 | `Max retries (2) exhausted for model: openai/gpt-oss-120b` (`last_status_code: 523`) | 51 |

## Request IDs (reproduced with the documented sample requests)

Requests were sent exactly as in the GMI docs samples, about 2 seconds apart.

| Time (PST) | Time (UTC) | Model | HTTP | `x-gmi-request-id` | `cf-ray` |
|---|---|---|---|---|---|
| 2026-11-05 23:40:32 | 2026-11-06T07:40:32Z | Nemotron-3.5-Lightning-30B-A3B-BF16 | 523 | `995d6838-d649-4c9f-b772-39b6dd46d3fc` | `a56273620fb02b10-SJC` |
| 2026-11-05 23:40:35 | 2026-11-06T07:40:35Z | Nemotron-3.5-Lightning-30B-A3B-BF16 | 523 | `f548cea1-d726-4e59-89db-2f1c5b93edf2` | `a56273721fa2552b-SJC` |
| 2026-11-05 23:40:39 | 2026-11-06T07:40:39Z | Nemotron-3.5-Lightning-30B-A3B-BF16 | 523 | `36a52db8-a3ac-4fd0-abb3-e0482bc4da72` | `a56273899993eb26-SJC` |
| 2026-11-05 23:40:50 | 2026-11-06T07:40:50Z | Nemotron-3.5-Super-VL-120B-A12B-BF16 | 429 | `abe8ae34-1e35-4aa1-a915-e5899123c190` | `a56273ce9e2cebf3-SJC` |
| 2026-11-05 23:40:52 | 2026-11-06T07:40:52Z | Nemotron-3.5-Super-VL-120B-A12B-BF16 | 429 | `d1aded80-d192-489d-8ee2-715af4d706d0` | `a56273dc2f097b83-SJC` |
| 2026-11-05 23:40:54 | 2026-11-06T07:40:54Z | Nemotron-3.5-Super-VL-120B-A12B-BF16 | 429 | `cdb59d00-48a6-4cdb-8643-26f6b14e62ff` | `a56273e9b8fa1613-SJC` |
| 2026-11-05 23:40:56 | 2026-11-06T07:40:56Z | gpt-oss-120b | 503 | `56621e09-4825-4790-9b02-e5174d0e33bd` | `a56273f75ee0c65e-SJC` |
| 2026-11-05 23:40:59 | 2026-11-06T07:40:59Z | gpt-oss-120b | 503 | `7040887c-8a05-436b-9cb1-7f5346cacfcc` | `a56274088b4f2519-SJC` |
| 2026-11-05 23:41:02 | 2026-11-06T07:41:02Z | gpt-oss-120b | 503 | `bd4f3a34-caf3-42da-9715-b5b26aec2ffe` | `a56274194cc0cf8f-SJC` |
| 2026-11-05 23:41:04 | 2026-11-06T07:41:04Z | gemma-4-26b-a4b-it (control) | 200 | `2f314737-1a7b-4c76-9aa5-6888efabf856` | `a562742a1b3e3ec8-SJC` |

**Re-test 2026-11-06 about 15:42 PST (23:42 UTC):** all three still fail with the same errors.
Other models that also returned 503 `Max retries (2) exhausted` in this check:
`google/gemma-4-31b-it`, `Qwen/Qwen3-Next-80B-A3B-Thinking`, `nvidia/nemotron-3-ultra-550b-a55b`,
`stepfun-ai/Step-3.7-Flash`.

| Model | HTTP | `x-gmi-request-id` |
|---|---|---|
| Nemotron-3.5-Lightning-30B-A3B-BF16 | 523 | `ca1f494f-c43e-4963-a10b-7d796efeb685` |
| Nemotron-3.5-Lightning-30B-A3B-BF16 | 523 | `18c6794e-df4f-4c23-80cf-2d6200f89258` |
| Nemotron-3.5-Super-VL-120B-A12B-BF16 | 429 | `b729dafe-008b-4105-a820-192db126b41d` |
| Nemotron-3.5-Super-VL-120B-A12B-BF16 | 429 | `a52dc722-875e-44bb-9a3d-5607335fec79` |
| gpt-oss-120b | 503 | `7f15b21b-c01a-4b88-b2b9-7627b27feed4` |
| gpt-oss-120b | 503 | `b81a6b36-a004-4dfc-b37c-d14ff708f597` |

Sample requests used:

```json
{"model": "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16",
 "messages": [{"role": "system", "content": "You are a knowledgeable AI assistant."},
              {"role": "user", "content": "Explain the concept of quantum entanglement in simple terms."}]}

{"model": "nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16",
 "messages": [{"role": "system", "content": "You are a knowledgeable AI assistant."},
              {"role": "user", "content": "Explain quantum entanglement in simple terms."}],
 "temperature": 1.0, "top_p": 0.95, "max_tokens": 4096}

{"model": "openai/gpt-oss-120b",
 "messages": [{"role": "system", "content": "You are a helpful AI assistant"},
              {"role": "user", "content": "List 3 countries and their capitals."}],
 "temperature": 0, "max_completion_tokens": 500}
```

## Other issues found (models that are up)

### 1. `google/gemma-4-26b-a4b-it`: streaming with `tools` returns an empty stream

With `"stream": true` and a `tools` array, the response is HTTP 200 whose whole body is
`data: [DONE]`: no content, no tool-call deltas, no usage. The same request without
streaming returns a correct tool call. This happens every time (40 of 40 in our runs).

| Time (PST) | Request | HTTP | Body | `x-gmi-request-id` |
|---|---|---|---|---|
| 2026-11-05 23:41:27 | stream + tools | 200 | `data: [DONE]` only (14 bytes) | `60aa9898-78b7-4fa2-a52d-c560d1f753e5` |
| 2026-11-05 23:41:28 | no stream + tools (control) | 200 | correct `tool_calls` | `c5ec3ede-ef0a-4511-8589-3034fb3fba1d` |

Small related detail: the non-streamed reply has `"role": "user"` on the assistant message.
It should be `"assistant"`.

### 2. `zai-org/GLM-5.3-Flash`: image requests fail at random

Requests with an `image_url` (PNG data URL, about 53 KB, 1000×856) fail about 1 time in 4
(4 of 16 in an interleaved test at about 23:43 PST). When streaming, the error arrives as an
in-stream error event (`Internal server error`, code 500). When not streaming, it is a 503
`routing: framework forward exhausted: Internal Server Error` (`last_status_code: 500`,
`exhaustion_reason: max_retries_exceeded`). Text-only requests to the same model work.
Where the image sits in the message (before or after the text) makes no difference.

**Update 2026-11-06:** much of this is tied to streaming. Some images fail **every time** with
`"stream": true` (in-stream `Internal server error`) and succeed with `"stream": false` on the
same request. Our files `hdoc-06.png` and `hdoc-18.png` reproduce it 3 of 3 with streaming,
whether or not `seed` or `stream_options` are set. Non-streamed requests also hit occasional
503 `routing_exhausted` errors, which clear on retry.

| Time (PST) | Request | HTTP | `x-gmi-request-id` |
|---|---|---|---|
| 2026-11-05 23:41:29 | image + text | 200 | `73688f76-cc42-4480-ad11-a32f38e234ba` |
| 2026-11-05 23:41:30 | same image + text (image first) | 503 | `63050d4e-bbb0-4b81-89fe-cb813edeed8c` |

### 3. `google/gemma-4-26b-a4b-it`: tool call returned as raw text (non-streamed)

On 2026-11-06 (about 17:00 PST), 1 of 60 non-streamed multi-turn tool requests returned the
tool call inside `message.content` as raw template tokens, with no `tool_calls` field and
`finish_reason: "stop"`:

```
<|tool_call>callget_customer{customer_id:<|"|>C-105<|"|>}<tool_call|>
```

The server's tool-call parser seems to miss this format at times. We did not keep the request ID
for this run.

## What we need

1. Bring the three models back, or take them off `GET /v1/models` while they are down.
2. For capacity outages, return `503` with `Retry-After` instead of `429 No available endpoints`.
   Clients treat 429 as "slow down" and keep waiting.
3. Fix streamed tool calls on Gemma 4 26B A4B.
4. Look into the random 500s on GLM-5.3-Flash image requests.
5. Check the Gemma 4 tool-call parser for raw `<|tool_call>` output.
