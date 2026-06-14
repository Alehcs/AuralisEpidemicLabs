# Architecture Notes

The dependency direction points inward: HTTP and file adapters call
application services, which coordinate pure domain and simulation modules.
The simulation package must remain independent of FastAPI, React, databases,
and presentation concerns so it can support interactive and headless modes.

Phase 2 executes each tick in this order: policy-before-mobility hook,
schedule-based movement, disease progression, policy-before-contacts hook,
zone contact aggregation, policy-before-transmission hook, transmission,
metrics, policy-after-metrics hook, and snapshot projection. A private
`random.Random` instance owned by each engine makes runs reproducible by seed.

Local run bundles are infrastructure artifacts under `outputs/runs`; batch
reports are written under `outputs/reports`. Neither mechanism changes the
framework independence of the simulation engine.
