# unboundedhackathon
Unbounded Hackathon  by Dell Technologies

# Storing Redfish Telemetry Metrics in Elastic Search using Pravega 

This project demonstrates, how we can collect Redfish Telemetry Metrics using Python redfish listener and write metrics to Pravega Streams. We can also 
read those data from stream and stores it in Elastic Search. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Make sure you have installed Python 3.8 or 3.9 on your device

### Project structure
```
* main-project/
  |--- utils/
  |    |--- __init__.py
  |    |--- context.py
  |    |--- helper.py    
  |--- settings.py
  |--- pravega_redfish_write.py
  |--- pravega_read.py
  |--- cert.pem
  |--- server.key
  |--- config.ini
  |--- requirements.txt

```

### Step to create project

A step by step series of examples that tell you how to get a development env running

1. Install virtual environment

```
pip install virtualenv
```
2. Create virtual environment and activate inside your flask-project directory according the above structure
```
virtualenv venv
> On windows -> venv\Scripts\activate
> On linux -> . env/bin/activate
```
3. Install all python modules on your virtual environment with pip
```
pip install -r requirement.txt
```
4. Update the settings.py with Elastic Search Host IP and Port and index.
```
es = Context(
    host=_("ELASTIC_HOST", "localhost"),
    port=_("ELASTIC_PORT", 9200, int),
    index=_("ELASTIC_INDEX", "my_index")
)
```
5. Update the settings.py with Pravega Host IP, Port, scope, stream,group,reader_id.
```
pravega = Context(
    host=_("PRAVEGA_HOST", "localhost"),
    port=_("PRAVEGA_PORT", 9090, int),
    scope=_("PRAVEGA_SCOPE", "scope"),
    stream=_("PRAVEGA_STREAM", "stream"),
    group=_("PRAVEGA_READER_GROUP", "rg"),
    reader_id=_("PRAVEGA_READER_ID", "rdr")
)

```
6. Make sure the system where user is running Stream writer and reader, should already mapped with atleast one iDRAC system as redfish listner
```
For more details -- https://github.com/dell/iDRAC-Telemetry-Scripting/tree/master/ConfigurationScripts 
```
7. Run the Python redfish listener and Pravega stream writer script 
```
python pravega_redfish_write.py
```
8. Run the Python Pravega stream reader and storing in Elastic Search script 
```
python pravega_read.py
```
9. Go to Kibana and check that index you should able to see the data

