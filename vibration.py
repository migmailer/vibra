import logging
import sys
import time
import threading
import RPi.GPIO as GPIO
import requests
import json
import tweepy
from time import localtime, strftime
import urllib
import paho.mqtt.publish as mqttpublish

from ConfigParser import SafeConfigParser
from tweepy import OAuthHandler as TweetHandler
from slackclient import SlackClient

def pushbullet(cfg, msg):
    try:
        data_send = {"type": "note", "title": ident, "body": msg}
        requests.post(
            'https://api.pushbullet.com/v2/pushes',
            data=json.dumps(data_send),
            headers={'Authorization': 'Bearer ' + cfg,
                     'Content-Type': 'application/json'})
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass

def pushover(user_key, app_key, msg):
    try:
        data_send = {"user": user_key, "token": app_key, "message": msg}
        requests.post(
            'https://api.pushover.net/1/messages.json',
            data=json.dumps(data_send),
            headers={'Content-Type': 'application/json'})
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass

def mqtt(msg):
    try:
        mqttpublish.single(mqtt_topic, msg, qos=0, retain=False, hostname=mqtt_hostname,
           port=1883, client_id=ident, keepalive=60, will=None, auth={'username': mqtt_username, 'password': mqtt_password},
           tls=None)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass

def mqtt_status(msg):
    try:
        mqttpublish.single(mqtt_topic + "/status", msg, qos=0, retain=False, hostname=mqtt_hostname,
           port=1883, client_id=ident, keepalive=10, will=None, auth={'username': mqtt_username, 'password': mqtt_password},
           tls=None)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass

def iftt(msg):
    try:
        iftt_url = "https://maker.ifttt.com/trigger/{}/with/key/{}".format(iftt_maker_channel_event,
                                                                           iftt_maker_channel_key)
        report = {"value1" : msg}
        resp = requests.post(iftt_url, data=report)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass

def slack_webhook(msg):

    try:
        payload = urllib.urlencode({'payload': '{"text": "' + msg+ '"}'})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        response = requests.request("POST", slack_webhook , data=payload, headers=headers)

    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass

def tweet(msg):
    try:
        # Twitter is the only API that NEEDS something like a timestamp,
        # since it will reject identical tweets.
        tweet = msg + ' ' + strftime("%Y-%m-%d %H:%M:%S", localtime())
        auth = TweetHandler(twitter_api_key, twitter_api_secret)
        auth.set_access_token(twitter_access_token,
                              twitter_access_token_secret)
        tweepy.API(auth).update_status(status=tweet)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass


def slack(msg):
    try:
        slack = msg + ' ' + strftime("%Y-%m-%d %H:%M:%S", localtime())
        sc = SlackClient(slack_api_token)
        sc.api_call(
            'chat.postMessage', channel='#random', text=slack)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass


def send_alert(message):
    if len(message) > 1:
        print message
        logger.info("Alert sent")
        if len(pushover_user_key) > 0 and len(pushover_app_key) > 0:
            pushover(pushover_user_key, pushover_app_key, message)
        if len(pushbullet_api_key) > 0:
            pushbullet(pushbullet_api_key, message)
        if len(pushbullet_api_key2) > 0:
            pushbullet(pushbullet_api_key2, message)
        if len(twitter_api_key) > 0:
            tweet(message)
        if len(slack_api_token) > 0:
            slack(message)
        if len (slack_webhook) > 0:
            slack_webhook(message)
        if len(iftt_maker_channel_key) > 0:
            iftt(message)
        if len(mqtt_topic) > 0:
            mqtt('{ "State": "' + message + '" }')


def send_appliance_active_message():
    send_alert(start_message)
    global appliance_active
    appliance_active = True


def send_appliance_inactive_message():
    send_alert(end_message)
    global appliance_active
    appliance_active = False

def vibrated(x):
    global vibrating
    global last_vibration_time
    global start_vibration_time
    global vibrate_count
    vibrate_count = vibrate_count + 1
#    print 'Vibrated'
    last_vibration_time = time.time()
    if not vibrating:
        start_vibration_time = last_vibration_time
        vibrating = True


def heartbeat():
    current_time = time.time()
#    logger.info("HB at {}".format(current_time))
    global vibrating
    global vibrate_count
    delta_vibration = last_vibration_time - start_vibration_time
    if (vibrating and delta_vibration > begin_seconds
            and not appliance_active):
        send_appliance_active_message()
    if (not vibrating and appliance_active
            and current_time - last_vibration_time > end_seconds):
        send_appliance_inactive_message()
    vibrating = current_time - last_vibration_time < 2
    threading.Timer(1, heartbeat).start()

def status():
    current_time = time.time()
#    logger.info("Status at {}".format(current_time))
    logger.info("Vibes: {}".format(vibrate_count))
    global vibrate_count
    mqtt_status('{ "value": ' + str(vibrate_count) + ' }')
    vibrate_count = 0
    threading.Timer(20, status).start()


if len(sys.argv) == 1:
    logger.error("No config file specified")
    sys.exit()

vibrating = False
vibrate_count = 0
appliance_active = False
last_vibration_time = time.time()
start_vibration_time = last_vibration_time

config = SafeConfigParser()
config.read(sys.argv[1])
sensor_pin = config.getint('main', 'SENSOR_PIN')
begin_seconds = config.getint('main', 'SECONDS_TO_START')
end_seconds = config.getint('main', 'SECONDS_TO_END')
pushbullet_api_key = config.get('pushbullet', 'API_KEY')

pushover_user_key = config.get('pushover', 'user_api_key')
pushover_app_key = config.get('pushover', 'app_api_key')

mqtt_hostname = config.get('mqtt', 'mqtt_hostname')
mqtt_topic = config.get('mqtt', 'mqtt_topic')
mqtt_username = config.get('mqtt', 'mqtt_username')
mqtt_password = config.get('mqtt', 'mqtt_password')

pushbullet_api_key2 = config.get('pushbullet', 'API_KEY2')
start_message = config.get('main', 'START_MESSAGE')
end_message = config.get('main', 'END_MESSAGE')
twitter_api_key = config.get('twitter', 'api_key')
twitter_api_secret = config.get('twitter', 'api_secret')
twitter_access_token = config.get('twitter', 'access_token')
twitter_access_token_secret = config.get('twitter', 'access_token_secret')
slack_api_token = config.get('slack', 'api_token')
slack_webhook = config.get('slack','webhook_url')
iftt_maker_channel_event = config.get('iftt','maker_channel_event')
iftt_maker_channel_key = config.get('iftt','maker_channel_key')

ident = config.get('main', 'Ident')

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(sensor_pin, GPIO.RISING)
GPIO.add_event_callback(sensor_pin, vibrated)

logger = logging.getLogger('vibration')
hdlr = logging.FileHandler('/config/' + ident + '.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

send_alert(config.get('main', 'BOOT_MESSAGE'))

logger.info('Running config file {} monitoring GPIO pin {}'\
      .format(sys.argv[1], str(sensor_pin)))

print('Running config file {} monitoring GPIO pin {}'\
      .format(sys.argv[1], str(sensor_pin)))

threading.Timer(1, heartbeat).start()
threading.Timer(10, status).start()
