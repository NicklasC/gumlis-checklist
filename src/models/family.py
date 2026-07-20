from dataclasses import dataclass


FAMILY_MEMBERS = ("Nicklas", "Ida", "Thor", "Johanna")


@dataclass(frozen=True)
class FamilyConnection:
    device_token: str
    member: str

    def __post_init__(self):
        if len(self.device_token) < 32:
            raise ValueError("Enhetsnyckeln är för kort")
        if self.member not in FAMILY_MEMBERS:
            raise ValueError("Okänd familjemedlem")
