# codesmith/wrapper.py

"""The Wrapper class and ω (omega) function for custom objects 
  in a TSP language"""

from string import capwords

class Wrapper(object):
  """Base Class for a wrapped object (the "candy" object in the wrapper)"""

  @classmethod
  def candy_class(cls):
    """Get the class object (type) for the candy"""
    # candy's class is always #2 in mro
    return cls.__mro__[2]

  
  def candy_repr(self):
    """Get the repr for the candy class"""
    # By default, just use the candy class's __repr__
    return self.candy_class().__repr__(self)

  def candy_type(self):
    """Get the type of the candy class"""
    return self.candy_class().__name__

  #def __repr__(self):
  #  return f"{self.candy_repr()}: {self.candy_type()}"

  def _repr_html_(self):
    """Generate suitable output html for the wrapped class"""
    if hasattr(self,"_repr_svg_"):
      out = self.candy_class()._repr_svg_(self)
    else:
      from html import escape
      out = escape(f"{self.candy_repr()}")
        
    out += ("\n<span style='float:right; font-family:monospace; "
            "font-weight:bold; background-color:#e5e5ff; color:black;'>"
            f"{self.candy_type()}</span>")
    return out

# Wrapper subclass for ints, that overrides the default behavior for repr
#class IntWrapper(Wrapper, int):
#  def candy_repr(self):
#    return "INT OVERIDE:" + int.__repr__(self)


def ω(x):
  """Wrapper factory that checks for defined subclass, or creates one if necessary"""
  candy_class = x.__class__
  try:
    return wrappers[candy_class](x)
  except (TypeError, KeyError):
    return x

wrappers = {}
def register_wrapper(*args):
  """Decorator to register a defined wrapper for one or more candy classes"""
  if len(args) == 1 and issubclass(args[0], Wrapper):
    wrapper = args[0]
    wrappers[wrapper.candy_class()] = wrapper
    return wrapper

  def _wrap(wrapper):
    for candy in args:
      wrappers[candy] = wrapper
    return wrapper
  return _wrap

def register_candy(*candy):
  """Generate a new, default Wrapper class for one or more candy class"""
  default = candy[0]
  wrapper_name = capwords(default.__name__) + "Wrapper"
  wrapper = type(wrapper_name, (Wrapper, default), {})
  for cls in candy:
    wrappers[cls] = wrapper

  def make_new(method):
    def newmethod(self, *args, **kwargs):
      out = getattr(default, method)(self, *args, **kwargs)
      # if isinstance(out, candy):
      #   print(wrapper_name, method, "->", out, type(out))
      #   return wrapper(out)
      return ω(out)
    return newmethod

  from inspect import getmembers, ismethoddescriptor
  for method in [m  for c in candy 
                    for m, _ in getmembers(c, ismethoddescriptor) ]:
    if method == '__init__': continue
    setattr(wrapper, method, make_new(method))
  return default

def unregister_candy(candy):
  """Unregister a wrapper for this candy class"""
  return wrappers.pop(candy,None)

