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

cd sfa/sfa

sfaadmin.py reg nuke

sfaadmin.py reg import

sudo sfa-config-tty #input openstack infomation
##########################
# run sfa

sfaadmin.py registry register -t authority -x auth.name

sfaadmin.py registry register -t user -x auth.name.user -e user@email.address -k publickey.pub

sfi.py add slice_record.xml

# add sliver

sfi.py allocate slice_name rspec.rspec

# delete sliver

sfi.py delete slice_name

# list slice

sfi.py status slice_name
