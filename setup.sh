# Instructions for using the script:

# Save this code in a file named setup.sh.
# Give it execute permissions with the command: chmod +x setup.sh.
# Run the script with: bash ./setup.sh.

#!/bin/bash

# Upgrade system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev libcairo2-dev libgirepository1.0-dev python3-cryptography cython3 python3-numpy python3-pil python3-gi python3-gi-cairo gir1.2-gtk-3.0 libglib2.0-dev gcc pkg-config arandr python3-pygame portaudio19-dev python3-pil.imagetk libttspico-utils apache2 php avahi-daemon
sudo apt install python3-torch
sudo apt install python3-omegaconf
sudo apt install python3-pyaudio
sudo apt-get install python3-flask-cors
pip3 install --upgrade pip --break-system-packages
pip3 install librosa --break-system-packages
pip3 install pyttsx3 --break-system-packages

# Cloning GitHub repository
git clone https://github.com/gbibbo/pisoundsensing.git

# Change to the cloned directory
cd pisoundsensing

# Update pip and setuptools
pip3 install --upgrade pip setuptools wheel

# Install Flask and additional dependencies
pip3 install Flask Flask-CORS pycairo PyGObject

# Install requirements from file
pip3 install -r requirements.txt
pip3 install --upgrade colorama

# Download .pth file
wget https://zenodo.org/record/3576599/files/Cnn9_GMP_64x64_300000_iterations_mAP%3D0.37.pth?download=1

# Copy and configure index.html file
sudo cp index.html /var/www/html/index.html
sudo chown ai4s:ai4s /var/www/html/index.html
sudo chmod 644 /var/www/html/index.html

# Set permissions for /var/www/html folder
sudo chown -R ai4s:ai4s /var/www/html/
sudo chmod -R 775 /var/www/html/

# Configuring Python scripts for auto-starting
mkdir -p ~/.config/autostart

# Copying and giving execution permissions to scripts
# sudo cp temperature.py run_sed_demo.sh /usr/local/bin/
sudo chown ai4s:ai4s /home/ai4s/pisoundsensing/temperature.py /home/ai4s/pisoundsensing/run_sed_demo.sh
sudo chmod +x /home/ai4s/pisoundsensing/temperature.py /home/ai4s/pisoundsensing/run_sed_demo.sh

# Create autostart files
echo -e "[Desktop Entry]\nType=Application\nName=Run Temperature\nExec=python3 /home/ai4s/pisoundsensing/temperature.py" > ~/.config/autostart/run_temperature.desktop
echo -e "[Desktop Entry]\nType=Application\nName=Run sed_demo\nExec=/home/ai4s/pisoundsensing/run_sed_demo.sh" > ~/.config/autostart/run_sed_demo.desktop

# Set ownership and permissions of autostart files
sudo chown ai4s:ai4s ~/.config/autostart/run_temperature.desktop ~/.config/autostart/run_sed_demo.desktop
sudo chmod 644 ~/.config/autostart/*.desktop

# Move logo to public folder and set permissions
sudo cp sed_demo/assets/logo.png /var/www/html/logo.png
sudo chown ai4s:ai4s /var/www/html/logo.png
sudo chmod 644 /var/www/html/logo.png

# Ensure that the state.json file and other generated files are editable.
touch /home/ai4s/pisoundsensing/state.json
sudo chown ai4s:ai4s /home/ai4s/pisoundsensing/state.json
sudo chmod 666 /home/ai4s/pisoundsensing/state.json

# Change hostname
echo "piss" | sudo tee /etc/hostname
sudo sed -i 's/127.0.1.1.*/127.0.1.1\tpiss/g' /etc/hosts

# Reboot the system
sudo reboot

