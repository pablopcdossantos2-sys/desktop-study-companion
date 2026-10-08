from dataclasses import dataclass


@dataclass(slots=True)
class Personality:
    warmth: int = 60
    sarcasm: int = 40
    strictness: int = 75
    patience: int = 45
    humor: int = 50
    initiative: int = 75

    def __post_init__(self) -> None:
        for name in (
            "warmth",
            "sarcasm",
            "strictness",
            "patience",
            "humor",
            "initiative",
        ):
            value = getattr(self, name)
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
