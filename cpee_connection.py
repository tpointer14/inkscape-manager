import requests as rest
import json

def post_process_model(process_family, CPEE_REPOSITORY, USER, CPEE_INSTANTIATION):
    #BEREITE INSTANZ VOR (READY)
    #url = "https://cpee.org/flow/start/xml/"
    payload={'behavior': 'fork_ready'}
    files=[
      ('xml',(process_family + '.xml',open(CPEE_REPOSITORY + process_family + '_' + USER + '.xml','rb'),'text/xml'))
    ]
    headers = {} #notwendig???
    response = rest.request("POST", CPEE_INSTANTIATION, headers=headers, data=payload, files=files)
    instance_header = json.loads(response.text)
    return instance_header

def put_dataelements(CPEE_SERVER, CPEE_INSTANCE, DATAELEMENTS):
    #PUT DATAELEMENTS TO INSTANCE
    url = CPEE_SERVER + CPEE_INSTANCE + '/properties/dataelements/'
    payload='<dataelements xmlns="http://cpee.org/ns/properties/2.0">'+DATAELEMENTS+'</dataelements>'
    headers = {
      'Content-ID': 'dataelements',
      'Content-Type': 'text/xml'
    }
    response = rest.request("PUT", url, headers=headers, data=payload)
    return response

def put_endpoints(CPEE_SERVER, CPEE_INSTANCE, ENDPOINTS):
    #PUT ENDPOINTS TO INSTANCE
    url = CPEE_SERVER + CPEE_INSTANCE + '/properties/endpoints/'
    payload='<endpoints xmlns="http://cpee.org/ns/properties/2.0">'+ENDPOINTS+'</endpoints>'
    headers = {
      'Content-ID': 'endpoints',
      'Content-Type': 'text/xml'
    }
    response = rest.request("PUT", url, headers=headers, data=payload)
    return response

def put_state_running(CPEE_SERVER, CPEE_INSTANCE):
    #START IT / LETS GO
    url = CPEE_SERVER + CPEE_INSTANCE + "/properties/state/"
    data = {"value" : "running"}
    response = rest.put(url,data)
    return response
