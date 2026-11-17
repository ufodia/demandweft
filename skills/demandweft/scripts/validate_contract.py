#!/usr/bin/env python3
"""Read-only structural lint for a Demandweft experiment contract (stdlib only)."""

import json
import math
import re
import sys
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
ID = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
ACTUAL = {"observed", "user_provided"}
MANUAL_CHECKS = [
    "Read each source: does it truly support the exact claim, scope, and current version?",
    "Check that evidence types, measurement independence, and comparison bases are honestly classified.",
    "Review causal identification, controls, sample, attribution, and uncertainty for causal claims.",
    "Check all public copy, not only listed claim IDs; unlisted or misclassified claims cannot be detected completely.",
    "Verify the real deliverable, useful not-a-fit path, privacy, testimonial permission, and voluntary sharing.",
    "Obtain any required publication or spending authorization separately; this result grants none.",
]
CAVEAT = (
    "Structural and evidence-reference lint only. Sources are not opened, claim truth is not "
    "verified, and ready_for_review is not approval to publish, contact people, or spend."
)


def reject_constant(value):
    raise ValueError("Non-finite JSON number is forbidden")


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite JSON number is forbidden")
    return number


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key is forbidden")
        result[key] = value
    return result


def parse_contract(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=reject_constant, parse_float=finite_float)


class Validator:
    def __init__(self):
        self.errors = []
        self.incomplete = []

    def error(self, path, message):
        self.errors.append({"path": path, "message": message})

    def missing(self, path, message="Required value is missing or empty"):
        self.incomplete.append({"path": path, "message": message})

    def obj(self, value, path, allowed):
        if value is None:
            self.missing(path)
            return {}
        if not isinstance(value, dict):
            self.error(path, "Must be an object")
            return {}
        if set(value) - set(allowed):
            self.error(path, "Contains unrecognized fields; consult the contract schema")
        return value

    def text(self, obj, key, path, required=True):
        value = obj.get(key)
        if value is None or value == "":
            if required:
                self.missing(path + "." + key)
            return None
        if not isinstance(value, str):
            self.error(path + "." + key, "Must be a nonempty string")
            return None
        if not value.strip():
            self.missing(path + "." + key)
            return None
        return value

    def choice(self, obj, key, path, choices, required=True):
        value = self.text(obj, key, path, required)
        if value is not None and value not in choices:
            self.error(path + "." + key, "Unsupported value")
            return None
        return value

    def boolean(self, obj, key, path, required=True):
        if key not in obj:
            if required:
                self.missing(path + "." + key)
            return None
        if type(obj[key]) is not bool:
            self.error(path + "." + key, "Must be a JSON boolean")
            return None
        return obj[key]

    def items(self, obj, key, path):
        if key not in obj:
            self.missing(path + "." + key)
            return []
        if not isinstance(obj[key], list):
            self.error(path + "." + key, "Must be an array")
            return []
        return obj[key]

    def identifier(self, obj, path):
        value = self.text(obj, "id", path)
        if value is not None and not ID.fullmatch(value):
            self.error(path + ".id", "Use 1-64 lowercase letters, digits, underscores or hyphens; start with a letter")
            return None
        return value

    def refs(self, obj, key, path, index):
        values = self.items(obj, key, path)
        found, seen = [], set()
        for value in values:
            if not isinstance(value, str) or not ID.fullmatch(value):
                self.error(path + "." + key, "Each reference must be a valid string ID")
            elif value in seen:
                self.error(path + "." + key, "Duplicate reference")
            else:
                seen.add(value)
                if value not in index:
                    self.error(path + "." + key, "Reference does not resolve")
                else:
                    found.append(index[value])
        return found

    def evidence(self, root):
        index = {}
        for i, raw in enumerate(self.items(root, "evidence", "$")):
            path = "$.evidence[%d]" % i
            item = self.obj(raw, path, {"id", "type", "kind", "source", "scope", "summary", "independent"})
            eid = self.identifier(item, path)
            self.choice(item, "type", path, ACTUAL | {"inferred", "synthetic"})
            kind = self.choice(item, "kind", path, {"customer", "implementation", "demonstration", "measurement", "testimonial", "reference"})
            for key in ("source", "scope", "summary"):
                self.text(item, key, path)
            independent = self.boolean(item, "independent", path, required=False)
            if independent is True and kind != "measurement":
                self.error(path + ".independent", "Independence applies only to measurement evidence")
            if eid in index:
                self.error(path + ".id", "Duplicate evidence ID")
            elif eid is not None:
                index[eid] = item
        return index

    @staticmethod
    def actual(evidence, kinds):
        return [e for e in evidence if isinstance(e.get("type"), str)
                and e["type"] in ACTUAL and isinstance(e.get("kind"), str)
                and e["kind"] in kinds]

    def buyer_and_experience(self, root, evidence):
        buyer = self.obj(root.get("buyer"), "$.buyer", {"segment", "decision_question", "barrier", "status", "evidence_ids"})
        for key in ("segment", "decision_question", "barrier"):
            self.text(buyer, key, "$.buyer")
        state = self.choice(buyer, "status", "$.buyer", {"hypothesis", "supported"})
        refs = self.refs(buyer, "evidence_ids", "$.buyer", evidence)
        if state == "supported" and not self.actual(refs, {"customer"}):
            self.error("$.buyer.status", "Without actual customer evidence, buyer understanding must be a hypothesis")
        experience = self.obj(root.get("experience"), "$.experience", {"deliverable", "personal_utility", "non_fit_outcome", "implementation_state", "verification_evidence_ids"})
        for key in ("deliverable", "personal_utility", "non_fit_outcome"):
            self.text(experience, key, "$.experience")
        state = self.choice(experience, "implementation_state", "$.experience", {"planned", "built", "verified"})
        refs = self.refs(experience, "verification_evidence_ids", "$.experience", evidence)
        if state == "planned":
            self.missing("$.experience.implementation_state", "Build a concrete deliverable before ready_for_review")
        if state == "verified" and not self.actual(refs, {"implementation", "demonstration"}):
            self.error("$.experience.verification_evidence_ids", "Verified requires actual implementation or demonstration evidence")
        return state

    def claims(self, root, evidence, experience_state, demo_only, explicitly_demo):
        index = {}
        for i, raw in enumerate(self.items(root, "claims", "$")):
            path = "$.claims[%d]" % i
            item = self.obj(raw, path, {"id", "text", "category", "status", "evidence_ids", "comparison_basis"})
            cid = self.identifier(item, path)
            self.text(item, "text", path)
            category = self.choice(item, "category", path, {"capability", "descriptive_outcome", "causal_outcome", "comparison", "testimonial"})
            state = self.choice(item, "status", path, {"supported", "hypothesis", "illustrative"})
            refs = self.refs(item, "evidence_ids", path, evidence)
            basis = self.choice(item, "comparison_basis", path, {"features", "performance"}, required=False)
            if "comparison_basis" in item and category != "comparison":
                self.error(path + ".comparison_basis", "Only comparison claims use this field")
            if state == "illustrative" and explicitly_demo is not True:
                self.error(path + ".status", "Illustrative claims require explicitly_demo=true")
            if state == "supported":
                if category == "capability":
                    if not self.actual(refs, {"implementation", "demonstration"}):
                        self.error(path + ".evidence_ids", "A supported capability needs actual implementation or demonstration evidence")
                    if experience_state == "planned":
                        self.error(path + ".status", "A planned experience cannot support a shipped capability")
                elif category in {"descriptive_outcome", "causal_outcome"}:
                    measurements = self.actual(refs, {"measurement"})
                    if not measurements:
                        self.error(path + ".evidence_ids", "Supported outcomes need actual measurement; demos, inferences and synthetic data cannot establish lift")
                    if category == "causal_outcome" and not any(e.get("independent") is True for e in measurements):
                        self.error(path + ".evidence_ids", "Causal outcomes require independent measurement evidence and manual causal review")
                elif category == "comparison":
                    if basis is None:
                        self.missing(path + ".comparison_basis", "Classify the comparison as features or performance for manual review")
                    elif basis == "performance" and not self.actual(refs, {"measurement"}):
                        self.error(path + ".evidence_ids", "Performance comparisons require actual measurement evidence")
                    elif basis == "features" and not self.actual(refs, {"reference", "implementation", "demonstration", "measurement"}):
                        self.error(path + ".evidence_ids", "Feature comparisons require actual reference or implementation evidence")
                elif category == "testimonial" and not self.actual(refs, {"testimonial"}):
                    self.error(path + ".evidence_ids", "Supported testimonials require actual testimonial evidence; review usage permission manually")
            if cid in index:
                self.error(path + ".id", "Duplicate claim ID")
            elif cid is not None:
                index[cid] = item
        public = self.obj(root.get("public"), "$.public", {"claim_ids"})
        for claim in self.refs(public, "claim_ids", "$.public", index):
            if claim.get("status") == "supported":
                continue
            if claim.get("status") == "illustrative" and demo_only is True and explicitly_demo is True:
                continue
            self.error("$.public.claim_ids", "Public claims must be supported; explicitly labeled demo-only bundles may also include illustrative claims")

    def propagation_and_success(self, root):
        p = self.obj(root.get("propagation"), "$.propagation", {"mode", "forced_sharing", "recipient_value", "sender_value", "privacy_scope"})
        mode = self.choice(p, "mode", "$.propagation", {"none", "adapt", "coordinate", "challenge"})
        if self.boolean(p, "forced_sharing", "$.propagation") is True:
            self.error("$.propagation.forced_sharing", "Sharing must be voluntary and cannot gate the user's useful result")
        enabled = mode in {"adapt", "coordinate", "challenge"}
        for key in ("recipient_value", "sender_value", "privacy_scope"):
            self.text(p, key, "$.propagation", required=enabled)
        success = self.obj(root.get("success"), "$.success", {"user_value", "business_outcome", "propagation_outcome"})
        metrics = []
        for key in ("user_value", "business_outcome") + (("propagation_outcome",) if enabled else ()):
            metric = self.obj(success.get(key), "$.success." + key, {"metric", "success_definition"})
            values = [self.text(metric, name, "$.success." + key) for name in ("metric", "success_definition")]
            metrics.append((key, values))
        if not enabled and "propagation_outcome" in success:
            self.error("$.success.propagation_outcome", "Only include a propagation outcome when propagation is enabled")
        for i, (key, values) in enumerate(metrics):
            for previous, prior in metrics[:i]:
                for value, old in zip(values, prior):
                    if value and old and " ".join(value.casefold().split()) == " ".join(old.casefold().split()):
                        self.error("$.success." + key, "Success metrics and definitions must be distinct from " + previous)

    def budget(self, root):
        budget = self.obj(root.get("budget"), "$.budget", {"currency", "max_cash", "max_hours"})
        currency = self.text(budget, "currency", "$.budget")
        if currency is not None and not re.fullmatch(r"[A-Z]{3}", currency):
            self.error("$.budget.currency", "Use a three-letter uppercase currency code; validity requires human review")
        for key in ("max_cash", "max_hours"):
            if key not in budget:
                self.missing("$.budget." + key)
                continue
            value = budget[key]
            valid = (type(value) is int and value >= 0) or (
                type(value) is float and math.isfinite(value) and value >= 0)
            if not valid:
                self.error("$.budget." + key, "Must be a finite nonnegative number; booleans are not numbers")

    def run(self, root):
        root = self.obj(root, "$", {"schema_version", "id", "status", "demo_only", "explicitly_demo", "evidence", "buyer", "experience", "claims", "public", "propagation", "success", "budget"})
        if type(root.get("schema_version")) is not int or root.get("schema_version") != 1:
            self.error("$.schema_version", "Must be the integer 1")
        if self.identifier(root, "$") is None:
            self.error("$.id", "A valid contract ID is required")
        status = self.choice(root, "status", "$", {"draft", "ready_for_review"})
        demo_only = self.boolean(root, "demo_only", "$")
        explicitly_demo = self.boolean(root, "explicitly_demo", "$")
        if demo_only is True and explicitly_demo is not True:
            self.error("$.explicitly_demo", "A demo-only contract must be explicitly labeled as a demo")
        evidence = self.evidence(root)
        state = self.buyer_and_experience(root, evidence)
        self.claims(root, evidence, state, demo_only, explicitly_demo)
        self.propagation_and_success(root)
        self.budget(root)
        if status == "draft":
            self.missing("$.status", "The contract is explicitly a draft")
        return self.result()

    def result(self):
        code = 2 if self.errors else 1 if self.incomplete else 0
        return code, {"validator": "demandweft-structural-lint", "schema_version": 1,
                      "status": ("ready_for_review", "draft", "invalid")[code],
                      "exit_code": code, "errors": self.errors, "incomplete": self.incomplete,
                      "caveat": CAVEAT, "manual_checks": MANUAL_CHECKS}


def validate_contract(contract):
    return Validator().run(contract)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    validator = Validator()
    try:
        if len(args) != 1:
            raise ValueError("Usage: validate_contract.py CONTRACT.json")
        with Path(args[0]).open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Contract exceeds the 2 MiB input limit")
        contract = parse_contract(raw.decode("utf-8-sig"))
        code, result = validator.run(contract)
    except (OSError, ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else type(exc).__name__
        validator.error("$", "Cannot read or parse the contract: " + detail)
        code, result = validator.result()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
