# sfa
# install postGre
# config postGre
sudo -u postgres psql template1
##########################
psql (9.1.14)

Type "help" for help.

template1=# ALTER USER postgres with password '<PASSWORD>';

ALTER ROLE

template1=# \q

##########################
# start sfa
git clone https://github.com/DayoungKim/sfa

chmod 777 sfa

cd sfa

sfaadmin.py reg nuke

sfaadmin.py reg import

sudo sfa-config-tty #input openstack infomation
