import json
import requests
from urllib.parse import urlencode

from zohocrm.exceptions import UnknownError, InvalidModuleError, NoPermissionError, MandatoryKeyNotFoundError, \
    InvalidDataError, MandatoryFieldNotFoundError

BASE_URL = 'https://www.zohoapis.com/crm/v2/'
ZOHOCRM_AUTHORIZE_URL = 'https://accounts.zoho.com/oauth/v2/auth'
ZOHOCRM_REQUEST_TOKEN_URL = 'https://accounts.zoho.com/oauth/v2/token'
ZOHOCRM_REFRESH_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
READ_MODULE_LIST = ['leads', 'accounts', 'contacts', 'deals', 'campaigns', 'tasks', 'cases', 'events', 'calls',
                    'solutions', 'products', 'vendors', 'pricebooks', 'quotes', 'salesorders', 'purchaseorders',
                    'invoices', 'custom', 'notes', 'approvals', 'dashboards', 'search', 'activities']
# module purchaseorders, 'invoices', salesorders and quotes are temporarily disable for writing this
# due to the complexity of the module
WRITE_MODULE_LIST = ['leads', 'accounts', 'contacts', 'deals', 'campaigns', 'tasks', 'cases', 'events', 'calls',
                     'solutions', 'products', 'vendors', 'pricebooks', 'purchaseorders', 'custom', 'notes']


class Client(object):

    def __init__(self, client_id, client_secret, redirect_uri, scope, access_type, refresh_token=None):
        self.code = None
        self.scope = scope
        self.access_type = access_type
        self.client_id = client_id
        self._refresh_token = refresh_token
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret
        self.access_token = None

    def get_authorization_url(self):
        """

        :return:
        """
        params = {'scope': ','.join(self.scope), 'client_id': self.client_id, 'access_type': 'offline',
                  'redirect_uri': self.redirect_uri, 'response_type': 'code', 'prompt':'consent'}
        url = ZOHOCRM_AUTHORIZE_URL + '?' + urlencode(params)
        return url

    def exchange_code(self, code):
        """

        :param code:
        :return:
        """
        params = {'code': code, 'client_id': self.client_id, 'client_secret': self.client_secret,
                  'redirect_uri': self.redirect_uri, 'grant_type': 'authorization_code'}
        url = ZOHOCRM_REQUEST_TOKEN_URL + '?' + urlencode(params)
        return self._post(url)

    def refresh_token(self):
        """

        :return:
        """
        params = {'refresh_token': self._refresh_token, 'client_id': self.client_id,
                  'client_secret': self.client_secret, 'grant_type': 'refresh_token'}
        url = ZOHOCRM_REFRESH_TOKEN_URL + '?' + urlencode(params)
        response = self._post(url)
        return response

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
            return [i for i in response['modules'] if i['api_supported'] is True]
        else:
            return None

    def get_fields_list(self, module):
        """

        :param module:
        :return:
        """
        params = {'module': module}
        url = BASE_URL + "settings/fields" + "?" + urlencode(params)
        response = self._get(url)
        if response:
            try:
                result = [
                    {
                        'id': i['id'],
                        'label': i['field_label'],
                        'api_name': i['api_name'],
                        'max_length': i['length'],
                        'read_only': i['read_only'],
                        'data_type': i['data_type'],
                        'currency': i['currency'],
                        'lookup': i['lookup'],
                        'pick_list_values': i['pick_list_values']
                    } for i in response['fields']]
            except Exception as e:
                print(e)
        else:
            return None
        return result

    def create_webhook(self, module, gearplug_webhook_id, notify_url):
        """

        :param module:
        :param gearplug_webhook_id:
        :param notify_url:
        :return:
        """
        endpoint = 'actions/watch'
        event = ["{0}.create".format(module)]
        data = [{'notify_url': notify_url, 'channel_id': gearplug_webhook_id, 'events': event, }]
        data = {'watch': data}
        url = BASE_URL + endpoint
        try:
            response = self._post(url, data=data)
        except Exception as e:
            return False
        if response['watch'][-1]['code'] == "SUCCESS":
            return response['watch'][-1]['details']
        else:
            return False

    def delete_webhook(self, webhook_id, module):
        """

        :return:
        """
        events = ["{0}.create".format(module)]
        data = [{'channel_id': webhook_id, 'events': events, '_delete_events': 'true'}]
        data = {'watch': data}
        endpoint = 'actions/watch'
        url = BASE_URL + endpoint
        response = self._patch(url, data=data)
        if response['watch'][-1]['code'] == "SUCCESS":
            return response['watch'][-1]['details']
        else:
            return False

    def get_records(self, module_name):
        """

        :param module_name: module from which to read record (api_name)
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

    def get_specific_record(self, module, id):
        """

        :return:
        """
        endpoint = '{0}/{1}'.format(module, id)
        url = BASE_URL + str(endpoint)
        response = self._get(url)
        if response and 'data' in response and len(response['data']) > 0 and response['data'][0]['id'] == id:
            return response['data']
        else:
            return False

    def get_all_active_users(self):
        """

        :return: all active users
        """
        endpoint = 'users?type=ActiveUsers'
        url = BASE_URL + str(endpoint)
        response = self._get(url)
        if response and 'users' in response and isinstance(response['users'], list) and len(response['users']) > 0:
            return response['users']
        else:
            return False

    def get_all_organizations(self):
        """

        :return: all oganizations
        """
        endpoint = 'org'
        url = BASE_URL + str(endpoint)
        response = self._get(url)
        if response and 'org' in response and isinstance(response['org'], list) and len(response['users']) > 0:
            return response['org']
        else:
            return False

    def insert_record(self, module_name, data):
        """

        :param module_name:
        :param data:
        :return:
        """
        if module_name.lower() not in WRITE_MODULE_LIST:
            return None
        url = BASE_URL + str(module_name)
        data = dict(data)
        for k, v in data.items():
            if v == 'False':
                data[k] = False
            if v == 'True':
                data[k] = True
        formatted_data = {'data': []}
        formatted_data['data'].append(data)
        return self._post(url, data=formatted_data)

    def _get(self, endpoint, params=None):
        headers = {'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token), }
        response = requests.get(endpoint, params=params, headers=headers)
        return self._parse(response, method='get')

    def _post(self, endpoint, params=None, data=None):
        headers = {'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token), }
        response = requests.post(endpoint, params=params, json=data, headers=headers)
        return self._parse(response, method='post')

    def _put(self, endpoint, params=None, data=None):
        headers = {'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token), }
        response = requests.put(endpoint, params=params, json=data, headers=headers)
        return self._parse(response, method='put')

    def _patch(self, endpoint, params=None, data=None):
        headers = {'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token), }
        response = requests.patch(endpoint, params=params, json=data, headers=headers)
        return self._parse(response, method='patch')

    def _delete(self, endpoint, params=None):
        headers = {'Authorization': 'Zoho-oauthtoken {0}'.format(self.access_token), }
        response = requests.delete(endpoint, params=params, headers=headers)
        return self._parse(response, method='delete')

    def _parse(self, response, method=None):
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
        try:
            if 'message' in r:
                message = r['message']
        except Exception:
            message = 'No error message.'
        if status_code == 400:
            raise InvalidModuleError(message)
        if status_code == 401:
            raise NoPermissionError(status_code)
        if status_code == 201:
            raise MandatoryFieldNotFoundError(message)
        elif status_code == 202:
            raise InvalidDataError(message)
        elif status_code == 400:
            raise InvalidDataError(message)
