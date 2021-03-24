import pandas as pd  # for handling csv and csv contents
from rdflib import Graph, Literal, RDF, URIRef, Namespace, Dataset  # basic RDF handling
from rdflib.namespace import FOAF, RDFS, XSD  # most common namespaces
import urllib.parse  # for parsing strings to URI's
import csv


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

            # -------------------------------------------------------------------------------------------------------
            # TODO: Complete code to add a new triple with [Course key, courseHas, acad.tutorial] (as done above)
            # -------------------------------------------------------------------------------------------------------
            elif row[5] == 'TUT':
                # If a course has a tutorial component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Tutorial))

            # -------------------------------------------------------------------------------------------------------
            # TODO: Complete code to add a new triple with [Course key, courseHas, acad.lab] (as done above)
            # -------------------------------------------------------------------------------------------------------
            elif row[5] == 'LAB':
                # If a course has a laboratory component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Lab))

            # -------------------------------------------------------------------------------------------------------
            # TODO: Complete code to add a new triple with [Course key, courseHas, acad.lab] (as done above)
            # -------------------------------------------------------------------------------------------------------
            elif row[5] == 'STU':
                # If a course has a studio component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Studio))

            # -------------------------------------------------------------------------------------------------------
            # TODO: Complete code to add a new triple with [Course key, courseHas, acad.courseOutline] (as done above) for COMP474 & COMP346
            # -------------------------------------------------------------------------------------------------------
            # Don't all courses have an outline?


            # -------------------------------------------------------------------------------------------------------
            # TODO: Link new Topic triple with respective course [Course key, courseHas, acad.lab]
            # -------------------------------------------------------------------------------------------------------
            if row[1] == "COMP" and row[2] == "346":
                # Add Topic triples
                all_topics = open("346topics.txt").readlines()
                for topic in all_topics:
                    topic = topic.replace("\n", "")
                    topic_arg = topic.split("\" ")
                    label = topic_arg[0].replace("\"", "")
                    uri = topic_arg[1]

                    g.add((URIRef(uri), RDF.type, URIRef("http://www.example.org/topic/")))
                    g.add((URIRef(uri), RDFS.label, Literal(label.title())))
                    # MUST FIND A WAY TO LINK THE TOPICS TO THE COURSE IN THE GRAPH
                g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Topic))
            
            if row[1] == "COMP" and row[2] == "474":
                # Add Topic triples
                all_topics = open("474topics.txt").readlines()
                for topic in all_topics:
                    topic = topic.replace("\n", "")
                    topic_arg = topic.split("\" ")
                    label = topic_arg[0].replace("\"", "")
                    uri = topic_arg[1]

                    g.add((URIRef(uri), RDF.type, URIRef("http://www.example.org/topic/")))
                    g.add((URIRef(uri), RDFS.label, Literal(label.title())))
                    # MUST FIND A WAY TO LINK THE TOPICS TO THE COURSE IN THE GRAPH
                g.add((URIRef(ACADDATA + key), ACAD.courseHas, ACAD.Topic))


print(g.serialize(format='turtle').decode('UTF-8'))
# g.serialize('GraphData.ttl', format='turtle')
