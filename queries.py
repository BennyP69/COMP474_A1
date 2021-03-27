import pandas as pd #for handling csv and csv contents
from rdflib import Graph, Literal, RDF, URIRef, Namespace #basic RDF handling
from rdflib.namespace import FOAF, RDFS, XSD #most common namespaces
import urllib.parse #for parsing strings to URI's
import requests

# course = input("What is course [course] about?")

g = Graph()
g.parse("GraphData.ttl", format='n3')

# This is an example for the following query: Which [topics] are covered in [course] [lecture]?

# python likes double curly brackets
q = g.query(
    f""" 
SELECT  ?courseName ?lecture ?topicLabel
WHERE{{
	?course a vivo:Course .
	?course acad:courseHas ?lecture.
 	?course foaf:name ?courseName.
  	?lecture a acad:Lecture.
  	?lecture acad:coversTopic ?topic.
 	?topic rdfs:label ?topicLabel.
}} """)

# Here you'll have to change the row.attribute accordingly
for row in q:
    print(f"Course Name: {row.courseName}\tLecture: {row.lecture}\tTopic: {row.topicLabel}")