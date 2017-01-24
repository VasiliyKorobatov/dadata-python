import requests
from copy import deepcopy

"""
Ограничения:
    не более 1 ФИО,
    3 адресов,
    3 телефонов,
    3 email
"""
EMAIL_LIMIT = 3
PHONE_LIMIT = 3
ADDRESS_LIMIT = 3
FIO_LIMIT = 1

"""
Errors
"""
class Errors:
    CLIENT_NO_KEY = 600
    CLIENT_NO_SECRET = 601
    CLIENT_NO_DATA = 602

"""
Exceptions
"""
class LimitExceed(Exception):
    pass


"""
Helper Mixins
"""
class ManyOneMixin(object):
    def _get_one(self):
        return self.client.data[0] if self.client.data else None

    def _set_one(self, value):
        self.client.data = []
        self.client.data.append(value)

    one = property(_get_one, _set_one)

    def _get_many(self):
        return self.client.data

    def _set_many(self, value):
        self.client.data = []
        if len(value) > self.limit:
            raise LimitExceed('Ограничение превышено. Введено %s значений из %s' % (len(value), self.limit))
        self.client.data.extend(value)

    many = property(_get_many, _set_many)


"""
Обертка над Dadata API
"""
class ApiURL(ManyOneMixin):
    limit = 1
    url = ''

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def request(self):
        return self.client.request()


class Clean(ApiURL):
    def __init__(self, *args, **kwargs):
        super(Clean, self).__init__(*args, **kwargs)

        kwargs['url'] = kwargs['url'] + '/address'
        self.address = Address(**kwargs)


class Address(ApiURL):
    limit = ADDRESS_LIMIT


class DaDataClient(object):
    url = 'https://dadata.ru/api/v2'
    key = ''
    secret = ''
    data = []

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.clean = Clean(
            url = self.url + '/clean',
            client = self,
        )

    @property
    def address(self):
        return self.clean.address

    def request(self):
        if not self.key:
            return Errors.CLIENT_NO_KEY
        if not self.secret:
            return Errors.CLIENT_NO_SECRET
        if not self.data:
            return Errors.CLIENT_NO_DATA

