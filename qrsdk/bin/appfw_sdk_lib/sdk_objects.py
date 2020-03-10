# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

from os.path import isfile
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, SSLError
from urllib3.poolmanager import PoolManager
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from sdk_exceptions import SdkServerSslError, SdkServerRequestError, SdkApiResponseError, SdkPemError

RESPONSE_CODE_SUCCESS = 200
RESPONSE_CODE_SUCCESS_CREATED = 201
RESPONSE_CODE_SUCCESS_ACCEPTED = 202
RESPONSE_CODE_SUCCESS_NO_CONTENT = 204


class HostNameIgnoringAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       assert_hostname=False,
                                       **pool_kwargs)


class HttpApiClient(object):
    def __init__(self, qradar_console, username, password, cert_path=None):
        self.__qradar_console = qradar_console
        self.__username = username
        self.__password = password
        self.__cert_path = cert_path

    # Helper functions

    def build_endpoint_url(self, request_endpoint):
        return 'https://' + self.__qradar_console + request_endpoint

    def handle_request_exception(self, exception):
        if type(exception) == SSLError:
            raise SdkServerSslError('SSL error from host {0}: {1}'.format(self.__qradar_console, exception))
        raise SdkServerRequestError('Request to host {0} failed: {1}'.format(self.__qradar_console, exception))

    def check_for_invalid_response(self, response, valid_codes):
        if (response.status_code not in valid_codes):
            try:
                responseJson = response.json()
                raise SdkApiResponseError(responseJson["message"], response.status_code)
            except ValueError:
                raise SdkApiResponseError(response.text(), response.status_code)

    def get_requests_session(self):
        if not isinstance(self.__cert_path, basestring):
            return Session()

        if not isfile(self.__cert_path):
            raise SdkPemError('PEM file {0} does not exist'.format(self.__cert_path))
        try:
            with open(self.__cert_path) as pem_file:
                pem_text = pem_file.read()
                cert = x509.load_pem_x509_certificate(pem_text, default_backend())
                session = Session()
                if self.is_cert_self_issued(cert):
                    session.mount('https://', HostNameIgnoringAdapter())
                return session
        except Exception as e:
            raise SdkPemError('Unable to load local PEM file {0}: {1}'.format(self.__cert_path, e))

    def is_cert_self_issued(self, cert):
        return self.get_cert_issuer_name(cert) == self.get_cert_subject_name(cert)

    def get_cert_issuer_name(self, cert):
        oid = getattr(x509, 'OID_COMMON_NAME')
        info = cert.issuer.get_attributes_for_oid(oid)
        if info:
            return info[0].value
        return ''

    def get_cert_subject_name(self, cert):
        oid = getattr(x509, 'OID_COMMON_NAME')
        info = cert.subject.get_attributes_for_oid(oid)
        if info:
            return info[0].value
        return ''

    # HTTP functions

    def get(self, request_endpoint, request_headers):
        session = self.get_requests_session()
        try:
            response = session.get(url = self.build_endpoint_url(request_endpoint),
                                   auth = (self.__username, self.__password),
                                   headers = request_headers,
                                   verify = self.__cert_path)
        except RequestException as e:
            self.handle_request_exception(e)
        else:
            self.check_for_invalid_response(response, {RESPONSE_CODE_SUCCESS})
        return response

    def post(self, request_endpoint, request_headers, request_json = None, request_package = None):
        session = self.get_requests_session()
        try:
            response = session.post(url = self.build_endpoint_url(request_endpoint),
                                    auth = (self.__username, self.__password),
                                    headers = request_headers,
                                    json = request_json,
                                    verify = self.__cert_path,
                                    data = request_package)
        except RequestException as e:
            self.handle_request_exception(e)
        else:
            self.check_for_invalid_response(response, {RESPONSE_CODE_SUCCESS, RESPONSE_CODE_SUCCESS_CREATED})
        return response

    def put(self, request_endpoint, request_headers, request_package = None):
        session = self.get_requests_session()
        try:
            response = session.put(url = self.build_endpoint_url(request_endpoint),
                                   auth = (self.__username, self.__password),
                                   headers = request_headers,
                                   verify = self.__cert_path,
                                   data = request_package)
        except RequestException as e:
            self.handle_request_exception(e)
        else:
            self.check_for_invalid_response(response, {RESPONSE_CODE_SUCCESS_ACCEPTED})
        return response

    def delete(self, request_endpoint):
        session = self.get_requests_session()
        try:
            response = session.delete(url = self.build_endpoint_url(request_endpoint),
                                      auth = (self.__username, self.__password),
                                      verify = self.__cert_path)
        except RequestException as e:
            self.handle_request_exception(e)
        else:
            self.check_for_invalid_response(response, {RESPONSE_CODE_SUCCESS_NO_CONTENT})
        return response
