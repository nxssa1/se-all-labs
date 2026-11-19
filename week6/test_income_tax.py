import pytest
from income_tax import taxable_income, tax_due, refund_status

#Example test cases:
def test_new_regime():
    assert taxable_income(1000000, "new", 0) == 925000

def test_below_exemption():
    assert tax_due(200000, 30) == 0

#Write the rest of the test cases so that the code is 90- 100% covered.

# --- taxable_income ---

def test_negative_gross_raises():
    with pytest.raises(ValueError):
        taxable_income(-1, "new", 0)


def test_old_regime_investments_under_cap():
    # deduction = 50000 + 100000 = 150000
    assert taxable_income(500000, "old", 100000) == 350000


def test_old_regime_investments_over_cap():
    # investments capped at 150000 -> deduction = 50000 + 150000 = 200000
    assert taxable_income(500000, "old", 300000) == 300000


def test_unknown_regime_raises():
    with pytest.raises(ValueError):
        taxable_income(500000, "flat", 0)


def test_taxable_income_floors_at_zero():
    # gross - deduction < 0 -> 0
    assert taxable_income(60000, "new", 0) == 0


# --- tax_due ---

def test_tax_due_negative_taxable_raises():
    with pytest.raises(ValueError):
        tax_due(-1, 30)


def test_tax_due_senior_exempt_300000():
    assert tax_due(300000, 60) == 0


def test_tax_due_super_senior_exempt_500000():
    assert tax_due(500000, 80) == 0


def test_tax_due_first_slab_5_percent():
    # exempt 250000, taxable 400000 -> slab 150000 <= 250000 -> 5%
    assert tax_due(400000, 30) == 7500


def test_tax_due_second_slab_20_percent():
    # exempt 250000, taxable 700000 -> slab 450000 > 250000
    # 12500 + (450000-250000)*20//100 = 12500 + 40000 = 52500
    assert tax_due(700000, 30) == 52500


# --- refund_status ---

def test_refund_on_time():
    assert refund_status(10000, 8000, True) == "refund"


def test_refund_delayed():
    assert refund_status(10000, 8000, False) == "refund delayed"


def test_pay_balance_on_time():
    assert refund_status(5000, 8000, True) == "pay balance"


def test_pay_balance_with_penalty():
    assert refund_status(5000, 8000, False) == "pay balance with penalty"


def test_settled():
    assert refund_status(8000, 8000, True) == "settled"
