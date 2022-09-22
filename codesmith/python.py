# codesmith/python.py

"""A codesmith grammar for the python language itself

Follows the offical python grammar very closely: 
https://docs.python.org/3/reference/grammar.html
"""

from pyparsing import *
from codesmith.read import Grammar, BlockOf, ListOf, OUT, common

py = Grammar()

################################################################################
# STARTING RULES
################################################################################

#-------------------------------------------------------------------------------
# Notebook cells
#-------------------------------------------------------------------------------
py.cell <<= OneOrMore(py.statement), lambda *stmts: '\n'.join(stmts)

################################################################################
# STATEMENTS: py.statement
################################################################################

py.statement <<= py.compound_stmt
py.statement <<= py.simple_stmts

#-------------------------------------------------------------------------------
# py.simple_stmts : Single-line list of simple statements
#-------------------------------------------------------------------------------
#py.simple_stmts <<= py.simple_stmt, NotAny(';'), LineEnd()
py.simple_stmts <<= ListOf(py.simple_stmt, delim=';'), FollowedBy(LineEnd())

#-------------------------------------------------------------------------------
# py.block: Indented block of statements, or single-line of statements
#-------------------------------------------------------------------------------
py.block <<= BlockOf(py.statement) #IndentedBlock(OneOrMore(py.statement))
py.block <<= py.simple_stmts

################################################################################
# SIMPLE STATEMENTS: py.simple_stmt
################################################################################
py.simple_stmt <<= py.assignment
py.simple_stmt <<= ListOf(py.star_expression)
py.simple_stmt <<= 'return', Opt(ListOf(py.star_expression))
py.simple_stmt <<= py.import_stmt
py.simple_stmt <<= py.raise_stmt
py.simple_stmt <<= 'pass'
py.simple_stmt <<= 'del', ListOf(py.del_target), FollowedBy(';' | LineEnd())
py.simple_stmt <<= py.yield_expr
py.simple_stmt <<= 'assert', py.expression, Opt(',' + py.expression)
py.simple_stmt <<= 'break'
py.simple_stmt <<= 'continue'
py.simple_stmt <<= 'global', ListOf(py.name)
py.simple_stmt <<= 'nonlocal', ListOf(py.name)

#-------------------------------------------------------------------------------
# py.assignment: Assignment statements, including augmented one like +=
#-------------------------------------------------------------------------------
py.assignment <<= ( ListOf(ListOf(py.star_target), delim='=', trailer=False),
                    '=', py.yield_expr | ListOf(py.star_expression), NotAny('=')
)
augassign = '+= -= *= @= /= %= &= |= ^= <<= >>= **= //='
py.assignment <<= (py.single_target, one_of(augassign), And._ErrorStop(), 
                   py.yield_expr | ListOf(py.star_expression)
)

#-------------------------------------------------------------------------------
# py.assert_stmt: Assert statements
#-------------------------------------------------------------------------------
py.assert_stmt <<= 'assert', py.expression
py.assert_stmt <<= 'assert', py.expression, ',', py.expression

#-------------------------------------------------------------------------------
# py.import_stmt: Import statements; TODO: not at all done
#-------------------------------------------------------------------------------
py.import_stmt <<= 'import', ListOf(py.dotted_as_name)
#py.import_stmt <<= 'from' #TODO

py.dotted_as_name <<= py.dotted_name
py.dotted_as_name <<= py.dotted_name, 'as', py.name
py.dotted_name <<= py.name
py.dotted_name <<= py.dotted_name, '.', py.name

################################################################################
# COMPOUND STATEMENTS: py.compound_stmt
################################################################################

py.compound_stmt <<= py.function_def  #TODO
py.compound_stmt <<= py.if_stmt       #TODO
py.compound_stmt <<= py.class_def     #TODO
py.compound_stmt <<= py.with_stmt     #TODO
py.compound_stmt <<= py.for_stmt      #TODO
py.compound_stmt <<= py.try_stmt      #TODO
py.compound_stmt <<= py.while_stmt
py.compound_stmt <<= py.match_stmt    #TODO (not in 3.7)

#-------------------------------------------------------------------------------
# py.while_stmt: While loops
#-------------------------------------------------------------------------------
py.while_stmt <<= 'while', py.expression, ':', py.block, Opt(py.else_block)

## TODO: the rest of the compound statements ##

################################################################################
# EXPRESSIONS: py.expression
################################################################################

py.expression <<= py.disjunction, 'if', py.disjunction, 'else', py.expression
py.expression <<= py.disjunction
py.expression <<= py.lambdef

#-------------------------------------------------------------------------------
# py.yield_expr: actually a statement without parens, used in generators
#-------------------------------------------------------------------------------
py.yield_expr <<= 'yield', 'from', py.expression
py.yield_expr <<= 'yield', ListOf(py.star_expression)


#-------------------------------------------------------------------------------
# py.star_expression: unpacking of an iterable
#-------------------------------------------------------------------------------

py.star_expression <<= '*', py.bitwise_or
py.star_expression <<= py.expression

py.disjunction <<= py.conjunction
py.disjunction <<= py.disjunction, 'or', py.conjunction

py.conjunction <<= py.inversion
py.conjunction <<= py.conjunction, 'and', py.inversion

py.inversion <<= py.comparison
py.inversion <<= 'not', py.inversion

py.comparison <<= py.bitwise_or
py.comparison <<= py.bitwise_or, OneOrMore(py.compare_op_bitwise_or_pair)

py.compare_op_bitwise_or_pair <<=  oneOf('== != <= < >= >'), py.bitwise_or
py.compare_op_bitwise_or_pair <<=  'not in', py.bitwise_or
py.compare_op_bitwise_or_pair <<=  'is not', py.bitwise_or
py.compare_op_bitwise_or_pair <<=  'in', py.bitwise_or
py.compare_op_bitwise_or_pair <<=  'is', py.bitwise_or

py.bitwise_or <<= py.bitwise_xor
py.bitwise_or <<= py.bitwise_or, '|', py.bitwise_xor

py.bitwise_xor <<= py.bitwise_and
py.bitwise_xor <<= py.bitwise_xor, '^', py.bitwise_and

py.bitwise_and <<= py.shift_expr
py.bitwise_and <<= py.bitwise_and, '&', py.shift_expr

py.shift_expr <<= py.sum
py.shift_expr <<= py.shift_expr, one_of('<< >>'), py.sum

py.sum <<= py.term
py.sum <<= py.sum, one_of('+ -'), py.term

py.term <<= py.factor
py.term <<= py.term, one_of('* // / % @'), py.factor

py.factor <<= py.power
py.factor <<= one_of('+ - ~'), py.factor

py.power <<= py.primary
py.power <<= py.power, '**', py.primary

# atom + () [] or .
py.primary <<= py.atom, OUT>>"ω({})"
py.primary <<= py.primary, py.genexp
py.primary <<= py.primary, '(', Opt(py.arguments), ')'
py.primary <<= py.primary, '[', py.slices, ']'
              
py.slices <<= py.slice, NotAny(',')
py.slices <<= ListOf(py.slice_or_star_exp)
py.slice_or_star_exp <<= py.slice
py.slice_or_star_exp <<= py.star_expression

py.slice <<= Opt(py.expression), ':', Opt(py.expression)
py.slice <<= Opt(py.expression), ':', Opt(py.expression), ':', Opt(py.expression)
py.slice <<= py.expression

# literals
py.atom <<= 'None'
py.atom <<= 'True', OUT>>'False'
py.atom <<= 'False'
py.atom <<= py.name
py.atom <<= common.number
py.atom <<= quoted_string
py.atom <<= '...'

from keyword import kwlist
keyword = one_of(kwlist, as_keyword=True)
py.name <<= ~keyword, common.identifier

# tuples
py.atom <<= '(', py.atom, ',)'
py.atom <<= '(', ListOf(py.atom, min=2), ')'

# group
py.atom <<= '(', py.expression, ')'

# generator
py.atom <<= py.genexp

# lists
py.atom <<= '[', Opt(ListOf(py.star_expression)), ']'
py.atom <<= '[', py.expression, ListOf(py.for_if_clause), ']'

#sets
py.atom <<= '{', ListOf(py.star_expression), '}'
py.atom <<= '{', py.expression, ListOf(py.for_if_clause), '}'

# dicts
py.atom                   <<= '{', Opt(ListOf(py.double_starred_kvpair)), '}'
py.atom                   <<= '{', py.kvpair, ListOf(py.for_if_clause), '}'
py.double_starred_kvpair  <<= py.kvpair
py.double_starred_kvpair  <<= '**', py.bitwise_or
py.kvpair                 <<= py.expression, ':', py.expression

# comprehensions / generators
py.for_if_clause <<= (
    'for', ListOf(py.star_target), 'in', And._ErrorStop(), py.disjunction,
    ZeroOrMore(py.if_clause)
)
py.if_clause <<= 'if', py.disjunction

py.genexp <<= '(', py.expression, ListOf(py.for_if_clause), ')'

# TODO: params
py.lambdef <<= 'lambda', ListOf(py.name), ':', py.expression

# function call arguments
py.arguments  <<= py.args, Opt(','), FollowedBy(')')
py.args       <<= ListOf(py.single_arg), ',', py.kwargs
py.args       <<= ListOf(py.single_arg)
py.args       <<= py.kwargs
py.single_arg <<= py.starred_expression, NotAny('=')
py.single_arg <<= py.expression, NotAny('=')

py.kwargs     <<= (
    ListOf(py.kwarg_or_starred, trailer=False), ',', 
    ListOf(py.kwarg_or_double_starred)
)
py.kwargs     <<= ListOf(py.kwarg_or_starred)
py.kwargs     <<= ListOf(py.kwarg_or_double_starred)

py.starred_expression       <<= '*', py.expression
py.kwarg_or_starred         <<= py.name, '=', py.expression
py.kwarg_or_starred         <<= py.starred_expression
py.kwarg_or_double_starred  <<= py.name, '=', py.expression
py.kwarg_or_double_starred  <<= '**', py.expression

# targets

py.star_targets_tuple_seq <<= py.star_target, ','
py.star_targets_tuple_seq <<= ListOf(py.star_target, min=2)

py.star_target <<= '*', NotAny('*'), py.star_target
py.star_target <<= py.target_with_star_atom

t_lookahead = one_of('( [ .')
py.target_with_star_atom  <<= py.t_primary, '.', py.name, NotAny(t_lookahead)
py.target_with_star_atom  <<= (
    py.t_primary, '[', py.slices, ']', NotAny(t_lookahead))
py.target_with_star_atom  <<= py.star_atom

py.star_atom <<= py.name
py.star_atom <<= '(', py.target_with_star_atom, ')'
py.star_atom <<= '(', py.star_targets_tuple_seq, ')'
py.star_atom <<= '[', ListOf(py.star_target), ']'

py.single_target <<= py.single_subscript_attribute_target
py.single_target <<= py.name
py.single_target <<= '(', py.single_target, ')' 

py.single_subscript_attribute_target <<= (
  py.t_primary, '.', py.name, ~t_lookahead)
py.single_subscript_attribute_target <<= (
  py.t_primary, '[', py.slices, ']', ~t_lookahead)

py.t_primary <<= py.atom, FollowedBy(t_lookahead)
py.t_primary <<= py.t_primary, '.', py.name, FollowedBy(t_lookahead)
py.t_primary <<= py.t_primary, '[', py.slices, ']', FollowedBy(t_lookahead)
py.t_primary <<= py.t_primary, py.genexp, FollowedBy(t_lookahead)
py.t_primary <<= py.t_primary, '(', Opt(py.arguments), ')', FollowedBy(t_lookahead)

py.del_target <<= py.t_primary, '.', py.name, NotAny(t_lookahead)
py.del_target <<= py.t_primary, '[', py.slices, ']', NotAny(t_lookahead)
py.del_target <<= py.del_t_atom

py.del_t_atom <<= py.name
py.del_t_atom <<= '(', ListOf(py.del_target), ')'
py.del_t_atom <<= '[', ListOf(py.del_target), ']'
