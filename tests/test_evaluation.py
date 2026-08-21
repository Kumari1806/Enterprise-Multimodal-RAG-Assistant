"""Tests for evaluation module — end-to-end evaluation pipeline."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.security import detect_prompt_injection, detect_sensitive_request
from backend.rbac import is_document_authorized
from backend.citation import extract_citations_from_chunks, validate_citations


class TestEvaluationFramework:
    """Test suite for the evaluation framework."""

    def test_evaluation_dataset_exists(self):
        """Test that the evaluation dataset file exists."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        assert eval_file.exists(), "Evaluation dataset not found!"

    def test_evaluation_dataset_is_valid_json(self):
        """Test that the evaluation dataset is valid JSON."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_evaluation_testcases_have_required_fields(self):
        """Test every test case has the required fields."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        required_fields = ["id", "question", "expected_answer", "user_role", "expected_result"]
        for case in data:
            for field in required_fields:
                assert field in case, f"Test case missing field '{field}': {case}"

    def test_evaluation_roles_are_valid(self):
        """Test that user roles in evaluation dataset are valid."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        valid_roles = {"Employee", "HR", "Finance", "Admin"}
        for case in data:
            assert case["user_role"] in valid_roles, f"Invalid role: {case['user_role']}"

    def test_evaluation_expected_results_are_valid(self):
        """Test that expected results are valid."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        valid_results = {"PASS", "BLOCK", "DENY", "INSUFFICIENT"}
        for case in data:
            assert case["expected_result"] in valid_results, f"Invalid result: {case['expected_result']}"

    def test_injection_testcases_are_detected(self):
        """Test that prompt injection test cases are detected by security."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        for case in data:
            if case["category"] == "prompt_injection":
                is_injection, _ = detect_prompt_injection(case["question"])
                assert is_injection is True, f"Prompt injection not detected: {case['question']}"

    def test_normal_queries_not_injection(self):
        """Test that normal queries are not flagged as injection."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        for case in data:
            if case["category"] in ("answer_correctness", "end_to_end"):
                is_injection, _ = detect_prompt_injection(case["question"])
                assert is_injection is False, f"Normal query flagged: {case['question']}"

    def test_rbac_denied_checks(self):
        """Test that RBAC denied test cases are correctly denied."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        for case in data:
            if case["category"] == "rbac_enforcement":
                if "salary" in case["question"].lower():
                    # Employee asking about salary
                    is_sensitive, _ = detect_sensitive_request(case["question"], case["user_role"])
                    assert is_sensitive is True, f"RBAC not enforced for: {case['question']}"

    def test_citation_extraction(self):
        """Test citation extraction from chunks."""
        chunks = [
            {
                "content": "Employees receive 18 earned leaves annually.",
                "metadata": {
                    "document": "Leave_Policy.pptx",
                    "slide": "5",
                    "document_name": "Leave Policy",
                }
            }
        ]
        citations = extract_citations_from_chunks(chunks)
        assert len(citations) == 1
        assert citations[0]["document"] == "Leave_Policy.pptx"
        assert citations[0]["slide"] == "5"

    def test_citation_validation_valid(self):
        """Test citation validation with matching answer."""
        citations = [
            {"document": "Leave_Policy.pptx", "slide": "5", "content": "test"},
        ]
        answer = "Employees get 18 days. (Source: Leave_Policy.pptx)"
        is_valid, issues = validate_citations(answer, citations)
        assert is_valid is True
        assert len(issues) == 0

    def test_all_categories_present(self):
        """Test that all expected evaluation categories are present."""
        eval_file = Path(__file__).resolve().parent.parent / "data" / "evaluation" / "evaluation_dataset.json"
        with open(eval_file) as f:
            data = json.load(f)

        categories = set(case["category"] for case in data)
        expected = {"answer_correctness", "rbac_enforcement", "prompt_injection",
                     "insufficient_information", "end_to_end"}
        for cat in expected:
            assert cat in categories, f"Missing category: {cat}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])