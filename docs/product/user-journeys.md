# User Journeys — Paraxis AI

> **Purpose**: Step-by-step operational workflows detailing human interactions, system automations, and agent checkpoints across core user journeys.

---

## 1. Journey A: Reporting and Auto-Resolving a Classroom IT Failure

- **Actor**: Dr. Priya Sharma (Faculty)
- **Context**: 5 minutes before CS301 begins in Room 204. The projector and ceiling Wi-Fi are unresponsive.

```mermaid
sequenceDiagram
    autonumber
    actor Faculty as Dr. Priya Sharma
    participant Portal as Paraxis Web Portal
    participant Core as Django Core
    participant Agent as LangGraph Agent Graph
    participant Staff as IT Technician

    Faculty->>Portal: Types: "Projector and Wi-Fi dead in Room 204, Block B. Class starts in 5 mins!"
    Portal->>Core: POST /api/v1/incidents
    Core->>Core: Ingest incident (Status: INGESTED, Priority: Unassigned)
    Core->>Agent: Trigger Incident Workflow
    
    Agent->>Agent: Extract: Room 204, Block B, Assets: Projector, Wi-Fi. Urgency: High.
    Agent->>Agent: Context: Seminar scheduled in 5 mins (Impact: 60 students).
    Agent->>Agent: Calculate Priority: HIGH.
    Agent->>Agent: Propose Action: Dispatch nearest on-duty IT tech + Notify AV lead.
    Agent->>Agent: Policy Gate: Action is routine classroom dispatch -> ALLOW.
    
    Agent->>Core: POST /internal/v1/tasks (Auto-assign to Neha Reddy, Start 15m SLA)
    Core-->>Portal: Realtime Update: "High Priority Task Dispatched to Neha Reddy (ETA 4 mins)"
    Faculty->>Portal: Sees assigned technician and live tracking.
    
    Staff->>Portal: Acknowledges task in 2 mins, arrives and resets HDMI switch & breaker.
    Staff->>Portal: Marks task COMPLETED with photo evidence.
    Core-->>Faculty: Notification: "Issue resolved. Please confirm status."
    Faculty->>Portal: Taps "Confirm Working". Incident CLOSED.
```

---

## 2. Journey B: Duplicate Detection and Incident Clustering

- **Actors**: Multiple students in Hostel Block B
- **Scenario**: A central fiber switch trips, disconnecting Wi-Fi across floors 2 and 3.

1. **Student 1 (Room 201)** reports: *"Internet is not working in 201."*
   - Paraxis creates master incident `INC-101`, contextualizes to Floor 2 Switch, dispatches Network Team.
2. **Student 2 (Room 204)** reports: *"Wi-Fi down in Block B Room 204."*
   - Agent graph calculates spatial-temporal similarity: same building (Block B), same timeframe (< 10 mins apart), same category (Wi-Fi).
   - Agent identifies `INC-101` as master incident.
   - Action proposed: `LINK_DUPLICATE`.
   - Policy evaluates `LINK_DUPLICATE` -> `ALLOW`.
   - Student 2's incident is marked `DUPLICATE_LINKED` to `INC-101`.
   - Student 2 receives notification: *"We are already actively addressing a network outage in Block B (Assigned to IT Team). Tracking master incident INC-101."*
3. **Operational Result**: Zero duplicate dispatches. Technicians focus on one central repair.

---

## 3. Journey C: Sensitive Safety Case with Masked Identity

- **Actor**: Student reporting harassment
- **Scenario**: Confidential report submitted through the Safety & Trust module.

1. Student opens **Safety & Trust** reporting tab and checks *"Submit Confidentially"*.
2. Inputs incident details regarding an encounter near the library.
3. Django Core encrypts details into `SafetyCase` table:
   - Reporter user ID is hashed and masked.
   - Access permission restricted strictly to `safety:view_confidential`.
   - Excluded from public command center dashboards.
4. Designated Safety Officer receives encrypted high-priority alert.
5. Officer coordinates private check-in with the student via secure one-way messaging.
