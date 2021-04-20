# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import requests
import json

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_person_info"


    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # dispatcher.utter_message(text=f"If you are asking about {tracker.slots['person']}, Best Human Ever!!! ;-) ")
        cnumber = "474"

        response = requests.post("http://localhost:3030/acad/query",
            data = {'query':"""
                    PREFIX vivo: <http://vivoweb.org/ontology/core#> 
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX DC: <http://purl.org/dc/terms/> 
                    PREFIX acad: <http://acad.io/schema#> 
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                    PREFIX acaddata: <http://acad.io/data#>
                    
                    SELECT ?cname ?cdescription
                    WHERE{
                    ?course a vivo:Course.
                    ?course foaf:name ?cname.
                    ?course acad:courseNumber {cnumber}^^xsd:int.
                    ?course acad:courseSubject "COMP"^^xsd:string.
                    ?course DC:description ?cdescription.
                    }
                    """
            })

        # # Use the json module to load CKAN's response into a dictionary.
        # response_dict = json.loads(response.text)

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]
        bindings = results["bindings"][0]
        description = bindings["cdescription"]
        vdescription = description["value"]
        print(vdescription)

        return []
