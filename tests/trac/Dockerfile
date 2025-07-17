# Copyright (c) 2025 Frank Sommer <Frank.Sommer@sherpa-software.de>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

FROM python:3.11

RUN pip install psycopg2-binary passlib trac trac_ticketrpc
RUN mkdir /opt/trac /opt/trac/eggcache /opt/trac/projects
COPY start-tracd /opt/trac/
COPY trac.ini /opt/trac/
COPY htpwd /opt/trac/.htpwd
COPY kiwitcms-logo.png /opt/trac/
CMD /opt/trac/start-tracd
