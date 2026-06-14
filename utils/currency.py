USD_TO_INR_RATE = 83.50

def convert_to_inr(amount: float, currency: str) -> float:
    """
    Converts amount to INR if the currency is USD.
    Uses the fixed historical rate of 1 USD = 83.50 INR.
    """
    currency = currency.strip().upper()
    if currency == 'USD':
        return round(amount * USD_TO_INR_RATE, 2)
    return round(amount, 2)
