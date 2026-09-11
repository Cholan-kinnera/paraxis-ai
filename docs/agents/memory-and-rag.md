# Operational Memory & RAG Architecture — Paraxis AI

> **Purpose**: Design for operational retrieval-augmented generation (RAG) and long-term institutional memory. Distinguishes FACT from INFERENCE and RECOMMENDATION.

---

## 1. Operational RAG (Not "Chat with PDF")

In Paraxis AI, RAG does not exist to power an open-ended conversational bot. It is an **active context retrieval pipeline** that equips the LangGraph agent with real-time operational knowledge:

1. **Campus Physical Graph Documents**: Floorplans, equipment manuals, access point deployment lists.
2. **Department Standard Operating Procedures (SOPs)**: Maintenance protocols, safety checklists, emergency contacts.
3. **Campus Policy Limits**: Spending thresholds, warranty coverage, vendor agreements.
4. **Historical Incident Embeddings**: Past resolutions, diagnostic notes, and part replacements.

All documents are embedded into `knowledge_embeddings` in PostgreSQL using `pgvector` with mandatory tenant filters.

---

## 2. The Operational Memory Engine

When incidents are resolved, Paraxis AI stores an operational vector containing:
- Failure mode description
- Asset tag and physical location
- Resolved component (e.g., "Replaced blown capacitor on power board")
- Total downtime duration

### Recurring Pattern Analysis
A periodic background task clusters resolved incidents within spatial and asset boundaries over 30-day windows. When 3 or more related failures occur on the same asset or circuit:
An `OperationalInsight` is created.

---

## 3. Strict Epistemological Classification: FACT vs. INFERENCE vs. RECOMMENDATION

To maintain absolute institutional credibility and prevent AI hallucinations from polluting facility records, every insight strictly segregates:

| Epistemic Level | Definition | Example in Paraxis UI |
| :--- | :--- | :--- |
| **FACT** | Verifiable empirical data from database records or telemetry logs. | *"Block B experienced 4 network outages in the last 28 days. 3 were linked to AP-04."* |
| **INFERENCE** | Probabilistic deduction derived from patterns or correlations. | *"AP-04 exhibits recurring firmware crash signatures following campus power surges."* |
| **RECOMMENDATION** | Actionable suggestion proposed for human decision-makers. | *"Schedule hardware diagnostics and deploy surge protectors on Block B switch rack."* |

> [!CAUTION]
> The AI must **never** state an inference as an empirical fact. Doing so damages operator trust and risks misallocating campus budget.
