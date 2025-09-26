from rdflib import Graph, Namespace, URIRef, BNode
from rdflib.namespace import RDF, OWL
import ssl
import urllib.request
from rdflib import _networking

DOCO = Namespace("http://purl.org/spar/doco/")

def get_local_name(uri):
    if isinstance(uri, URIRef):
        return uri.split('/')[-1]
    return str(uri)

def custom_urlopen(request):
    return urllib.request.urlopen(request, context=ssl_context)

def extract_owl_rules(g):
    rules = []

    for class_uri in g.subjects(RDF.type, OWL.Class):
        if str(class_uri).startswith(str(DOCO)):
            class_name = get_local_name(class_uri)

            for _, predicate, obj in g.triples((class_uri, None, None)):
                if not isinstance(obj, BNode):
                    property_name = get_local_name(predicate)
                    object_name = get_local_name(obj)
                    rules.append(f"{class_name} {property_name} {object_name}")
    return rules

if __name__ == "__main__":

    ssl_context = ssl._create_unverified_context()
    _networking.urlopen = custom_urlopen

    g = Graph()
    ontology_file_path = 'https://svn.code.sf.net/p/sempublishing/code/DoCO/2015-07-03_doco-1_3.owl'
    g.parse(ontology_file_path, format="xml")

    rules = extract_owl_rules(g)

    for rule in rules:
        print(rule)