import sys

from ledger import CreditLedger, InvalidCreditError

DATABASE_PATH = "ledger.db"


def main() -> int:
    if len(sys.argv) != 4:
        print("Uso: python cli.py <event_id> <account_id> <amount_cents>")
        return 1

    event_id, account_id, raw_amount = sys.argv[1:4]
    ledger = CreditLedger(DATABASE_PATH)

    try:
        result = ledger.apply_credit(event_id, account_id, int(raw_amount))
    except InvalidCreditError as exc:
        print(f"Evento inválido: {exc}")
        return 2

    status = "aplicado" if result.applied else "ignorado (duplicado)"
    print(f"Evento {event_id}: {status}")
    print(f"Saldo de {account_id}: {result.balance_cents} centavos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
