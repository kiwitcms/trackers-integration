# Copyright (c) 2025 Frank Sommer <Frank.Sommer@sherpa-software.de>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

FROM python:3.11-slim

RUN mkdir -p /opt/trac/eggcache /opt/trac/products
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY kiwitcms.ini .
COPY start-tracd /opt/trac/
CMD ["/opt/trac/start-tracd"]
