# codesmith/read.py

"""Provides the parsing functions for codesmith grammars"""

from pyparsing import *
from ast import parse, AST, dump
from astor import to_source, dump_tree
from functools import reduce
from types import FunctionType, BuiltinFunctionType

common = pyparsing_common

# The reference language for now is python. In general, the reference language
# determines the AST format, and what is an identifier.
reference_class = AST
def unparse_reference(node):
  if isinstance(node, reference_class):
    try:    return to_source(node).rstrip()
    except: return dump(node)
  return node
def parse_reference(s, mode='exec'): 
  s = str(s)
  return parse(s, s, mode)
def is_reference_id(s): return s.isidentifier()

class Out:
  """Class to allow special outputs in grammars.
  Instatiated once as `OUT` below, and used like: `OUT>>"{}{}"` with a 
  formatted string after a right-shift operator.
  """
  def __rshift__(self, other):
    return lambda *toks: other.format(*toks)
OUT = Out()

def ListOf(p, delim=',', trailer=True, min=None):
  """The codesmith version of pyparsing's `delimited_list`"""
  return delimited_list(p, delim=delim, combine=True, min=min,
                        allow_trailing_delim=trailer)

def BlockOf(p):
  """The codesmith version of pyparsings `IndentedBlock`"""
  blockp = IndentedBlock(p, grouped=False)
  @blockp.set_parse_action
  def a(s,loc, toks):
    while s[loc] in blockp.whiteChars: loc +=1
    white = '\n' + ' '*col(loc,s)
    #print("COLS", white, "d", toks)
    return white + white.join(str(t) for t in toks)
  return blockp

class Rule(Forward):
  """A single rule in a (codesmith-style) pyparsing grammar"""

  def __init__(self, name):
    self.rule_name = name
    self.clauses = []
    Forward.__init__(self)
    self.set_name(self.rule_name)

  def __ilshift__(self, syntax):
    """The main way to define a rule uses the augmented left-shift operator <<="""
    semantics = lambda *toks: ' '.join(str(t) for t in toks)
    try:
      if syntax.parseAction:
        semantics = lambda *x: x[0]
    except: pass

    if isinstance(syntax, tuple):
      if isinstance(syntax[-1], (FunctionType, BuiltinFunctionType)):
        *syntax, semantics = syntax
    else: 
      syntax = (syntax,)
    syntax = list(syntax)

    for i,s in enumerate(syntax):
      #if isinstance(s, Literal): s = s.match
      if isinstance(s,str):
        if is_reference_id(s): syntax[i] = Keyword(s)
        else:                  syntax[i] = Literal(s)

    #print("LR check", self, self == syntax[0], syntax)
    if syntax[0] == self: #left recursive
      if not self.expr: 
        raise ValueError("left resursion requires a base case (prior clauses)")
      syntax = self.expr + OneOrMore(Group(And(syntax[1:])))
      f = semantics
      semantics = lambda *toks: reduce(lambda first, second: f(first, *second), toks)
    else: syntax = And(syntax)

    syntax.set_parse_action(lambda ts: semantics(*ts))
    self.clauses.append(syntax)
    self << (Or(self.clauses) if len(self.clauses) > 1 else self.clauses[0])
    return self

  def parse(self, s):
    """ deprecated """
    result = self.parse_string(s, parse_all=True)[0]
    print("Original parse", result)
    toast = parse_reference(result)
    print("AST", dump_tree(toast, maxline=75))
    back = unparse_reference(toast)
    print(back)
    try: return exec(back)
    except Exception as e: return e
  
  def read(self, s, verbose=False):
    """Applies this rule to string s, returning an AST in the reference language"""
    result = self.parse_string(s, parse_all=True)[0]
    if verbose: print("Original parse", result)
    toast = parse_reference(result)
    if verbose: print("AST", dump_tree(toast, maxline=75))
    return toast

_PASS_CODE = (lambda:None).__code__.co_code
def just_pass(f): return f.__code__.co_code == _PASS_CODE

class Grammar(dict):
  """Stores an entire TSP Language grammar in a dict of Rule's"""

  def __getitem__(self, name):
    """Generate a new Rule if it doesn't exist"""
    if name not in self:
      self[name] = Rule(name)
    return super().__getitem__(name)
  __getattr__ = __getitem__ # dot values work like subscripts

  def __setitem__(self, name, value):
    super().__setitem__(name, value)
  __setattr__ = __setitem__

  def __call__(self, f):
    """ deprecated: for use as a decorator"""
    name = f.__name__
    syntax = [f.__annotations__.get(var, Empty()) 
                for var in f.__code__.co_varnames]

    if not just_pass(f): syntax.append(f)
    self[name] <<= tuple(syntax)
    return self.name
