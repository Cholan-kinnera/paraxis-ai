# Design System & UI Specification — Paraxis AI

> **Purpose**: Design tokens, component aesthetics, layout principles, and engineering UI workflow for Paraxis AI.
> **Visual Direction**: Premium, enterprise-grade, technical, restrained, trustworthy, information-dense, and modern. Avoids generic bright college ERP styling.

---

## 1. Design Philosophy & Aesthetic Core

Paraxis AI is styled as an **institutional mission-control platform**:
- **Palette**: Deep slate and obsidian backgrounds paired with crisp neutral typography, subtle borders, and vivid functional status accents (emerald, amber, rose, cyan).
- **Surface Elevation**: Layered card surfaces using subtle borders (`border-border/40`) and soft backdrop blurs (`backdrop-blur-md`), giving a precision aerospace/fintech aesthetic.
- **Information Density**: High data density with clean tabular rows, badge indicators, and collapsible inspector panels rather than excessive white space.
- **Cognitive Transparency**: Agent activities are rendered through structured **Evidence Cards** and **Decision Summaries**—never through raw markdown streaming or chat-bubble walls.

---

## 2. Design Tokens & Color Palette

### 2.1 Neutral Foundation (Dark Mode Default)
- `background`: `#090D16` (Obsidian Base)
- `card`: `#0F172A` (Deep Slate Surface)
- `card-hover`: `#1E293B`
- `border`: `#1E293B` (Subtle divider)
- `foreground`: `#F8FAFC` (High-contrast text)
- `muted-foreground`: `#94A3B8` (Secondary text)

### 2.2 Semantic & Operational Accents
- `status-success` / `status-operational`: `#10B981` (Emerald) — System normal, task completed, SLA met.
- `status-warning` / `status-triaging`: `#F59E0B` (Amber) — Triaging, pending human approval, SLA warning.
- `status-error` / `status-critical`: `#EF4444` (Rose) — Outage, critical safety hazard, SLA breached.
- `status-info` / `status-agent`: `#06B6D4` (Cyan) — Agent reasoning step, context retrieved, memory updated.
- `brand-primary`: `#3B82F6` (Electric Blue) — Primary interactive actions and active navigation.

### 2.3 Typography Hierarchy
- **Font Family**: Inter, SF Pro, or Outfit for UI; JetBrains Mono for system IDs, asset tags, and telemetry coordinates.
- `text-xs` (12px / 16px): Timestamps, asset tags, status badges.
- `text-sm` (14px / 20px): Body copy, table cells, form labels.
- `text-base` (16px / 24px): Subheadings, card titles.
- `text-xl` (20px / 28px): Section titles.
- `text-2xl` (24px / 32px): Dashboard metrics, modal headers.

---

## 3. Core Component Library (shadcn/ui Based)

1. **Operational Status Badges**:
   - `<Badge variant="success">Operational</Badge>`
   - `<Badge variant="warning">Pending Approval</Badge>`
   - `<Badge variant="destructive">Critical Outage</Badge>`
   - `<Badge variant="agent">Agent Reasoning</Badge>`
2. **Agent Evidence Card**:
   - Renders resolved entities (Building, Room, Asset) with a verification icon.
   - Displays confidence score (e.g., `98% Confidence`).
   - Links to related incidents with a duplicate indicator.
3. **Interactive Approval Drawer**:
   - High-impact modal/drawer highlighting action cost, justification, and policy rule violated.
   - Explicit `Approve & Dispatch` (Primary Green) vs. `Reject Action` (Outline Red) buttons.
4. **Live Telemetry Timeline**:
   - Step-by-step progress bar showing `Ingested -> Triaging -> Policy Check -> Dispatched -> Resolved`.

---

## 4. Engineering Workflow & Figma Policy (Decoupled & Non-Blocking)

### 4.1 Guiding Principle
```
DOCUMENTATION + DESIGN SYSTEM + API CONTRACTS + IMPLEMENTATION
(with Figma as an OPTIONAL visual reference)
```

### 4.2 Non-Negotiable Policy Invariants
- **Figma is OPTIONAL for engineering execution**: Figma may exist and may be used as a visual reference/source of approved designs, but engineering must NEVER wait for Figma.
- **No Blocking Dependencies**: A missing Figma design must NEVER block implementation. Developers must NOT be required to create a Figma design before implementing a feature.
- **Figma is NOT the Source of Truth**: Figma must NOT be treated as the source of truth for architecture, APIs, backend behavior, domain logic, security, or product requirements.
- **Authoritative Sources**: Product, architecture, and technical documentation alongside approved API contracts remain authoritative for engineering behavior. The design system tokens and reusable UI components remain authoritative for implementation consistency.
- **Execution Rule**: If an approved Figma design exists, frontend engineers MAY use it as a visual reference. If no Figma design exists, frontend engineers MUST proceed immediately using documented product requirements, design tokens, component primitives, accessibility requirements, and established UI patterns. Figma can be updated later when useful, but this must never block delivery.

### 4.3 Frontend Engineering Workflow
When implementing frontend screens or components, follow this decoupled sequence:
1. **Read Product Requirements**: Understand the problem, user journey, and functional acceptance criteria.
2. **Read Architecture & API Documentation**: Understand endpoint contracts, error envelopes, and data schemas.
3. **Check Design System & UI Components**: Review existing design tokens, status badges, cards, and shadcn primitives.
4. **Check Figma (Optional)**: If an approved Figma design exists, implement the visual direction faithfully.
5. **Proceed If Missing**: If no Figma design exists, proceed immediately without waiting.
6. **Validate in Browser**: Verify responsiveness, loading, error, and empty states.
7. **Maintain Consistency**: Keep implementation aligned with design system tokens and accessibility standards.
8. **Optional Sync**: Optionally reflect useful visual patterns back into Figma at a later time.

---

## 5. Optional Reference Figma Workspace Architecture

When visual designers or engineers choose to maintain or update an optional visual workspace in Figma, the following 13-page reference structure may be used:

- **00 — Cover**: Project title, version, contributors, status.
- **01 — Foundations**: Colors, typography, spacing, shadows, elevation, iconography.
- **02 — Design System**: Reusable buttons, inputs, badges, cards, modals, tables.
- **03 — Marketing**: Landing page, product overview, architecture diagram graphics.
- **04 — Student Experience**: Mobile-first issue reporting screen, tracking view, confirmation modal.
- **05 — Admin Command Center**: Global multi-campus map, live incident feed, KPI metrics.
- **06 — Incident Intelligence**: Detailed incident inspection view, entity breakdown, timeline.
- **07 — Attendance**: Class session monitor, cohort anomaly alerts, warden communication.
- **08 — Mess Intelligence**: Headcount forecast graph, food waste logging interface.
- **09 — Safety & Trust**: Encrypted safety case review, whistleblower masking view, broadcast dispatch.
- **10 — Agent Activity**: Live agent run inspector, tool execution telemetry, token/cost monitor.
- **11 — Prototypes**: Interactive click-through prototypes for hackathon demo.
- **12 — Design Reference & Asset Exports (Optional)**: Design reference redlines and asset exports.
