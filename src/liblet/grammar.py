from collections import namedtuple
from itertools import chain
from operator import attrgetter, itemgetter

from . import ε
from .utils import letstr

HAIR_SPACE = '\u200a'

def _letlrhstostr(s):
    return HAIR_SPACE.join(map(str, s)) if isinstance(s, tuple) else str(s)

class Production:
    """A grammar production.

    This class represents a grammar production, it has a *lefthand* and a
    *righthand* side that can be :obj:`strings <str>`, or :obj:`tuples <tuple>`
    of strings; a production is :term:`iterable` and unpackig can be used to
    obain its sides, so for example
    
    .. doctest::

        >>> lhs, rhs = Production('A', ('B', 'C'))
        >>> lhs
        'A'
        >>> rhs 
        ('B', 'C')

    Args: 
        lhs: The left hand side of the production. 
        rhs: The right hand side of the production.

    Raises:

        ValueError: in case the lefthand or righthand side are not string, or tuples of strings.
    """

    __slots__ = ('lhs', 'rhs')

    def __init__(self, lhs, rhs):
        if isinstance(lhs, str):
            self.lhs = lhs
        elif isinstance(lhs, (list, tuple)) and all(map(lambda _: isinstance(_, str), lhs)): 
            self.lhs = tuple(lhs)
        else:
            raise ValueError('The lhs is not a str, nor a list/tuple of str')
        if isinstance(rhs, (list, tuple)) and all(map(lambda _: isinstance(_, str), rhs)): 
            self.rhs = tuple(rhs)
        else:
            raise ValueError('The rhs must be a list/tuple of str')        

    def __eq__(self, other):
        if not isinstance(other, Production): return False
        return (self.lhs, self.rhs) == (other.lhs, other.rhs)

    def __hash__(self):
        return hash((self.lhs, self.rhs))

    def __iter__(self):
        return iter((self.lhs, self.rhs))

    def __repr__(self):
        return '{} -> {}'.format(_letlrhstostr(self.lhs), _letlrhstostr(self.rhs))

    @classmethod 
    def from_string(cls, prods, context_free = True):
        """Builds a tuple of productions obtained from the given string.

        Args:
            prods (str): a string representing the set of productions.
            context_free (bool): if ``True`` all the *lefthand* sides will be string (not tuples).

        The string must be a sequence of lines of the form::

            lhs -> alternatives

        where ``alternatives`` is a list of ``rhs`` strings (possibly separated by ``|``)
        and ``lhs`` and ``rhs`` are space separated strings that will be used as *lefthand* and 
        *righthand* of the returned productions; for example::

            S -> ( S ) | x T y
            x T y -> t

        Raises:

            ValueError: in case the productions are declared as ``context_free`` but on of 
                        them has more than one symbol on the righthand side.
        """
        P = []
        for p in prods.splitlines():
            if not p.strip(): continue
            lh, rha = p.split('->')
            lhs = tuple(lh.split())
            if context_free:
                if len(lhs) != 1: raise ValueError('Production "{}" has more than one symbol as left-hand side'.format(p))
                lhs = lhs[0]
            for rh in rha.split('|'):
                P.append(cls(lhs, tuple(rh.split())))
        return tuple(P)


class Item(Production): # pragma: no cover
    __slots__ = ('pos',)
    def __init__(self, lhs, pos, rhs):
        if isinstance(lhs, (list, tuple)):
            raise ValueError('The lhs must be a str')
        super().__init__(lhs, rhs)
        self.pos = pos
    def __eq__(self, other):
        if not isinstance(other, Item): return False
        return (self.lhs, self.pos, self.rhs) == (other.lhs, other.pos, other.rhs)
    def __hash__(self):
        return hash((self.lhs, self.pos, self.rhs))
    def __iter__(self):
        return iter((self.lhs, self.pos, self.rhs))
    def __repr__(self):
        return '{} -> {}•{}'.format(_letlrhstostr(self.lhs), _letlrhstostr(self.rhs[:self.pos]), _letlrhstostr(self.rhs[self.pos:]))


class EarleyItem(Item):  # pragma: no cover
    __slots__ = ('orig', )
    def __init__(self, lhs, pos, rhs, orig):
        if isinstance(lhs, (list, tuple)):
            raise ValueError('The lhs must be a str')
        super().__init__(lhs, pos, rhs)
        self.orig = orig
    def __eq__(self, other):
        if not isinstance(other, EarleyItem): return False
        return (self.lhs, self.pos, self.rhs, self.orig) == (other.lhs, other.pos, other.rhs, other.orig)
    def __hash__(self):
        return hash((self.lhs, self.pos, self.rhs, self.orig))
    def __iter__(self):
        return iter((self.lhs, self.pos, self.rhs, self.orig))
    def __repr__(self):
        return '{} -> {}•{}@{}'.format(_letlrhstostr(self.lhs), _letlrhstostr(self.rhs[:self.pos]), _letlrhstostr(self.rhs[self.pos:]), self.orig)


class Grammar:
    """A grammar.

    This class represents a formal grammar, that is a tuple :math:`(N, T, P, S)` where
    :math:`N` is the finite set of *nonterminals* or *variables* symbols, :math:`T` is the 
    finite set of *terminals*, :math:`P` are the grammar *productions* or *rules* and, 
    :math:`S \in N` is the *start* symbol.

    Args:
        N (set): the grammar nonterminals.
        T (set): the grammar terminals.
        P (tuple): the grammar productions.
        S (str): the grammar start symbol.

    """

    __slots__ = ('N', 'T', 'P', 'S')

    def __init__(self, N, T, P, S):
        self.N = frozenset(N)
        self.T = frozenset(T)
        self.P = tuple(P)
        self.S = S

    @classmethod
    def from_string(cls, prods, context_free = True):
        """Builds a grammar obtained from the given productions.

        Args:
            prods (str): a string describing the productions.
            context_free (bool): if ``True`` the grammar is expected to be context free.

        Once the *productions* are determined via a call to :func:`Production.from_string`, 
        the remaining defining elements of the grammar are obtained as follows:
        
        * if the grammar is *not* context-free the *nonterminals* is the set of symbols,
          appearing in (the lefthand, or righthand side of) any production, beginning with 
          an uppercase letter, the *terminals* are the remaining symbols. The *start* symbol
          is the lefthand of the first production;

        * if the grammar is *context-free* the *nonterminals* is the set of symbols appearing
          in a lefthand side of any production, the *terminals* are the remaining symbols. The
          *start* symbol is the lefthand of the first production.           
        """
        P = Production.from_string(prods, context_free)
        if context_free:
            S = P[0].lhs
            N = set(map(attrgetter('lhs'), P))
            T = set((chain.from_iterable(map(attrgetter('rhs'), P)))) - N - {ε}
        else:
            S = P[0].lhs[0]
            symbols = set(chain.from_iterable(map(attrgetter('lhs'), P))) | set(chain.from_iterable(map(attrgetter('rhs'), P)))
            N = set(_ for _ in symbols if _[0].isupper())
            T = symbols - N - {ε}
        return cls(N, T, P, S)

    def rhs(self, N): 
        return (P.rhs for P in self.P if P.lhs == N)

    def all_terminal(self, word):
        return all(_ in self.T for _ in word)

    def __repr__ (self):
        return 'Grammar(N={}, T={}, P={}, S={})'.format(letstr(self.N), letstr(self.T), self.P, letstr(self.S))

def _ensure_tuple(lhs):
    return lhs if isinstance(lhs, tuple) else (lhs, )    

class Derivation:

    def __init__(self, G):
        self.G = G
        self._sf = (G.S, )
        self._repr = G.S
        self._steps = tuple()

    def leftmost(self, prod):
        return self.step(prod, min(self.matches(prod))[1])

    def rightmost(self, prod):
        return self.step(prod, max(self.matches(prod))[1])

    def step(self, prod, pos): # consider adding rightmost/leftmost (with no pos)
        sf = self._sf
        P = self.G.P[prod]
        lhs = _ensure_tuple(P.lhs)
        if sf[pos: pos + len(lhs)] != lhs: raise ValueError('Cannot apply {} at position {} of {}'.format(P, pos, HAIR_SPACE.join(sf)))
        copy = Derivation(self.G)
        copy._repr = self._repr
        copy._steps = self.steps()
        copy._sf = tuple(_ for _ in sf[:pos] + P.rhs + sf[pos + len(lhs):] if _ != 'ε')
        copy._steps = self._steps + ((prod, pos), )
        copy._repr = self._repr + ' -> ' + HAIR_SPACE.join(copy._sf)
        return copy

    def matches(self, prod = None, pos = None):
        for n, P in enumerate(self.G.P) if prod is None else ((prod, self.G.P[prod]), ):
            lhs = _ensure_tuple(P.lhs)
            for p in range(len(self._sf) - len(lhs) + 1) if pos is None else (pos, ):
                if self._sf[p: p + len(lhs)] == lhs:
                    yield n, p
    
    def steps(self):
        return tuple(self._steps)
        
    def sentential_form(self):
        return tuple(self._sf)
    
    def __repr__(self):
        return self._repr
