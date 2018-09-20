import requests

from zohocrm.exceptions import UnknownError, InvalidModuleError, NoPermissionError, MandatoryKeyNotFoundError, InvalidDataError, MandatoryFieldNotFoundError

BASE_URL = 'https://www.zohoapis.com/crm/'
ZOHOCRM_AUTHORIZE_URL = 'https://accounts.zoho.com/oauth/v2/auth?scope={0}&client_id={1}&response_type=code&\
access_type={2}&redirect_uri={3}'
ZOHOCRM_REQUEST_TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token?code={0}&redirect_uri={1}&\
client_id={2}&client_secret={3}&grant_type=authorization_code'
ZOHOCRM_REFRESH_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token?refresh_token={0}&\
client_id={1}&client_secret={2}&grant_type=refresh_token"
READ_MODULE_LIST = ['leads', 'accounts', 'contacts', 'deals', 'campaigns', 'tasks', 'cases', 'events', 'calls',
                    'solutions', 'products', 'vendors', 'pricebooks', 'quotes', 'salesorders', 'purchaseorders',
                    'invoices', 'custom', 'notes', 'approvals', 'dashboards', 'search', 'activities']
WRITE_MODULE_LIST = ['leads', ' accounts', ' contacts', ' deals', ' campaigns', ' tasks', ' cases', ' events', ' calls',
                     ' solutions', ' products', ' vendors', ' pricebooks', ' quotes', ' salesorders', ' purchaseorders',
                     ' invoices', ' custom', ' notes']


class Client(object):

    def __init__(self, client_id, client_secret, redirect_uri, scope, access_type):
        self.code = None
        self.scope = scope
        self.access_type = access_type
        self.client_id = client_id
        self._refresh_token = None
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret
        self.access_token = None

    def get_authorization_url(self):
        """

        :return:
        """
        url = ZOHOCRM_AUTHORIZE_URL.format(self.scope, self.client_id, self.access_type, self.redirect_uri)
        return url

    def exchange_code(self, code):
        """

        :param code:
        :return:
        """
        url = ZOHOCRM_REQUEST_TOKEN_URL.format(code, self.redirect_uri, self.client_id, self.client_secret)
        return self._post(url)

    def refresh_token(self):
        """

        :return:
        """
        url = ZOHOCRM_REFRESH_TOKEN_URL.format(self._refresh_token, self.client_id, self.client_secret)
        return self._post(url)

    def set_access_token(self, token):
        """

        :param token:
        :return:
        """
        if isinstance(token, dict):
            self.access_token = token['access_token']
            if 'refresh_token' in token:
                self._refresh_token = token['refresh_token']
        else:
            self.access_token = token

    def get_module_list(self):
        """

        :return:
        """
        url = BASE_URL + "settings/modules"
        response = self._get(url)
        if response:
            return [i for i in response['modules'] if i['api_supported'] == 'true']
        else:
            return None

    def get_records(self, module_name):
        """

        :param module_name: module from which to read record
        :return:
        """
        if module_name not in READ_MODULE_LIST:
            return None
        url = BASE_URL + str(module_name)
        response = self._get(url)
        all_data = [response['data']]
        while response['info']['more_records'] == 'true':
            page = response['info']['page']
            response = self._get(url, params={'page': int(page) + 1})
            all_data.append(response['data'])
        return all_data

    def insert_record(self, module_name, data):
        """

        :param module_name:
        :param data:
        :return:
        """
        if module_name not in WRITE_MODULE_LIST:
            return None
        if not isinstance(data, list):
            return None
        if len(data) <= 0:
            return None
        if not isinstance(data[-1], dict):
            return None
        url = BASE_URL + str(module_name)
        return self._post(url, data={'data': data})

    def _get(self, endpoint, params=None):
        headers = {
            'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token),
        }
        response = requests.get(endpoint, params=params, headers=headers)
        return self._parse(response, method='get')

    def _post(self, endpoint, params=None, data=None):
        headers = {
            'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token),
        }
        response = requests.post(endpoint, params=params, json=data, headers=headers)
        return self._parse(response, method='post')

    def _put(self, endpoint, params=None, data=None):
        headers = {
            'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token),
        }
        response = requests.put(endpoint, params=params, json=data, headers=headers)
        return self._parse(response, method='put')

    def _delete(self, endpoint, params=None):
        headers = {
            'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token),
        }
        response = requests.delete(endpoint, params=params, headers=headers)
        return self._parse(response, method='delete')

    def _parse(self, response, method=None):
        # TODO obtener metodo de request
        # TODO diferenciar entre los errores de _post y _get
        status_code = response.status_code
        if 'application/json' in response.headers['Content-Type']:
            r = response.json()
        else:
            r = response.text
        if status_code in (200, 201):
            return r
        if status_code == 204:
            return None
        message = None
        print(r)
        print(r.__dict__)
        try:
            if 'errorMessages' in r:
                message = r['errorMessages']
        except Exception:
            message = 'No error message.'
        if method == 'get':
            if status_code == 400:
                raise InvalidModuleError(message)
        if method == 'post':
            if status_code == 201:
                raise MandatoryFieldNotFoundError(message)
            elif status_code == 202:
                raise InvalidDataError(message)
            elif status_code == 400:
                raise InvalidDataError(message)
