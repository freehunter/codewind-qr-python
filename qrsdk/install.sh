#!/bin/bash

# (C) Copyright IBM Corp. 2015, 2016
# The source code for this program is not published or
# otherwise divested of its trade secrets, irrespective of
# what has been deposited with the US Copyright Office.

QRADAR_APP_CREATOR=/usr/local/bin/qradar_app_creator
INSTALL_DIR=/usr/local/etc/QRadarAppSDK
CREATE_WORKSPACE=$INSTALL_DIR/bin/create_workspace.sh
RUN_APP=$INSTALL_DIR/bin/run_app.sh
SDK_README=$INSTALL_DIR/README.html
PIP_WHEEL=pip-18.0-py2.py3-none-any.whl

# PIP MODULES columns
# extra pip flags | linux ucs4 | linux ucs2 | mac ucs4 | mac ucs2 | install location
PIP_MODULES=(
 "--upgrade|virtualenv-12.0.7-py2.py3-none-any.whl|virtualenv-12.0.7-py2.py3-none-any.whl|virtualenv-12.0.7-py2.py3-none-any.whl|virtualenv-12.0.7-py2.py3-none-any.whl|sdk"
 "--upgrade|repoze.lru-0.6-py2-none-any.whl|repoze.lru-0.6-py2-none-any.whl|repoze.lru-0.6-py2-none-any.whl|repoze.lru-0.6-py2-none-any.whl|sdk"
 "--upgrade|argparse-1.3.0.tar.gz|argparse-1.3.0.tar.gz|argparse-1.3.0.tar.gz|argparse-1.3.0.tar.gz|workspace"
 "--upgrade|jsonschema-2.4.0-py2.py3-none-any.whl|jsonschema-2.4.0-py2.py3-none-any.whl|jsonschema-2.4.0-py2.py3-none-any.whl|jsonschema-2.4.0-py2.py3-none-any.whl|sdk"
 "--upgrade|ordereddict-1.1-py2-none-any.whl|ordereddict-1.1-py2-none-any.whl|ordereddict-1.1-py2-none-any.whl|ordereddict-1.1-py2-none-any.whl|workspace"
 "|enum34-1.1.6-py2-none-any.whl|enum34-1.1.6-py2-none-any.whl|enum34-1.1.6-py2-none-any.whl|enum34-1.1.6-py2-none-any.whl|workspace"
 "--upgrade|pyparsing-2.2.0-py2.py3-none-any.whl|pyparsing-2.2.0-py2.py3-none-any.whl|pyparsing-2.2.0-py2.py3-none-any.whl|pyparsing-2.2.0-py2.py3-none-any.whl|workspace"
 "--upgrade|pycparser-2.17.tar.gz|pycparser-2.17.tar.gz|pycparser-2.17.tar.gz|pycparser-2.17.tar.gz|workspace"
 "--upgrade|asn1crypto-0.22.0-py2.py3-none-any.whl|asn1crypto-0.22.0-py2.py3-none-any.whl|asn1crypto-0.22.0-py2.py3-none-any.whl|asn1crypto-0.22.0-py2.py3-none-any.whl|workspace"
 "--upgrade|ipaddress-1.0.18-py2-none-any.whl|ipaddress-1.0.18-py2-none-any.whl|ipaddress-1.0.18-py2-none-any.whl|ipaddress-1.0.18-py2-none-any.whl|workspace"
 "--upgrade|six-1.10.0.tar.gz|six-1.10.0.tar.gz|six-1.10.0.tar.gz|six-1.10.0.tar.gz|workspace"
 "|packaging-16.8-py2.py3-none-any.whl|packaging-16.8-py2.py3-none-any.whl|packaging-16.8-py2.py3-none-any.whl|packaging-16.8-py2.py3-none-any.whl|workspace"
 "--upgrade|setuptools-17.0.tar.gz|setuptools-17.0.tar.gz|setuptools-17.0.tar.gz|setuptools-17.0.tar.gz|workspace"
 "|cffi-1.10.0-cp27-cp27mu-manylinux1_x86_64.whl|cffi-1.10.0-cp27-cp27m-manylinux1_x86_64.whl|cffi-1.10.0-cp27-cp27mu-macosx_10_10_x86_64.whl|cffi-1.10.0-cp27-cp27m-macosx_10_6_intel.whl|workspace"
 "--upgrade|idna-2.6-py2.py3-none-any.whl|idna-2.6-py2.py3-none-any.whl|idna-2.6-py2.py3-none-any.whl|idna-2.6-py2.py3-none-any.whl|workspace"
 "|cryptography-1.8.1-cp27-cp27mu-linux_x86_64.whl|cryptography-1.8.1-cp27-cp27m-linux_x86_64.whl|cryptography-1.8.1-cp27-cp27mu-macosx_10_10_x86_64.whl|cryptography-1.8.1-cp27-cp27m-macosx_10_6_intel.whl|workspace"
 "|pyOpenSSL-17.0.0-py2.py3-none-any.whl|pyOpenSSL-17.0.0-py2.py3-none-any.whl|pyOpenSSL-17.0.0-py2.py3-none-any.whl|pyOpenSSL-17.0.0-py2.py3-none-any.whl|workspace"
 "|click-6.6.tar.gz|click-6.6.tar.gz|click-6.6.tar.gz|click-6.6.tar.gz|workspace"
 "|dnspython-1.15.0.zip|dnspython-1.15.0.zip|dnspython-1.15.0.zip|dnspython-1.15.0.zip|workspace"
 "|chardet-3.0.4-py2.py3-none-any.whl|chardet-3.0.4-py2.py3-none-any.whl|chardet-3.0.4-py2.py3-none-any.whl|chardet-3.0.4-py2.py3-none-any.whl|workspace"
 "|certifi-2017.7.27.1-py2.py3-none-any.whl|certifi-2017.7.27.1-py2.py3-none-any.whl|certifi-2017.7.27.1-py2.py3-none-any.whl|certifi-2017.7.27.1-py2.py3-none-any.whl|workspace"
 "|urllib3-1.22-py2.py3-none-any.whl|urllib3-1.22-py2.py3-none-any.whl|urllib3-1.22-py2.py3-none-any.whl|urllib3-1.22-py2.py3-none-any.whl|workspace"
 "|requests-2.18.4.tar.gz|requests-2.18.4.tar.gz|requests-2.18.4.tar.gz|requests-2.18.4.tar.gz|workspace"
 "|MarkupSafe-0.23.tar.gz|MarkupSafe-0.23.tar.gz|MarkupSafe-0.23.tar.gz|MarkupSafe-0.23.tar.gz|workspace"
 "|Werkzeug-0.12.1.tar.gz|Werkzeug-0.12.1.tar.gz|Werkzeug-0.12.1.tar.gz|Werkzeug-0.12.1.tar.gz|workspace"
 "|Jinja2-2.7.3.tar.gz|Jinja2-2.7.3.tar.gz|Jinja2-2.7.3.tar.gz|Jinja2-2.7.3.tar.gz|workspace"
 "|itsdangerous-0.24.tar.gz|itsdangerous-0.24.tar.gz|itsdangerous-0.24.tar.gz|itsdangerous-0.24.tar.gz|workspace"
 "|Flask-0.12.tar.gz|Flask-0.12.tar.gz|Flask-0.12.tar.gz|Flask-0.12.tar.gz|workspace"
 "|pycrypto-2.6.1-cp27-cp27mu-linux_x86_64.whl|pycrypto-2.6.1-cp27-cp27m-linux_x86_64.whl|pycrypto-2.6.1-cp27-none-macosx_10_12_intel.whl|pycrypto-2.6.1-cp27-none-macosx_10_12_intel.whl|workspace"
)


check_caller_is_root()
{
    if [ "$(id -u)" != "0" ]
    then
        echo "Please run this installer as root" 1>&2
        exit 1
    fi
}


remove_previous_install()
{
    rm -rf $INSTALL_DIR
    rm -f $QRADAR_APP_CREATOR
}


install_files()
{
    mkdir -p $INSTALL_DIR
    ZIP_DIR=`dirname "$0"`
    cp -r $ZIP_DIR/bin $INSTALL_DIR
    cp -r $ZIP_DIR/template $INSTALL_DIR
    cp -r $ZIP_DIR/src_packages $INSTALL_DIR
    cp -r $ZIP_DIR/sample_apps $INSTALL_DIR
    cp -r $ZIP_DIR/validation $INSTALL_DIR
    cp -r $ZIP_DIR/README.html $INSTALL_DIR 2>/dev/null
    cp -r $ZIP_DIR/get-pip.py $INSTALL_DIR/bin
}


initialize_bash_script()
{
    echo "#!/bin/bash" >$1
    echo >>$1
}


append_pip_module_list()
{
    echo "PIP_MODULES=(" >>$1
    for ((i=0; i < ${#PIP_MODULES[@]}; i++))
    do
        echo \"${PIP_MODULES[$i]}\" >>$1
    done
    echo ")" >>$1

    cat <<CUT_EOF >>$1

get_pip_module()
{
    echo \$1 | cut -d'|' -f\$2
}

CUT_EOF
}


append_python_version_check()
{
    cat <<PYTHON_VERSION_EOF >>$1
python_version_output=\$(python --version 2>&1)

if [ \$? -e 0 ]
then
    echo "This SDK requires a Python 3 interpreter with version 3 or greater."
    exit 1
fi

python_version=\$(echo \$python_version_output | awk '{print \$2}')

IFS='.' read major minor patch<<<"\$python_version"

if [ -z "\$patch" ]
then
    patch=0
fi

if [ "\$major" -eq "2" ] && ([ "\$minor" -gt "7" ] || ([ "\$minor" -eq "7" ] && [ "\$patch" -ge "9" ]))
then
    echo "Using Python version \$python_version"
else
    echo "Found Python version \$python_version. This SDK requires a Python 2 version with version 2.7.9 or greater."
    exit 1
fi

PYTHON_VERSION_EOF
}


append_get_pip_major_version()
{
    cat <<PIP_VERSION_EOF >>$1
get_pip_major_version()
{
    pip2 --version | cut -f2 -d' ' | cut -d'.' -f1
}

PIP_VERSION_EOF
}


append_pip_install_check()
{
    cat <<PIP_INSTALL_EOF >>$1
pip2 --version >/dev/null 2>&1

if [ \$? -ne 0 ]
then
    echo "Installing pip"
    python $INSTALL_DIR/bin/get-pip.py --no-index --find-links=$INSTALL_DIR/src_packages
else
    pip_version=\$(get_pip_major_version)

    if [[ \$pip_version -lt 9 ]]
    then
        echo "Detected major version of pip: \$pip_version. This SDK requires pip version 9 or greater."
        exit 1
    fi
fi

PIP_INSTALL_EOF
}


append_pip_upgrade_check()
{
    cat <<PIP_UPGRADE_EOF >>$1
pip_version=\$(get_pip_major_version)

if [[ \$pip_version -lt 18 ]]
then
    echo "Detected major version of pip: \$pip_version. Upgrading pip."
    python -m pip install --no-index --upgrade $INSTALL_DIR/src_packages/$PIP_WHEEL
fi

PIP_UPGRADE_EOF
}


append_skip_module_false()
{
    cat <<SKIP_FALSE_EOF >>$1
skip_module()
{
    false
}

SKIP_FALSE_EOF
}


append_skip_module_sdk()
{
    cat <<SKIP_SDK_EOF >>$1
skip_module()
{
    INSTALL_LOCATION=\`get_pip_module \$1 6 \`
    [ "\${INSTALL_LOCATION}" = "sdk" ]
}

SKIP_SDK_EOF
}


append_invoke_sdk()
{
    cat <<SDK_EOF >>$QRADAR_APP_CREATOR
export QRADAR_APPFW_SDK=true
python $INSTALL_DIR/bin/qradar_app_builder.py "\$@"

SDK_EOF
}

    
append_virtual_env_activate()
{
    cat <<VENV_EOF >>$1
cd "\$1"
virtualenv qradar_appfw_venv
source qradar_appfw_venv/bin/activate

VENV_EOF
}


append_pip_modules_install()
{
    cat <<PIP_INSTALL_EOF >>$1
is_python_ucs2()
{
    [ \`python -c "import sys;print sys.maxunicode" \` -eq 65535 ]
}

is_mac_os()
{
    [[ "\$OSTYPE" = *"darwin"* ]]
}

PIP_USER_OPTION=$2
PIP_MODULE_ARR=( \$(pip2 list --format=freeze | cut -d'=' -f1) )
MODULE_INSTALL=0

for ((i=0; i < \${#PIP_MODULES[@]}; i++))
do
    PIP_MODULE_NAME=\`get_pip_module \${PIP_MODULES[\$i]} 2 | cut -d'-' -f1\`

    # argparse does not show up in pip list
    if [[ \${PIP_MODULE_NAME} = "argparse" ]]
    then
        continue
    fi

    if skip_module \${PIP_MODULES[\$i]}
    then
        continue
    fi

    FOUND=0
    for ((j=0; j < \${#PIP_MODULE_ARR[@]}; j++))
    do
        if [[ "\${PIP_MODULE_ARR[\$j]}" = "\${PIP_MODULE_NAME}" ]]
        then
            FOUND=1
            break
        fi
    done

    if [[ \$FOUND -eq 0 ]]
    then
        echo "\${PIP_MODULE_NAME}" is not installed
        MODULE_INSTALL=1
    fi
done

if [ \$MODULE_INSTALL -eq 1 ]
then
    if is_python_ucs2
    then
        echo "A UCS2 version of python was found";
    else
        echo "A UCS4 version of python was found";
    fi

    for ((i=0; i < \${#PIP_MODULES[@]}; i++))
    do
        if skip_module \${PIP_MODULES[\$i]}
        then
            continue
        fi

        if is_python_ucs2
        then
            if is_mac_os
            then
                PIP_MODULES_COLUMN=5
            else
                PIP_MODULES_COLUMN=3
            fi
        else
            if is_mac_os
            then
                PIP_MODULES_COLUMN=4
            else
                PIP_MODULES_COLUMN=2
            fi
        fi

        PIP_MODULE=\`get_pip_module \${PIP_MODULES[\$i]} \$PIP_MODULES_COLUMN \`
        UPGRADE_OPTION=\`get_pip_module \${PIP_MODULES[\$i]} 1 \`

        INSTALL_LINE="pip2 install --no-index \${PIP_USER_OPTION} \${UPGRADE_OPTION} ${INSTALL_DIR}/src_packages/\${PIP_MODULE}"
        echo \${INSTALL_LINE}

        \${INSTALL_LINE}

        PIP_ERROR=\$?
        if [ \$PIP_ERROR -ne 0 ]
        then
            echo "Pip install failed with code \${PIP_ERROR}"
            exit \$PIP_ERROR
        fi
    done
fi

PIP_INSTALL_EOF
}


generate_qradar_app_creator_script()
{
    initialize_bash_script $QRADAR_APP_CREATOR
    append_pip_module_list $QRADAR_APP_CREATOR
    append_python_version_check $QRADAR_APP_CREATOR
    append_get_pip_major_version $QRADAR_APP_CREATOR
    append_pip_install_check $QRADAR_APP_CREATOR
    append_skip_module_false $QRADAR_APP_CREATOR
    append_pip_modules_install $QRADAR_APP_CREATOR "--user"
    append_invoke_sdk
    chmod +x $QRADAR_APP_CREATOR
}


generate_create_workspace_script()
{
    initialize_bash_script $CREATE_WORKSPACE
    append_pip_module_list $CREATE_WORKSPACE
    append_virtual_env_activate $CREATE_WORKSPACE
    append_get_pip_major_version $CREATE_WORKSPACE
    append_pip_upgrade_check $CREATE_WORKSPACE
    append_skip_module_sdk $CREATE_WORKSPACE
    append_pip_modules_install $CREATE_WORKSPACE
    chmod +x $CREATE_WORKSPACE
}


generate_run_app_script()
{
    initialize_bash_script $RUN_APP

    cat <<RUN_EOF >>$RUN_APP
source "\$1"/qradar_appfw_venv/bin/activate

cd "\$1"
RUN_SRC_DEPS=0

if [ -z "\$3" ]
then
    echo "SRC_DEPS will not be executed"
else
    if [ "\$3" = "True" ]
    then
        RUN_SRC_DEPS=1
        echo "SRC_DEPS will be executed"
    fi
fi

# install rpms
if [ -f src_deps/rpms/ordering.txt ]
then
    if [ \$RUN_SRC_DEPS ]
    then
        echo "Found src_deps/rpms/ordering.txt file"
        for line in \$(cat src_deps/rpms/ordering.txt)
        do
            echo "RPMs Need to be installed as root. Quit now if you do not want to install them"
            read -n1 -r -p "Press any key to continue..." key
            sudo rpm -Uvh src_deps/rpms/\$line
        done
    else
        echo "Found src_deps/rpms/ordering.txt file, you will need to install these rpms manually ..."
        for line in \$(cat src_deps/rpms/ordering.txt)
        do
            echo rpm -Uvh src_deps/rpms/\$line
        done
    fi
else
    if ls src_deps/rpms/*.rpm 1>/dev/null 2>&1
    then
        if [ \$RUN_SRC_DEPS ]
        then
            echo "Found src_deps/rpms/*rpm file"
            rpm -Uvh src_deps/rpms/*.rpm
        else
            echo "Found src_deps/rpms/*rpm file, you will need to make sure you have installed this rpm ..."
            echo rpm -Uvh src_deps/rpms/*.rpm
        fi
    fi
fi

# install python pip packages
if [ -f src_deps/pip/ordering.txt ]
then
    if [ \$RUN_SRC_DEPS ]
    then
        echo "Found src_deps/pip/ordering.txt file"
        for line in \$(cat src_deps/pip/ordering.txt)
        do
            pip2 install src_deps/pip/\$line
        done
    else
        echo "Found src_deps/pip/ordering.txt file, you will need to install these pip packages manually ..."
        for line in \$(cat src_deps/pip/ordering.txt)
        do
            echo pip2 install src_deps/pip/\$line
        done
    fi
else
    if ls src_deps/pip/*.whl 1> /dev/null 2>&1
    then
        if [ \$RUN_SRC_DEPS ]
        then
            echo "Found src_deps/pip/*whl file"
            pip2 install src_deps/pip/*.whl
        else
            echo "Found src_deps/pip/*whl file, you will need to install these pip packages manually ..."
            echo pip2 install src_deps/pip/*.whl
        fi
    fi
    if ls src_deps/pip/*.tar.gz 1> /dev/null 2>&1
    then
        if [ \$RUN_SRC_DEPS ]
        then
            echo "Found src_deps/pip/*tar.gz file"
            pip2 install src_deps/pip/*.tar.gz
        else
            echo "Found src_deps/pip/*tar.gz file, you will need to install these pip packages manually ..."
            echo pip2 install src_deps/pip/*.tar.gz
        fi
    fi
fi

# install other stuff
if [ -f src_deps/init/ordering.txt ]
then
    if [ \$RUN_SRC_DEPS ]
    then
        echo "Found src_deps/init/ordering.txt"
        while read line || [[ -n "\$line" ]]
        do
            \$line;
        done < src_deps/init/ordering.txt
    else
        echo "Found src_deps/init/ordering.txt, you will need to manually install these actions ..."
        while read line || [[ -n "\$line" ]]
        do
            echo \$line;
        done < src_deps/init/ordering.txt
    fi
fi

# make any background processes executable
if [ -d /src_deps/services ]
then
    Log "Found /src_deps/services directory, giving scripts executable permissions ..."
    if [ \$RUN_SRC_DEPS ]
    then
        # set executable file permissions for files in this folder
        for fileName in /src_deps/services/*
        do
            chmod +x $fileName
        done
    else
        # set executable file permissions for files in this folder
        for fileName in /src_deps/services/*
        do
            echo chmod +x $fileName
        done
    fi
fi

if [ -z "\$2" ]
then
    python "\$1"/run.py
else
    python "\$2"
fi

RUN_EOF

    chmod +x $RUN_APP
}


open_readme()
{
    if which xdg-open &>/dev/null
    then
        xdg-open $SDK_README &>/dev/null &
    else
        open $SDK_README &>/dev/null &
    fi
}


check_caller_is_root
echo "========== REMOVING PREVIOUS SDK =============="
remove_previous_install
echo "========== INSTALLING SDK RESOURCES ==========="
install_files
echo "========== WRITING OS-SPECIFIC UTILS =========="
generate_qradar_app_creator_script
generate_create_workspace_script
generate_run_app_script
echo "========== INSTALLED SDK SUCCESSFULLY ========="
open_readme
