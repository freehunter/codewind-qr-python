#!/usr/bin/python

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

import argparse
from appfw_sdk_lib.qradar_app_builder_funcs import create_workspace, package, deploy, authorize, run_app, check_qradar_version, check_app_status, cancel_app_install, delete_app

parser = argparse.ArgumentParser(prog='qradar_app_creator')
subparsers = parser.add_subparsers()

parser_create = subparsers.add_parser('create', help='Instantiate a new QRadar app workspace')
parser_create.add_argument("-w", "--workspace", action="store", dest="workspace", default='.', help="Path to workspace folder. Defaults to the current directory.")
parser_create.add_argument("-k", "--key", action="store", dest="key", default='', help="Application identifer key. Leave blank to allow the SDK to generate a key for your app.")
parser_create.set_defaults(function=create_workspace)

parser_package = subparsers.add_parser('package', help='Package app files into a zip archive')
parser_package.add_argument("-w", "--workspace", action="store", dest="workspace", default='.', help="Path to workspace folder. Defaults to the current directory.")
parser_package.add_argument("-p", "--package", action="store", dest="package", help="Package name destination, e.g. com.ibm.app.1.0.0.zip", required=True)
parser_package.set_defaults(function=package)

parser_deploy = subparsers.add_parser('deploy', help='Deploy app zip archive to QRadar appliance')
parser_deploy.add_argument("-p", "--package", action="store", dest="package", help="Package to deploy, e.g. com.ibm.app.1.0.0.zip", required=True)
parser_deploy.add_argument("-q", "--qradar-console", action="store", dest="qradar_console", help="Address of QRadar console to deploy to", required=True)
parser_deploy.add_argument("-u", "--user", action="store", dest="user", help="QRadar user", required=True)
parser_deploy.add_argument("-o", "--auth-user", action="store", dest="auth_user", help="QRadar app authorization user", required=False)
parser_deploy.add_argument("-d", "--debug", nargs='?', const="run.py", dest="debug", help="Path of run.py file that is dynamically added to the package zip before deployment. Defaults to run.py.")
parser_deploy.set_defaults(function=deploy)

parser_authorize = subparsers.add_parser('authorize', help='Finish deployment of an app by supplying an authorization user')
parser_authorize.add_argument("-q", "--qradar-console", action="store", dest="qradar_console", help="Address of QRadar console to deploy to", required=True)
parser_authorize.add_argument("-u", "--user", action="store", dest="user", help="QRadar user", required=True)
parser_authorize.add_argument("-a", "--application-id", action="store", dest="application_id", help="ID of the QRadar app to deploy", required=True)
parser_authorize.add_argument("-o", "--auth-user", action="store", dest="auth_user", help="QRadar app authorization user", required=False)
parser_authorize.set_defaults(function=authorize)

parser_run = subparsers.add_parser('run', help='Run a QRadar app locally')
parser_run.add_argument("-w", "--workspace", action="store", dest="workspace", default='.', help="Path to workspace folder. Defaults to the current directory.")
parser_run.add_argument("-r", "--run-script", action="store", dest="runscript", default='run.py', help="Name of script to execute when running the app locally. Defaults to run.py. Must exist in workspace folder.")
parser_run.add_argument("-e", "--enable_deps", action="store_true", dest="enable_deps", required=False, help="Attempt to run scripts under src_deps. Defaults to false.")
parser_run.set_defaults(function=run_app)

parser_version = subparsers.add_parser('version', help='Check QRadar version')
parser_version.add_argument("-q", "--qradar-console", action="store", dest="qradar_console", help="Address of QRadar console", required=True)
parser_version.add_argument("-u", "--user", action="store", dest="user", help="QRadar user", required=True)
parser_version.set_defaults(function=check_qradar_version)

parser_status = subparsers.add_parser('status', help='Check the status of an app')
parser_status.add_argument("-q", "--qradar-console", action="store", dest="qradar_console", help="Address of QRadar console", required=True)
parser_status.add_argument("-u", "--user", action="store", dest="user", help="QRadar user", required=True)
parser_status.add_argument("-a", "--application-id", action="store", dest="application_id", help="ID of the QRadar app to check", required=True)
parser_status.set_defaults(function=check_app_status)

parser_cancel = subparsers.add_parser('cancel', help='Cancel an app install')
parser_cancel.add_argument("-q", "--qradar-console", action="store", dest="qradar_console", help="Address of QRadar console", required=True)
parser_cancel.add_argument("-u", "--user", action="store", dest="user", help="QRadar user", required=True)
parser_cancel.add_argument("-a", "--application-id", action="store", dest="application_id", help="ID of the QRadar app to cancel", required=True)
parser_cancel.set_defaults(function=cancel_app_install)

parser_delete = subparsers.add_parser('delete', help='Delete an app')
parser_delete.add_argument("-q", "--qradar-console", action="store", dest="qradar_console", help="Address of QRadar console", required=True)
parser_delete.add_argument("-u", "--user", action="store", dest="user", help="QRadar user", required=True)
parser_delete.add_argument("-a", "--application-id", action="store", dest="application_id", help="ID of the QRadar app to delete", required=True)
parser_delete.set_defaults(function=delete_app)

args = parser.parse_args()
args.function(args)
