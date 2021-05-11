from collections import UserList

from .config_entry import ConfigEntry


class NotSupported(Exception):
    pass


class List(ConfigEntry):
    class _BaseProxyType(ConfigEntry._BaseProxyType, UserList):
        def __init__(self, entry):
            ConfigEntry._BaseProxyType.__init__(self, entry)

            UserList.__init__(self)
            self.data = entry._value

        def __iadd__(self, other):
            """Operator += is removed, because there is no -= operator.

            Consistent way of working with list config entries are methods:
            - to add element: append or extend
            - to remove element: remove
            """

            raise NotSupported(
                f'Operator += is removed. Use methods "{self.append.__name__}" or "{self.extend.__name__}" instead.'
            )

    class _UnsetProxyType(_BaseProxyType, ConfigEntry._UnsetProxy):
        pass

    class _ValueProxyType(_BaseProxyType, ConfigEntry._ValueProxy):
        pass

    _UnsetProxy = _UnsetProxyType
    _ValueProxy = _ValueProxyType

    def __init__(self, item_type, separator=' ', begin='', end='', single_line=True):
        super().__init__()

        self._value = []

        self.__item_type = item_type

        self.__separator = separator
        self.__begin = begin
        self.__end = end
        self.__single_line = single_line

    def _is_set(self):
        return bool(self._value)

    def _parse_from_text(self, text):
        import re
        match_result = re.match(fr'^\s*{re.escape(self.__begin)}(.*){re.escape(self.__end)}\s*$', text)
        # TODO: Raise if can't match

        for item_text in match_result[1].split(self.__separator):
            item = self.__item_type()
            parsed = item.parse_from_text(item_text)
            self._value.append(parsed)

        return self._value

    def _serialize_to_text(self):
        def serialize_value(value):
            item = self.__item_type()
            item.set_value(value)
            return item.serialize_to_text()

        values = [serialize_value(value) for value in self._value]
        return self.__begin + self.__separator.join(values) + self.__end if self.__single_line else values

    def _set_value(self, value):
        if not isinstance(value, list):
            value = [value]

        self._value = value

    def _clear(self):
        self._value = []
