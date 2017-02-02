# coding: utf-8
import requests
import json
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
PASSPORT_LIMIT = 1
DATE_LIMIT = 1
AUTO_LIMIT = 1


"""
Методы Стандартизации
"""
CLEAN_NAMES = ['address', 'phone', 'passport', 'fio', 'email', 'auto', 'date']


"""
Constants & Errors
"""
SUCCESS = 200

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
class Result(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ApiURL(ManyOneMixin):
    limit = 1
    url = ''

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.url += self.url_postfix

    def request(self):
        return self.client.request(self)

    def process_result(self, client):
        result = Result(**client._result[0])
        return result

    def update(self, value):
        if isinstance(value, list):
            self.many = value
        else:
            self.one = value


class Clean(ApiURL):
    url_postfix = '/clean'

    def __init__(self, *args, **kwargs):
        super(Clean, self).__init__(*args, **kwargs)
        kwargs['url'] = self.url
        self.address = Address(**kwargs)
        self.phone = Phone(**kwargs)
        self.passport = Passport(**kwargs)
        self.fio = FIO(**kwargs)
        self.email = EMail(**kwargs)
        self.date = Date(**kwargs)
        self.auto = Auto(**kwargs)


class Address(ApiURL):
    url_postfix = '/address'
    limit = ADDRESS_LIMIT


class Phone(ApiURL):
    url_postfix = '/phone'
    limit = PHONE_LIMIT


class Passport(ApiURL):
    url_postfix = '/passport'
    limit = PASSPORT_LIMIT


class FIO(ApiURL):
    url_postfix = '/name'
    limit = FIO_LIMIT


class EMail(ApiURL):
    url_postfix = '/email'
    limit = EMAIL_LIMIT


class Date(ApiURL):
    url_postfix = '/birthdate'
    limit = DATE_LIMIT


class Auto(ApiURL):
    url_postfix = '/vehicle'
    limit = AUTO_LIMIT


class DaDataClient(object):
    url = 'https://dadata.ru/api/v2'
    key = ''
    secret = ''
    data = []
    result = None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.clean = Clean(
            url = self.url,
            client = self,
        )

        self.session = requests.Session()

    def __getattr__(self, name):
        if name in CLEAN_NAMES:
            return getattr(self.clean, name)
        return super(DaDataClient, self).__getattr__(name)

    def __setattr__(self, name, value):
        if name in CLEAN_NAMES:
            return self.clean.__dict__[name].update(value)
        return super(DaDataClient, self).__setattr__(name, value)

    def request(self, api_method=None, secret=True):
        # TODO: Rethink..
        if not self.key:
            return Errors.CLIENT_NO_KEY
        if not self.secret:
            return Errors.CLIENT_NO_SECRET
        if not self.data:
            return Errors.CLIENT_NO_DATA

        headers={
            'Authorization': 'Token %s' % self.key,
        }

        if secret:
            headers['X-Secret'] = self.secret

        response = self.session.post(api_method.url,
                                     data=json.dumps(self.data),
                                     headers=headers)

        if not response.status_code == SUCCESS:
            return response.status_code

        self._result = json.loads(response.content.decode('utf-8'))
        self.result = api_method.process_result(self)
        self.response = response
        return SUCCESS

