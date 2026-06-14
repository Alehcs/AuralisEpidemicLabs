# Architecture Notes

The dependency direction points inward: HTTP and file adapters call
application services, which coordinate pure domain and simulation modules.
The simulation package must remain independent of FastAPI, React, databases,
and presentation concerns so it can support interactive and headless modes.
