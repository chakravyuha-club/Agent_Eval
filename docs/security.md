# AgentScore Security & SSRF Defense Model

Evaluating untrusted team submission files and connecting to arbitrary user-supplied HTTP endpoints poses severe security risks. AgentScore implements defense-in-depth measures.

---

## 1. Multi-Layer SSRF Protection for Stage 2 URLs

Arbitrary URLs submitted by teams undergo strict validation before any socket connection is established:

```
Submitted URL: https://agent.team01.cloud/predict
       │
       ▼
[1. Scheme Allowlist] ──► Must be 'http' or 'https' (https required in strict prod)
       │
       ▼
[2. Hostname Resolution] ──► DNS lookup resolving all A / AAAA records
       │
       ▼
[3. IP Subnet Validation] ──► Reject if IP matches:
                              - Loopback: 127.0.0.0/8, ::1
                              - RFC 1918 Private: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
                              - Link-Local: 169.254.0.0/16, fe80::/10
                              - Cloud Metadata: 169.254.169.254, metadata.google.internal
                              - Broadcast / Multicast: 224.0.0.0/4, 255.255.255.255/32
       │
       ▼
[4. Socket Connection with Timeout] ──► Isolated HTTP client with strict 10s timeout
       │
       ▼
[5. Redirect Hop Validation] ──► Follow redirects only if target IP passes checks 1-3
```

---

## 2. Spreadsheet Formula Injection (CSV Injection) Defense
When users upload team names, explanations, or notes, malicious actors may attempt spreadsheet formula injection:
- Formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped or prepended with a single quote `'` in all CSV/XLSX exports.

---

## 3. Ground-Truth Data Isolation
- Hidden test datasets reside only in server-side storage.
- Evaluator processes hidden data in memory and outputs only aggregated dimensional scores and high-level safe error categories (e.g., `schema_mismatch`, `timeout`, `incorrect_prediction`) without leaking actual expected values.
