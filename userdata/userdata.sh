#!/bin/bash
# Update the instance
sudo yum update -y

# Install git
sudo yum install git -y

# Install Python and pip
sudo yum install python3 -y

cd /home/ec2-user/fastapi_demo

python3 -m pip install -r requirements.txt

# Clone the git repository
git clone https://github.com/pybites/fastapi_demo.git /home/ec2-user/fastapi_demo

chown -R ec2-user:ec2-user /home/ec2-user/fastapi_demo/

echo '#!/bin/bash
cd /home/ec2-user/fastapi_demo
python3 -m uvicorn app:app --host 0.0.0.0 --port 80
' > /home/ec2-user/run_fastapi.sh
chmod +x /home/ec2-user/run_fastapi.sh
chown ec2-user:ec2-user /home/ec2-user/run_fastapi.sh

# Create a systemd service for your FastAPI application
echo '[Unit]
Description=FastAPI application
After=network.target

[Service]
ExecStart=/home/ec2-user/run_fastapi.sh
User=root
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
' > /etc/systemd/system/fastapi.service


# Start the FastAPI service
systemctl daemon-reload
systemctl start fastapi
systemctl enable fastapi