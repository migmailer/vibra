docker run --privileged -d -it --name vibra1 -v "$PWD":/config vibration /config/vibration.py /config/vibra1.ini --restart always
