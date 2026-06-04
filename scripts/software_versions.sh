echo "Debian $(cat /etc/debian_version)"
python --version
echo "Node $(node --version)"
psql --version
echo "PostGIS $(psql -At -d gregrs_fhrs -c 'SELECT PostGIS_Version();')"
redis-server --version
go version
R --version | head -n 1
