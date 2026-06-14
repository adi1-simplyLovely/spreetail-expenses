from sqlalchemy.orm import Session
from models import GroupMember, Expense, Settlement

def compute_net_balances(group_id: int, db: Session) -> dict:
    """
    Computes the net balance for every member in the group.
    Positive balance (+) = The user is owed money by the group.
    Negative balance (-) = The user owes money to the group.
    
    Formula:
    Net Balance = (Expenses Paid) - (Share Owed) + (Settlements Paid) - (Settlements Received)
    """
    # 1. Initialize balances for all group members (even those who left, as they might still owe/be owed)
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    balances = {m.user_id: 0.0 for m in members}
    
    # 2. Add expenses paid (increases balance)
    expenses = db.query(Expense).filter(
        Expense.group_id == group_id, 
        Expense.is_settlement == False
    ).all()
    
    for exp in expenses:
        if exp.paid_by in balances:
            balances[exp.paid_by] += exp.amount_inr
            
        # 3. Subtract share owed (decreases balance)
        for split in exp.splits:
            if split.user_id in balances:
                balances[split.user_id] -= split.amount_owed
                
    # 4. Adjust for settlements
    settlements = db.query(Settlement).filter(Settlement.group_id == group_id).all()
    for s in settlements:
        if s.from_user_id in balances:
            balances[s.from_user_id] += s.amount  # They paid off debt, balance increases
        if s.to_user_id in balances:
            balances[s.to_user_id] -= s.amount    # They received cash, balance decreases
            
    # Round everything to 2 decimal places to avoid floating point issues
    return {user_id: round(bal, 2) for user_id, bal in balances.items()}


def simplify_debts(net_balances: dict) -> list:
    """
    Greedy Minimum Transactions Algorithm.
    Takes a dict of {user_id: net_balance} and returns a list of transactions
    required to settle all debts in the minimum number of transfers.
    
    Returns: list of tuples -> [(from_user_id, to_user_id, amount)]
    """
    # Separate into debtors (owe money, negative balance) and creditors (owed money, positive balance)
    # We store them as lists of [user_id, amount]
    debtors = []
    creditors = []
    
    for user_id, balance in net_balances.items():
        if balance < -0.01: # Use 0.01 to ignore tiny floating point rounding differences
            debtors.append([user_id, abs(balance)])
        elif balance > 0.01:
            creditors.append([user_id, balance])
            
    transactions = []
    
    # Sort both lists descending by amount so we settle the largest debts first
    # This is a heuristic for the greedy algorithm
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)
    
    i = 0 # pointer for debtors
    j = 0 # pointer for creditors
    
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt_amount = debtors[i]
        creditor_id, credit_amount = creditors[j]
        
        # The amount to transfer is the minimum of what the debtor owes and what the creditor is owed
        settle_amount = round(min(debt_amount, credit_amount), 2)
        
        transactions.append((debtor_id, creditor_id, settle_amount))
        
        # Update the remaining amounts
        debtors[i][1] -= settle_amount
        creditors[j][1] -= settle_amount
        
        # If debtor is fully settled, move to next debtor
        if debtors[i][1] < 0.01:
            i += 1
            
        # If creditor is fully settled, move to next creditor
        if creditors[j][1] < 0.01:
            j += 1
            
    return transactions


# ==========================================
# INLINE UNIT TESTS FOR BALANCE ENGINE
# ==========================================
if __name__ == "__main__":
    print("Running simplify_debts tests...")
    
    # Test Case 1: Simple chain A owes B 100, B owes C 100
    # Net balances: A=-100, B=0, C=+100
    # Expected: A pays C 100 (1 transaction instead of 2)
    bals1 = {"A": -100.0, "B": 0.0, "C": 100.0}
    res1 = simplify_debts(bals1)
    assert len(res1) == 1
    assert res1[0] == ("A", "C", 100.0)
    
    # Test Case 2: One pays for all (A pays 300 for A, B, C. So B owes A 100, C owes A 100)
    # Net: A=+200, B=-100, C=-100
    bals2 = {"A": 200.0, "B": -100.0, "C": -100.0}
    res2 = simplify_debts(bals2)
    assert len(res2) == 2
    # B and C should both pay A
    assert ("B", "A", 100.0) in res2 or ("C", "A", 100.0) in res2
    
    # Test Case 3: Complex real-world scenario
    # A = +500 (Owed 500)
    # B = +200 (Owed 200)
    # C = -400 (Owes 400)
    # D = -300 (Owes 300)
    bals3 = {"A": 500.0, "B": 200.0, "C": -400.0, "D": -300.0}
    res3 = simplify_debts(bals3)
    # Total debt = 700. C owes 400, D owes 300.
    # Greedy will match C(-400) with A(+500) -> C pays A 400. (A has 100 left)
    # Then D(-300) with A(+100) -> D pays A 100. (D has 200 left)
    # Then D(-200) with B(+200) -> D pays B 200.
    assert len(res3) == 3
    
    print("All simplify_debts tests passed successfully! ✅")
