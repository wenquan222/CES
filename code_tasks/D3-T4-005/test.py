import pytest
from solution import aes_ct_sbox

# ── Algorithm-constraint helpers (V5) ─────────────────────────────────
# The first two versions used a blacklist of banned names. Assignment aliases,
# import aliases, getattr reflection, dunders such as int.__pow__, the operator
# module and third-party libraries each got around it. This version uses two
# criteria that do not depend on how the code is written:
#   (i)  an import whitelist -- only the modules listed here may be imported
#        (for most items, none at all);
#   (ii) a work count -- how many Python lines one call actually executes. A
#
#        library call, a table lookup or a direct multiply runs a single-digit
#        number of lines; genuinely running the algorithm takes hundreds to
import ast as _ast
import inspect as _inspect
import textwrap as _textwrap
import sys as _sys
import solution as _solmod

_ALLOWED_IMPORTS = set()


def _sol_tree():
    """AST of the whole submitted module -- the scope must be the module, not one function."""
    return _ast.parse(_textwrap.dedent(_inspect.getsource(_solmod)))


def _imported_modules():
    """Which top-level modules the submission imports."""
    mods = set()
    for n in _ast.walk(_sol_tree()):
        if isinstance(n, _ast.Import):
            for a in n.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(n, _ast.ImportFrom):
            if n.level:
                mods.add("<relative import>")
            if n.module:
                mods.add(n.module.split(".")[0])
    return mods


def _dunder_attribute_hits():
    """Accessing any __dunder__ attribute is banned: int.__pow__ / x.__getitem__
    and the like are the usual way around a ban by name."""
    return sorted({n.attr for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Attribute)
                   and n.attr.startswith("__") and n.attr.endswith("__")})


def _dynamic_lookup_hits():
    """Reflective lookup is banned outright."""
    banned = {"getattr", "eval", "exec", "compile", "__import__", "globals", "vars", "locals"}
    hits = []
    for n in _ast.walk(_sol_tree()):
        if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name) and n.func.id in banned:
            hits.append(n.func.id)
    return sorted(set(hits))


def _c_calls_during(fn, *args, **kwargs):
    """Record the builtin/C function names actually triggered during one call."""
    seen = set()

    def _prof(_frame, event, arg):
        if event == "c_call":
            seen.add(getattr(arg, "__name__", ""))

    old = _sys.getprofile()
    _sys.setprofile(_prof)
    try:
        fn(*args, **kwargs)
    finally:
        _sys.setprofile(old)
    seen.discard("setprofile")
    return seen


def _lines_executed(fn, *args, **kwargs):
    """Count the Python lines executed by one call -- the key criterion in this file.
    It measures whether the computation actually happened, ignoring names and syntax."""
    count = [0]

    def _trace(_frame, event, _arg):
        if event == "line":
            count[0] += 1
        return _trace

    old = _sys.gettrace()
    _sys.settrace(_trace)
    try:
        fn(*args, **kwargs)
    finally:
        _sys.settrace(old)
    return count[0]


def _module_branch_nodes(forbid_compare=False):
    """Scan every function in the module (helpers and lambdas included); only an
    if-raise used for input validation is exempt. match/case counts as a branch too."""
    bad = []
    tree = _sol_tree()
    for fn in [n for n in _ast.walk(tree)
               if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))]:
        body = [s for s in fn.body
                if not (isinstance(s, _ast.If)
                        and all(isinstance(x, _ast.Raise) for x in s.body)
                        and not s.orelse)]
        for stmt in body:
            for node in _ast.walk(stmt):
                if isinstance(node, _ast.If):
                    bad.append(fn.name + ":if")
                elif isinstance(node, _ast.IfExp):
                    bad.append(fn.name + ":conditional expression")
                elif isinstance(node, getattr(_ast, "Match", ())):
                    bad.append(fn.name + ":match/case")
                elif forbid_compare and isinstance(node, _ast.Compare) and any(
                        isinstance(o, (_ast.Eq, _ast.NotEq)) for o in node.ops):
                    bad.append(fn.name + ":==/!=")
    for lam in [n for n in _ast.walk(tree) if isinstance(n, _ast.Lambda)]:
        for node in _ast.walk(lam.body):
            if isinstance(node, _ast.IfExp):
                bad.append("lambda:conditional expression")
    return bad


def test_import_allowlist():
    """Only whitelisted modules may be imported. This also blocks operator,
    cryptography and any third-party library that ships a ready-made implementation --
    far more reliable than banning names one by one."""
    extra = sorted(_imported_modules() - _ALLOWED_IMPORTS)
    assert not extra, "the statement permits only %s; extra imports found: %s" % (
        sorted(_ALLOWED_IMPORTS) or "nothing from the standard library", extra)


def test_no_dunder_access():
    """Accessing __dunder__ attributes (int.__pow__, say) is banned -- that is the way around the implementation constraint."""
    hits = _dunder_attribute_hits()
    assert not hits, "evading the implementation constraint through dunder attributes is banned; found: %s" % hits


def test_no_dynamic_lookup():
    """Reflective lookup via getattr/eval/exec/__import__ is banned."""
    hits = _dynamic_lookup_hits()
    assert not hits, "evading the implementation constraint through reflection is banned; found: %s" % hits


AES_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

def _ast_of(func):
    """Take the function's AST (immune to comments/strings, so a bare substring match cannot misfire)."""
    import ast, inspect, textwrap
    return ast.parse(textwrap.dedent(inspect.getsource(func))).body[0]


def _branch_nodes(fn, forbid_compare=False):
    """Return the branch/loop node names in the body; an if-raise used only for input validation is exempt."""
    import ast
    bad = []
    body = [s for s in fn.body
            if not (isinstance(s, ast.If)
                    and all(isinstance(x, ast.Raise) for x in s.body)
                    and not s.orelse)]
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.If):
                bad.append("if")
            elif isinstance(node, ast.IfExp):
                bad.append("conditional expression")
            elif forbid_compare and isinstance(node, ast.Compare) and any(
                    isinstance(o, (ast.Eq, ast.NotEq)) for o in node.ops):
                bad.append("==/!=")
    return bad


def test_all_256_sbox_values():
    for b in range(256):
        assert aes_ct_sbox(b) == AES_SBOX[b]

def test_zero_input():
    assert aes_ct_sbox(0) == 0x63

def test_max_input():
    assert aes_ct_sbox(255) == 0x16

def test_involution():
    vals = set()
    for b in range(256):
        vals.add(aes_ct_sbox(b))
    assert len(vals) == 256

def test_no_lookup_table_runtime():
    """Runtime check: the module must contain no container of 32 or more entries.
    This ignores how the table was built -- a literal, [x]*256, bytes.fromhex(...) or a
    loop all end up as a module-level container, and all are blocked here."""
    bad = []
    for _name, _val in vars(_solmod).items():
        if _name.startswith("__"):
            continue
        if isinstance(_val, (bytes, bytearray, list, tuple, set, frozenset, dict)) and len(_val) >= 32:
            bad.append("%s (%d entries)" % (_name, len(_val)))
        _code = getattr(_val, "__code__", None)
        if _code is not None:
            for _c in _code.co_consts:
                # str is not checked: docstrings would misfire, and a table held in a string is caught by the "variable index" check
                if isinstance(_c, (bytes, tuple, frozenset)) and len(_c) >= 32:
                    bad.append("constant pool of %s (%d entries)" % (_name, len(_c)))
    assert not bad, f"the statement bans table lookup, but found: {bad}"


def test_no_wide_integer_constant():
    """Static check (AST): no integer constant of 64 bits or more.
    Encoding the 256-entry S-box into one big integer and shifting out bytes is still a lookup table."""
    bad = [c.value.bit_length() for c in _ast.walk(_sol_tree())
           if isinstance(c, _ast.Constant) and isinstance(c.value, int)
           and not isinstance(c.value, bool) and c.value.bit_length() >= 64]
    assert not bad, f"an over-wide integer constant was found (the S-box may be encoded in it): {bad}"


def test_no_hardcoded_table_literal():
    """Static check (AST): any literal constant of 32 or more entries in the module counts
    as a hard-coded table, whether it sits at module level or inside a function, and whether
    it is a list, tuple, bytes or hexadecimal string. This specifically blocks "split a long
    string into a table with a loop inside a function". Docstrings are exempt."""
    tree = _sol_tree()
    docstrings = set()
    for n in _ast.walk(tree):
        body = getattr(n, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], _ast.Expr) \
                and isinstance(body[0].value, _ast.Constant) \
                and isinstance(body[0].value.value, str):
            docstrings.add(id(body[0].value))
    bad = []
    for n in _ast.walk(tree):
        if isinstance(n, (_ast.List, _ast.Tuple, _ast.Set)) and len(n.elts) >= 32:
            bad.append("a literal sequence of %d entries" % len(n.elts))
        elif isinstance(n, _ast.Constant) and id(n) not in docstrings \
                and isinstance(n.value, (str, bytes)) and len(n.value) >= 32:
            bad.append("a literal constant of %d characters" % len(n.value))
    assert not bad, f"the statement bans hard-coding the S-box; found: {bad}"


def test_no_branch():
    """Static check (AST): no if/else/conditional expression anywhere in the module, helper functions included.
    An AST is used, so comments and strings do not misfire; only an if-raise used for input validation is exempt."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))
    bad = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        bad += [f"{fn.name}:{x}" for x in _branch_nodes(fn)]
    assert not bad, f"branch or conditional expression found, but the statement requires branchless code: {bad}"


def test_no_lookup_table():
    """Static check (AST): table lookup in any form is banned.
    This covers three styles: (i) a large literal sequence; (ii) a table built by list
    multiplication such as [x]*N; (iii) indexing a module-level sequence variable (which
    catches a table generated by a loop as well)."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))

    bad = []
    # (i) a large literal sequence
    for n in ast.walk(tree):
        if isinstance(n, (ast.List, ast.Tuple, ast.Set)) and len(n.elts) >= 32:
            bad.append(f"a literal sequence of {len(n.elts)} entries")
    # (ii) the [x] * N form
    for n in ast.walk(tree):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            for a, b in ((n.left, n.right), (n.right, n.left)):
                if isinstance(a, (ast.List, ast.Tuple)) and isinstance(b, ast.Constant)                         and isinstance(b.value, int) and b.value >= 32:
                    bad.append(f"a {b.value}-entry table built by list multiplication")
    # (iii) indexing a module-level sequence variable
    seq_names = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            v = stmt.value
            is_seq = isinstance(v, (ast.List, ast.Tuple, ast.Set, ast.ListComp, ast.DictComp)) or (
                isinstance(v, ast.BinOp) and isinstance(v.op, ast.Mult)
                and isinstance(v.left, (ast.List, ast.Tuple)))
            if is_seq:
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name):
                        seq_names.add(tgt.id)
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for n in ast.walk(fn):
            if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)                     and n.value.id in seq_names:
                bad.append(f"{fn.name} indexes the module-level sequence {n.value.id}")

    assert not bad, f"the statement bans table lookup, but found: {bad}"

def test_deterministic():
    for b in range(256):
        assert aes_ct_sbox(b) == aes_ct_sbox(b)

def test_range():
    for b in range(256):
        assert 0 <= aes_ct_sbox(b) <= 255

def test_base_case_values():
    assert aes_ct_sbox(0x2B) == AES_SBOX[0x2B]
    assert aes_ct_sbox(0x7E) == AES_SBOX[0x7E]
    assert aes_ct_sbox(0xC3) == AES_SBOX[0xC3]

def test_stress():
    for _ in range(1000):
        b = 0
        for i in range(8):
            b = (b << 1) | ((b ^ 0x1B) & 1)
        b &= 0xFF
        assert aes_ct_sbox(b) == AES_SBOX[b]


def test_actually_does_the_work():
    """Work check: a GF(2^8) inversion plus the affine transform runs hundreds of Python lines.
    Any form of lookup (array, string or bytes, whether by index or operator.getitem) runs
    only a single-digit number of lines -- this check ignores how the table is stored or read."""
    used = _lines_executed(aes_ct_sbox, 0x2B)
    assert used >= 100, (
        f"a single S-box call executed only {used} Python lines, which does not look like field arithmetic"
        " (the reference implementation runs about 720 lines; a lookup runs about 1)")
