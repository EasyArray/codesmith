from codesmith.wrapper import ω
# ast comes with python, generates parse trees
from ast import *
# astor includes a astor.to_source() function to unparse trees.
# It is made defunct by Python 3.9 (which includes ast.unparse)
# but colab only comes with Python 3.7
import astor
from types import FunctionType, BuiltinFunctionType

expressions = (
  BoolOp, BinOp, UnaryOp, Lambda, IfExp, Dict, Set, Dict,
  ListComp, SetComp, DictComp, GeneratorExp, Await, Yield, YieldFrom,
  Compare, Call, FormattedValue, JoinedStr, Constant, 
  Attribute, Subscript, Starred, Name, List, Tuple, Slice, Expression
  )
statements = (
  FunctionDef, AsyncFunctionDef, ClassDef, Return, Delete, Assign, AugAssign,
  AnnAssign, For, AsyncFor, While, If, With, AsyncWith, Raise, Try,
  Assert, Import, ImportFrom, Global, Nonlocal, Pass, Break, Continue, Module
)

def do_eval(node, globals, locals, debug=False, shadowed=[]):
  #node = AddAst().visit(node)
  node = fix_missing_locations(node)
  if shadowed:
    globals = {k:globals[k] for k in globals if k not in shadowed}
    locals = {k:locals[k] for k in locals if k not in shadowed}
  source = unparse(node) #For debugging only, remove later
  if debug: print("do_eval on", source)
  if (isinstance(node, Module) and len(node.body) == 1 
        and isinstance(node.body[0], Expr)):
    node = Expression(body=node.body[0].value)
  if isinstance(node, expressions):
    if not isinstance(node, Expression): node = Expression(body=node)
    code = compile(node, source, "eval")
    evaled = eval(code, globals, locals)
    if debug: print("eval of", dump(node), "returned",  evaled, type(evaled))
    return evaled

  if not isinstance(node, statements): return
  if not isinstance(node, Module): node = Module(body=[node])
  code = compile(node, source, "exec")
  exec(code, globals, locals)

class RemoveOmega(NodeTransformer):
  def visit_Call(self, node):
    self.generic_visit(node) #visit children
    if isinstance(node.func, Name) and node.func.id == 'ω': out = node.args[0]
    else: out = node
    return out
    
def unparse(node, remove_omega=False):
  """ Attempts to convert node into python source code, 
      or at least dump the AST; otherwise, returns node """
  if isinstance(node, AST):
    if remove_omega: node = fix_missing_locations(RemoveOmega().visit(node))
    try:    return astor.to_source(node).rstrip()
    except: return dump(node)
  return node

def ensurenode(node):
  """ Parses node into AST if necessary """
  if isinstance(node, AST): return node
  if hasattr(node, "__ast__"): return node.__ast__
  node = str(node)
  return parse(node, node, "eval").body

def argvars(node):
  """ Returns the argument list for a lambda expression """
  node = ensurenode(node)
  if not isinstance(node, Lambda): return []
  return [arg.arg for arg in node.args.args]

def newvar(oldvar, usedvars):
  """ Generates a name for oldvar that is not in usedvars """
  var = oldvar
  while var in usedvars:
    var = var + oldvar #repeat the name to form a new name
  return var

def freevars(node):
  """ Returns the free variables in node """
  node = ensurenode(node)
  if isinstance(node, Name): return {node.id}

  free = set()
  for child in iter_child_nodes(node):
    free |= freevars(child)
  # remove bound variables
  if isinstance(node, Lambda): free -= set(argvars(node))
  return free

def get_lambda(node):
  if isinstance(node, Lambda): return node
  if hasattr(node, "__ast__"): return get_lambda(node.__ast__)
  return False

def unprintable(x):
  #print("unprintable?", x, type(x), repr(x))
  if isinstance(x,str): return False
  return (isinstance(x,(type, FunctionType, BuiltinFunctionType)))
#            or (repr(x)[0] == '<' and repr(x)[-1] == '>'))

def sub(node, subs):
  """ Makes the substitutions in subs to node without variable capture 
        subs maps variables (as strings) to their AST substitutions
        returns the new AST node
  """ 
  node = ensurenode(node) #For debugging, remove? -no, in case of __ast__ node

  if isinstance(node, Name) and node.id in subs:
    return ensurenode(subs[node.id])  #ensurenode for debugging, remove?

  # Capture avoidance code for lambdas
  if isinstance(node, Lambda):
    args = argvars(node)
    # Shadow any variables bound inside the lambda
    for arg in args: subs.pop(arg, "")
    # Collect potential variable capture cases
    frees = {var for val in subs.values() for var in freevars(val)}
    # captures will hold the actual name clashes
    captures = {arg for arg in args if arg in frees}
    if captures:
      #print("CLASH! with", captures)
      varsubs = dict()
      frees |= set(args) | freevars(node) # more vars to avoid in renaming
      for oldvar in captures:
        varsubs[oldvar] = newvar(oldvar, frees)
        frees.add(varsubs[oldvar]) # now avoid the new name too!
      # Replace in the lambda signature:
      for arg in node.args.args: #One level up from argvars, to make changes
        if arg.arg in varsubs: arg.arg = varsubs[arg.arg]
      # Replace in the body:
      node.body = sub(node.body, varsubs)      

  # Recurse on children of node
  for field, value in iter_fields(node):
    if isinstance(value, list):
      setattr(node,field,[ensurenode(sub(val, subs)) for val in value])
    elif isinstance(value, AST):
      setattr(node,field,ensurenode(sub(value, subs)))

  return node
  
def eval_(node, globals=None, locals=None, debug=False):
  """ Returns the value for node if evaluable, or 
      a string with as many parts of node eval'ed as possible otherwise """
  
  # set parsed, globals, and locals correctly
  node = ensurenode(node)
  from sys import _getframe
  caller = _getframe(1)
  globals = globals or caller.f_globals
  locals = locals or caller.f_locals

  # define _simplify based on these values for globals and locals
  def _simplify(node, shadowed=set()):
    """ Returns the value for parsed if evaluable, or 
        an AST with as many parts of parsed eval'ed as possible otherwise """

    if debug: print("Simplifying", dump(node))

    if isinstance(node, Lambda):
      shadowed |= set(argvars(node))
      node.body = ensurenode(_simplify(node.body, shadowed))
      return node

    # Do lambda applications manually, in case they return a lambda
    if isinstance(node, Call):
      if debug: print("In Call", unparse(node))
      func = _simplify(node.func)
      func = get_lambda(func)
      if func:
        args = argvars(func)
        body = func.body
        subs = dict(zip(args, node.args))
        if debug: print("Lambda sub", unparse(body), {arg : dump(subs[arg]) for arg in subs})
        node = sub(body, subs)
        if debug: print("Body with subs:", unparse(node))
        node = _simplify(node)
        if debug: print("After simplification:", unparse(node))
        return node

    try:
      evaled = do_eval(node, globals, locals, debug, shadowed)
      if unprintable(evaled): return node
      return evaled
    except Exception as e: #TODO: be more selective
      if debug: print("Error in do_eval of", unparse(node), e) 

    for field, value in iter_fields(node):
      if debug: print("Working on", field)#, ":", dump(value))
      if isinstance(value, list):
        repl = [ensurenode(_simplify(x)) #need ensurenode?
                  if isinstance(x, AST) else x 
                for x in value]
      elif not isinstance(value, AST): continue #skip constants
      else:
        repl = ensurenode(_simplify(value))

      setattr(node,field,repl)

    return node

  # call the internal function and return the value or a string
  out = _simplify(node)
  ret = unparse(out)
  if isinstance(node, Lambda):
    print(ret)
    lm = eval_(node, globals, locals, debug)
    lm.__ast__ = node
    return lm
  return ω(ret)