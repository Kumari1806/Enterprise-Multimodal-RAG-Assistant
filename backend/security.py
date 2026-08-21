"""Security module — prompt injection detection and sensitive info protection."""

import re
from typing import Optional

# Patterns that may indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|commands)",
    r"(?i)forget\s+(all\s+)?(your|previous)\s+(instructions|prompts|constraints)",
    r"(?i)you\s+(are\s+)?(now|are\s+free)\s+(to\s+)?(ignore|disregard|bypass)",
    r"(?i)reveal\s+(your|the|hidden|system)\s+(prompt|instructions|system\s+prompt)",
    r"(?i)print\s+(your|the)\s+(system\s+)?(prompt|instructions|directive)",
    r"(?i)output\s+(your|the)\s+initial\s+(instructions|prompt|system)",
    r"(?i)show\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions|directives)",
    r"(?i)what\s+(is|are)\s+(your|the)\s+(system\s+)?(prompt|instructions|directives|rules)",
    r"(?i)role\s*[-:]\s*(system|assistant|ai)",
    r"(?i)you\s+are\s+now\s+(a\s+)?(different|another)\s+(ai|assistant|bot|persona)",
    r"(?i)access\s+(all|restricted|confidential|internal)\s+(documents|files|data|records)",
    r"(?i)show\s+(me\s+)?(all|restricted|confidential)\s+(employees|salaries|salary)",
    r"(?i)bypass\s+(the\s+)?(security|access\s+control|rbac|authentication|restrictions|system)",
    r"(?i)override\s+(security|access|restrictions|controls|safety)",
    r"(?i)(dump|show|print|list)\s+(the\s+)?(entire\s+)?(database|collection|documents|chunks|vectors|files)",
    r"(?i)list\s+(all|every)\s+(documents|files|employees|people)",
    r"(?i)who\s+(all|else)\s+(is\s+)?(in|has)\s+(the\s+)?(database|system)",
    r"(?i)hack|exploit|jailbreak|breach|crack",
    r"(?i)simulate\s+(a\s+)?(different|another|new)\s+(persona|role|identity)",
    r"(?i)act\s+as\s+(if\s+)?(you\s+are|you're)\s+(a\s+)?(different|another|new)\s+(person|ai|bot)",
]

# Patterns for sensitive information requests
_SENSITIVE_PATTERNS = [
    r"(?i)(salary|ctc|compensation|pay)(\s+of|\s+for|\s+details)?",
    r"(?i)(bank|account|pan|aadhar|ssn|credit\s+card|debit\s+card)\s+(details|number|info)",
    r"(?i)personal\s+(information|data|details)\s+of",
    r"(?i)phone\s+(number|details|of)",
    r"(?i)email\s+(address|id)\s+of",
    r"(?i)address\s+of\s+(employee|rahul|sneha|amit|neha|vikram)",
]


def detect_prompt_injection(query: str) -> tuple[bool, Optional[str]]:
    """Detect if a query contains a prompt injection attempt.

    Returns:
        (is_injection: bool, reason: Optional[str])
    """
    # Check injection patterns
    for pattern in _INJECTION_PATTERNS:
        match = re.search(pattern, query)
        if match:
            return True, f"Prompt injection detected: query matches pattern '{match.group()[:60]}...'"

    # Check for attempts to get system prompt
    system_prompt_keywords = [
        "system prompt", "system instructions", "initial prompt",
        "hidden prompt", "your instructions", "your directive",
        "original prompt", "first instruction", "base prompt",
    ]
    query_lower = query.lower()
    for keyword in system_prompt_keywords:
        if keyword in query_lower and any(v in query_lower for v in ["what", "show", "tell", "reveal", "print", "output"]):
            return True, f"Attempt to reveal system prompt detected (keyword: '{keyword}')"

    return False, None


def detect_sensitive_request(query: str, user_role: str) -> tuple[bool, Optional[str]]:
    """Detect if a query is requesting sensitive information the user shouldn't access."""
    query_lower = query.lower()

    # Employees cannot ask about salary information
    if user_role == "Employee":
        salary_keywords = ["salary", "ctc", "compensation", "pay", "salary records", "rahul", "sneha", "amit", "neha", "vikram"]
        salary_match_count = sum(1 for kw in salary_keywords if kw in query_lower)
        if salary_match_count >= 2:
            return True, "SENSITIVE INFORMATION REQUESTED: You do not have permission to access salary information."

        # Employees cannot ask about termination policy
        term_keywords = ["termination", "termination policy", "firing", "fired"]
        if any(kw in query_lower for kw in term_keywords):
            return True, "ACCESS DENIED: You do not have permission to access the Termination Policy document."

    # Finance role can't ask about HR policies
    if user_role == "Finance":
        hr_keywords = ["hr policy", "leave policy", "termination", "notice period", "probation", "attendance",
                        "working hours", "dress code", "grievance", "casual leave", "sick leave", "earned leave"]
        if any(kw in query_lower for kw in hr_keywords):
            return True, "ACCESS DENIED: You do not have permission to access HR-related documents."

    return False, None


def sanitize_response(answer: str) -> str:
    """Sanitize the response to ensure no system prompts or hidden info is leaked."""
    # Remove any accidental system prompt leakage
    patterns_to_remove = [
        r"(?i)you\s+are\s+(an\s+)?(enterprise\s+)?(ai\s+)?(helpful\s+)?(assistant|rag|bot)",
        r"(?i)your\s+(task|role|purpose|job)\s+is\s+to",
        r"(?i)as\s+(an\s+)?(ai|enterprise)\s+(assistant|rag|bot)",
    ]
    sanitized = answer
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)

    return sanitized