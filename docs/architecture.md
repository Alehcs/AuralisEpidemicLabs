# Architecture Notes

The dependency direction points inward: HTTP and file adapters call
application services, which coordinate pure domain and simulation modules.
The simulation package must remain independent of FastAPI, React, databases,
and presentation concerns so it can support interactive and headless modes.

Phase 1 executes each tick in this order: movement, disease progression,
zone contact aggregation, transmission, metrics, and snapshot projection. A private
`random.Random` instance owned by each engine makes runs reproducible by seed.
