with open('dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql', 'r', encoding='utf-8') as f:
    text = f.read()

for term in ['4990', 'account_4990', 'user_22', 'elena.popova', 'popova']:
    print(f"{term} in evidence_54: {term in text}")
