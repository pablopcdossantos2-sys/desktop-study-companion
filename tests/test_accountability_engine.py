from desktop_study_companion.accountability.engine import AccountabilityEngine
from desktop_study_companion.accountability.models import InterventionKind


def test_escalation_thresholds() -> None:
    engine = AccountabilityEngine()
    assert engine.evaluate_distraction(59).kind == InterventionKind.NONE
    assert engine.evaluate_distraction(60).kind == InterventionKind.GENTLE_REMINDER
    assert engine.evaluate_distraction(180).kind == InterventionKind.FIRM_REMINDER
    assert engine.evaluate_distraction(300).kind == InterventionKind.DIRECT_CHALLENGE
    assert engine.evaluate_distraction(600).kind == InterventionKind.INSISTENT_CHALLENGE
