# Copyright (c) 2022-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

FROM registry.access.redhat.com/ubi9/php-80

ADD mantisbt-2.26.2.zip .
RUN unzip mantisbt-*.zip && mv mantisbt-*/ mantisbt/

# Note: we still need to perform the install procedure b/c
# it will create the database. This is part of initialize-data!
ADD config_inc.php /opt/app-root/src/mantisbt/config

CMD /usr/libexec/s2i/run
