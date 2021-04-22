__all__ = (
    'EqualityComparable',
    'Hashable',
)

cdef class EqualityComparable:
    cpdef bint __eq__(self, other: object):
        return isinstance(other, self.__class__) and other.id == self.id

    cpdef bint __ne__(self, other: object):
        if isinstance(other, self.__class__):
            return other.id != self.id

        return True

cdef class Hashable(EqualityComparable):
    cpdef signed int __hash__(self):
        return self.id >> 22
