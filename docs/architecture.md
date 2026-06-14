# Architecture Notes

The dependency direction points inward: HTTP and file adapters call
application services, which coordinate pure domain and simulation modules.
The simulation package must remain independent of FastAPI, React, databases,
and presentation concerns so it can support interactive and headless modes.

Phase 3 executes each tick in this order: resolve active policy modifiers,
update official-alert exposure and perceived risk, progress disease, apply
symptomatic isolation, run schedule-based movement, aggregate policy-adjusted
zone contacts, transmit with contact/transmission multipliers, compute metrics,
and project a snapshot. A private `random.Random` instance owned by each engine
makes runs reproducible by seed.

`PolicyHookEngine` resolves bounded effects but does not implement movement,
contacts, or disease logic itself. `InformationEngine` owns official alert
exposure. This preserves narrow simulation components and keeps policy
configuration independent from HTTP and presentation layers.

Local run bundles are infrastructure artifacts under `outputs/runs`; batch
reports are written under `outputs/reports`. Neither mechanism changes the
framework independence of the simulation engine.
