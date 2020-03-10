# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

import getpass
import json
import collections
import os
import zipfile
import subprocess
import time
import uuid
import shutil
import jsonschema
import io
import sys
import socket
from qpylib.qpylib import get_cert_filepath
from sdk_objects import HttpApiClient
from sdk_exceptions import SdkApiResponseError, SdkFatalError,\
                           SdkServerConnectionError, SdkServerSslError,\
                           SdkPemError

DEFAULT_RUN_SCRIPT_PATH = 'run.py'
PEM_FILE = '.qradar_appfw.console_cert.{0}.pem'

ENDPOINT_APPLICATIONS = '/api/gui_app_framework/applications'
ENDPOINT_APPLICATION = ENDPOINT_APPLICATIONS + '/{0}'
ENDPOINT_APPLICATION_INSTALL = '/api/gui_app_framework/application_creation_task'
ENDPOINT_APPLICATION_INSTALL_STATUS = ENDPOINT_APPLICATION_INSTALL + '/{0}'
ENDPOINT_APPLICATION_INSTALL_AUTH = ENDPOINT_APPLICATION_INSTALL_STATUS + '/auth'
ENDPOINT_APPLICATION_CANCEL = ENDPOINT_APPLICATION_INSTALL_STATUS + '?status=CANCELLED'
ENDPOINT_USERS_WITH_CAPABILITIES = '/api/config/access/users_with_capability_filter?capabilities={0}'

HEADERS_JSON = {'Accept': 'application/json', 'Content-Type': 'application/json'}
HEADERS_ZIP = {'Content-Type': 'application/zip'}

STATUS_CREATING = 'CREATING'
STATUS_UPGRADING = 'UPGRADING'
STATUS_AUTH_REQUIRED = 'AUTH_REQUIRED'
STATUS_ERROR = 'ERROR'

# Any time we do GET ENDPOINT_APPLICATION we have to check _qradar_version_ to
# determine the shape of the JSON response.
_qradar_version_ = ""

zip_file_exclude_root_directories_list = ["store", "qradar_appfw_venv", ".git"]
zip_file_exclude_extension_list = [".pyc"]
zip_file_exclude_from_top_level_file_list = ["run.py", ".gitattributes", ".gitignore"]
zip_file_exclude_file_list = [".DS_Store"]

class ManifestException(Exception):
    pass

def add_manifest(manifest_path, destination_package, compression):
    with open(manifest_path) as manifest_file:
        manifest = json.load (manifest_file)
    if 'dev_opts' in manifest:
        manifest.pop("dev_opts")
    manifest_str = json.dumps(manifest,indent=4, sort_keys=True)
    destination_package.writestr("manifest.json", manifest_str, compress_type=compression)

def pack(workspace_path, zip_path):
    zip_file_exclude_file_list.append(os.path.basename(zip_path))
    destination_package = zipfile.ZipFile(zip_path, "w")
    original_working_directory = os.getcwd()
    os.chdir(workspace_path)
    valid_file_paths_in_cwd = get_list_of_valid_paths_in_cwd()
    for path in valid_file_paths_in_cwd:
        add_path_to_zip(destination_package, path)
    os.chdir(original_working_directory)

def add_path_to_zip(destination_package, path):
    if os.path.isfile(path):
        compression = zipfile.ZIP_DEFLATED
        print "Compressing file to zip: " + path
    else:
        compression = zipfile.ZIP_STORED
        print "Adding directory to zip: " + path
    if path == "manifest.json":
        add_manifest(path, destination_package, compression)
    else:
        destination_package.write(path, compress_type=compression)

def get_list_of_valid_paths_in_cwd():
    paths = []
    for path in get_files_in_root_dir():
        paths.append(os.path.join(path))
    root_directories_to_walk = get_root_directories_to_walk()
    for root_directory in root_directories_to_walk:
        paths.append(root_directory)
        for root, directories, file_names in os.walk(root_directory):
            for directory in directories:
                paths.append(os.path.join(root, directory))
            for file_name in file_names:
                if not is_excluded_file_path(file_name):
                    paths.append(os.path.join(root, file_name))
    return paths

def get_files_in_root_dir():
    paths = []
    for entity in os.listdir("."):
        if os.path.isfile(entity) and not is_excluded_file_path(entity) and not is_excluded_root_file_path(entity):
            paths.append(entity)
    return paths

def is_excluded_root_file_path(file_path):
    return file_path in zip_file_exclude_from_top_level_file_list

def is_excluded_file_path(file_path):
    return is_excluded_file_extension(file_path) or is_excluded_file(file_path)

def is_excluded_file_extension(entry):
    return entry.endswith(tuple(zip_file_exclude_extension_list))

def is_excluded_file(entry):
    return entry in zip_file_exclude_file_list

def get_directories_in_path(path):
    directories_in_path = []
    for entity in os.listdir(path):
        if os.path.isdir(entity):
            directories_in_path.append(entity)
    return directories_in_path

def get_root_directories_to_walk():
    all_directories = get_directories_in_path(".")
    directories_to_walk = []
    for directory in all_directories:
        if directory not in zip_file_exclude_root_directories_list:
            directories_to_walk.append(directory)
    return directories_to_walk

def set_qradar_version_from_response_code(response_code):
    global _qradar_version_
    if response_code == 200:
        _qradar_version_ = '7.2.6p2+'
    else:
        _qradar_version_ = '7.2.6'

def set_qradar_version(api_client):
    try:
        response = api_client.get(request_endpoint=ENDPOINT_APPLICATIONS,
                                  request_headers=HEADERS_JSON)
        status_code = response.status_code
    except SdkApiResponseError as e:
        status_code = e.httpStatus
        if status_code != 404:
            raise e
    set_qradar_version_from_response_code(status_code)

def deploy_app(package_path, auth_user_name, api_client, debug_run_script_path):
    app_uuid = extract_uuid_from_zip(package_path)
    app_id = get_app_id_for_uuid(app_uuid, api_client)
    zip_in_memory = get_zip_in_memory(package_path, debug_run_script_path)
    if app_id is None:
        new_install(package_path, auth_user_name, api_client, zip_in_memory)
    else:
        upgrade_install(package_path, app_id, auth_user_name, api_client, zip_in_memory)

def extract_uuid_from_zip(package_path):
    app_zip = zipfile.ZipFile(package_path, 'r')
    for name in app_zip.namelist():
        if name == 'manifest.json':
            ex_file = app_zip.open(name)
            parsed_json = json.load(ex_file)
            return parsed_json["uuid"]
    return None

def get_app_id_for_uuid(app_uuid, api_client):
    response = api_client.get(request_endpoint=ENDPOINT_APPLICATIONS,
                              request_headers=HEADERS_JSON)
    set_qradar_version_from_response_code(response.status_code)
    response_json = response.json()
    for app in response_json:
        if 'uuid' in app["manifest"]:
            if app["manifest"]["uuid"] == app_uuid:
                if app["application_state"]["status"] == "ERROR":
                    return None
                return app["application_state"]["application_id"]
    return None

def new_install(package_path, auth_user_name, api_client, zip_in_memory):
    print "Application fresh install detected"
    print "Uploading {} {} bytes".format(package_path, os.path.getsize(package_path))
    response = api_client.post(request_endpoint=ENDPOINT_APPLICATION_INSTALL,
                               request_headers=HEADERS_ZIP,
                               request_package=zip_in_memory.read())
    task_json = response.json()
    app_id = task_json['application_id']
    finish_install(task_json, app_id, api_client, auth_user_name, expected_status=STATUS_CREATING)

def upgrade_install(package_path, app_id, auth_user_name, api_client, zip_in_memory):
    print "Application upgrade detected"
    print "Uploading {} {} bytes".format(package_path, os.path.getsize(package_path))
    response = api_client.put(request_endpoint=ENDPOINT_APPLICATION.format(app_id),
                              request_headers=HEADERS_ZIP,
                              request_package=zip_in_memory.read())
    task_json = response.json()
    finish_install(task_json, app_id, api_client, auth_user_name, expected_status=STATUS_UPGRADING)

def finish_install(task_json, app_id, api_client, auth_user_name, expected_status):
    task_status = task_json['status']
    print "Application {}: {}".format(app_id, task_status)
    if task_status == expected_status:
        wait_for_deploy_end(app_id, api_client)
    elif task_status == STATUS_AUTH_REQUIRED:
        handle_auth_request(str(app_id), auth_user_name, api_client)

def get_zip_in_memory(package_path, debug_run_script_path):
    app_zip = open(package_path, 'rb')
    zip_in_memory = put_file_into_memory(app_zip)
    if debug_run_script_path:
        zip_in_memory = add_run_script_to_zip_in_memory(zip_in_memory, debug_run_script_path)
    return zip_in_memory

def add_run_script_to_zip_in_memory(zip_in_memory, run_script_path):
    print "Adding run script"
    zipfile_object = file_object_to_zipfile(zip_in_memory)
    zip_in_memory = add_run_to_zip_in_memory(zipfile_object, run_script_path)
    return zip_in_memory

def add_run_to_zip_in_memory(zip_object, run_script_path):
    in_memory_file = io.BytesIO()
    zipfile_in_mem = zipfile.ZipFile(in_memory_file, 'w')

    for file_name in zip_object.namelist():
        zipfile_in_mem.writestr(file_name, zip_object.read(file_name))

    with open(run_script_path) as run_script_file:
        zipfile_in_mem.writestr(DEFAULT_RUN_SCRIPT_PATH, run_script_file.read())

    zipfile_in_mem.close()
    in_memory_file.seek(0)
    return in_memory_file

def file_object_to_zipfile(file_object):
    modifiable_zipfile = zipfile.ZipFile(file_object, 'r')
    return modifiable_zipfile

def put_file_into_memory(file_object):
    in_memory_file = io.BytesIO()
    in_memory_file.write(file_object.read())
    in_memory_file.seek(0)
    return in_memory_file

def authorize_app(app_id, auth_user_name, api_client):
    set_qradar_version(api_client)
    handle_auth_request(str(app_id), auth_user_name, api_client)

def handle_auth_request(app_id, auth_user_name, api_client):
    # What capabilities is the app requesting?
    auth_response = api_client.get(request_endpoint=ENDPOINT_APPLICATION_INSTALL_AUTH.format(app_id),
                                   request_headers=HEADERS_JSON)
    requested_capabilities = json.dumps(auth_response.json()['capabilities'])
    print 'Application {} is requesting capabilities {}'.format(app_id, requested_capabilities)

    # Which QRadar users have those capabilities?
    users_response = api_client.get(request_endpoint=ENDPOINT_USERS_WITH_CAPABILITIES.format(requested_capabilities),
                                    request_headers={'Allow-Hidden': 'true'})
    capable_users_list = users_response.json()

    auth_user_id = 0
    stop_install = False

    if auth_user_name is not None:
        # The caller supplied an authorization user. Is is valid?
        for capable_user in capable_users_list:
            if capable_user['username'] == auth_user_name:
                auth_user_id = capable_user['id']
                break
        if auth_user_id == 0:
            print 'Supplied authorization user {0} does not have the requested capabilities'.format(auth_user_name)
        else:
            print 'Using supplied authorization user {0}'.format(auth_user_name)

    if auth_user_id == 0:
        # The caller must choose an authorization user from the list.
        print 'These users have the requested capabilities:'
        for capable_user in capable_users_list:
            print '  {0}'.format(capable_user['username'])

        if len(capable_users_list) == 1:
            # Only one authorization user is available to select, so a simple yes or no response will do.
            # "No" means don't proceed with the deployment.
            answer = read_yes_no_input('Use {0} as the authorization user? (y/n): '.format(capable_users_list[0]['username']))
            if answer == 'y':
                auth_user_id = capable_users_list[0]['id']
            else:
                stop_install = True

        while auth_user_id == 0 and stop_install == False:
            # The caller must select one of the capable user names.
            # An empty response means don't proceed with the deployment, subject to a confirmatory "yes".
            selected_user_name = raw_input('Select a user: ').strip()
            if len(selected_user_name) == 0:
                answer = read_yes_no_input('Stop deployment? (y/n): ')
                if answer == 'y':
                    stop_install = True
            else:
                for capable_user in capable_users_list:
                    if capable_user['username'] == selected_user_name:
                        auth_user_id = capable_user['id']
                        break
            if auth_user_id == 0:
                print 'User name {0} not recognized'.format(selected_user_name)

    if stop_install:
        print 'Deployment of application {0} is waiting for authorization'.format(app_id)
    else:
        auth_body = {}
        auth_body['user_id'] = auth_user_id
        api_client.post(request_endpoint=ENDPOINT_APPLICATION_INSTALL_AUTH.format(app_id),
                        request_headers=HEADERS_JSON,
                        request_json=auth_body)
        wait_for_deploy_end(app_id, api_client)

def wait_for_deploy_end(app_id, api_client):
    # Loop over the application_creation_endpoint until the deploy finishes.
    # Note that any error message is not committed to the installed_application table
    # until the very end of the deployment, so there is no point in trying to print
    # error details inside this loop.
    task_status = STATUS_CREATING
    while (task_status == STATUS_CREATING or task_status == STATUS_UPGRADING):
        task_response = api_client.get(request_endpoint=ENDPOINT_APPLICATION_INSTALL_STATUS.format(app_id),
                                       request_headers=HEADERS_JSON)
        task_json = task_response.json()
        task_status = task_json['status']
        print "Application {}: {}".format(app_id, task_status)
        if (task_status == STATUS_CREATING or task_status == STATUS_UPGRADING):
            time.sleep(5)

    # Now call the applications endpoint to get the final status of the deployment.
    app_response = api_client.get(request_endpoint=ENDPOINT_APPLICATION.format(app_id),
                                  request_headers=HEADERS_JSON)
    if (_qradar_version_ == '7.2.6'):
        app_json = app_response.json()[0]
    else:
        app_json = app_response.json()

    app_final_status = app_json['application_state']['status']
    additional_app_details = ''

    if app_final_status != STATUS_ERROR:
        additional_app_details = ' ' + app_json['manifest']['version']

    errors = app_json['application_state']['error_message']
    if len(errors) > 0:
        additional_app_details = additional_app_details + ' ' + errors

    print "Final application state: {}{}".format(app_final_status, additional_app_details)

def read_yes_no_input(message):
    answer = ''
    while True:
        answer = raw_input(message).strip().lower()
        if answer == 'y' or answer == 'yes':
            return 'y'
        if answer == 'n' or answer == 'no':
            return 'n'

def get_sdk_path():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

def get_os_specific(script):
    run_script = ''
    sdk_path = get_sdk_path()
    bin_path = os.path.join(sdk_path,"bin")
    script_windows = os.path.join(bin_path, script+".bat")
    script_unix = os.path.join(bin_path, script+".sh")
    if os.path.isfile(script_windows):
        run_script = os.path.join(bin_path, script+".bat")
    if os.path.isfile(script_unix):
        run_script = os.path.join(bin_path, script+".sh")
    return run_script

def create_virtualenv(workspace):
    create_workspace_script = get_os_specific("create_workspace")
    cmd = [create_workspace_script, os.path.realpath(workspace)]
    print 'Running ' + str(cmd)
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
    lines_iterator = iter(p.stdout.readline, b"")
    for line in lines_iterator:
        print(line),

def copy_template(workspace):
    sdk_path = get_sdk_path()
    template_source_dir = os.path.join(sdk_path,"template")
    print "Template source directory [" + template_source_dir + "]"
    print "Destination directory [" + workspace + "]"
    copy_tree(template_source_dir, workspace)

def create_workspace_dir_if_not_there(workspace):
    if not os.path.exists(workspace):
        print 'Creating App Workspace'
        os.makedirs(workspace)

def copy_tree(source, destination):
    for _file in os.listdir(source):
        _src = os.path.join(source, _file)
        _dst = os.path.join(destination, _file)
        _run = os.path.join(destination, 'run.py')

        if os.path.isdir(_src):
            if not os.path.exists(_dst):
                os.mkdir(_dst)
            copy_tree(source=_src, destination=_dst)
        elif not os.path.exists(_dst) or _dst == _run:
            shutil.copy(_src, _dst)

def create_store(workspace):
    store_path = os.path.join(workspace,"store")
    if not os.path.exists(store_path):
        os.mkdir(store_path)

def run_local(workspace, runscript_realpath, enable_deps):
    os.environ["QRADAR_APPFW_SDK"] = "true"
    os.environ["QRADAR_APPFW_WORKSPACE"] = os.path.abspath(workspace)
    run_app_script = get_os_specific("run_app")
    cmd = [run_app_script, os.path.realpath(workspace), runscript_realpath, str(enable_deps)]
    print('Running ' + str(cmd))
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
    lines_iterator = iter(p.stdout.readline, b"")
    for line in lines_iterator:
        print(line),

def get_manifest_schema():
    sdk_path = get_sdk_path()
    validation_path = os.path.join(sdk_path, "validation")
    schema_json_path = os.path.join(validation_path, "manifest-schema.json")
    schema = open(schema_json_path).read()
    return schema

def check_workspace_manifest_valid(workspace):
    if not os.path.isdir(workspace):
        raise IOError('Directory {0} does not exist'.format(workspace))
    schema = get_manifest_schema()
    manifest_data = open(workspace + "/manifest.json", 'r').read()
    validate_manifest(manifest_data, schema)

def check_zip_manifest_valid(appPackage):
    schema = get_manifest_schema()
    archive = zipfile.ZipFile(appPackage, 'r')
    manifest_data = archive.open('manifest.json', 'r').read()
    validate_manifest(manifest_data, schema)

def find_duplicate_json_keys(list_of_pairs):
    key_count = collections.Counter(k for k,v in list_of_pairs)
    duplicate_keys = ', '.join(k for k,v in key_count.items() if v>1)
    if len(duplicate_keys) != 0:
        raise ManifestException('Duplicate keys found in manifest.json: {}'.format(duplicate_keys))
    return dict(list_of_pairs)

def validate_manifest(manifest_data, schema):
    try:
        manifest_json = json.loads(manifest_data, object_pairs_hook=find_duplicate_json_keys)
        v = jsonschema.Draft4Validator(json.loads(schema))
        errors = sorted(v.iter_errors(manifest_json), key=lambda e: e.path)
        if errors:
            err_str=''
            for error in errors:
                err_str += '\n'
                for err_thing in error.path:
                    err_str += '[' + str(err_thing) + ']'
                if error.path:
                    err_str += ': '
                err_str += error.message
            raise ManifestException('Your manifest.json contains these schema violations:' + err_str)
    except (ValueError, TypeError) as err:
        raise ManifestException('Your manifest.json is not valid JSON:\n' + str(err))

def check_manifest_key_value(workspace_path, key, expected_value):
    with open(workspace_path + "/manifest.json", 'r') as manifest_file:
        manifest_dict = json.load(manifest_file)
        if key in manifest_dict:
            return manifest_dict[key] == expected_value
        return True

def set_key_in_manifest(key, manifest_path):
    if key == '':
        uuid_entry = {'uuid':str(uuid.uuid4())}
    else:
        uuid_entry = {'uuid':key}
    with open(manifest_path, 'r') as manifest_file:
        manifest_dict = json.load(manifest_file)
    manifest_dict.update(uuid_entry)
    with open(manifest_path, 'w') as manifest_file:
        json.dump(manifest_dict, manifest_file)

def check_run_script_valid(runscript):
    if not os.path.exists(runscript):
        raise ValueError("ERROR: Run script {0} not found".format(runscript))
    if not has_permission(runscript):
        raise IOError("ERROR: Permission denied for run script {0}".format(runscript))

def has_permission(filepath):
    try:
        with open(filepath, 'r'):
            return True
    except IOError:
        return False

def read_password(user):
    return getpass.getpass("Please enter password for user " + user + ":")

def handle_ssl_error(ssl_error, console_address):
    print ''
    print ssl_error
    console_pem_file_path = os.path.join(os.path.expanduser("~"),
                                         PEM_FILE.format(console_address))
    try:
        print('Refreshing cert file {0}'.format(console_pem_file_path))
        os.remove(console_pem_file_path)
    except OSError:
        pass

def handle_fatal_error(sdk_error, is_ssl_error = False):
    print(sdk_error)
    if is_ssl_error:
        print 'Unable to resolve SSL certificate issue'
    sys.exit(1)

def get_cert_path(host):
    try:
        return get_cert_filepath(host)
    except (socket.gaierror, socket.error) as e:
        raise SdkServerConnectionError('Unable to retrieve certificate from host {0}: {1}'.format(host, e))
    except ValueError as e:
        raise SdkPemError(e.message)

def get_api_client(args_inst, cert_path):
    password = read_password(args_inst.user)
    return HttpApiClient(args_inst.qradar_console, args_inst.user, password, cert_path)

def get_certified_api_client(args_inst, existing_api_client = None):
    cert_path = get_cert_path(args_inst.qradar_console)
    if existing_api_client is None:
        return get_api_client(args_inst, cert_path)
    return existing_api_client


#####################################################
# argparse entry points
#####################################################

def create_workspace(args_inst):
    try:
        create_workspace_dir_if_not_there(args_inst.workspace)
        copy_template(args_inst.workspace)
        set_key_in_manifest(args_inst.key, args_inst.workspace + "/manifest.json")
        check_workspace_manifest_valid(args_inst.workspace)
        create_store(args_inst.workspace)
        create_virtualenv(args_inst.workspace)
    except (OSError, IOError, ManifestException) as e:
        print e
        sys.exit(1)

def package(args_inst):
    try:
        check_workspace_manifest_valid(args_inst.workspace)
        pack(args_inst.workspace, args_inst.package)
    except (IOError, ManifestException) as e:
        print e
        sys.exit(1)

def run_app(args_inst):
    try:
        check_workspace_manifest_valid(args_inst.workspace)
    except (IOError, ManifestException) as e:
        print e
        sys.exit(1)
    runscript_realpath = os.path.realpath(os.path.join(args_inst.workspace, args_inst.runscript))
    if not os.path.exists(runscript_realpath):
        print "ERROR: Run script {0} not found".format(runscript_realpath)
        sys.exit(1)
    run_local(args_inst.workspace, runscript_realpath, args_inst.enable_deps)

def check_qradar_version(args_inst, existing_api_client = None):
    retry = (existing_api_client is None)
    try:
        api_client = get_certified_api_client(args_inst, existing_api_client)
        set_qradar_version(api_client)
        print "QRadar console on {0} is version {1}".format(args_inst.qradar_console, _qradar_version_)
    except SdkServerSslError as sse:
        if retry:
            handle_ssl_error(sse, args_inst.qradar_console)
            check_qradar_version(args_inst, api_client)
        else:
            handle_fatal_error(sse, True)
    except SdkFatalError as sfe:
        handle_fatal_error(sfe)

def check_app_status(args_inst, existing_api_client = None):
    retry = (existing_api_client is None)
    try:
        api_client = get_certified_api_client(args_inst)
        set_qradar_version(api_client)
        response = api_client.get(request_endpoint=ENDPOINT_APPLICATION.format(args_inst.application_id),
                                  request_headers=HEADERS_JSON)
        response_json = response.json()
        if (_qradar_version_ == '7.2.6'):
            app_status = response_json[0]['application_state']['status']
        else:
            app_status = response_json['application_state']['status']

        # See if we can get some extra status info
        if app_status == STATUS_CREATING or app_status == STATUS_UPGRADING:
            response = api_client.get(request_endpoint=ENDPOINT_APPLICATION_INSTALL_STATUS.format(args_inst.application_id),
                                      request_headers=HEADERS_JSON)
            task_status = response.json()['status']
            if task_status != STATUS_CREATING and task_status != STATUS_UPGRADING:
                app_status = app_status + ':' + task_status

        else:
            errors = response_json['application_state']['error_message']
            if len(errors) > 0:
                app_status = app_status + ':' + errors

        print args_inst.application_id + ':' + app_status
    except SdkServerSslError as sse:
        if retry:
            handle_ssl_error(sse, args_inst.qradar_console)
            check_app_status(args_inst, api_client)
        else:
            handle_fatal_error(sse, True)
    except SdkFatalError as sfe:
        handle_fatal_error(sfe)

def deploy(args_inst, existing_api_client = None):
    retry = (existing_api_client is None)
    try:
        if args_inst.debug:
            check_run_script_valid(args_inst.debug)
        check_zip_manifest_valid(args_inst.package)
        api_client = get_certified_api_client(args_inst)
        deploy_app(args_inst.package, args_inst.auth_user, api_client, args_inst.debug)
    except SdkServerSslError as sse:
        if retry:
            handle_ssl_error(sse, args_inst.qradar_console)
            deploy(args_inst, api_client)
        else:
            handle_fatal_error(sse, True)
    except (KeyError, ManifestException, SdkFatalError, IOError, ValueError) as e:
        handle_fatal_error(e)

def authorize(args_inst, existing_api_client = None):
    retry = (existing_api_client is None)
    try:
        api_client = get_certified_api_client(args_inst)
        authorize_app(args_inst.application_id, args_inst.auth_user, api_client)
    except SdkServerSslError as sse:
        if retry:
            handle_ssl_error(sse, args_inst.qradar_console)
            authorize(args_inst, api_client)
        else:
            handle_fatal_error(sse, True)
    except SdkFatalError as sfe:
        handle_fatal_error(sfe)

def cancel_app_install(args_inst, existing_api_client = None):
    retry = (existing_api_client is None)
    try:
        api_client = get_certified_api_client(args_inst)
        api_client.post(request_endpoint=ENDPOINT_APPLICATION_CANCEL.format(args_inst.application_id),
                        request_headers=HEADERS_JSON)
        print "Cancel request accepted for application {0}.".format(str(args_inst.application_id))
    except SdkServerSslError as sse:
        if retry:
            handle_ssl_error(sse, args_inst.qradar_console)
            cancel_app_install(args_inst, api_client)
        else:
            handle_fatal_error(sse, True)
    except SdkFatalError as sfe:
        handle_fatal_error(sfe)

def delete_app(args_inst, existing_api_client = None):
    retry = (existing_api_client is None)
    try:
        api_client = get_certified_api_client(args_inst)
        api_client.delete(request_endpoint=ENDPOINT_APPLICATION.format(args_inst.application_id))
        print "Application {0} has been deleted.".format(str(args_inst.application_id))
    except SdkServerSslError as sse:
        if retry:
            handle_ssl_error(sse, args_inst.qradar_console)
            delete_app(args_inst, api_client)
        else:
            handle_fatal_error(sse, True)
    except SdkFatalError as sfe:
        handle_fatal_error(sfe)
