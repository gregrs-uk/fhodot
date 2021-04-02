cd /home/gregrs/fhodot || exit 1
echo "Copying production config files into repository"
# preserving permissions etc.
cp -p ../fhodot-production-config/config.py fhodot/ || exit 1
cp -p ../fhodot-production-config/imposm_config.json import/osm/ || exit 1
echo "Building UI static files"
npm run build || exit 1
echo "Copying UI static files to public_html"
# not clearing directory first to avoid deleting graphs and summary.html
cp fhodot/app/ui/dist/* /home/gregrs/public_html/fhodot/
touch /home/gregrs/public_html/wsgi-bin/fhodot.wsgi
