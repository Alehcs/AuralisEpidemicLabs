"""Contact record and scheduled policy hook tests."""


def test_contact_summary_is_generated_per_populated_zone(engine_factory) -> None:
    engine = engine_factory(seed=12, with_policy=False)

    snapshot = engine.step()

    assert snapshot.contact_summary
    assert all(record.tick == 1 for record in snapshot.contact_summary)
    assert sum(record.contact_count for record in snapshot.contact_summary) > 0
    assert sum(record.new_infections for record in snapshot.contact_summary) == snapshot.metrics.new_infections


def test_policy_hooks_activate_on_configured_tick(engine_factory) -> None:
    engine = engine_factory(seed=12, with_policy=True)

    engine.run(24)

    hooks = [item[1] for item in engine.policy_engine.hook_history if item[0] == 24]
    assert hooks == [
        "before_mobility",
        "before_contacts",
        "before_transmission",
        "after_metrics",
    ]
    assert engine.snapshot().active_policies == ["local_alert_policy"]
