echo "### Installing dependencies for remote runner, example plugin and tests ###"

sudo apt-get install rabbitmq-server
sudo -EH pip3 install --upgrade pika pytest entropy
