# codesmith/__init__.py

"""Entry point for the codesmith package, defines the IPython magic functions."""


from codesmith.eval import eval_
from codesmith.python import py
from codesmith.wrapper import ω
import sys

def reload():
  """For active development: reloads this module and all submodules"""
  package_name = 'codesmith'
  import importlib
  for k,v in list(sys.modules.items()):
    if k.startswith(package_name): importlib.reload(v)
    # Question: is there an ordering issue? toplevel must reload last

# Only load the magics if we are running inside IPython
if "ipykernel" in sys.modules:
  from IPython.core.magic import (register_line_cell_magic, needs_local_scope)
  from IPython.display import display
  from IPython.core.getipython import get_ipython

  # Problem: before IPython 7.3, there was no way to opt out of variable 
  # expansion in the magic line (there is no expansion in a magic cell). 
  # This is OK for $var since that is not valid python. But 
  # {var} notation IS valid python, so we cannot do sets or dicts inside a
  # line magic call (easily at least). 7.3 added the @no_var_expand decorator.
  @register_line_cell_magic
  @needs_local_scope
  def codesmith(line='', cell=None, local_ns=None):
    """ Defines line and cell magic functions %codesmith and %%codesmith 
        (respectively). local_ns *should* be set by IPython """

    global_ns = get_ipython().user_ns
    if local_ns is None: local_ns = global_ns
    verbose = debug = False
    p = py.cell  # Default language is python (py), and entry point is py.cell
    line += '  ' # Need spaces at end for cell magic argument parsing

    # Parse the arguments to (%)%codesmith, each starts with '-'
    while line[0] == '-':
      first_space = line.index(' ')
      arg = line[1:first_space]
      line = line[first_space+1:]
      if arg == 'v': verbose = True
      elif arg == 'vd': verbose = debug = True
      else:
        if verbose: print(f"parser:>>{arg}<<")
        import builtins
        p = builtins.eval(arg, local_ns)
        if verbose: print(p)

    if verbose: print(f"line:>>{line}<<")
    if not cell: cell = line

    readout = p.read(cell, verbose=verbose)
    if verbose: print("output of read_", readout, type(readout))
    try:
      evalout = eval_(readout, global_ns, local_ns, debug)
      if verbose: print("output of eval_", evalout, type(evalout))
      if evalout: display(evalout)
    except Exception as e:
      display(e)
    return None

  del codesmith