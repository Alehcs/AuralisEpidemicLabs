# Declarative Configurations

JSON files are grouped by domain: scenarios, diseases, populations, policies,
experiments, and information. Config names are file stems, for example
`respiratory_like_v1` resolves to `diseases/respiratory_like_v1.json`.

`information/` holds Phase 4 official messages and rumors (`official_alert`,
`local_warning`, `false_safety_rumor`, `false_danger_rumor`,
`anti_authority_rumor`, `panic_rumor`). Population configs may carry an optional
`cognition` block (trust/fatigue/skepticism/curiosity/rumor-belief/compliance
means) and `behavioral_profiles` biases; both default safely when omitted so
earlier configs keep working.

`behavior/` holds Phase 6 behavior/transmission strength sets (defaults match the
calibrated Phase 5 constants). `adaptive/` holds adaptive-policy rule bundles that
react to live metrics (`counter_messaging`, `peer_warning_campaign`,
`trust_repair_message`, `targeted_local_alert`, `adaptive_isolation_encouragement`).
`sweeps/` holds parameter-grid sensitivity configs consumed by
`POST /experiments/sweep`. Experiments and their variants may reference a
`behavior_config` and an `adaptive_policy_config`; all default safely when omitted.

The examples are synthetic and are not epidemiological guidance or calibrated
models of real-world disease.

In Phase 1, disease `beta_base` is interpreted as transmission probability per
effective contact, `tick_minutes` defines simulation resolution, and zone
`contact_rate` is interpreted as effective contacts per agent per day.
