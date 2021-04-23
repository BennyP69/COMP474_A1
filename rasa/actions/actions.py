# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import requests
import json
import re
import inflect

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

        if len(lnumber) == 1:
            lnumber = "0" + lnumber


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
                    ?course acad:courseHas acaddata:%s-LEC-%s.
                    ?course foaf:name ?courseName.
                    acaddata:%s-LEC-%s a acad:Lecture.
                    acaddata:%s-LEC-%s acad:hasContent ?content.
                    ?content acad:coversTopic ?topic.
                    ?topic rdfs:label ?topicLabel.
                    }
                    """ % (course, lnumber, course, lnumber, course, lnumber)
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
            dispatcher.utter_message(text=f"Lecture {lnumber} of the course {course} does not exist or does not cover any topic.")
        else:
            answer = "Lecture " + lnumber + " of the course " + course + " covers the following topics:\n"
            for topic in topics_offered:
                topic = topic.replace("_", " ")
                answer = answer + "- " + topic + "\n"
            dispatcher.utter_message(text=f"{answer}")

        return []


# Q2) What is course [course] about?
class CourseDescription(Action):

    def name(self) -> Text:
        return "action_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = tracker.slots['course'].replace(" ", "")

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)

        csubject = values[1].upper()
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

        dispatcher.utter_message(text=f"Description of course {csubject} {cnumber}: {vdescription}")

        return []


# Q3) Which courses at [university] teach [topic]?
class WhichCourseAtUniTeachTopic(Action):

    def name(self) -> Text:
        return "action_course_uni_topic"

    def response_request(self, topic):
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

                            SELECT  ?c1 ?cname (COUNT( ?content) AS ?topicCount)
                            WHERE {
                                ?course a vivo:Course.
                                ?course foaf:name ?cname.
                                ?course acad:courseSubject ?csubject.
                                ?course acad:courseNumber ?cnumber.
                                ?course acad:courseHas ?component.
                                ?component acad:hasContent ?content.
                                ?content acad:coversTopic acaddata:%s.

                                BIND(CONCAT(?csubject, " ", STR(?cnumber)) AS ?c1)
                            } 
                            GROUP BY ?cname ?c1
                            ORDER BY DESC(?topicCount)
                            """ % topic
                                       })
        # Use the json module to load CKAN's response into a dictionary.

        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]

        # print(results)

        courses = []

        for result in results["bindings"]:
            courseCode = result["c1"]
            courseName = result["cname"]
            topicCount = result["topicCount"]
            code = courseCode["value"]
            name = courseName["value"]
            count = topicCount["value"]
            course = {"courseCode": code, "courseName": name, "topicCount": count}
            courses.append(course)

        return courses

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        p = inflect.engine()

        t = tracker.slots['topic'].strip()

        t_sing = p.singular_noun(t)

        if t_sing is False:
            t_sing = t

        otopic = t_sing.replace(" ", "_")

        courses_offer_topic = self.response_request(otopic)

        if not courses_offer_topic:
            topic = otopic[0].upper() + otopic[1:]
            courses_offer_topic = self.response_request(topic)

        if not courses_offer_topic:
            topic = otopic.title()
            courses_offer_topic = self.response_request(topic)

        if not courses_offer_topic:
            topic = otopic.upper()
            courses_offer_topic = self.response_request(topic)

        if not courses_offer_topic:
            topic = otopic.lower()
            courses_offer_topic = self.response_request(topic)

        if not courses_offer_topic:
            topic = topic.replace("_", " ")
            dispatcher.utter_message(text=f"No courses at Concordia University cover the topic {topic}.")
        else:
            topic = otopic.replace("_", " ")
            answer = f"The following courses at Concordia University cover the topic {topic}:\n"
            for course in courses_offer_topic:
                code = course['courseCode']
                name = course['courseName']
                count = course['topicCount']
                answer = answer + "- " + code + " " + name + "\tFrequency of Topic: " + count + "\n"
            dispatcher.utter_message(text=f"{answer}")

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

        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)

        csubject = values[1].upper()
        cnumber = values[2]

        departments = self.response_request(csubject, cnumber)

        if not departments:
            dispatcher.utter_message(text=f"The course {course} is not offered in any departments.")
        else:
            answer = f"The course {course} is offered in the department:\n"
            for dep in departments:
                answer = answer + "- " + dep + "\n"
            dispatcher.utter_message(text=f"{answer}")

        return []


# Q5) What content does [course] [lecture] consist of?
class ContentCourseLecture(Action):

    def name(self) -> Text:
        return "action_content_course_lecture"

    def response_request(self, course, lnumber):
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
                            acaddata:%s-LEC-%s acad:hasContent ?content.
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

        if len(lnumber) == 1:
            lnumber = "0" + lnumber

        content = self.response_request(course, lnumber)

        if not content:
            dispatcher.utter_message(text=f"The course {course} lecture {lnumber} does not have any content.")
        else:
            answer = f"The course {course} lecture {lnumber} consists of the following content:\n"
            for con in content:
                answer = answer + "- " + con + "\n"
            dispatcher.utter_message(text=f"{answer}")

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
            dispatcher.utter_message(text="Sorry, we currently only support finding components of COMP 474 and COMP 346.")
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

                            SELECT ?cname ?component ?componentLabel
                            WHERE{
                                ?course a vivo:Course.
                                ?course foaf:name ?cname.
                                ?course acad:courseNumber "%s"^^xsd:int.
                                ?course acad:courseSubject "%s"^^xsd:string.
                                ?course acad:courseHas ?component.
                                ?component rdfs:label ?componentLabel.
                            }
                            """ % (cnumber, csubject)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        dispatcher.utter_message(text=f"{csubject} {cnumber} has:\n")

        for component in bindings:
            dispatcher.utter_message(text=f"\t-->{component['componentLabel']['value']}\n")

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

        result = y["boolean"]

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

        # print("\n\n--------------------\n" + department + "\n--------------------\n\n")

        if department.lower() == "CSSE" or department.lower() == "computer science and software engineering" or \
                department.lower() == "computer science" or department.lower() == "software engineering":
            department = "Computer Science and Software Engineering (CSSE)"
        elif department.lower() == "BCCE" or \
                department.lower() == "building, civil and environmental engineering" or \
                department.lower() == "building engineering" or department.lower() == "civil engineering" or \
                department.lower() == "environmental engineering":
            department = "Building, Civil and Environmental Engineering (BCEE)"
        elif department.lower() == "ECE" or department.lower() == "electrical engineering" \
                or department.lower() == "computer engineering":
            department = "Electrical and Computer Engineering (ECE)"

        # print("\n\n--------------------\n" + department + "\n--------------------\n\n")

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

        if "concordia" in university.lower() or "university" in university.lower():
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


# CHATBOT Q3 - Which topics are covered in <course event>?"
class ActionTopicsCovered(Action):

    def name(self) -> Text:
        return "action_topics_covered"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course']
        values = re.split(r'([^\d]*)(\d.*)', course, maxsplit=1)
        csubject = values[1].upper().strip()
        cnumber = values[2].strip()

        courseEvent = tracker.slots['courseEvent'].strip()
        og_courseEvent = courseEvent

        eventNumber = re.split(r'([^\d]*)(\d.*)', courseEvent, maxsplit=1)[2]
        if len(eventNumber) == 1:
            eventNumber = "0" + eventNumber

        query = ""

        if "lec" in courseEvent.lower():
            courseEvent = "acaddata:" + csubject + cnumber + "-LEC-" + eventNumber
            query = """
                        PREFIX vivo: <http://vivoweb.org/ontology/core#> 
                        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX DC: <http://purl.org/dc/terms/> 
                        PREFIX acad: <http://acad.io/schema#> 
                        PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                        PREFIX acaddata: <http://acad.io/data#>

                        SELECT ?topic ?topicLabel ?dbpediaURI
                        WHERE {
                          ?course a vivo:Course.
                          ?course foaf:name ?courseName.
                          ?course acad:courseNumber "%s"^^xsd:int.
                          ?course acad:courseSubject "%s"^^xsd:string.
                          ?course acad:courseHas %s.
                          %s acad:hasContent ?eventDoc.
                          ?eventDoc acad:coversTopic ?topic.
                          ?topic a acad:topic.
                          ?topic rdfs:label ?topicLabel.
                          ?topic rdfs:seeAlso ?dbpediaURI
                        }
                        """ % (cnumber, csubject, courseEvent, courseEvent)

        if "tut" in courseEvent.lower():
            courseEvent = "acaddata:" + csubject + cnumber + "-TUT-" + eventNumber
            query = """
                        PREFIX vivo: <http://vivoweb.org/ontology/core#> 
                        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX DC: <http://purl.org/dc/terms/> 
                        PREFIX acad: <http://acad.io/schema#> 
                        PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                        PREFIX acaddata: <http://acad.io/data#>

                        SELECT ?topic ?topicLabel ?dbpediaURI
                        WHERE {
                          ?course a vivo:Course.
                          ?course foaf:name ?courseName.
                          ?course acad:courseNumber "%s"^^xsd:int.
                          ?course acad:courseSubject "%s"^^xsd:string.
                          ?course acad:courseHas ?courseLec.
                          ?courseLec acad:lectureEvent %s.
                          %s a acad:Tutorial.
                          %s acad:hasContent ?eventDoc.
                          ?eventDoc acad:coversTopic ?topic.
                          ?topic a acad:topic.
                          ?topic rdfs:label ?topicLabel.
                          ?topic rdfs:seeAlso ?dbpediaURI
                        }
                        """ % (cnumber, csubject, courseEvent, courseEvent, courseEvent)

        if "lab" in courseEvent.lower() or "stu" in courseEvent.lower():
            dispatcher.utter_message(text=f"Sorry, {csubject} {cnumber} does not have a {courseEvent}")
            return

        # print(query)

        response = requests.post("http://localhost:3030/acad/sparql",
                                 data={'query': query})

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        # print(bindings)

        if not bindings:
            dispatcher.utter_message(text=f"Sorry, {csubject} {cnumber} doesn't have a {courseEvent}\n")
            return

        dispatcher.utter_message(text=f"{og_courseEvent} of {csubject} {cnumber} covers:\n")

        for result in bindings:
            dispatcher.utter_message(text=f"\t--> {result['topicLabel']['value']} || URI: {result['dbpediaURI']['value']}\n")

        return []
