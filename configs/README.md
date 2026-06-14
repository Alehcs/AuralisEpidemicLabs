# Declarative Configurations

JSON files are grouped by domain: scenarios, diseases, populations, policies,
and experiments. Config names are file stems, for example
`respiratory_like_v1` resolves to `diseases/respiratory_like_v1.json`.

The examples are synthetic and are not epidemiological guidance or calibrated
models of real-world disease.

In Phase 1, disease `beta_base` is interpreted as transmission probability per
effective contact, `tick_minutes` defines simulation resolution, and zone
`contact_rate` is interpreted as effective contacts per agent per day.
