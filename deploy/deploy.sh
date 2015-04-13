# make sure in correct directory
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..

INSTALL_DIR="/home/cloo/repl/apps/catalogue/src/catalogue/"
APP_NAME="catalogue"

# prep sym links for gateway nginx
ln -sf $INSTALL_DIRdeploy/$APP_NAME-gate /home/cloo/repl/gateway/nginx/sites-available/$APP_NAME-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/$APP_NAME-gate /home/cloo/repl/gateway/nginx/sites-enabled/$APP_NAME-gate

# prep sym links for app servers supervisor and nginx
ln -sf $DIR/$APP_NAME.conf /home/cloo/repl/apps/supervisor/conf.d/$APP_NAME.conf
ln -sf $DIR/nginx/$APP_NAME-apps /home/cloo/repl/apps/nginx/sites-available/$APP_NAME-apps
ln -sf /home/cloo/repl/apps/nginx/sites-available/$APP_NAME-apps /home/cloo/repl/apps/nginx/sites-enabled/$APP_NAME-apps
# end of simple default stuff

# reload the nginx if syntax is OK, and gateway should now be prepped to serve the apps
sudo nginx -t && sudo nginx -s reload

# NOW DO WHATEVER INSTALLS AND DOWNLOADS CAN BE DONE INSIDE THE repl/apps FOLDER OF THIS APP
# if needing to install into the virtualenv, assume we are in one that was manually created on first install
. ../../bin/activate
pip install -e .

cd ../

# AND THEN replicate the repl folders across the infrastructure servers
/home/cloo/repl/replicate.sh

# NOW ISSUE ANY NECESSARY COMMANDS TO SETUP OR INSTALL DIRECTLY ON THE APPS SERVERS

# issue commands to the apps servers to get things running on them

# AND NOW RESTART SUPERVISOR FOR THE APP ON THE APPS MACHINES, THEN NGINX ON THE APPS MACHINES

# restart the supervisor script looking after this, on the apps machines
/home/cloo/repl/command.sh apps sudo supervisorctl reread $APP_NAME
/home/cloo/repl/command.sh apps sudo supervisorctl update $APP_NAME
/home/cloo/repl/command.sh apps sudo supervisorctl restart $APP_NAME
# reload the nginx on the apps
/home/cloo/repl/command.sh apps sudo nginx -t && sudo nginx -s reload

# APP SHOULD NOW BE UP AND RUNNING ON THE APPS MACHINES AND BEING SERVED BY THE GATEWAY

