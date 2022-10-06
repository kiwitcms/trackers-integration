FROM registry.access.redhat.com/ubi9/php-80

ADD mantisbt-2.25.5.zip .
RUN unzip mantisbt-*.zip && \
    mv mantisbt-*/ mantisbt/ && \
    rm -rf mantisbt/admin/

ADD config_inc.php /opt/app-root/src/mantisbt/config

CMD /usr/libexec/s2i/run
