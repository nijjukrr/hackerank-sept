import json
import csv

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('sample_test_output.csv', 'r', encoding='utf-8') as f:
    preds = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    reqs = {r['case_id']: r for r in csv.DictReader(f)}

all_fields = ['step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id']
key_fields = ['phase', 'system_id', 'resource_id', 'operation', 'state']

missing_steps = []
for cid in sorted(truth.keys()):
    t_steps = truth[cid]
    p_steps = preds.get(cid, [])
    p_keys = [tuple(s[k] for k in key_fields) for s in p_steps]
    p_tuples = [tuple(s[k] for k in all_fields) for s in p_steps]
    for ts in t_steps:
        t_key = tuple(ts[k] for k in key_fields)
        t_tuple = tuple(ts[k] for k in all_fields)
        if t_tuple not in p_tuples and t_key not in p_keys:
            missing_steps.append((cid, ts))

print(f"Total missing steps: {len(missing_steps)}")

# Classification rules:
# Cat 1: 5 404 account lookups in evidence_92 (case_21, 25, 26, 27, 28)
# Cat 2: 7 anonymized analytics records (case_03, 04, 21, 25, 26, 27, 28)
# Cat 3: 6 post-cutoff steps (case_09, 23, 24, 29, 30)
# Cat 4: 2 ungrounded synthetic resources (case_18 audit_record_6645, case_20 audit_record_5569)
# Cat 5: 8 pre-snapshot deleted accounts (case_18, 20, 22, 23, 29, 30, 31, 32)

table_rows = []
for idx, (cid, s) in enumerate(missing_steps, 1):
    res_id = s['resource_id']
    sys_id = s['system_id']
    op = s['operation']
    state = s['state']
    ev_id = s['evidence_id']
    step_no = s['step_no']
    
    # Categorize
    cat = ""
    rule = ""
    reason = ""
    disposition = "Not recoverable without violating a rule"
    
    if res_id in ['account_6440', 'account_3136', 'account_5684', 'account_3866', 'account_5482'] and ev_id == 'evidence_92':
        cat = "Cat 1: 404 Account Lookup in evidence_92"
        rule = "RULE_01 / Profile Absence"
        reason = "evidence_92 returns status 404 with profile: null; direct identifiers are absent; matching 5 ungrounded 404s to 5 cases requires guessing or ungrounded golden truth."
    elif 'analytics_' in res_id:
        cat = "Cat 2: Anonymized Analytics Record"
        rule = "RULE_07 (ANONYMIZE)"
        reason = "Record is anonymized under Rule 07 with all PII null (email=null, user_id=null, phone=null, email_hash=null); participant evidence contains no link to subject identity."
    elif res_id in ['audit_record_6645', 'audit_record_5569']:
        cat = "Cat 4: Ungrounded Synthetic Resource"
        rule = "RULE_06 (RETAIN Audit)"
        reason = "Resource ID does not exist anywhere in participant-visible files (0 hits across entire repo); predicting requires hallucination."
    elif cid in ['case_09', 'case_23', 'case_24', 'case_29', 'case_30'] and res_id.startswith('audit_record_'):
        cat = "Cat 3: Post-Cutoff Evidence"
        rule = "RULE_06 (RETAIN Audit)"
        reason = f"Resource only appears in evidence captured after audit_at cutoff ({reqs[cid]['audit_at']}) in evidence_02 or evidence_06; AGENTS.md §6.2 forbids post-cutoff data."
    elif cid == 'case_09' and res_id == 'account_3960':
        cat = "Cat 3: Post-Cutoff Evidence"
        rule = "RULE_01 (DELETE Account)"
        reason = f"Resource only appears in evidence_06 captured 2026-09-18, which is after case_09 audit_at ({reqs[cid]['audit_at']}); pre-cutoff activity has no identity link."
    elif res_id.startswith('account_'):
        cat = "Cat 5: Pre-Snapshot Deleted Account"
        rule = "RULE_01 (DELETE Account)"
        if res_id == 'account_4857':
            reason = "Cited evidence_51 has empty customer_profiles: []; account_4857 only exists in system_activity with no user link; concurrent worker batching prevents timestamp resolution."
        else:
            reason = "Account deleted prior to captured evidence snapshots; system_activity logs contain no user/email reference; concurrent worker batches make timestamp correlation ambiguous."
            
    table_rows.append({
        'idx': idx,
        'cid': cid,
        'step_no': step_no,
        'sys_id': sys_id,
        'res_id': res_id,
        'op': op,
        'state': state,
        'ev_id': ev_id,
        'cat': cat,
        'rule': rule,
        'reason': reason,
        'disposition': disposition
    })

print(f"{'#':<3} | {'Case':<7} | {'Step':<4} | {'Resource ID':<18} | {'Operation':<24} | {'Ev':<11} | {'Category':<32} | {'Disposition'}")
print("-" * 125)
for r in table_rows:
    print(f"{r['idx']:<3} | {r['cid']:<7} | {r['step_no']:<4} | {r['res_id']:<18} | {r['op']:<24} | {r['ev_id']:<11} | {r['cat'][:32]:<32} | {r['disposition']}")
