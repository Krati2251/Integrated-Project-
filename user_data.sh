#!/bin/bash
set -e

# Update system
yum update -y
yum install -y python3.11 python3.11-devel python3.11-pip git postgresql15-devel gcc curl

# Create app directory
mkdir -p /opt/finance-triage
cd /opt/finance-triage

# Clone repository (replace with your GitHub URL if needed)
# Alternatively, you can deploy code via CodeDeploy, S3, or manual SSH
if [ -z "$REPO_URL" ]; then
  REPO_URL="https://github.com/YOUR_USERNAME/finance-support-triage-agent-final-streamlit-1.git"
fi

# Clone the repo (set your branch if needed)
git clone --depth 1 $REPO_URL . || echo "Note: Could not clone repo. Deploy code manually via SSH."

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
if [ -f requirements.txt ]; then
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
fi

# Create systemd service for backend
cat > /etc/systemd/system/finance-backend.service <<'EOF'
[Unit]
Description=Finance Support Triage Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/finance-triage
Environment="PATH=/opt/finance-triage/venv/bin"
Environment="PORT=8000"
ExecStart=/opt/finance-triage/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend
cat > /etc/systemd/system/finance-frontend.service <<'EOF'
[Unit]
Description=Finance Support Triage Frontend (Streamlit)
After=network.target finance-backend.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/finance-triage
Environment="PATH=/opt/finance-triage/venv/bin"
Environment="STREAMLIT_SERVER_PORT=8501"
Environment="STREAMLIT_SERVER_ADDRESS=0.0.0.0"
Environment="STREAMLIT_SERVER_HEADLESS=true"
ExecStart=/opt/finance-triage/venv/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Fix permissions
chown -R ec2-user:ec2-user /opt/finance-triage

# Enable and start services (commented out because code may not be deployed yet)
# systemctl daemon-reload
# systemctl enable finance-backend.service finance-frontend.service
# systemctl start finance-backend.service
# systemctl start finance-frontend.service

# Log bootstrap completion
echo "✓ Bootstrap complete. App directory: /opt/finance-triage" >> /var/log/finance-bootstrap.log
echo "✓ Services configured: finance-backend, finance-frontend" >> /var/log/finance-bootstrap.log
echo "TODO: Deploy code and run: sudo systemctl start finance-backend finance-frontend" >> /var/log/finance-bootstrap.log
