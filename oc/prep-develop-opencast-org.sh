#!/bin/sh

scp podcast.yaml develop.opencast.org:/tmp
ssh develop.opencast.org sudo mv /tmp/podcast.yaml /srv/opencast/opencast-dist-allinone/etc/workflows/
scp podcast.properties develop.opencast.org:/tmp
ssh develop.opencast.org sudo mv /tmp/podcast.properties /srv/opencast/opencast-dist-allinone/etc/encoding/
