#external modules
from flask import Flask, render_template, Response, stream_with_context, redirect, request
import requests as rest
import json
import os
import time
from lxml import etree
import pyqrcode
from aztec_code_generator import AztecCode
#from gevent import monkey; monkey.patch_all()
#from gevent.pywsgi import WSGIServer

#my modules
import functions as funcs


app = Flask(__name__)


#PATH TO GUI - depending on wether app.py is running on localhost, or on cpee.org
#GUI = "http://localhost:6000/"
GUI = "https://cpee.org/inkscape-manager/"


#index page - GUI
@app.route('/')
def render_index():
    return render_template("index.html")


# WORKER
# starts the process, waits until it's finished and returns the svg-code as string
# @param process: process family to get started
@app.route('/worker', methods=['GET'])
def worker():
    instance_header = funcs.start_process(request.args.get('process'))

    #check if process is still running
    i = 0
    while(True):
        #update counter
        i = i+1

        #check if object.xml file already exists (object.xml contains the svg-code after the task /inkscape)
        if(os.path.exists("object.xml")):
            break

        #every tenth time check on CPEE Engine if process is already finished or abandoned (in case that the process was terminated or abandoned)
        if(i%10 == 0):
            state = rest.get(instance_header["CPEE-INSTANCE-URL"]+'/properties/state').text
            if(state == "finished" or state == "abandoned"):
                break

        #wait 0.5 seconds before rerunning the loop
        time.sleep(0.5)

    #update GUI to "FINISH"
    with open('gui_information.json') as json_file:
        data = json.load(json_file)
    data['CPEE-STATE'] = " - finished"
    with open('gui_information.json', 'w') as outfile:
        json.dump(data, outfile)

    #return the svg-code as string from object.xml (in case object.xml doesn't exist, return "terminated")
    code = "terminated"
    if(os.path.exists("object.xml")):
        with open('object.xml', 'r') as file:
            code = file.read()
        os.remove('object.xml')
    return code


#LISTEN
#Service that listens to the new data and constantly delivers it to the GUI (EventStream will be opened to that service)
@app.route("/listen")
def listen():
    def respond_to_client():
        #counter
        i=0
        while True:
            #get user every tenth time
            user = "variant"
            if(i%10 == 0):
                if(os.path.exists("config.xml")):
                    config = etree.parse('config.xml').getroot()
                    user = config.find('user').text
                else:
                    user = "no config file!"

            with open('gui_information.json') as json_file:
                data = json.load(json_file)

            info = data["CPEE-INSTANCE"]
            cpee_uuid = data["CPEE-INSTANCE-UUID"]
            cpee_state = data["CPEE-STATE"]
            message = data["message"]
            user_confirmation_visible = data['user_confirmation_visible']
            user_confirmation_text = data['user_confirmation_text']
            text_input_visible = data['text_input_visible']
            history = data['history']

            _data = json.dumps({
                "user":user,
                "info":info,
                "cpee_uuid":cpee_uuid,
                "cpee_state":cpee_state,
                "message":message,
                "user_confirmation_visible":user_confirmation_visible,
                "user_confirmation_text":user_confirmation_text,
                "text_input_visible":text_input_visible,
                "history":history
            })

            yield f"id: 1\ndata:{_data}\nevent: online\n\n"

            time.sleep(0.2)
    response = Response(respond_to_client(), mimetype='text/event-stream')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


#CREATE AZTEC CODE
#service that creates an aztec code in svg-code from an input-text
@app.route('/createaztec')
def createaztec():
    #read args
    text = request.args.get('text')

    #create aztec code
    aztec_code = AztecCode(text)

    #convert lines of aztec code to strings
    lines = []
    for elem in aztec_code.matrix:
        x = ''
        for char in elem:
            x=x+str(char)
        lines.append(x)

    #create svg code from the lines (lines as strings)
    svg_code = funcs.get_svg_code(lines)

    #Update GUI (add to history)
    funcs.updateGUIhistory("Aztec-Code created\n")

    #return svg_code to running CPEE
    data = {"code":svg_code}
    return data


#CREATE QR CODE
#service that creates a qr code in svg-code from an input-text
@app.route('/createqr')
def createqr():
    #read args
    text = request.args.get('text')

    #create qr code
    code = pyqrcode.create(text)

    #split lines in arrays
    lines = code.text().split('\n')

    #delete spaces at the margin of the code
    lines_no_margin = []
    for i in range(len(lines)):
        if(i>=4 and i<=len(lines)-6):
            lines_no_margin.append(lines[i][4:len(lines[i])-4])

    #create svg code from the lines_no_margin (lines array without margin)
    svg_code = funcs.get_svg_code(lines_no_margin)

    #Update GUI (add to history)
    funcs.updateGUIhistory("QR-Code created\n")

    #return svg_code to running CPEE
    data = {"code":svg_code}
    return data

#USER TEXT
#get text from user
@app.route('/user_text', methods=['POST'])
def user_text():
    #request headers (for CPEE CALLBACK)
    headers = request.headers

    #SET CPEE-CALLBACK url, text_input_visible and history in file
    with open('gui_information.json') as json_file:
        data = json.load(json_file)
    data['CPEE-CALLBACK'] = headers["Cpee-Callback"]
    data['text_input_visible'] = "true"
    data['history'] += "user text input: "
    with open('gui_information.json', 'w') as outfile:
        json.dump(data, outfile)

    #tell CPEE to wait for CALLBACK
    resp = Response()
    resp.headers['CPEE-CALLBACK'] = "true"
    return resp

#USER TEXT CALLBACK
#answer of user text - comes from GUI and puts back to CPEE
@app.route('/user_answer_text', methods=['POST'])
def user_answer_text():
    #request args
    cpee_uuid = request.form['cpee_uuid']
    user_input_text = request.form['user_input_text']

    #update GUI and get cpee_callback
    with open('gui_information.json') as json_file:
        json_file = json.load(json_file)
    json_file['text_input_visible'] = "false"
    json_file['history'] += user_input_text + "\n"
    cpee_callback = json_file['CPEE-CALLBACK']
    with open('gui_information.json', 'w') as outfile:
        json.dump(json_file, outfile)

    #put back to CPEE
    data = {"user_input_text":user_input_text}
    rest.put(cpee_callback, json=data)

    #redirect to GUI
    return redirect(GUI)


#USER CONFIRMATION
#user can confirm or abort
@app.route('/user_confirmation', methods=['POST'])
def user_confirmation():
    #request headers (for CPEE CALLBACK)
    headers = request.headers

    #request args
    confirmation = request.form['confirmation']

    #SET CPEE-CALLBACK url, user_confirmation_text/_visible and history in file
    with open('gui_information.json') as json_file:
        data = json.load(json_file)
    data['CPEE-CALLBACK'] = headers["Cpee-Callback"]
    data['user_confirmation_visible'] = "true"
    data['user_confirmation_text'] = confirmation
    data['history'] += "user confirmation: " + confirmation
    with open('gui_information.json', 'w') as outfile:
        json.dump(data, outfile)

    #tell CPEE to wait for CALLBACK
    resp = Response()
    resp.headers['CPEE-CALLBACK'] = "true"
    return resp

#USER CONFIRMATION CALLBACK
#answer of user confirmation - comes from GUI and puts back to CPEE
@app.route('/user_answer', methods=['POST'])
def user_answer():
    #request args
    cpee_uuid = request.form['cpee_uuid']
    forward = request.form['forward']

    #update GUI and get cpee_callback
    with open('gui_information.json') as json_file:
        json_file = json.load(json_file)
    json_file['user_confirmation_visible'] = "false"
    json_file['history'] += " - user answer: " + forward
    cpee_callback = json_file['CPEE-CALLBACK']
    with open('gui_information.json', 'w') as outfile:
        json.dump(json_file, outfile)

    #put back to CPEE
    data = {"forward":forward}
    rest.put(cpee_callback, json=data)

    #redirect to GUI
    return redirect(GUI)

#USER message
#outputs a message for the user in the GUI
@app.route('/user_message', methods=['POST'])
def user_message():
    #request args
    message = request.form['message']

    #set message and history in file
    with open('gui_information.json') as json_file:
        data = json.load(json_file)
    data['message'] = message
    data['history'] += "message for user: " + message + "\n"
    with open('gui_information.json', 'w') as outfile:
        json.dump(data, outfile)

    #return to CPEE
    return '200'


#CHANGE SIZE
#takes svg code from CPEE, changes its size and returns the code
@app.route('/changesize')
def changesize():
    #request args
    size = request.args.get('size')
    code = request.args.get('code')

    #update size
    code_as_xml = etree.ElementTree(etree.fromstring(code)).getroot()
    code_as_xml.set('transform', 'scale(' + size + ')')

    #update GUI history
    funcs.updateGUIhistory("size: "+size+"\n")

    #return updated code
    data = {"code":etree.tostring(code_as_xml).decode('utf-8')}
    return data

#CHANGE COLOR
#takes svg code from CPEE, changes its color and returns the code
@app.route('/changecolor')
def changecolor():
    #request args
    color = request.args.get('color')
    code = request.args.get('code')

    #update color
    code_as_xml = etree.ElementTree(etree.fromstring(code)).getroot()
    code_as_xml.set('stroke', color)

    #update GUI history
    funcs.updateGUIhistory("color: "+ color +"\n")

    #return updated code
    data = {"code":etree.tostring(code_as_xml).decode('utf-8')}
    return data

#SERVICE: START INKSCAPE MIT EXTENSION
@app.route('/inkscape')
def inkscape():
    #request args
    code = request.args.get('code')

    code_as_xml = etree.ElementTree(etree.fromstring(code)).getroot()

    #write code to object.xml, so that the worker can see it
    with open("object.xml", "wb") as f:
        f.write(etree.tostring(code_as_xml))

    #update GUI history
    funcs.updateGUIhistory("sent to Inkscape\n")

    return '200'

#main function
if __name__ == '__main__':
    #app.run()
    app.run(port=6000, debug = True)
