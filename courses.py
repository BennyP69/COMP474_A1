import pandas as pd #for handling csv and csv contents
from rdflib import Graph, Literal, RDF, URIRef, Namespace #basic RDF handling
from rdflib.namespace import FOAF, RDFS, XSD #most common namespaces
import urllib.parse #for parsing strings to URI's

url = 'opendata/CATALOG.csv'
df = pd.read_csv(url, sep=",", quotechar='"')

g = Graph()
ACAD = Namespace('http://acad.io/schema#')
ACADDATA = Namespace('http://acad.io/data#')
VIVO = Namespace('http://vivoweb.org/ontology/core#')

for index, row in df.iterrows():
    g.add((URIRef(ACADDATA+row['Key']), RDF.type, VIVO.Course))
    if not pd.isnull(row['Title']):
        g.add((URIRef(ACADDATA+row['Key']), FOAF.name, Literal(row['Title'], datatype=XSD.string)))
    if not pd.isnull(row['Course code']):
        g.add((URIRef(ACADDATA+row['Key']), ACAD.courseSubject, Literal(row['Course code'], datatype=XSD.string)))
    if not pd.isnull(row['Course number']):
        g.add((URIRef(ACADDATA+row['Key']), ACAD.courseNumber, Literal(row['Course number'], datatype=XSD.Integer)))
    if not pd.isnull(row['Description']):
        g.add((URIRef(ACADDATA+row['Key']), VIVO.description, Literal(row['Description'], datatype=XSD.string)))
    if not pd.isnull(row['Website']):
        g.add((URIRef(ACADDATA+row['Key']), RDFS.seeAlso, Literal(row['Website'], datatype=XSD.string)))
    if not pd.isnull(row['Faculty']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.departmentOrSchool, Literal(row['Faculty'], datatype=XSD.string)))
    if not pd.isnull(row['Department']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.AcademicDepartment, Literal(row['Department'], datatype=XSD.string)))
    if not pd.isnull(row['Program']):
        g.add((URIRef(ACADDATA + row['Key']), VIVO.Program, Literal(row['Program'], datatype=XSD.string)))

print(g.serialize(format='turtle').decode('UTF-8'))
g.serialize('coursesData.ttl', format='turtle')