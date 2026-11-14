"""
patch_passed_failed.py: the patch passed in the repository and failed in the company.

Run:  python patch_passed_failed.py

An agent must move the certificate-handling library in the payment service to a new version
before the certificate expires on Friday. Two patches, both 12 lines, both pass the tests.

  benchmark-style grading: do the tests tied to the issue pass?
  product evaluation:      run what actually happens next, in a small simulation of the service
    - the test environment uses a certificate that never expires
    - the real certificate expires on Friday: does the service pick up the renewed one?
    - in the staged rollout the new token exchange times out once and is retried:
      is the payment authorized once or twice?
  and the work around the patch: dependencies found, missing access requested, payment
  instructions respected, evidence left for the reviewer.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

FRIDAY = datetime(2026, 11, 20, 0, 0)


@dataclass
class Cert:
    name: str
    not_after: Optional[datetime]           # None: never expires (the test environment)

    def valid(self, now: datetime) -> bool:
        return self.not_after is None or now < self.not_after


@dataclass
class Gateway:
    """The payment provider. It authorizes every request it receives, unless it saw the idempotency key."""
    authorizations: List[str] = field(default_factory=list)
    seen_keys: set = field(default_factory=set)
    fail_next_response: bool = False

    def exchange_and_authorize(self, order: str, key: Optional[str]) -> str:
        if key is None or key not in self.seen_keys:
            self.authorizations.append(order)
            if key:
                self.seen_keys.add(key)
        if self.fail_next_response:                 # the work was done, but the response is lost
            self.fail_next_response = False
            raise TimeoutError("token exchange timed out")
        return "ok"


@dataclass
class PaymentService:
    patch: Dict
    cert: Cert
    renewed: Optional[Cert] = None

    def handshake(self, now: datetime) -> bool:
        if not self.cert.valid(now) and self.patch["reloads_renewed_cert"] and self.renewed:
            self.cert = self.renewed
        return self.cert.valid(now)

    def pay(self, gw: Gateway, order: str) -> None:
        key = f"pay-{order}" if self.patch["idempotency_key"] else None
        for _ in range(2):                          # the new library retries once on timeout
            try:
                gw.exchange_and_authorize(order, key)
                return
            except TimeoutError:
                continue


PATCHES = [
    {"id": "patch-A", "lines": 12, "reloads_renewed_cert": False, "idempotency_key": False,
     "process": {"found the cert-renewal job that the new library no longer triggers": False,
                 "asked for access to the production certificate store": False,
                 "respected PAYMENTS.md: 'every retry must carry an idempotency key'": False,
                 "left evidence: rollout plan, what was tested and what was not": True}},
    {"id": "patch-B", "lines": 12, "reloads_renewed_cert": True, "idempotency_key": True,
     "process": {"found the cert-renewal job that the new library no longer triggers": True,
                 "asked for access to the production certificate store": True,
                 "respected PAYMENTS.md: 'every retry must carry an idempotency key'": True,
                 "left evidence: rollout plan, what was tested and what was not": True}},
]


def unit_tests(p: Dict) -> bool:
    svc = PaymentService(p, Cert("staging", None))
    gw = Gateway()
    svc.pay(gw, "o-1")
    return svc.handshake(FRIDAY) and gw.authorizations == ["o-1"]


def friday(p: Dict) -> bool:
    svc = PaymentService(p, Cert("prod-2025", FRIDAY), renewed=Cert("prod-2026", datetime(2027, 11, 20)))
    return svc.handshake(datetime(2026, 11, 20, 0, 1))


def canary_retry(p: Dict) -> int:
    svc = PaymentService(p, Cert("prod-2026", datetime(2027, 11, 20)))
    gw = Gateway(fail_next_response=True)
    svc.pay(gw, "o-42")
    return len(gw.authorizations)


def main() -> None:
    print("=" * 78 + "\nBENCHMARK-STYLE GRADING: DO THE TESTS PASS?\n" + "=" * 78)
    for p in PATCHES:
        print(f"  {p['id']}: {p['lines']} lines changed, tests {'PASS' if unit_tests(p) else 'FAIL'}  -> score 100%")
    print("  Perfect score for both. The test environment's certificate never expires.")

    print("\n" + "=" * 78 + "\nPRODUCT EVALUATION: WHAT HAPPENS NEXT\n" + "=" * 78)
    for p in PATCHES:
        auths = canary_retry(p)
        print(f"\n  {p['id']}")
        print(f"    Friday 00:01, the old certificate expires: "
              f"{'payments continue on the renewed certificate' if friday(p) else 'HANDSHAKE FAILS, first deploy breaks payments'}")
        print(f"    staged rollout, token exchange times out once and is retried: "
              f"{auths} authorization{'s' if auths > 1 else ''}{'  <- DUPLICATE CHARGE' if auths > 1 else ''}")
        done = sum(p["process"].values())
        print(f"    the work around the patch: {done} of {len(p['process'])}")
        for item, ok in p["process"].items():
            print(f"      [{'x' if ok else ' '}] {item}")
    print("\n  Neither failure exists in a public benchmark. Public evaluations show whether an agent solves")
    print("  a bounded task. Product evaluations show whether it survives in your organization.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
