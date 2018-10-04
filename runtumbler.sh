docker run --privileged -d -it --name vibra2 -v "$PWD":/config vibration /config/vibration.py /config/vibra2.ini --restart always
