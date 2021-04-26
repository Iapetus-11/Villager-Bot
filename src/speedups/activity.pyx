import datetime

__all__ = ("BaseActivity",)

cdef class BaseActivity:
    """The base activity that all user-settable activities inherit from.
    A user-settable activity is one that can be used in :meth:`Client.change_presence`.
    The following types currently count as user-settable:
    - :class:`Activity`
    - :class:`Game`
    - :class:`Streaming`
    - :class:`CustomActivity`
    Note that although these types are considered user-settable by the library,
    Discord typically ignores certain combinations of activity depending on
    what is currently set. This behaviour may change in the future so there are
    no guarantees on whether Discord will actually let you set these types.
    .. versionadded:: 1.3
    """

    cdef double _created_at

    def __init__(self, **kwargs):
        self._created_at = kwargs.pop('created_at', None)

    @property
    def created_at(self):
        """Optional[:class:`datetime.datetime`]: When the user started doing this activity in UTC.
        .. versionadded:: 1.3
        """

        if self._created_at is not None:
            return datetime.datetime.utcfromtimestamp(self._created_at / 1000)
