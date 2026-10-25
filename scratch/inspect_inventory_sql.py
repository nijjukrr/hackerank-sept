p = 'dataset/evidence/databases/customer_data_inventory_20260905.sql'
for line in open(p, encoding='utf-8', errors='ignore'):
    if 'CREATE TABLE customer_profiles' in line or 'INSERT INTO customer_profiles' in line:
        print(line.strip()[:140])
        # print first 5 rows
    if 'INSERT INTO customer_profiles' in line:
        # print next 3 rows
        break

with open(p, encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'customer_profiles' in line:
            print(line.strip()[:120])
