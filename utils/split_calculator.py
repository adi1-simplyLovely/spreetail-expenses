def calculate_equal_split(total_amount: float, members: list) -> dict:
    """
    Splits the total amount equally among all members.
    Handles rounding errors by giving the remaining paisa to the first member.
    """
    if not members:
        return {}
        
    base_share = round(total_amount / len(members), 2)
    splits = {member: base_share for member in members}
    
    # Check if rounding caused a mismatch
    total_split = sum(splits.values())
    difference = round(total_amount - total_split, 2)
    
    # Add difference to the first person (to ensure exact sum)
    if difference != 0:
        splits[members[0]] = round(splits[members[0]] + difference, 2)
        
    return splits


def calculate_percentage_split(total_amount: float, percentages: dict) -> dict:
    """
    Splits amount based on percentage shares.
    percentages: dict of {user_id: percentage} (e.g., {"Aisha": 30, "Rohan": 30})
    Validates that percentages sum to 100%.
    """
    if not percentages:
        return {}
        
    total_pct = sum(percentages.values())
    if not (99.9 <= total_pct <= 100.1):  # Allow tiny floating point rounding error
        raise ValueError(f"Percentages must sum to 100%. Got {total_pct}%")
        
    splits = {}
    for user_id, pct in percentages.items():
        splits[user_id] = round((total_amount * pct) / 100, 2)
        
    # Fix any rounding remainders like equal split
    total_split = sum(splits.values())
    difference = round(total_amount - total_split, 2)
    if difference != 0:
        first_user = list(splits.keys())[0]
        splits[first_user] = round(splits[first_user] + difference, 2)
        
    return splits


def calculate_unequal_split(exact_amounts: dict) -> dict:
    """
    Directly assigns exact amounts.
    exact_amounts: dict of {user_id: amount} (e.g., {"Rohan": 700, "Priya": 400})
    """
    if not exact_amounts:
        return {}
        
    # We do not validate against a total_amount here because the user provides 
    # the exact amounts directly, but the caller should validate that the sum 
    # of these equals the total expense amount.
    return {user_id: round(amount, 2) for user_id, amount in exact_amounts.items()}


def calculate_share_split(total_amount: float, shares: dict) -> dict:
    """
    Splits amount based on relative shares.
    shares: dict of {user_id: number_of_shares} (e.g., {"Aisha": 1, "Rohan": 2})
    """
    if not shares:
        return {}
        
    total_shares = sum(shares.values())
    if total_shares <= 0:
        raise ValueError("Total shares must be greater than zero.")
        
    splits = {}
    for user_id, share in shares.items():
        splits[user_id] = round((total_amount * share) / total_shares, 2)
        
    # Fix any rounding remainders
    total_split = sum(splits.values())
    difference = round(total_amount - total_split, 2)
    if difference != 0:
        first_user = list(splits.keys())[0]
        splits[first_user] = round(splits[first_user] + difference, 2)
        
    return splits


# ==========================================
# INLINE UNIT TESTS (with CSV examples)
# ==========================================

if __name__ == "__main__":
    print("Running split calculator tests...")
    
    # 1. Equal Split Test (Pizza Friday - 1440 / 3 people)
    # Testing rounding logic: 100 / 3 = 33.33 + 33.33 + 33.33 (sum 99.99), so person 1 gets 33.34
    res1 = calculate_equal_split(100.0, ["A", "B", "C"])
    assert res1["A"] == 33.34
    assert res1["B"] == 33.33
    assert res1["C"] == 33.33
    assert sum(res1.values()) == 100.0

    # 2. Percentage Split Test (Pizza Friday - 1440)
    # Aisha 30%, Rohan 30%, Priya 30%, Meera 10%
    res2 = calculate_percentage_split(1440.0, {"Aisha": 30, "Rohan": 30, "Priya": 30, "Meera": 10})
    assert res2["Aisha"] == 432.0
    assert res2["Rohan"] == 432.0
    assert res2["Priya"] == 432.0
    assert res2["Meera"] == 144.0
    assert sum(res2.values()) == 1440.0
    
    # Test percentage overflow (Anomaly 07: 110%)
    try:
        calculate_percentage_split(1440.0, {"Aisha": 30, "Rohan": 30, "Priya": 30, "Meera": 20})
        assert False, "Should have raised ValueError for 110%"
    except ValueError:
        pass # Expected

    # 3. Unequal Split Test (Aisha Birthday Cake - 1500)
    # Rohan 700; Priya 400; Meera 400
    res3 = calculate_unequal_split({"Rohan": 700, "Priya": 400, "Meera": 400})
    assert res3["Rohan"] == 700.0
    assert res3["Priya"] == 400.0
    assert res3["Meera"] == 400.0
    assert sum(res3.values()) == 1500.0

    # 4. Share Split Test (Scooter Rentals - 3600)
    # Aisha 1; Rohan 2; Priya 1; Dev 2 (Total shares = 6)
    res4 = calculate_share_split(3600.0, {"Aisha": 1, "Rohan": 2, "Priya": 1, "Dev": 2})
    assert res4["Aisha"] == 600.0
    assert res4["Rohan"] == 1200.0
    assert res4["Priya"] == 600.0
    assert res4["Dev"] == 1200.0
    assert sum(res4.values()) == 3600.0
    
    print("All tests passed successfully! ✅")
