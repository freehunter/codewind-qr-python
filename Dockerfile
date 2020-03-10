FROM centos:centos7.5.1804
ADD . /code
WORKDIR /code
USER root
RUN yum -y install epel-release && yum clean all
RUN yum -y install python-pip && yum clean all
RUN chmod 755 sdk
RUN sdk/install.sh
RUN pip install flask
CMD ["python", "app.py"]
EXPOSE 5000
