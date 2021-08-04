from lxml import etree
import json
import os
import cpee_connection as cpee


def start_process(process_family):
    config = read_config_file(process_family)

    instance_header = cpee.post_process_model(process_family, config["CPEE_REPOSITORY"], config["USER"], config["CPEE_INSTANTIATION"])

    prepare_gui_file(process_family, instance_header["CPEE-INSTANCE-UUID"], instance_header["CPEE-INSTANCE"])

    reponse = cpee.put_dataelements(config["CPEE_SERVER"], instance_header["CPEE-INSTANCE"], config["DATAELEMENTS"])
    reponse = cpee.put_endpoints(config["CPEE_SERVER"], instance_header["CPEE-INSTANCE"], config["ENDPOINTS"])

    #START IT / LETS GO
    response = cpee.put_state_running(config["CPEE_SERVER"], instance_header["CPEE-INSTANCE"])

    return instance_header


def read_config_file(process_family):
    config_dictionary = {}

    config = etree.parse('config.xml').getroot()
    config_dictionary["USER"] = config.find('user').text
    config_dictionary["CPEE_SERVER"] = config.find('cpee').find('server').text
    config_dictionary["CPEE_INSTANTIATION"] = config.find('cpee').find('instantiation').text + 'xml/'
    config_dictionary["CPEE_REPOSITORY"] = config.find('cpee').find('repository').text
    config_dictionary["DATAELEMENTS"] = ''
    config_dictionary["ENDPOINTS"] = ''
    for process in config.find('processes'):
        if(process.get('id') == process_family):
            dataelems = process.find('dataelements')
            for elem in dataelems:
                config_dictionary["DATAELEMENTS"] += '<' + elem.tag +'>' + elem.text + '</' + elem.tag + '>'
            epoints = process.find('endpoints')
            for elem in epoints:
                config_dictionary["ENDPOINTS"] += '<' + elem.tag +'>' + elem.text + '</' + elem.tag + '>'
    return config_dictionary


def prepare_gui_file(process_family, CPEE_INSTANCE_UUID, CPEE_INSTANCE):
    #SET UUID und INSTANCE in JSON
    with open('gui_information.json') as json_file:
        data = json.load(json_file)

    data = {
        "CPEE-INSTANCE-UUID":CPEE_INSTANCE_UUID,
        "CPEE-INSTANCE":CPEE_INSTANCE,
        "CPEE-STATE":"",
        "message":"",
        "user_confirmation_visible":"false",
        "user_confirmation_text":"",
        "text_input_visible":"false",
        "history":"Process " + process_family + " started\n"
    }

    with open('gui_information.json', 'w') as outfile:
        json.dump(data, outfile)
    return 'ok'


#transform QR/Aztec object from bit arrays (per line) into a SVG readable code.
def get_svg_code(lines):
    dim_qr = len(lines)
    init_svg = '<path stroke="#000" d="M0 '
    svg = init_svg
    line_num = 0
    for line in lines:
        line_num = line_num + 1
        i=0
        while i<dim_qr:
            curr_char = line[i]
            number_black = 0
            number_white = 0

            #Zeile: Wenn Erste: 0.5h; wenn neue Zeile aber nicht erste: 1h; wenn fortlaufend: 0h
            zeile = '0h'
            if(i == 0):
                zeile = '1h'
            if(svg == init_svg):
                zeile = '0.5h'

            #Ausnahme für erste Runde
            if(i==0 and curr_char == '0'):
                while line[i] == curr_char:
                    i = i+1
                    number_white = number_white+1
                    #HIER GEHÖRT NOCH EINE AUSNAHME HER, FALLS EINE GESAMTE ZEILE WEISS IST
                svg = svg + zeile +'0m' + str(number_white) + ' '
            else:
                #counting black chars
                while line[i] == '1':
                    i = i+1
                    number_black = number_black+1
                    if (i==dim_qr):
                        #Falls es die letzte Zeile ist
                        if(line_num == len(lines)):
                            svg = svg + zeile + str(number_black)
                            break
                        svg = svg + zeile + str(number_black) + 'm-' + str(dim_qr) + ' '
                        break

                if(i==dim_qr):
                    break

                #counting white chars
                while line[i] == '0':
                    number_white = number_white+1
                    i = i+1
                    if (i==dim_qr):
                        #Falls es die letzte Zeile ist
                        if(line_num == len(lines)):
                            svg = svg + zeile + str(number_black)
                            break
                        svg = svg + zeile + str(number_black) + 'm-' + str(dim_qr-number_white) + ' '
                        break

                if(i==dim_qr):
                    break

                svg = svg + zeile + str(number_black) + 'm' + str(number_white) + ' '

    svg = svg + '" />'
    #print(svg)
    return svg


def updateGUIhistory(update):
    with open('gui_information.json') as json_file:
        data = json.load(json_file)
    data['history'] += update
    with open('gui_information.json', 'w') as outfile:
        json.dump(data, outfile)
    return '200'
