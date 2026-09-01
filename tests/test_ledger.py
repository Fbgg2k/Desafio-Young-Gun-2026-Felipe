import threading

import pytest

from ledger import CreditLedger, InvalidCreditError


def test_applies_credit_once(ledger):
    result = ledger.apply_credit("evt-1", "acc-1", 1000)

    assert result.applied is True
    assert result.balance_cents == 1000
    assert ledger.balance("acc-1") == 1000


def test_different_events_accumulate(ledger):
    ledger.apply_credit("evt-1", "acc-1", 1000)
    ledger.apply_credit("evt-2", "acc-1", 250)

    assert ledger.balance("acc-1") == 1250


def test_accounts_are_independent(ledger):
    ledger.apply_credit("evt-1", "acc-1", 1000)
    ledger.apply_credit("evt-2", "acc-2", 700)

    assert ledger.balance("acc-1") == 1000
    assert ledger.balance("acc-2") == 700


def test_duplicate_event_is_applied_only_once(ledger):
    ledger.apply_credit("evt-1", "acc-1", 1000)
    result = ledger.apply_credit("evt-1", "acc-1", 1000)

    assert result.applied is False
    assert ledger.balance("acc-1") == 1000


def test_duplicate_event_is_ignored_after_restart(database_path):
    CreditLedger(database_path).apply_credit("evt-1", "acc-1", 1000)

    restarted = CreditLedger(database_path)
    result = restarted.apply_credit("evt-1", "acc-1", 1000)

    assert result.applied is False
    assert restarted.balance("acc-1") == 1000


def test_invalid_credit_raises_and_keeps_balance(ledger):
    ledger.apply_credit("evt-valid", "acc-1", 250)

    for event_id, account_id, amount in [
        ("", "acc-1", 100),
        ("evt-invalid", "", 100),
        ("evt-invalid", "acc-1", 0),
        ("evt-invalid", "acc-1", -1),
    ]:
        with pytest.raises(InvalidCreditError):
            ledger.apply_credit(event_id, account_id, amount)

    assert ledger.balance("acc-1") == 250

    result = ledger.apply_credit("evt-valid", "acc-1", 100)
    assert result.applied is False
    assert ledger.balance("acc-1") == 250


def test_concurrent_duplicate_event_is_applied_only_once(database_path):
    ledger = CreditLedger(database_path)
    barrier = threading.Barrier(8)
    results = []
    lock = threading.Lock()

    def worker():
        barrier.wait()
        result = ledger.apply_credit("evt-shared", "acc-1", 100)
        with lock:
            results.append(result)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    applied_count = sum(1 for result in results if result.applied)
    assert applied_count == 1
    assert ledger.balance("acc-1") == 100


def test_unknown_account_has_zero_balance(ledger):
    assert ledger.balance("acc-inexistente") == 0
