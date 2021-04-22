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
        print(course)

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

        print("\n\n--------------------\n", y, "\n--------------------\n\n")

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

        if csubject != "COMP" or (cnumber != "346" and cnumber != "474"):
            print("Sorry, we currently only support finding components of COMP 474 and COMP 346.")
            return

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
            dispatcher.utter_message(text=f"COMPONENT: {value} \n")
            # print("COMPONENT: ", value, "\n")

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

        if csubject != "COMP" or (cnumber != "346" and cnumber != "474"):
            print("Sorry, we currently only support finding whether or not COMP 474 or COMP 346 have labs.")
            return

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

        # print(result)
        # print(type(result))
        # dispatcher.utter_message(text=f"{result}")
        if result:
            dispatcher.utter_message(text=f"YES, {csubject} {cnumber} has labs.")
        else:
            dispatcher.utter_message(text=f"NO, {csubject} {cnumber} does not have labs.")

        return []


# Q8) What courses does the [department] department offer?
class ActionDepartmentCourses(Action):

    def name(self) -> Text:
        return "action_department_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        department = tracker.slots['department'].strip()

        print("\n\n--------------------\n" + department + "\n--------------------\n\n")

        if department.upper().replace(" ", "") == "CSSE":
            department = "Computer Science and Software Engineering (CSSE)"
        elif department.upper().replace(" ", "") == "BCCE":
            department = "Building, Civil and Environmental Engineering (BCEE)"
        elif department.upper().replace(" ", "") == "ECE":
            department = "Electrical and Computer Engineering (ECE)"

        print("\n\n--------------------\n" + department + "\n--------------------\n\n")

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

        # print("\n" + department + " offers:\n")
        # for course in courses_offered:
        #     print(course, "\n")

        dispatcher.utter_message(text=f"\n{department} offers:\n")

        for course in courses_offered:
            dispatcher.utter_message(text=f" - {course}\n")

        return []


# Q9) How many courses does the university [university] offer?
class ActionNumberOfUniCourses(Action):

    def name(self) -> Text:
        return "action_number_of_uni_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        university = tracker.slots['university']

        if university.lower() == "concordia university":
            university = "Concordia_University"

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

                                                    SELECT  (COUNT(?course) AS ?coursesNum)
                                                    WHERE{
                                                       acaddata:%s a acad:University.
                                                       acaddata:%s acad:offers ?course.
                                                    } GROUP BY ?uni
                                                    """ % (university, university)
                                       })

        y = json.loads(response.text)

        # print("\n\n--------------------\n", y, "\n--------------------\n\n")

        results = y["results"]
        bindings = results["bindings"]

        numberOfCourses = 0

        for result in bindings:
            for key in result:
                if key == "coursesNum":
                    for subKey in result[key]:
                        if subKey == "value":
                            numberOfCourses = result[key][subKey]

        university = university.replace("_", " ")

        dispatcher.utter_message(text=f"\n {university} offers a total of {numberOfCourses} courses")

        # print("\n", university.replace("_", " "), "offers a total of", numberOfCourses, "courses.\n")


# Q10) How many topics are covered in [course]?
class ActionNumTopicsInCourse(Action):

    def name(self) -> Text:
        return "action_num_topics_in_course"

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

                                                            SELECT (COUNT(?topic) AS ?topicNum)
                                                            WHERE {
                                                                ?course a vivo:Course.
                                                                ?course foaf:name ?courseName.
                                                                ?course acad:courseNumber "%s"^^xsd:int.
                                                                ?course acad:courseSubject "%s"^^xsd:string.
                                                                ?course acad:coversTopic ?topic.
                                                            } GROUP BY ?course ?courseName
                                                            """ % (cnumber, csubject)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        dispatcher.utter_message(text=f"{csubject} {cnumber} covers {bindings[0]['topicNum']['value']} topics")
