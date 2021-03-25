import pandas as pd  # for handling csv and csv contents
from rdflib import Graph, Literal, RDF, URIRef, Namespace, Dataset  # basic RDF handling
from rdflib.namespace import FOAF, RDFS, XSD  # most common namespaces
import urllib.parse  # for parsing strings to URI's
import csv
import os.path
from os import path


url = 'opendata/CATALOG.csv'
df = pd.read_csv(url, sep=",", quotechar='"')

# Namespaces for our vocabulary items (schema information, existing vocabulary, etc.)
ACAD = Namespace('http://acad.io/schema#')
ACADDATA = Namespace('http://acad.io/data#')
VIVO = Namespace('http://vivoweb.org/ontology/core#')
DC = Namespace('http://purl.org/dc/terms/')

# Initialize a dataset and bind namespaces
dataset = Dataset()
dataset.bind('ACAD', ACAD)
dataset.bind('ACADDATA', ACADDATA)
dataset.bind('VIVO', VIVO)
dataset.bind('DC', DC)

g = dataset.graph()

# Load the externally defined schema into the default graph (context) of the dataset
dataset.default_context.parse('courseSchema.ttl', format='turtle')

# List to store course keys so we can create new triples when accessing the .csv file that does not have them
key_number_name = []

for index, row in df.iterrows():
    g.add((URIRef(ACADDATA + row['Key']), RDF.type, VIVO.Course))

    key = row['Key']
    number = int("0")
    name = ""

    g.add((ACADDATA.Concordia_University, ACAD.offers, URIRef(ACADDATA + row['Key'])))
    if not pd.isnull(row['Title']):
        g.add((URIRef(ACADDATA + row['Key']), FOAF.name, Literal(row['Title'], datatype=XSD.string)))
    if not pd.isnull(row['Course code']):
        g.add((URIRef(ACADDATA + row['Key']), ACAD.courseSubject, Literal(row['Course code'], datatype=XSD.string)))
        name = row['Course code']
    if not pd.isnull(row['Course number']):
        g.add((URIRef(ACADDATA + row['Key']), ACAD.courseNumber, Literal(row['Course number'], datatype=XSD.int)))
        number = row['Course number']
    if not pd.isnull(row['Description']):
        g.add((URIRef(ACADDATA + row['Key']), DC.description, Literal(row['Description'], datatype=XSD.string)))
    if not pd.isnull(row['Website']):
        g.add((URIRef(ACADDATA + row['Key']), RDFS.seeAlso, Literal(row['Website'], datatype=XSD.string)))
    if not pd.isnull(row['Faculty']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.departmentOrSchool, Literal(row['Faculty'], datatype=XSD.string)))
    if not pd.isnull(row['Department']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.AcademicDepartment, Literal(row['Department'], datatype=XSD.string)))
    if not pd.isnull(row['Program']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.Program, Literal(row['Program'], datatype=XSD.string)))

    # Create new entry in the list with course key, number, and name
    key_number_name.append([key, number, name])

url2 = 'opendata/CU_SR_OPEN_DATA_CATALOG.csv'
columns = []

with open(url2, encoding='ISO-8859-1') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    name = ""
    number = ""

    for row in csv_reader:
        if line_count == 0:
            for name in row:
                columns.append(name)
            line_count += 1
        else:
            if row[5] == 'LEC':
                # If a course has a lecture component, get it's name and number
                name = row[1]
                number = row[2]
                # Iterate the list previously made containing the course keys
                # If the name and number matches anything in the list, grab the course key
                # Create a new triple stating that the course has a lecture component.
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Lecture))

            elif row[5] == 'TUT':
                # If a course has a tutorial component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Tutorial))

            elif row[5] == 'LAB':
                # If a course has a laboratory component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Lab))

            elif row[5] == 'STU':
                # If a course has a studio component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Studio))

            # -----------------------------------------------------
            #                   C O M P  3 4 6
            # -----------------------------------------------------
            if row[1] == "COMP" and row[2] == "346":
                # -----------------------------------------------------
                #           ADD OUTLINE TRIPLES
                # Check if outline file exists
                course_outline_uri = "COURSES/COMP346/Outline/comp346_F20_course_outline.pdf"
                if path.exists(course_outline_uri):
                    # If it does, make outline triple
                    g.add((URIRef(course_outline_uri), RDF.type, ACAD.courseOutline))
                    # And link outline to course
                    g.add((URIRef(ACADDATA + key), ACAD.courseHas, URIRef(course_outline_uri)))

                # -----------------------------------------------------
                #           ADD LECTURE TRIPLES
                lec_num = 1
                lectures_path = "COURSES/COMP346/LEC/"
                for filename in os.listdir(lectures_path):
                    if filename.endswith(".pdf"):
                        # Add triple defining each lecture of a course.
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(lec_num)), RDF.type, ACAD.Lecture))

                        # Add triple for lecture number
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(lec_num)), ACAD.lectureNumber,
                               Literal(lec_num, datatype=XSD.int)))

                        # Add triple defining lecture slides
                        g.add((URIRef(lectures_path + filename), RDF.type, ACAD.slides))

                        # Add triple linking slide to lecture
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(lec_num)), ACAD.hasContent,
                               URIRef(lectures_path + filename)))

                        # Triple linking lecture to course
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, URIRef(ACADDATA + "COMP346-LEC" + str(lec_num))))

                        lec_num = lec_num + 1
                # -----------------------------------------------------
                #           ADD TUT TRIPLES
                tut_num = 1
                tuts_path = "COURSES/COMP346/TUT/"
                for filename1 in os.listdir(tuts_path):
                    if filename1.endswith(".pdf"):
                        # Triple defining tut
                        g.add((URIRef(ACADDATA + "COMP346-TUT" + str(tut_num)), RDF.type, ACAD.Tutorial))

                        # Triple defining tut number
                        g.add((URIRef(ACADDATA + "COMP346-TUT" + str(tut_num)), ACAD.lectureNumber,
                               Literal(tut_num, datatype=XSD.int)))

                        # Triple defining tut slides
                        g.add((URIRef(tuts_path + filename1), RDF.type, ACAD.slides))

                        # Triple linking slide to tut
                        g.add((URIRef(ACADDATA + "COMP346-TUT" + str(tut_num)), ACAD.hasContent,
                               URIRef(tuts_path + filename1)))

                        # Triple linking tut to lecture
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(tut_num)), ACAD.lectureEvent,
                               URIRef(ACADDATA + "COMP346-TUT" + str(tut_num))))

                        tut_num = tut_num + 1

                # -----------------------------------------------------
                #           ADD TOPIC TRIPLES
                all_topics = open("346topics.txt").readlines()
                count = 1
                for topic in all_topics:
                    topic = topic.replace("\n", "")
                    topic_arg = topic.split("\" ")
                    label = topic_arg[0].replace("\"", "")
                    uri = topic_arg[1]

                    # Adding triples for each topic of COMP 346
                    g.add((URIRef(ACADDATA + label), RDF.type, ACAD.topic))
                    g.add(((URIRef(ACADDATA + label)), RDFS.seeAlso, URIRef(uri)))
                    g.add((URIRef(ACADDATA + label), RDFS.label, Literal(label)))
                    # Triple linking course to topic
                    g.add((URIRef(ACADDATA + key), ACAD.coversTopic, URIRef(ACADDATA + label)))

                    # Triple linking topic to lecture
                    if count == 1:
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(count)), ACAD.coversTopic,
                               URIRef(ACADDATA + label)))
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(count + 1)), ACAD.coversTopic,
                               URIRef(ACADDATA + label)))
                        count = count + 1
                    else:
                        g.add((URIRef(ACADDATA + "COMP346-LEC" + str(count)), ACAD.coversTopic,
                               URIRef(ACADDATA + label)))

                    count = count + 1

            # -----------------------------------------------------
            #                   C O M P  4 7 4
            # -----------------------------------------------------
            if row[1] == "COMP" and row[2] == "474":

                # -----------------------------------------------------
                #           ADD OUTLINE TRIPLES
                # Check if outline file exists
                course_outline_uri = "COURSES/COMP474/Outline/course_outline_comp474_6741_w2021.pdf"
                if path.exists(course_outline_uri):
                    # If it does, make outline triple
                    g.add((URIRef(course_outline_uri), RDF.type, ACAD.courseOutline))
                    # And link outline to course
                    g.add((URIRef(ACADDATA + key), ACAD.courseHas, URIRef(course_outline_uri)))

                # -----------------------------------------------------
                #           ADD LECTURE TRIPLES
                lec_num = 1
                lectures_path = "COURSES/COMP474/LEC/"
                for filename in os.listdir(lectures_path):
                    if filename.endswith(".pdf"):
                        # Add triple defining each lecture of a course.
                        g.add((URIRef(ACADDATA + "COMP474-LEC" + str(lec_num)), RDF.type, ACAD.Lecture))

                        # Add triple for lecture number
                        g.add((URIRef(ACADDATA + "COMP474-LEC" + str(lec_num)), ACAD.lectureNumber,
                                Literal(lec_num, datatype=XSD.int)))

                        # Add triple defining lecture slides
                        g.add((URIRef(lectures_path + filename), RDF.type, ACAD.slides))

                        # Add triple linking slide to lecture
                        g.add((URIRef(ACADDATA + "COMP474-LEC" + str(lec_num)), ACAD.hasContent,
                                URIRef(lectures_path + filename)))
                        lec_num = lec_num + 1

                # -----------------------------------------------------
                #           ADD WORKSHEET TRIPLES
                worksheet_num = 1
                worksheet_path = "COURSES/COMP474/Worksheets/"
                for filename2 in os.listdir(worksheet_path):
                    if filename2.endswith(".pdf"):
                        # Triple defining each worksheet
                        g.add((URIRef(worksheet_path + filename2), RDF.type, ACAD.Worksheet))

                        # Triple linking worksheet to lecture
                        g.add((URIRef(ACADDATA + "COMP474-LEC" + str(worksheet_num)), ACAD.hasContent,
                               URIRef(worksheet_path + filename2)))

                        worksheet_num = worksheet_num + 1

                # -----------------------------------------------------
                #           ADD TOPIC TRIPLES
                all_topics = open("474topics.txt").readlines()
                for topic in all_topics:
                    topic = topic.replace("\n", "")
                    topic_arg = topic.split("\" ")
                    label = topic_arg[0].replace("\"", "")
                    uri = topic_arg[1]

                    print(topic_arg)
                    print(label)
                    print(uri, "\n\n")

                    # Adding triples for each topic of COMP 474
                    g.add((URIRef(ACADDATA + label), RDF.type, ACAD.topic))
                    g.add((URIRef(ACADDATA + label), RDFS.seeAlso, URIRef(uri)))
                    g.add((URIRef(ACADDATA + label), RDFS.label, Literal(label)))
                    # Triple linking course to topic
                    g.add((URIRef(ACADDATA + key), ACAD.coversTopic, URIRef(ACADDATA + label)))

                    # Triple linking topic to lecture
                    # Picking the proper lecture corresponding to the correct topic in 474topics.txt
                    if label == "Intelligent_Systems":
                        count = 1
                    elif label == "Knowledge_Graph":
                        count = 2
                    elif label == "Vocabularies" or label == "Ontologies":
                        count = 3
                    elif label == "Knowledge_Base_Queries" or label == "SPARQL" or \
                            label == "Web_Ontology_Language":
                        count = 4
                    elif label == "Linked_Open_Data" or label == "Knowledge_Base":
                        count = 5
                    elif label == "Personalization_And_Recommender_Systems":
                        count = 6
                    elif label == "Machine_Learning":
                        count = 7
                    elif label == "Intelligent_Agents":
                        count = 8
                    elif label == "Text_Mining":
                        count = 9
                    # Linking the topic to the proper lecture
                    g.add((URIRef(ACADDATA + "COMP474-LEC" + str(count)), ACAD.coversTopic,
                           URIRef(ACADDATA + label)))


# print(g.serialize(format='turtle').decode('UTF-8')) # For testing
g.serialize('GraphData.ttl', format='turtle')
