# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import requests
import json
import re
from rdflib import Graph, Literal, RDF, URIRef, Namespace, Dataset  # basic RDF handling

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course']

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)
        csubject = values[1].upper().replace(" ", "")
        cnumber = values[2]

        print(csubject)
        print(cnumber)

        response = requests.post("http://localhost:3030/acad/sparql",
                                 data={'query': """
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
                    ?course acad:courseNumber "%s"^^xsd:int.
                    ?course acad:courseSubject "%s"^^xsd:string.
                    ?course DC:description ?cdescription.
                    }
                    """ % (cnumber, csubject)
                                       })

        # # Use the json module to load CKAN's response into a dictionary.

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]
        bindings = results["bindings"][0]
        description = bindings["cdescription"]
        vdescription = description["value"]
        print(vdescription)

        return []


# Q6) What components does the course [course] have?
class ActionCourseComponents(Action):

    def name(self) -> Text:
        return "action_course_components"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course']

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)
        csubject = values[1].upper().replace(" ", "")
        cnumber = values[2]

        response = requests.post("http://localhost:3030/acad/sparql",
                                 data={'query': """
                            PREFIX vivo: <http://vivoweb.org/ontology/core#> 
                            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                            PREFIX DC: <http://purl.org/dc/terms/> 
                            PREFIX acad: <http://acad.io/schema#> 
                            PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                            PREFIX acaddata: <http://acad.io/data#>

                            SELECT ?cname ?component
                            WHERE{
                                ?course a vivo:Course.
                                ?course foaf:name ?cname.
                                ?course acad:courseNumber "%s"^^xsd:int.
                                ?course acad:courseSubject "%s"^^xsd:string.
                                ?course acad:courseHas ?component.
                            }
                            """ % (cnumber, csubject)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        components = []

        for result in bindings:
            for key in result:
                if key == "component":
                    components.append(result[key])

        for value in components:
            print("COMPONENT: ", value, "\n")

        return []


# Q7) Does [course] have labs?
class ActionCourseLabs(Action):

    def name(self) -> Text:
        return "action_course_labs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course']

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)
        csubject = values[1].upper().replace(" ", "")
        cnumber = values[2]

        response = requests.post("http://localhost:3030/acad/sparql",
                                 data={'query': """
                                    PREFIX vivo: <http://vivoweb.org/ontology/core#> 
                                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                                    PREFIX DC: <http://purl.org/dc/terms/> 
                                    PREFIX acad: <http://acad.io/schema#> 
                                    PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                                    PREFIX acaddata: <http://acad.io/data#>

                                    ASK{
                                    ?course a vivo:Course.
                                    ?course acad:courseNumber "%s"^^xsd:int.
                                    ?course acad:courseSubject "%s"^^xsd:string.
                                    ?course acad:courseHas acad:Lab.
                                    }
                                    """ % (cnumber, csubject)
                                       })

        y = json.loads(response.text)

        # print("\n\n--------------------\n", y, "\n--------------------\n\n")

        result = y["boolean"]

        print(result)

        return []


# Q8) What courses does the [department] department offer?
class ActionDepartmentCourses(Action):

    def name(self) -> Text:
        return "action_department_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        department = tracker.slots['department']

        if department.upper() == "CSSE":
            department = "Computer Science and Software Engineering (CSSE)"

        response = requests.post("http://localhost:3030/acad/sparql",
                                 data={'query': """
                                            PREFIX vivo: <http://vivoweb.org/ontology/core#> 
                                            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                                            PREFIX DC: <http://purl.org/dc/terms/> 
                                            PREFIX acad: <http://acad.io/schema#> 
                                            PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                                            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                                            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                                            PREFIX acaddata: <http://acad.io/data#>

                                            SELECT  ?csubject ?cnumber ?cname
                                            WHERE{
                                                ?course a vivo:Course;
                                                foaf:name ?cname;
                                                acad:courseNumber ?cnumber;
                                                acad:courseSubject ?csubject;
                                                vivo:AcademicDepartment "%s"^^xsd:string.      
                                            }
                                            """ % department
                                       })

        y = json.loads(response.text)

        # print("\n\n--------------------\n", y, "\n--------------------\n\n")

        results = y["results"]
        bindings = results["bindings"]

        course = ""
        courses_offered = []

        for result in bindings:
            for key in result:
                if key == "csubject":
                    for subKey in result[key]:
                        if subKey == "value":
                            course = result[key][subKey]
                if key == "cnumber":
                    for subKey in result[key]:
                        if subKey == "value":
                            course = course + " " + result[key][subKey]
            courses_offered.append(course)

        print("\n", department, " Offers:\n")
        for course in courses_offered:
            print(course, "\n")

        return []
