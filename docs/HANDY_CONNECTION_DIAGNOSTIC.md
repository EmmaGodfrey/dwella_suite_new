# Handy chat connection failure

## Current status after provider redeployment

Rechecked on 2026-10-23 after the provider corrected the path and redeployed:

- The correct script is `https://handyai.wazabanda.dev/widget/v1/agent.js` (singular `widget`). It returns HTTP 200, `application/javascript`, and actual JavaScript. The guide now specifies this corrected URL.
- The guide's token-based-app option documents `window.HandyAgent.getToken()` and `window.HandyAgent.refresh()`. Dwella can supply its existing short-lived token response through that callback; no durable Dwella API credential is sent to Handy.
- Loaded the corrected official widget on the staging origin in a real browser, authenticated as the test landlord, using this documented callback and Dwella's token endpoint. The widget mounted and opened successfully.
- Sending a no-tools greeting through the official widget displayed `the connection is closed`. Screenshot: ignored local artifact `output/redeployed-official-widget.png`.
- Direct authenticated `/agent/me/` still returns HTTP 200 with thinker and actor enabled. A fresh direct `/agent/chat/` request still emits the same error and done events without reply text. Fresh session: `644a5248-b499-46b0-af3b-6d2f10e554a6`.

The script-loading issue is resolved at the corrected URL. The chat failure is reproducible through both the official widget and Dwella's native client. Earlier plural-path findings below are historical and must not be presented as a current defect at the corrected URL.

Reproduced on 2026-10-23 against the staging landlord. No business records were changed.

## Confirmed behavior

- Dwella issues a short-lived, organization-scoped token successfully.
- Handy `GET /agent/me/` returns HTTP 200 with thinker and actor enabled for the landlord.
- Direct authenticated `POST /agent/chat/` requests return HTTP 200 with `text/event-stream`.
- Both a vacant-unit question and a greeting explicitly requesting no tools produce a session event, an error event, and a done event, without answer text.
- The error is returned by Handy, independently of the Dwella browser interface:

```text
data: {"type": "error", "message": "the connection is closed"}
data: {"type": "done"}
```

## Correlation IDs

- Vacant-unit question: `1babd2da-af81-46df-bd69-40bbe8e22213`
- Greeting without tools: `620f720d-cc10-41af-8a27-3029fb165619`

## Boundary and next investigation

The failing endpoint is `https://dwella.handyagents.wazabanda.dev/agent/chat/`.
Staging PostgreSQL/gateway logs inspected during reproduction did not expose a corresponding PostgreSQL error. This does not establish which connection inside Handy failed.

The Handy maintainer needs the server exception traceback for these session IDs. Check connection acquisition/lifetime and exception handling inside the chat stream, including provider bookkeeping, external database access, and model-provider connections. The HTTP 200 response alone is not a successful chat check.

After a fix, verify actual reply text, a portfolio read, and an approved creation through the live assistant. A successful identity check or mocked browser stream does not validate these flows.

No credentials or signing tokens are included in this report.

## Official interface cross-check

On 2026-10-23, the alternative provider interfaces were checked without changing Dwella's deployed integration:

- `https://dwella.handyagents.wazabanda.dev/` returned HTTP 404 in a browser.
- `https://dwella.handyagents.wazabanda.dev/agent/` returned HTTP 404 in a browser.
- The approved integration guide still specifies `https://handyai.wazabanda.dev/widgets/v1/agent.js` as its widget script.
- That script URL returned HTTP 200 with `Content-Type: text/html` and an HTML document beginning with `<!doctype html>`.
- Attempting to insert that official script on the staging origin triggered the script error handler; the widget did not bootstrap (`window.HandyAgent` remained undefined).

Consequently, the official widget could not reach a chat test. These are two separate provider problems: the advertised widget asset is not served as JavaScript, and the working chat API emits a connection error. A working hosted UI URL or corrected official widget URL is required to compare actual chat behavior through the provider UI.
