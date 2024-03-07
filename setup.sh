#Instrucciones para usar el script:

# Guarda este código en un archivo llamado setup.sh.
# Dale permisos de ejecución con el comando: chmod +x setup.sh.
# Ejecuta el script con: sudo ./setup.sh.

#!/bin/bash

# Actualizar los paquetes del sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev libcairo2-dev libgirepository1.0-dev python3-cryptography cython3 python3-numpy python3-pil python3-gi python3-gi-cairo gir1.2-gtk-3.0 libglib2.0-dev gcc pkg-config arandr python3-pygame portaudio19-dev python3-pil.imagetk libttspico-utils apache2 php avahi-daemon
sudo apt install python3-torch
sudo apt install python3-omegaconf
sudo apt install python3-pyaudio
sudo apt-get install python3-flask-cors
pip3 install --upgrade pip --break-system-packages
pip3 install librosa --break-system-packages
pip3 install pyttsx3 --break-system-packages

# Clonar el repositorio de GitHub
git clone https://github.com/gbibbo/pisoundsensing.git

# Cambiar al directorio clonado
cd pisoundsensing

# Actualizar pip y setuptools
pip3 install --upgrade pip setuptools wheel

# Instalar Flask y dependencias adicionales
pip3 install Flask Flask-CORS pycairo PyGObject

# Instalar requisitos desde el archivo
pip3 install -r requirements.txt
pip3 install --upgrade colorama

# Descargar el archivo .pth
wget https://zenodo.org/record/3576599/files/Cnn9_GMP_64x64_300000_iterations_mAP%3D0.37.pth?download=1

# Copiar y configurar archivo index.html
sudo cp index.html /var/www/html/index.html
sudo chown ai4s:ai4s /var/www/html/index.html
sudo chmod 644 /var/www/html/index.html

# Configurar los permisos de la carpeta /var/www/html
sudo chown -R ai4s:ai4s /var/www/html/
sudo chmod -R 775 /var/www/html/

# Configuración de scripts de Python para autoinicio
mkdir -p ~/.config/autostart

# Copiar y dar permisos de ejecución a los scripts
# sudo cp temperature.py run_sed_demo.sh /usr/local/bin/
sudo chown ai4s:ai4s /home/ai4s/pisoundsensing/temperature.py /home/ai4s/pisoundsensing/run_sed_demo.sh
sudo chmod +x /home/ai4s/pisoundsensing/temperature.py /home/ai4s/pisoundsensing/run_sed_demo.sh

# Crear archivos de autoinicio
echo -e "[Desktop Entry]\nType=Application\nName=Run Temperature\nExec=python3 /home/ai4s/pisoundsensing/temperature.py" > ~/.config/autostart/run_temperature.desktop
echo -e "[Desktop Entry]\nType=Application\nName=Run sed_demo\nExec=/home/ai4s/pisoundsensing/run_sed_demo.sh" > ~/.config/autostart/run_sed_demo.desktop

# Ajustar la propiedad y permisos de los archivos de autoinicio
sudo chown ai4s:ai4s ~/.config/autostart/run_temperature.desktop ~/.config/autostart/run_sed_demo.desktop
sudo chmod 644 ~/.config/autostart/*.desktop

# Mover el logo a la carpeta pública y ajustar permisos
sudo cp assets/logo.png /var/www/html/logo.png
sudo chown ai4s:ai4s /var/www/html/logo.png
sudo chmod 644 /var/www/html/logo.png

# Asegurarse de que el archivo state.json y otros archivos generados sean editables
touch /home/ai4s/pisoundsensing/state.json
sudo chown ai4s:ai4s /home/ai4s/pisoundsensing/state.json
sudo chmod 666 /home/ai4s/pisoundsensing/state.json

echo "piss" | sudo tee /etc/hostname
sudo sed -i 's/127.0.1.1.*/127.0.1.1\tpiss/g' /etc/hosts

# Reiniciar el sistema
sudo reboot

