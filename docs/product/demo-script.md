# North-Star Demo Script — Paraxis AI

> **Scenario**: "Wi-Fi is down in Block B, Room 204"  
> **Duration**: 3 Minutes  
> **Target Audience**: Hackathon Judges, University Leadership, Technical Evaluators

---

## Turn-by-Turn Execution Script

### Act 1: The Incident Report (0:00 - 0:45)
- **Presenter Action**: Open the Student Portal on mobile viewport (or simulated mobile frame).
- **Spoken Narrative**:
  > *"Every day, thousands of students face broken equipment in classrooms and dorms. Usually, they send a message to a WhatsApp group or submit a ticket into an unmonitored portal. Watch what happens when a student reports an issue in Paraxis AI."*
- **Presenter Action**: Type into the report box:
  ```
  "Wi-Fi is completely down in Block B, Room 204. Can't submit my assignment."
  ```
- **Presenter Action**: Click **Submit Report**.
- **Immediate UI Feedback**:
  - Report transitions to status `Ingested`.
  - Notification appears: *"Analyzing campus context and dispatching response..."*

---

### Act 2: The Command Center & Agent Reasoning (0:45 - 1:45)
- **Presenter Action**: Switch tab to the **Admin Command Center**.
- **Spoken Narrative**:
  > *"Over in the Operations Command Center, facilities staff don't see an unassigned ticket. They see Paraxis AI's agentic workflow actively coordinating the response in real time via Server-Sent Events."*
- **Visual Callouts on Screen**:
  1. **Entity Extraction**: System shows `Building: Block B`, `Room: 204`, `Category: IT_NETWORK`.
  2. **Campus Graph Resolution**: Highlights `Asset AP-04 (Cisco Catalyst 9120)` mounted in Room 204.
  3. **Duplicate Detection**: Agent finds a report submitted 4 minutes ago from Room 202 and automatically links them under master incident `INC-101`.
  4. **Policy Check**: The Policy Engine evaluates the action: `ALLOW: Routine IT work order`.
  5. **Automated Dispatch**: Work order auto-created and assigned to `Neha Reddy (IT Network Team)`.
  6. **SLA Countdown**: 15-minute acknowledgment timer starts.

---

### Act 3: Tool Safety & Deterministic Human-in-the-Loop (1:45 - 2:20)
- **Presenter Action**: Open a second report simulating an exceptional maintenance request:
  ```
  "The water pipe in the 3rd floor restroom has burst. Flooding the corridor. Estimated repair cost is $1,200."
  ```
- **Spoken Narrative**:
  > *"Now notice what happens when a request carries high financial or safety impact. The AI does NOT have unrestricted authority to dispatch contracts or spend money."*
- **Visual Callouts on Screen**:
  - The Policy Engine intercepts the proposed action:
    `Status: REQUIRE_HUMAN_APPROVAL`.
    `Reason: Cost exceeds $500 threshold ($1,200)`.
  - An interactive **Approval Drawer** pops up on the Director's screen.
  - Presenter clicks **Approve & Dispatch**. The work order is released.

---

### Act 4: Operational Memory & Recurring Patterns (2:20 - 3:00)
- **Presenter Action**: Navigate to the **Operational Insights** panel.
- **Spoken Narrative**:
  > *"Finally, Paraxis doesn't forget. Once the technician completes the Wi-Fi repair, our memory engine updates historical incident clusters."*
- **Visual Callouts on Screen**:
  - An Insight Card appears:
    > **⚠️ Chronic Failure Pattern Detected: Block B Wi-Fi**  
    > *Fact*: 4 network outages logged in Block B over the last 28 days.  
    > *Fact*: 3 incidents linked to Asset `AP-04`.  
    > *Recommendation*: Schedule firmware upgrade or hardware replacement for AP-04 to avoid recurring downtime.
- **Concluding Line**:
  > *"Paraxis AI doesn't just manage tickets. It sees what is happening, understands what matters, and coordinates what happens next. Thank you."*
