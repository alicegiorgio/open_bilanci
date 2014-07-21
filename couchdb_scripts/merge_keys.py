__author__ = 'stefano'

#!/usr/local/bin/python
# coding: utf-8

import sys
import gspread
import logging
import argparse
from pprint import pprint
import requests
import utils
import csv
import settings_local


def write_csv(result_set, output_filename, translation_type):

    csv_file = open(output_filename, "wb+")
    csv_header = settings_local.accepted_types[translation_type]['csv_keys']

    if translation_type != 'simplify':
        csv_header.append("normalized_"+translation_type)
    else:
        csv_header.extend(["voce normalizzata","Categoria","titolo","entrate / uscite"])

        
    udw = utils.UnicodeDictWriter(csv_file, csv_header, dialect=csv.excel, encoding="utf-8")

    # scrive l'intestazione
    udw.writeheader()
    logging.info("Write CSV file: "+output_filename)
    for json_row in result_set:

        csv_dict = {}

        if len(json_row) == len(csv_header):

            udw.writerow_list(json_row)
        else:
            logging.error("Error: number of keys in settings ({0}) != number of keys in Json file({1}), exiting...".format(len(csv_header),len(json_row),))
            return

    logging.info("Finished writing file: "+output_filename)

def merge(view_data, worksheet, translation_type):

    #get json data from couchdb view
    #transform json view into table
    #get data from google drive spreadsheet
    #merge the two tables

    data_couch=[]
    keys_result_set = []
    data_result_set = []
    gdoc = {}
    voci_separation_token = '///'

    # from view_data gets only the key value and append it to a list
    for row in view_data['rows']:
        if translation_type == 'titoli':
            data_couch.append(row['key'][0])
        else:
            # if voci / simplify is considered the voce value is added
            tipo_b_quadro_titolo = row['key'][0]
            voce = row['key'][1]
            result = tipo_b_quadro_titolo+voci_separation_token+voce
            data_couch.append(result)

    # get data from gdoc
    # create a list of keys (tipobilancio_quadro_titolo)
    # create a list of dicts that stores all the previous info and the normalized titolo name
    
    for row in worksheet:
        string_key = "_".join([row[0], row[1].zfill(2), row[2]])
        if translation_type != 'titoli':
            string_key = string_key + voci_separation_token + row[3]

        keys_result_set.append(string_key)

        # adds the coloumn with normalized data to the gdoc dict
        if translation_type == 'titoli':
            row_keys = [row[0], row[1].zfill(2), row[2], row[3]]

        elif translation_type == 'voci':
            row_keys = [row[0], row[1].zfill(2), row[2], row[3], row[4]]

        else:
            row_keys = [row[0], row[1].zfill(2), row[2], row[3], row[4], row[5], row[6], row[7]]

        gdoc[string_key] = row_keys

    # checks that every key in titoli_couch is present in titoli_gdoc
    # if not so, adds the key to the result set
    for string_key in data_couch:
        if string_key not in gdoc.keys():
            logging.debug(u'Append "{0}" to the result set'.format(string_key))
            keys_result_set.append(string_key)


    # orders result set keys in alphabetical order
    sorted_keys_set =  sorted(keys_result_set)

    # considering the complete set of the keys:
    # if the key was already in the gdoc -> moves all the info to the result csv
    # else: adds to the csv the tuple (tipobilancio,quadro,titolo,'')
    for string_key in sorted_keys_set:
        if string_key in gdoc.keys():
            values = gdoc[string_key]
            data_result_set.append(values)

        else:
            if translation_type == 'titoli':
                values = string_key.split("_")
            else:
                # splits tipobilancio, quadro, titolo, voce
                values_set = string_key.split(voci_separation_token)
                values = values_set[0].split("_")
                values.append(values_set[1])

            if translation_type != 'simplify':
                values.append('')
            else:
                values.extend(['','','',''])

            data_result_set.append(values)

    return data_result_set


def main(argv):
    parser = argparse.ArgumentParser(description='Merge keys for titoli / voci comparing couch db views and gdoc')

    # construct help text
    accepted_servers_help = "Server name: "
    for accepted_servers_name in settings_local.accepted_servers.keys():
        accepted_servers_help+= accepted_servers_name+" | "


    parser.add_argument('--server','-s', dest='server_name', action='store',
               default='localhost',
               help=accepted_servers_help)

    parser.add_argument('--type','-t', dest='type', action='store',
           default='titoli',
           help='Type to translate: titoli | voci | simplify')

    parser.add_argument('--tipo_bilancio','-tb', dest='tipo_bilancio', action='store',
           default='preventivo',
           help="Bilancio type: preventivo | consuntivo"
        )

    parser.add_argument('--output','-o', dest='output', action='store',
           default='output.csv',
           help="Output filename"
        )

    args = parser.parse_args()
    output_filename = args.output
    server_name= args.server_name
    tipo_bilancio= args.tipo_bilancio
    translation_type = args.type

    # init logging
    logging.basicConfig(level=logging.DEBUG)

    if translation_type in settings_local.accepted_types.keys():

        if server_name in settings_local.accepted_servers.keys():
            # Login with the script Google account
            gc = gspread.login(settings_local.g_user, settings_local.g_password)

            # open the list worksheet
            list_sheet = None
            try:
                list_sheet = gc.open_by_key(settings_local.gdoc_keys[translation_type])
            except gspread.exceptions.SpreadsheetNotFound:
                logging.error("Error: gdoc url not found")
                return

            worksheet = list_sheet.worksheet(tipo_bilancio).get_all_values()[2:]

            # set source db name / destination db name
            if translation_type == 'titoli':
                source_db_name = settings_local.accepted_servers[server_name]['raw_db_name']
                view_name = '{0}_{1}'.format(translation_type, tipo_bilancio)
            elif translation_type == 'voci':
                source_db_name = settings_local.accepted_servers[server_name]['normalized_titoli_db_name']
                view_name = '{0}_{1}'.format(translation_type, tipo_bilancio)
            elif translation_type == 'simplify':
                source_db_name = settings_local.accepted_servers[server_name]['normalized_voci_db_name']
                view_name = 'voci_{0}'.format(tipo_bilancio)
            else:
                logging.error("Type not accepted: " + translation_type)
                return

            # connessione a couchdb
            # costruisce la stringa per la connessione al server aggiungendo user/passw se necessario
            host = settings_local.accepted_servers[server_name]['host']
            server_connection_address ='http://{0}:5984/{1}/_design/{2}/_view/{3}?group_level=4'.format(host,source_db_name, view_name,view_name)
            logging.info("Getting Json data from couch View:{0}".format(view_name))


            user = passw = None
            if settings_local.accepted_servers[server_name]['user']:
                user = settings_local.accepted_servers[server_name]['user']
                if settings_local.accepted_servers[server_name]['password']:
                    passw =settings_local.accepted_servers[server_name]['password']


            if user is None and passw is None:
                r = requests.get(server_connection_address)
            else:
                r = requests.get(server_connection_address, auth=(user,passw))

            result_set = merge(view_data=r.json(), worksheet=worksheet, translation_type=translation_type)
            write_csv(result_set=result_set, output_filename=output_filename, translation_type=translation_type)


        else:
            logging.error("server not accepted:"+server_name)
    else:
        logging.error("Type not accepted: " + translation_type)


# launches main function
if __name__ == "__main__":
   main(sys.argv[1:])
