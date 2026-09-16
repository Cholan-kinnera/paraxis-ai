# Paraxis AI — Web Frontend (`frontend`)

Next.js 14 (App Router) application: the public landing page and the operational console.

## Tech Stack
- Next.js 14 · React 18 · TypeScript
- Tailwind CSS (monochrome design system: black landing, white console)
- Three.js / React Three Fiber / @react-three/postprocessing — scroll-driven particle field on the landing page
- framer-motion (reveal animations) · lucide-react (icons)
- TanStack Query for server state (`lib/hooks.ts`), JWT auth with refresh rotation (`lib/api.ts`, `lib/auth.ts`)

## Routes
| Route | Theme | Purpose |
| :-- | :-- | :-- |
| `/` | black | Landing page (hero → features → showcase → governance → proof → pricing → CTA) over a single WebGL particle field driven by scroll progress |
| `/login` | white | Sign in (Core `POST /auth/token/`) |
| `/dashboard` | white | Command center: KPIs, live incident feed, pattern insights, active dispatch |
| `/incidents`, `/incidents/new`, `/incidents/[id]` | white | Incident list/filters, natural-language report form, detail with timeline, triage, state transitions and the **Agent Copilot** panel (Intelligence `POST /orchestrate/incident` + approval drawer → `/orchestrate/resume`) |
| `/tasks`, `/tasks/[id]` | white | Work orders with SLA meters and assign / start / complete / cancel actions |
| `/campus` | white | Buildings → floors → rooms → assets browser |
| `/agent` | white | Triage queue, workflow graph, policy rules |
| `/settings` | white | Profile, permissions, SLAs, tenancy |

Console routes live under `app/(platform)/` and share `components/platform/Shell.tsx` (sidebar + auth gate).

## Booting Locally
```bash
npm install
npm run dev          # http://localhost:3000
```
Requires Core (`:8000`) and Intelligence (`:8001`) — see `docs/operations/local-development.md`. Seed accounts (`python manage.py seed_dev_data`) use password `DevPassword123!`, e.g. `campus.admin@apex.edu`.

## Landing page 3D scene
`components/landing/3d/DashSphere.tsx` renders one `InstancedMesh`: a sphere built from ~6k short glowing dashes laid along latitude rows (one draw call), with bloom from `@react-three/postprocessing`. `stage.ts` holds a keyframe per section (`KEYS`, anchored to section ids) and interpolates between neighbouring keys as the viewport centre moves down the document, so the object makes one continuous journey and is never hidden:

hero bowl (pole anchored under `#hero-cta`) → rides up with the page and recedes → distant globe behind `#product` → weaves opposite the copy through `#platform` / `#report` / `#workflow`, tilting more each time → far behind `#governance` → aside at `#proof` → behind the `#stats` cards → right and back at `#pricing` → pole-on vortex at the right edge of `#final`.

Middle keys scale their side offset and radius on narrow viewports. `color`, `rings` and `density` are props on `<DashSphere>`.

## Fluid sizing
`app/globals.css` defines a `clamp()`-based type scale (`--step--2 … --step-7`), space scale (`--space-3xs … --space-3xl`), `--gutter` and `--container`, exposed in Tailwind as `text-f-*`, `p-fl-*`/`gap-fl-*`, `px-gutter` and `max-w-container`. Landing components use only these, so every size interpolates between 360px and 1600px viewports.
