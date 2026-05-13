"""Whitelist parser for required-artifacts condition DSL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class ConditionError(ValueError):
    """Raised when a condition string is outside the allowed DSL."""


ALLOWED_VARIABLES = {
    "scenario": "enum",
    "scenario_subtype": "enum",
    "current_stage": "enum",
    "release": "string",
    "srs.is_multi_module": "bool",
    "srs.architecture_change": "bool",
}

ENUM_VALUES_BY_VARIABLE = {
    "scenario": {"S1", "S2", "S3", "S4"},
    "scenario_subtype": {"S2-1", "S2-2", "S2-3", "S2-4"},
    "current_stage": {
        "prd-inception",
        "srs-specification",
        "architecture-design",
        "development",
        "testing",
        "delivery",
        "project-retrospective",
        "workflow-incident-analysis",
    },
}

ENUM_LITERALS = set().union(*ENUM_VALUES_BY_VARIABLE.values())


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


@dataclass(frozen=True)
class Comparison:
    variable: str
    operator: str
    literal: Any


@dataclass(frozen=True)
class BinaryOp:
    operator: str
    left: Any
    right: Any


def tokenize(condition: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    while i < len(condition):
        ch = condition[i]
        if ch.isspace():
            i += 1
            continue
        two = condition[i : i + 2]
        if two in {"==", "!=", "&&", "||"}:
            tokens.append(Token("OP", two))
            i += 2
            continue
        if ch in "().":
            tokens.append(Token(ch, ch))
            i += 1
            continue
        if ch == '"':
            j = i + 1
            value = []
            while j < len(condition) and condition[j] != '"':
                value.append(condition[j])
                j += 1
            if j >= len(condition):
                raise ConditionError("Unterminated quoted string")
            tokens.append(Token("STRING", "".join(value)))
            i = j + 1
            continue
        if ch.isalnum() or ch in "_-":
            j = i
            while j < len(condition) and (condition[j].isalnum() or condition[j] in "_-"):
                j += 1
            tokens.append(Token("WORD", condition[i:j]))
            i = j
            continue
        if ch == "=":
            raise ConditionError("Use == for comparison, not =")
        raise ConditionError(f"Unexpected character in condition: {ch!r}")
    tokens.append(Token("EOF", ""))
    return tokens


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> Token:
        token = self.current()
        self.index += 1
        return token

    def expect(self, kind: str, value: str | None = None) -> Token:
        token = self.current()
        if token.kind != kind or (value is not None and token.value != value):
            expected = value if value is not None else kind
            raise ConditionError(f"Expected {expected}, got {token.value or token.kind}")
        return self.advance()

    def parse(self) -> Any:
        expr = self.parse_or()
        self.expect("EOF")
        return expr

    def parse_or(self) -> Any:
        node = self.parse_and()
        while self.current().kind == "OP" and self.current().value == "||":
            op = self.advance().value
            node = BinaryOp(op, node, self.parse_and())
        return node

    def parse_and(self) -> Any:
        node = self.parse_primary()
        while self.current().kind == "OP" and self.current().value == "&&":
            op = self.advance().value
            node = BinaryOp(op, node, self.parse_primary())
        return node

    def parse_primary(self) -> Any:
        if self.current().kind == "(":
            self.advance()
            node = self.parse_or()
            self.expect(")")
            return node
        return self.parse_comparison()

    def parse_variable(self) -> str:
        first = self.expect("WORD").value
        if not _is_identifier(first):
            raise ConditionError(f"Invalid variable identifier: {first}")
        parts = [first]
        while self.current().kind == ".":
            self.advance()
            part = self.expect("WORD").value
            if not _is_identifier(part):
                raise ConditionError(f"Invalid variable identifier: {part}")
            parts.append(part)
            if len(parts) > 2:
                raise ConditionError("Variable property chain length must be <= 2")
        variable = ".".join(parts)
        if variable not in ALLOWED_VARIABLES:
            raise ConditionError(f"Unknown variable: {variable}")
        return variable

    def parse_comparison(self) -> Comparison:
        variable = self.parse_variable()
        op = self.expect("OP").value
        if op not in {"==", "!="}:
            raise ConditionError("Comparison operator must be == or !=")
        literal = self.parse_literal(variable)
        return Comparison(variable, op, literal)

    def parse_literal(self, variable: str) -> Any:
        token = self.current()
        var_type = ALLOWED_VARIABLES[variable]
        if token.kind == "STRING":
            value = self.advance().value
            if var_type != "string":
                raise ConditionError(f"Variable {variable} must compare to an enum/bool literal, not a quoted string")
            return value
        if token.kind != "WORD":
            raise ConditionError("Expected literal")
        word = self.advance().value
        if word in {"true", "false"}:
            if var_type != "bool":
                raise ConditionError(f"Variable {variable} must compare to an enum/string literal, not bool")
            return word == "true"
        if word in ENUM_LITERALS:
            if var_type != "enum":
                raise ConditionError(f"Variable {variable} must compare to a quoted string or bool, not enum")
            allowed = ENUM_VALUES_BY_VARIABLE.get(variable, ENUM_LITERALS)
            if word not in allowed:
                raise ConditionError(f"Enum literal {word} is not valid for {variable}")
            return word
        raise ConditionError(f"Unknown literal: {word}")


def _is_identifier(value: str) -> bool:
    if not value:
        return False
    if not ("a" <= value[0] <= "z"):
        return False
    return all(("a" <= ch <= "z") or ch.isdigit() or ch == "_" for ch in value)


def parse(condition: str) -> Any:
    return Parser(tokenize(condition)).parse()


def evaluate_ast(node: Any, variables: Mapping[str, Any]) -> bool:
    if isinstance(node, BinaryOp):
        if node.operator == "&&":
            return evaluate_ast(node.left, variables) and evaluate_ast(node.right, variables)
        if node.operator == "||":
            return evaluate_ast(node.left, variables) or evaluate_ast(node.right, variables)
        raise ConditionError(f"Unknown binary operator: {node.operator}")
    if isinstance(node, Comparison):
        if node.variable not in variables:
            raise ConditionError(f"Missing value for variable: {node.variable}")
        left = variables[node.variable]
        if node.operator == "==":
            return left == node.literal
        return left != node.literal
    raise ConditionError("Invalid condition AST")


def evaluate(condition: str, variables: Mapping[str, Any]) -> bool:
    return evaluate_ast(parse(condition), variables)
