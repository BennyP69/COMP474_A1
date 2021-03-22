import pandas as pd  # for handling csv and csv contents
from rdflib import Graph, Literal, RDF, URIRef, Namespace  # basic RDF handling
from rdflib.namespace import FOAF, RDFS, XSD  # most common namespaces
import urllib.parse  # for parsing strings to URI's
import csv


url = 'opendata/CATALOG.csv'
df = pd.read_csv(url, sep=",", quotechar='"')

g = Graph()
ACAD = Namespace('http://acad.io/schema#')
ACADDATA = Namespace('http://acad.io/data#')
VIVO = Namespace('http://vivoweb.org/ontology/core#')

# List to store course keys so we can create new triples when accessing the .csv file that does not have them
key_number_name = []


for index, row in df.iterrows():
    g.add((URIRef(ACADDATA + row['Key']), RDF.type, VIVO.Course))

    key = row['Key']
    number = int("0")
    name = ""

    if not pd.isnull(row['Title']):
        g.add((URIRef(ACADDATA + row['Key']), FOAF.name, Literal(row['Title'], datatype=XSD.string)))
    if not pd.isnull(row['Course code']):
        g.add((URIRef(ACADDATA + row['Key']), ACAD.courseSubject, Literal(row['Course code'], datatype=XSD.string)))
        name = row['Course code']
    if not pd.isnull(row['Course number']):
        g.add((URIRef(ACADDATA + row['Key']), ACAD.courseNumber, Literal(row['Course number'], datatype=XSD.int)))
        number = row['Course number']
    if not pd.isnull(row['Description']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.description, Literal(row['Description'], datatype=XSD.string)))
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

with open(url2) as csv_file:
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
                        g.add((URIRef(ACADDATA + key), ACAD.has_component, ACAD.Lecture))
            # -------------------------------------------------------------------------------------------------------
            # TODO: Complete code to add a new triple with [Course key, has_component, acad.tutorial] (as done above)
            # -------------------------------------------------------------------------------------------------------
            elif row[5] == 'TUT':
                # If a lecture has a tutorial component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.has_component, ACAD.Tutorial))


            # -------------------------------------------------------------------------------------------------------
            # TODO: Complete code to add a new triple with [Course key, has_component, acad.lab] (as done above)
            # -------------------------------------------------------------------------------------------------------
            elif row[5] == 'LAB':
                # If a lecture has a laboratory component, get name and number
                name = row[1]
                number = row[2]
                for element in key_number_name:
                    if element[1] == number and element[2] == name:
                        key = element[0]
                        g.add((URIRef(ACADDATA + key), ACAD.has_component, ACAD.Lab))


# print(g.serialize(format='turtle').decode('UTF-8'))
g.serialize('coursesData.ttl', format='turtle')
