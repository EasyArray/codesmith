from string import capwords

# Base Class for a wrapped object (the "candy" object in the wrapper)
class Wrapper(object):
  # Get the class object (type) for the candy
  @classmethod
  def candy_class(cls):
    # candy's class is always #2 in mro
    return cls.__mro__[2]

  # By default, just use the candy class's __repr__
  def candy_repr(self):
    return self.candy_class().__repr__(self)

  def candy_type(self):
    return self.candy_class().__name__

  #def __repr__(self):
  #  return f"{self.candy_repr()}: {self.candy_type()}"

  def _repr_html_(self):
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

# Wrapper factory that checks for defined subclass, or creates one if necessary
def ω(x):
  candy_class = x.__class__
  try:
    return wrappers[candy_class](x)
  except (TypeError, KeyError):
    return x

wrappers = {}
def register_wrapper(*args):
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
  return wrappers.pop(candy,None)

