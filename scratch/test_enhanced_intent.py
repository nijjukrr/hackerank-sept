import csv
import re

class EnhancedIntentClassifier:
    NON_DELETION_PATTERNS = [
        re.compile(r"leave (?:the|my) account active", re.IGNORECASE),
        re.compile(r"keep (?:the|my) account", re.IGNORECASE),
        re.compile(r"leave my (?:profile|purchase|history)", re.IGNORECASE),
        re.compile(r"(?:want to )?continue using (?:the|this) service", re.IGNORECASE),
        re.compile(r"do not (?:delete|close|erase|remove|change)", re.IGNORECASE),
        re.compile(r"don['’]t (?:delete|close|erase|remove|change)", re.IGNORECASE),
        re.compile(r"not (?:asking for |a request to |requesting )(?:deletion|delete|erase|erasure|closing|close|removal|remove)", re.IGNORECASE),
        re.compile(r"without (?:removing|deleting|erasing|closing)", re.IGNORECASE),
        re.compile(r"marketing lists? only", re.IGNORECASE),
        re.compile(r"stop (?:the )?promotional emails", re.IGNORECASE),
        re.compile(r"information request", re.IGNORECASE),
        re.compile(r"still use (?:it|the account)", re.IGNORECASE),
        re.compile(r"still need (?:it|the account)", re.IGNORECASE),
    ]

    DELETION_TERMS = [
        r"delet", r"eras", r"remov", r"clos", r"suppress", r"purg", r"wip",
        r"supprim", r"effac", r"clotur", r"fermer",
        r"elimin", r"borr", r"cancel", r"cerr",
        r"exclu", r"apag", r"fech",
        r"l[oö]sch", r"entfern", r"schlie[sß]",
        r"cancell", r"audit", r"gone",
        r"削除", r"消去", r"삭제"
    ]
    DELETION_REGEX = re.compile("|".join(DELETION_TERMS), re.IGNORECASE)

    @classmethod
    def authorizes_deletion(cls, request_text: str) -> bool:
        if not request_text:
            return False
        text = request_text.strip()
        for pat in cls.NON_DELETION_PATTERNS:
            if pat.search(text):
                return False
        if cls.DELETION_REGEX.search(text):
            return True
        return False

with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    eval_requests = list(csv.DictReader(f))

with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_requests = list(csv.DictReader(f))

na_eval = [r for r in eval_requests if not EnhancedIntentClassifier.authorizes_deletion(r["request_text"])]
print(f"Eval NOT_APPLICABLE count: {len(na_eval)}")
for r in na_eval:
    print(f"  {r['case_id']}: {r['request_text']}")

na_sample = [r for r in sample_requests if not EnhancedIntentClassifier.authorizes_deletion(r["request_text"])]
print(f"\nSample NOT_APPLICABLE count: {len(na_sample)}")
for r in na_sample:
    print(f"  {r['case_id']}: {r['request_text']}")
