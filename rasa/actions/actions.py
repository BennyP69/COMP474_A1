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


# Q1) Which [topics] are covered in [course] [lecture]?
class TopicsCourseLecture(Action):

    def name(self) -> Text:
        return "action_course_lecture_topics"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].upper().replace(" ", "")
        lecture = tracker.slots['lecture'].replace(" ", "")

        values = re.split(r'([^\d]*)(\d.*)', lecture, maxsplit=1)

        lnumber = values[2]

        # print(course)
        # print(lecture)

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
                    
                    SELECT ?courseName ?topicLabel
                    WHERE{
                    ?course acad:courseHas acaddata:%s-%s.
                    ?course foaf:name ?courseName.
                    acaddata:%s-%s acad:coversTopic ?topic.
                    ?topic rdfs:label ?topicLabel.
                    }
                    """ % (course, lecture, course, lecture)
                                       })

        # # Use the json module to load CKAN's response into a dictionary.

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]

        topics_offered = []

        for result in results["bindings"]:
            topicLabel = result["topicLabel"]
            topic = topicLabel["value"]
            topics_offered.append(topic)

        if not topics_offered:
            print(f"Lecture {lnumber} of the course {course} does not exist or does not cover any topic.")
        else:
            answer = "Lecture " + lnumber + " of the course " + course + " covers the following topics:\n"
            for topic in topics_offered:
                answer = answer + "- " + topic + "\n"
            print(answer)

        return []


# Q2) What is course [course] about?
class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = tracker.slots['course'].replace(" ", "")

        print(course)

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)
        print(values)

        csubject = values[1].upper()
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


# Q3) Which courses at [university] teach [topic]?
class WhichCourseAtUniTeachTopic(Action):

    def name(self) -> Text:
        return "action_course_uni_topic"

    def response_request(self, uni, topic):
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

                            SELECT ?courseName
                            WHERE{
                            acaddata:%s acad:offers ?course.
                            ?course foaf:name ?courseName.
                            ?course acad:coversTopic acaddata:%s.
                            }
                            """ % (uni, topic)
                                       })
        # Use the json module to load CKAN's response into a dictionary.

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]

        courses_offer_topic = []

        for result in results["bindings"]:
            courseName = result["courseName"]
            course = courseName["value"]
            courses_offer_topic.append(course)

        return courses_offer_topic

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        uni = tracker.slots['university'].capitalize()

        if uni == "Concordia":
            uni = f"{uni}_University"

        if uni == "":
            uni = "Concordia"

        topic = tracker.slots['topic'].title().replace(" ", "_")

        print(topic)

        courses_offer_topic = self.response_request(uni, topic)

        if not courses_offer_topic:
            topic = topic.upper()
            courses_offer_topic = self.response_request(uni, topic)

        if not courses_offer_topic:
            topic = topic.lower()
            courses_offer_topic = self.response_request(uni, topic)

        if not courses_offer_topic:
            uni = uni.replace("_", " ")
            topic = topic.replace("_", " ")
            print(f"No courses at {uni} offer the topic {topic}.")
        else:
            uni = uni.replace("_", " ")
            topic = topic.replace("_", " ")
            answer = f"The following courses at {uni} offer the topic {topic}:\n"
            for course in courses_offer_topic:
                answer = answer + "- " + course + "\n"
            print(answer)

        return []


# Q4) Which department offers the course [course]?
class WhichDepOffersCourse(Action):

    def name(self) -> Text:
        return "action_dep_offer_course"

    def response_request(self, csubject, cnumber):
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

                            SELECT ?cname ?cdepartment
                            WHERE{
                            ?course a vivo:Course.
                            ?course foaf:name ?cname.
                            ?course acad:courseNumber "%s"^^xsd:int.
                            ?course acad:courseSubject "%s"^^xsd:string.
                            ?course vivo:AcademicDepartment ?cdepartment.
                            }
                            """ % (cnumber, csubject)
                                       })
        # Use the json module to load CKAN's response into a dictionary.

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]

        departments = []

        for result in results["bindings"]:
            cdepartment = result["cdepartment"]
            dep = cdepartment["value"]
            departments.append(dep)

        return departments

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].replace(" ", "")

        # print(course)

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)
        print(values)

        csubject = values[1].upper()
        cnumber = values[2]

        departments = self.response_request(csubject, cnumber)

        if not departments:
            print(f"The course {course} is not offered in any departments.")
        else:
            answer = f"The course {course} is offered in the department:\n"
            for dep in departments:
                answer = answer + "- " + dep + "\n"
            print(answer)

        return []


# Q5) What content does [course] [lecture] consist of?
class ContentCourseLecture(Action):

    def name(self) -> Text:
        return "action_content_course_lecture"

    def response_request(self, course, lnumber):
        # print(course)
        # print(lnumber)
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

                            SELECT ?typeLabel
                            WHERE{
                            acaddata:%s-LEC%s acad:hasContent ?content.
                            ?content a ?type.
                            ?type rdfs:label ?typeLabel.
                            }
                            """ % (course, lnumber)
                                       })
        # Use the json module to load CKAN's response into a dictionary.

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]

        content = []

        for result in results["bindings"]:
            typeLabel = result["typeLabel"]
            con = typeLabel["value"]
            content.append(con)

        return content

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].upper().replace(" ", "")
        lecture = tracker.slots['lecture'].replace(" ", "")

        values = re.split(r'([^\d]*)(\d.*)', lecture, maxsplit=1)

        lnumber = values[2]

        content = self.response_request(course, lnumber)

        if not content:
            print(f"The course {course} lecture{lnumber} does not have any content.")
        else:
            answer = f"The course {course} lecture{lnumber} consists of the following content:\n"
            for con in content:
                answer = answer + "- " + con + "\n"
            print(answer)

        return []
