cd /home/gregrs/fhodot || exit 1
echo "Copying production config files into repository"
# preserving permissions etc.
cp -p ../fhodot-production-config/config.py fhodot/ || exit 1
cp -p ../fhodot-production-config/imposm_config.json import/osm/ || exit 1
echo "Building UI static files"
npm run build || exit 1
echo "Copying UI static files to public_html"
find /home/gregrs/public_html/fhodot/* -maxdepth 0 \
	-not -name 'graphs' \
	-not -name 'summary.html' \
	-not -name '.htaccess' \
	-delete
cp fhodot/app/ui/dist/* /home/gregrs/public_html/fhodot/
touch /home/gregrs/public_html/wsgi-bin/fhodot.wsgi
