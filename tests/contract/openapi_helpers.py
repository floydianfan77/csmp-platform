"""Resolve OpenAPI component schemas for response validation."""

from __future__ import annotations

from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def load_openapi_spec(path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validator_for_schema(spec: dict[str, Any], schema_name: str) -> Draft202012Validator:
    components = spec.get("components", {}).get("schemas", {})
    if schema_name not in components:
        raise KeyError(f"Schema {schema_name!r} not in OpenAPI components")
    schema = _resolve_refs(components[schema_name], components)
    return Draft202012Validator(schema)


def _resolve_refs(node: Any, components: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            ref = node["$ref"]
            if not ref.startswith("#/components/schemas/"):
                raise ValueError(f"Unsupported ref: {ref}")
            name = ref.rsplit("/", 1)[-1]
            return _resolve_refs(components[name], components)
        return {k: _resolve_refs(v, components) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, components) for item in node]
    return node


def assert_valid(instance: Any, validator: Draft202012Validator) -> None:
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        messages = "; ".join(e.message for e in errors)
        raise ValidationError(messages)
