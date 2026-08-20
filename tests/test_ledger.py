from ledger import CreditLedger


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


def test_unknown_account_has_zero_balance(ledger):
    assert ledger.balance("acc-inexistente") == 0
