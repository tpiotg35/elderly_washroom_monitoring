import time
import grovepi
import datetime
import ssl
import json
import paho.mqtt.client as mqtt

# TODO: Name of our Raspberry Pi, also known as our "Thing Name"
deviceName = "g27_pi"
# TODO: Public certificate of our Raspberry Pi, as provided by AWS IoT.
deviceCertificate = "09ad9c1d6a-certificate.pem.crt"
# TODO: Private key of our Raspberry Pi, as provided by AWS IoT.
devicePrivateKey = "09ad9c1d6a-private.pem.key"
# Root certificate to authenticate AWS IoT when we connect to their server.
awsCert = "aws-iot-rootCA.crt"
 
# Connect the Grove PIR Motion Sensor to digital port D3
pir_sensor = 3
led = 4
buzzer = 2
current_state = 0
daily_counter = 0
daily_previous = 0
now = datetime.datetime.now()
start = time.time()
end = time.time()
elapsed_time = 0
start_time = 0
isConnected = False

grovepi.pinMode(pir_sensor,"INPUT")
grovepi.pinMode(led,"OUTPUT")
grovepi.pinMode(buzzer,"OUTPUT")

# This is called when we are connected to AWS IoT via MQTT.
def on_connect(client2, userdata, flags, rc):
    print("Connected to AWS IoT...")
    # Subscribe to our MQTT topic so that we will receive notifications of updates.
    client2.subscribe("$aws/things/" + deviceName + "/shadow/update")
    global isConnected
    isConnected = True

# This is called when we receive a subscription notification from AWS IoT.
def on_message(client2, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


# Print out log messages for tracing.
def on_log(client2, userdata, level, buf):
    print("Log: " + buf)

# Create an MQTT client for connecting to AWS IoT via MQTT.
client = mqtt.Client("awsiot")
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log

# Set the certificates and private key for connecting to AWS IoT.  TLS 1.2 is mandatory for AWS IoT and is supported
# only in Python 3.4 and later, compiled with OpenSSL 1.0.1 and later.
client.tls_set(awsCert, deviceCertificate, devicePrivateKey, ssl.CERT_REQUIRED, ssl.PROTOCOL_TLSv1_2)

# Connect to AWS IoT server.  Use AWS command line "aws iot describe-endpoint" to get the address.
print("Connecting to AWS IoT...")
client.connect("A1P01IYM2DOZA0.iot.us-west-2.amazonaws.com", 8883, 60)

# Start a background thread to process the MQTT network commands concurrently, including auto-reconnection.
client.loop_start()

while True:
    try:
        # If we are not connected yet to AWS IoT, wait 1 second and try again.
        if not isConnected:
            time.sleep(1)
            continue

        grovepi.digitalWrite(led,0)
        grovepi.digitalWrite(buzzer,0)

        # Sense motion, usually human, within the target range
        if grovepi.digitalRead(pir_sensor):
            current_state=current_state+1
            if current_state == 1:
                start_time = time.time()
                elapsed_time = int(time.time() - start_time)
                print ('-')
                print ('Elderly has entered the washroom.')
                print ("Date: %s/%s/%s" % (now.day, now.month, now.year))
                print ("Time: %s:%s:%s" % (now.hour, now.month, now.second))
                # Read sensor values. Prepare our sensor data in JSON format.
                payload = json.dumps({
                    "state": {
                        "reported": {
                            "motion": current_state,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "elapsed_time": elapsed_time,
                        }
                    }
                })
                print("Sending sensor data to AWS IoT: ", payload)

                # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
                client.publish("$aws/things/" + deviceName + "/shadow/update", payload)
                print("Sent to AWS IoT")

            elif current_state == 2:
                elapsed_time = int(time.time() - start_time)
                print ('-')
                print ('Elderly has exited the washroom.')
                print ("Date: %s/%s/%s" % (now.day, now.month, now.year))
                print ("Time: %s:%s:%s" % (now.hour, now.month, now.second))
                print ('Time taken: ', elapsed_time, 'seconds')
                daily_counter = daily_previous + 1
                print ('Number of washroom visits: ', daily_counter)
                daily_previous = daily_previous + 1
                payload = json.dumps({
                    "state": {
                        "reported": {
                            "motion": current_state,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "elapsed_time": elapsed_time,
                        }
                    }
                })
                print("Sending sensor data to AWS IoT: ", payload)

                # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
                client.publish("$aws/things/" + deviceName + "/shadow/update", payload)
                print("Sent to AWS IoT")
                current_state = 0
                start_time = 0
                elapsed_time = 0
                grovepi.digitalWrite(led,0)
                grovepi.digitalWrite(buzzer,0)

            time.sleep(3)

        else:
            if current_state != 0:
                elapsed_time = int(time.time() - start_time)
                # Read sensor values. Prepare our sensor data in JSON format.
                payload = json.dumps({
                    "state": {
                        "reported": {
                            "motion": current_state,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "elapsed_time": elapsed_time,
                        }
                    }
                })
                print("Sending sensor data to AWS IoT: ", payload)

                # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
                client.publish("$aws/things/" + deviceName + "/shadow/update", payload)
                print("Sent to AWS IoT")

            print ('-')
            print ('Current State: ', current_state)
            print ('Elapsed time: ', elapsed_time)
            time.sleep(1)
            #For demonstration purpose, the threshold for warning is set at 10 seconds.
            if elapsed_time > 10:
                grovepi.digitalWrite(led,1)
                grovepi.digitalWrite(buzzer,1)
                print ('Warning! Elderly is taking too long!')


        # if your hold time is less than this, you might not see as many detections
        time.sleep(.3)

        # Read sensor values. Prepare our sensor data in JSON format.
        #payload = json.dumps({
        #    "state": {
        #        "reported": {
        #            "motion": current_state,
        #            "timestamp": datetime.datetime.now().isoformat(),
        #            "elapsed_time": elapsed_time,
        #        }
        #    }
        #})
        #print("Sending sensor data to AWS IoT: ", payload)

        # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
        #client.publish("$aws/things/" + deviceName + "/shadow/update", payload)
        #print("Sent to AWS IoT")

        # Wait 1 second before sending the next set of sensor data.
        #time.sleep(1)

    except IOError:
        print ("Error")

