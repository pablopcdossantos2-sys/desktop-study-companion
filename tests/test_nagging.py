from desktop_study_companion.accountability.nagging import NaggingPolicy


def test_higher_urgency_gets_shorter_initial_delay() -> None:
    policy = NaggingPolicy()
    assert policy.initial_delay_seconds(10) < policy.initial_delay_seconds(8)
    assert policy.initial_delay_seconds(8) < policy.initial_delay_seconds(5)
    assert policy.initial_delay_seconds(5) < policy.initial_delay_seconds(2)


def test_repeated_nags_escalate_and_speed_up() -> None:
    policy = NaggingPolicy()
    first = policy.decide(6, 0)
    later = policy.decide(6, 6)

    assert later.severity > first.severity
    assert later.delay_seconds < first.delay_seconds
