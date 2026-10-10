import json
import re

_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")
_MD_CONTROL = re.compile(r"[\r\x00-\x08\x0b\x0c\x1b​-‏  ]")


def one_line(s, max_len: int = 400) -> str:
    """Flatten a spec-derived value to a single inert line.

    info.title/summary/description/tags are untrusted input that gets
    embedded in generated Markdown and YAML frontmatter. A raw newline lets a
    crafted value break out of a single-line context (e.g. the `description:`
    frontmatter entry) and forge new YAML keys or Markdown structure, so
    newlines and other control characters are stripped before use.
    """
    s = _MD_CONTROL.sub("", "" if s is None else str(s))
    s = " ".join(s.split())
    return (s[:max_len] + "…") if len(s) > max_len else s


def yaml_scalar(s) -> str:
    """Render a spec-derived value as a safe YAML double-quoted scalar.

    A YAML 1.2 double-quoted scalar is a superset of JSON string syntax, so
    json.dumps already produces valid, safely-escaped YAML for it (no quote,
    backslash, or colon in the value can end the scalar early or start a new
    key). Always pass the value through one_line() first so it stays a single
    line even before this escaping is applied.
    """
    return json.dumps(one_line(s), ensure_ascii=False)


def py_literal(s) -> str:
    """Render a spec-derived value as a safe Python string literal.

    Anything taken from an OpenAPI document — parameter names, paths, URLs,
    descriptions — is untrusted input that ends up inside generated source.
    Interpolating it raw allows a crafted spec to execute arbitrary code in
    the generated client, so every such value must go through here.
    """
    return json.dumps("" if s is None else str(s))


def to_snake(name: str) -> str:
    name = _NON_ALNUM.sub("_", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.strip("_").lower() or "op"


def to_kebab(name: str) -> str:
    return to_snake(name).replace("_", "-")


def py_identifier(name: str) -> str:
    ident = to_snake(name)
    if ident[:1].isdigit():
        ident = f"op_{ident}"
    return ident


OPENAPI_TO_PY_TYPE = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}


def schema_to_py_type(schema: dict) -> str:
    if not isinstance(schema, dict):
        return "str"
    t = schema.get("type")
    if t in OPENAPI_TO_PY_TYPE:
        return OPENAPI_TO_PY_TYPE[t]
    if "$ref" in schema or "oneOf" in schema or "anyOf" in schema:
        return "dict"
    return "str"
