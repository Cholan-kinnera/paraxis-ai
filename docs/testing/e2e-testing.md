# End-to-End (E2E) Browser Testing — Paraxis AI

> **Purpose**: Playwright browser automation verifying the North-Star demo workflow and mission-critical user journeys.

---

## 1. The North-Star E2E Test Suite (`tests/e2e/test_wifi_demo.spec.ts`)

The critical automated E2E test asserts the entire Wi-Fi outage loop:
1. Student logs into portal and submits: `"Wi-Fi is down in Block B, Room 204"`.
2. Verifies that the UI transitions to status `INGESTED`.
3. Operator views the Command Center; verifies that the incident appears with extracted entities:
   - `Building: Block B`
   - `Room: 204`
   - `Asset: AP-04`
4. Verifies that the task was automatically dispatched and assigned to IT Network staff.
5. Verifies that the SLA timer starts counting down.
6. Simulates technician completing repair; verifies reporter receives confirmation prompt.

---

## 2. Test Execution
```bash
# Run all Playwright E2E tests headless
npx playwright test

# Run interactive UI mode for debugging
npx playwright test --ui
```
