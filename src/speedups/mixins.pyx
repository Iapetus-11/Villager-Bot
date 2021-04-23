__all__ = (
    'EqualityComparable',
    'Hashable',
)

cdef class EqualityComparable:
    def __eq__(self, other: object):
        return isinstance(other, self.__class__) and other.id == self.id

    def __ne__(self, other: object):
        if isinstance(other, self.__class__):
            return other.id != self.id

        return True

cdef class Hashable(EqualityComparable):
    def __hash__(self):
        return self.id >> 22
