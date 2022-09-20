from pyparsing import *
from ast import parse, AST, dump
from astor import to_source, dump_tree
from functools import reduce
from types import FunctionType, BuiltinFunctionType

common = pyparsing_common

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
  def __rshift__(self, other):
    return lambda *toks: other.format(*toks)
OUT = Out()

def ListOf(p, delim=',', trailer=True, min=None):
  return delimited_list(p, delim=delim, combine=True, min=min,
                        allow_trailing_delim=trailer)

def BlockOf(p):
  blockp = IndentedBlock(p, grouped=False)
  @blockp.set_parse_action
  def a(s,loc, toks):
    while s[loc] in blockp.whiteChars: loc +=1
    white = '\n' + ' '*col(loc,s)
    #print("COLS", white, "d", toks)
    return white + white.join(str(t) for t in toks)
  return blockp

class Rule(Forward):
  def __init__(self, name):
    self.rule_name = name
    self.clauses = []
    Forward.__init__(self)
    self.set_name(self.rule_name)

  def __ilshift__(self, syntax):
    semantics = lambda *toks: ' '.join(str(t) for t in toks)
    if isinstance(syntax, tuple):
      if isinstance(syntax[-1], (FunctionType, BuiltinFunctionType)):
        *syntax, semantics = syntax
    else: syntax = (syntax,)
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
    result = self.parse_string(s, parse_all=True)[0]
    print("Original parse", result)
    toast = parse_reference(result)
    print("AST", dump_tree(toast, maxline=75))
    back = unparse_reference(toast)
    print(back)
    try: return exec(back)
    except Exception as e: return e
  
  def read(self, s, verbose=False):
    result = self.parse_string(s, parse_all=True)[0]
    if verbose: print("Original parse", result)
    toast = parse_reference(result)
    if verbose: print("AST", dump_tree(toast, maxline=75))
    return toast

_PASS_CODE = (lambda:None).__code__.co_code
def just_pass(f): return f.__code__.co_code == _PASS_CODE

class Grammar(dict):
  def __getitem__(self, name):
    if name not in self:
      self[name] = Rule(name)
    return super().__getitem__(name)
  __getattr__ = __getitem__

  def __setitem__(self, name, value):
    super().__setitem__(name, value)
  __setattr__ = __setitem__

  def __call__(self, f):
    name = f.__name__
    syntax = [f.__annotations__.get(var, Empty()) 
                for var in f.__code__.co_varnames]

    if not just_pass(f): syntax.append(f)
    self[name] <<= tuple(syntax)
    return self.name
