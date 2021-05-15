#!/usr/bin/env python3
# Copyright Notice:
# Copyright 2017-2019 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Event-Listener/blob/m-ster/LICENSE.md
import argparse
import json
import logging
import logging.config
import os
import signal
import socket
import ssl
import sys
import threading
import traceback
from datetime import datetime as DT
from elasticsearch import Elasticsearch, helpers
import configparser
import requests
import pravega_client
### Print the tool banner
#from InfluxWriter import InfluxWriter
from http_parser.http import HttpStream
from http_parser.reader import SocketReader

#print('Redfish Event Listener v1.0.2')
os.chdir(os.path.dirname(os.path.realpath(__file__)))
#parser = argparse.ArgumentParser( description = "Python redfish listener")
#parser.add_argument('-p', help = 'Listening Port',default = 40096, required = False)
#parser.add_argument('-l', help = 'Local Path to save report json files', required = True)
#parser.add_argument('-v', help = 'verbose logging', required = False)
#parser.add_argument('script_examples', action = "store_true",help = "-p 443" )

#args = vars(parser.parse_args())

useSSL = True
verbose = False
certcheck = False

pravega_ip = "127.64.25.48"
pravega_port = "9090"
pravega_scope = "dell-scope5"
pravega_stream = "dell-stream5"

if useSSL:
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="server.key")

# exit gracefully on CTRL-C
signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))



# elastic_ip = "100.102.128.28"
# elastic_port = "8080"
# elastic_index = "telemetry"
# elastic_type = "_doc"
#elastic_url = "http://{}:{}/{}/{}".format(elastic_ip, elastic_port, elastic_index, elastic_type)


def init_logger(report_location, listenerport):
    folder_suffix = "-{}".format(listenerport) if listenerport != '443' else ''
    directory = '{}{}/{}'.format(report_location, folder_suffix, "logs")
    os.makedirs(directory, exist_ok=True)
    FORMAT = '%(asctime)-15s %(name)s %(levelname)s %(threadName)s | %(message)s'
    file_handler = logging.handlers.TimedRotatingFileHandler(filename=os.path.join(directory, "rf_logs.txt"), when='h',
                                                             interval=3, backupCount=40, encoding=None, delay=False,
                                                             utc=False, atTime=None)
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(handlers=handlers, level=logging.INFO,format=FORMAT)
### Bind socket connection and listen on the specified port
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
### Function to perform GET/PATCH/POST/DELETE operation for REDFISH URI
def callResourceURI(ConfigURI, URILink, Method='GET', payload=None, header=None, LocalUser=None, LocalPassword=None):
    #print("URI is: ", ConfigURI + URILink)
    try:
        startTime2 = DT.now()
        response = statusCode = expCode = None
        if certcheck:
            if Method == 'GET':
                response = requests.get(ConfigURI + URILink, auth=(LocalUser, LocalPassword), timeout=30)
            elif Method == 'PATCH':
                response = requests.patch(ConfigURI + URILink, data=payload, auth=(LocalUser, LocalPassword),
                                          timeout=30)
            elif Method == 'POST':
                response = requests.post(ConfigURI + URILink, data=payload, auth=(LocalUser, LocalPassword), timeout=30)
        else:
            if header is None:
                if Method == 'GET':
                    response = requests.get(ConfigURI + URILink, verify=False, auth=(LocalUser, LocalPassword),
                                            timeout=30)
                elif Method == 'PATCH':
                    header = {"content-type": "application/json"}
                    response = requests.patch(ConfigURI + URILink, data=payload, verify=False,
                                              auth=(LocalUser, LocalPassword), headers=header, timeout=30)
                elif Method == 'POST':
                    header = {"content-type": "application/json"}
                    response = requests.post(ConfigURI + URILink, data=payload, verify=False,
                                             auth=(LocalUser, LocalPassword), headers=header, timeout=30)
                elif Method == 'CREATE':
                    header = {"content-type": "application/json"}
                    response = requests.post(ConfigURI + URILink, data=payload, verify=False, headers=header,
                                             timeout=30)
                elif Method == 'DELETE':
                    header = {"content-type": "application/json"}
                    response = requests.delete(ConfigURI + URILink, data=payload, verify=False,
                                               auth=(LocalUser, LocalPassword), headers=header, timeout=30)
            else:
                if Method == 'GET':
                    response = requests.get(ConfigURI + URILink, verify=False, headers=header, timeout=30)
                elif Method == 'PATCH':
                    response = requests.patch(ConfigURI + URILink, data=payload, verify=False, headers=header,
                                              timeout=30)
                elif Method == 'POST':
                    response = requests.post(ConfigURI + URILink, data=payload, verify=False, headers=header,
                                             timeout=30)
                elif Method == 'DELETE':
                    response = requests.delete(ConfigURI + URILink, data=payload, verify=False, headers=header,
                                               timeout=30)

        endTime2 = DT.now()
        execTime2 = endTime2 - startTime2

        if response is not None:
            statusCode = response.status_code
        if Method == 'GET':
            expCode = 200
        elif Method == 'PATCH':
            expCode = [200, 204]
        elif Method == 'POST' or Method == 'CREATE':
            expCode = [200, 201, 204]
        elif Method == 'DELETE':
            expCode = [200, 201, 204]

        #print('Method = {}, status = {}, expected status = {}'.format(Method, statusCode, expCode))

        try:
            decoded = response.json()
        except:
            decoded = ""
        if (Method == 'GET' and statusCode == expCode):
            return statusCode, True, decoded, response.headers, str(execTime2)
        elif (Method == 'PATCH' and statusCode in expCode):
            return statusCode, True, decoded, response.headers, str(execTime2)
        elif (Method == 'DELETE' and statusCode in expCode):
            return statusCode, True, decoded, response.headers, str(execTime2)
        elif Method == 'POST' and (statusCode in expCode):
            return statusCode, True, decoded, response.headers, str(execTime2)
        elif (Method == 'CREATE') and (statusCode in expCode):
            Token = response.headers['X-Auth-Token']
            #print("Token value: ", Token)
            header = {"X-Auth-Token": Token}
            return statusCode, True, "", response.headers, str(execTime2)
        else:
            return statusCode, False, "", response.headers, str(execTime2)

    except Exception as err:
        print("Exception occurred in while performing subscription.")
        print(traceback.print_exc())
        return None, False, "", [], ""


def GetPostPayload(AttributeNameList, AttributeValueList, DataType="string"):
    payload = ""
    if DataType.lower() == "string":
        for i in range(0, len(AttributeNameList)):
            if i == len(AttributeNameList) - 1:
                payload = payload + "\"" + str(AttributeNameList[i]) + "\":\"" + str(AttributeValueList[i]) + "\""
            elif AttributeNameList[i] == "EventTypes":
                payload = payload + "\"" + str(AttributeNameList[i]) + "\":" + str(AttributeValueList[i]) + ","
            else:
                payload = payload + "\"" + str(AttributeNameList[i]) + "\":\"" + str(AttributeValueList[i]) + "\","

        payload = "{" + payload + "}"
        #print("Payload details are ", payload)

    return payload


### Create Subsciption on the servers provided by users if any
def PerformSubscription():
    global ServerIPs, UserNames, Passwords, Destination, EventTypes, ContextDetail, Protocol, SubscriptionURI, verbose
    ServerIPList = [x for x in ServerIPs.split(",") if x.strip() != '']
    UserNameList = UserNames.split(",")
    PasswordList = Passwords.split(",")
    AttributeNameList = ['Destination', 'EventTypes', 'Context', 'Protocol']
    AttributeValueList = [Destination, EventTypes, ContextDetail, Protocol]

    if (len(ServerIPList) == len(UserNameList) == len(PasswordList)) and (len(ServerIPList) > 0):
        #print("Count of Server is ", len(ServerIPList))
        payload = GetPostPayload(AttributeNameList, AttributeValueList, "string")
        for i in range(0, len(ServerIPList)):
            #print("ServerIPList:::", ServerIPList[i])
            #print("UserNameList:::", UserNameList[i])
            statusCode, Status, body, headers, ExecTime = callResourceURI(ServerIPList[i].strip(), SubscriptionURI,
                                                                          Method='POST', payload=payload, header=None,
                                                                          LocalUser=UserNameList[i].strip(),
                                                                          LocalPassword=PasswordList[i].strip())

            if Status:
                pass
                #print("Subcription is successful for %s" % ServerIPList[i])

            else:
                pass
                #print("Subcription is not successful for %s or it is already present." % ServerIPList[i])

    else:
        pass
        #print("\nNo subscriptions are specified. Continuing with Listener.")

    #print("\nContinuing with Listener.")


### Function to read data in json format using HTTP Stream reader, parse Headers and Body data, Response status OK to service and Update the output into file
def process_data(newsocketconn, fromaddr,threads):
    if useSSL:
        connstreamout = context.wrap_socket(newsocketconn, server_side=True)
    else:
        connstreamout = newsocketconn
    ### Output File Name
    outputfile = "Events_" + str(fromaddr[0]) + ".txt"
    logfile = "TimeStamp.log"
    global event_count, data_buffer
    outdata = headers = HostDetails = ""
    try:
        try:
            ### Read the json response using Socket Reader and split header and body
            r = SocketReader(connstreamout)
            p = HttpStream(r)
            headers = p.headers()
            #print("headers: ", headers)

            if p.method() == 'POST':
                bodydata = p.body_file().read()
                bodydata = bodydata.decode("utf-8", errors='ignore')
                for eachHeader in headers.items():
                    if eachHeader[0] == 'Host' or eachHeader[0] == 'host':
                        HostDetails = eachHeader[1]

                ### Read the json response and print the output
                #logging.info(f"Server IP Address is {}".format(fromaddr[0])
                outdata = dict()
                current_date = DT.now().strftime("%Y%m%d")
                folder_suffix = "-{}".format(listenerport)  if listenerport != '443' else ''
                directory = '{}{}/{}/{}'.format(report_location,folder_suffix,fromaddr[0],current_date)
                try:
                    outdata = json.loads(bodydata)
                except json.decoder.JSONDecodeError:
                    raw_invalid_file_thread = threading.Thread(target=writeInvalidJason, args=(directory, outdata ), name="{}_F".format(fromaddr[0]))
                    threads.append(raw_invalid_file_thread)
                    raw_invalid_file_thread.start()
                if outdata:
                    #writeRawJson(directory, outdata)
                    raw_file_thread = threading.Thread(target=writeRawJson, args=(directory, outdata,fromaddr[0]), name="{}_F".format(fromaddr[0]))
                    threads.append(raw_file_thread)
                    raw_file_thread.start()

                    #influx_thread = threading.Thread(target=writeReportToInflux, args=(fromaddr[0],directory, outdata),name=f"{fromaddr[0]}_I")
                    #threads.append(influx_thread)
                    #influx_thread.start()

                StatusCode = """HTTP/1.1 200 OK\r\n\r\n"""
                connstreamout.send(bytes(StatusCode, 'UTF-8'))
                try:
                    if event_count.get(str(fromaddr[0])):
                        event_count[str(fromaddr[0])] = event_count[str(fromaddr[0])] + 1
                    else:
                        event_count[str(fromaddr[0])] = 1
                    logging.info("Event Counter for Host %s = %s" % (str(fromaddr[0]), event_count[fromaddr[0]]))
                except Exception as err:
                    logging.error(err)
                    #print(traceback.print_exc())
                for th in threads:
                    th.join()

            if p.method() == 'GET':
                res = "HTTP/1.1 200 OK\n" \
                      "Content-Type: application/json\n" \
                      "\n" + json.dumps(data_buffer)
                connstreamout.send(res.encode())
                data_buffer.clear()
        except Exception as err:
            outdata = connstreamout.read()
            traceback.print_exc()
            #logging.exception(f"Data needs to read in normal Text format.{err}. Message is : {str(outdata)}")
    finally:
        connstreamout.shutdown(socket.SHUT_RDWR)
        connstreamout.close()
        logging.debug("Connection closed")

def writeRawJson(directory, outdata, server_ip):
    #print(outdata)
    iceman_json_data = {}
    json_list_data = []
    try:
        id = outdata.get('Id', 'No ID')
        iceman_json_data["fields.IDRACIP"] = server_ip 
        iceman_json_data["MetricReport"] = id
        iceman_json_data["source"] = "Telemetry-Redfish-Listener"
        iceman_json_data["@timestamp"] = DT.utcnow().strftime("%Y-%m-%dT%H:%M:%S%z")
        for data in outdata["MetricValues"]:
            metric_value_data = {}
            metric_value_data["MetricId"] = data.get("MetricId")
            try:
                metric_value_data["MetricValue"] = float(data.get("MetricValue"))
                metric_value_data["MetricType"] = "Number"
            except:
                metric_value_data["MetricValue1"] = data.get("MetricValue")
                metric_value_data["MetricType"] = "String"
            metric_value_data["ContextID"] = data.get("Oem").get("Dell").get("ContextID")
            metric_value_data.update(iceman_json_data)
            json_list_data.append(metric_value_data)
        
        str_data = json.dumps(json_list_data)
        #print(str_data)
        
        manager=pravega_client.StreamManager("{}:{}".format(pravega_ip, pravega_port))
        # assuming the Pravega scope and stream are already created.
        manager.create_scope(pravega_scope)
        manager.create_stream(pravega_scope, pravega_stream, 1)
        writer=manager.create_writer(pravega_scope, pravega_stream)
        # write into Pravega stream without specifying the routing key.
        #jsol_data = """{"key":"value"}"""
        writer.write_event(str_data)
        #elastic = Elasticsearch("{}:{}".format(elastic_ip,elastic_port))   
        #response = helpers.bulk(elastic, json_list_data, index=elastic_index, doc_type=elastic_type)
        
            
        #awsr_payload = json_list_data[0]
        # headers = {
        #       "content-type": "application/json",
        #       }
        # print("elastic_url",elastic_url)
        # try:
        #     response = requests.request("POST", elastic_url, json=metric_value_data, headers=headers, verify = False)
        # except:
        #     print("Failed to connect to Elastic Search")
        # print(response.status_code)
        # print(response.text)
        # if response.status_code == 200 or response.status_code == 201:
        #     print("Logs has been Successfully updated into ELK!!!")
        # else:
        #     print("Logs has not been Uploaded into ELK!!!")
        """
        report_sequence = outdata.get('ReportSequence', '00000')
        report_timestamp = outdata.get('Timestamp', '00000').replace(':', '')
        local_time_stamp = DT.now().strftime("%H%M%S.%f")
        json_filename = f"{local_time_stamp}_{id}_{report_sequence}_{report_timestamp}.json"
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, json_filename), 'w', errors='ignore') as file:  # Use file to refer to the file object
            file.write(json.dumps(outdata, sort_keys=True, indent=4))
        logging.info(f"Writen file {json_filename} ")
        """
    except Exception as e:
        logging.exception("Failed to send data to ELK")

def writeReportToInflux(idrac_ip, directory, outdata):
    global listenerport
    influx_write_status = InfluxWriter('subscriptions').writeDataToInflux(idrac_ip,outdata,destination_id="123_"+listenerport)
    if not influx_write_status:
        writeInvalidJason(directory,outdata, "invalid_for_influx")

def writeInvalidJason(directory, outdata, name_prefix='invalid'):
  try:
    local_time_stamp = DT.now().strftime("%H%M%S.%f")
    name_prefix = "empty" if (isinstance(outdata, dict) and not outdata.get('MetricValues')) else name_prefix
    invalid_json_filename = f"{local_time_stamp}_{name_prefix}_report.json"
    with open(os.path.join(directory,invalid_json_filename), "w", errors='ignore') as invalid_json_file:
      outdata = json.dumps(outdata) if isinstance(outdata,dict) else outdata
      invalid_json_file.write(outdata)
    logging.info(f"Writen file {invalid_json_filename} ")
  except Exception as e:
    logging.exception(f"Exception occurred while writing invalid json.{e}")
### Perform the Subscription if provided
#PerformSubscription()

### Accept the TCP connection using certificate validation using Socket wrapper
config = configparser.ConfigParser()
config.read('config.ini')
listenerport = config['SystemInformation']['ListenerPort']
elastic_ip = config['ElasticSearchDetails']['ElasticSearchIP']
elastic_port = config['ElasticSearchDetails']['ElasticSearchPort']
elastic_index = config['ElasticSearchDetails']['ElasticSearchIndex']
elastic_type = config['ElasticSearchDetails']['ElasticSearchType']
#elastic_url = "http://{}:{}/{}/{}".format(elastic_ip, elastic_port, elastic_index, elastic_type)
#listenerport = str(args['p']).strip()
listenerip = get_ip()
report_location = os.path.join("JSON")
init_logger(report_location,listenerport)
try:
    bindsocket = socket.socket()
    bindsocket.bind((listenerip, int(listenerport)))
    bindsocket.listen(5)
except Exception as e:
    #logging.exception(f"Unable to start listener on port {listenerport}")
    sys.exit(0)
logging.info('Listening on {}:{} via {}'.format(listenerip, listenerport, 'HTTPS' if useSSL else 'HTTP'))
event_count = {}
data_buffer = []
while True:
    threads =[]
    try:
        ### Socket Binding
        newsocketconn, fromaddr = bindsocket.accept()
        try:
            ### Multiple Threads to handle different request from different servers
            threading.Thread(target=process_data, args=(newsocketconn, fromaddr,threads), name=fromaddr[0]).start()
        except Exception as err:
            print(traceback.print_exc())
    except Exception as err:
        print("Exception occurred in socket binding.")
        print(traceback.print_exc())
