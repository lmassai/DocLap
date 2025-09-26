import re
from pathlib import Path
from rdflib import Graph, Namespace
from collections import defaultdict
import ontology_relations_generator
import ssl
import urllib.request
from rdflib import _networking

def custom_urlopen(request):
    return urllib.request.urlopen(request, context=ssl_context)

ssl_context = ssl._create_unverified_context()
_networking.urlopen = custom_urlopen

g = Graph()
ontology_file_path = 'https://svn.code.sf.net/p/sempublishing/code/DoCO/2015-07-03_doco-1_3.owl'
g.parse(ontology_file_path, format="xml")

disjointWith = defaultdict(list)
subClassOf = defaultdict(list)
equivalentClass = defaultdict(list)

def process_relations_into_dicts(relations):
    for relation in relations:
        components = relation.split(' ')
        if len(components) >= 3:
            subject = components[0]
            predicate = components[1]
            obj = ' '.join(components[2:])

            if predicate == 'owl#disjointWith':
                disjointWith[subject].append(obj)
            elif predicate == 'rdf-schema#subClassOf':
                subClassOf[subject].append(obj)
            elif predicate == 'owl#equivalentClass':
                equivalentClass[subject].append(obj)

    categories = {
        "title": [
            "list of authors", "abstract", "table label", "figure label",
            "figure", "table", "section title", "footnote",
            "Acknowledgements", "Reference"
        ],
        "list of authors": [
            "title", "abstract", "table label", "figure label",
            "figure", "table", "formula", "section title", "footnote",
            "Acknowledgements", "Reference"
        ],
        "abstract": [
            "title", "list of authors", "table label", "figure label",
            "figure", "table", "section title", "footnote",
            "Acknowledgements", "Reference"
        ],
        "table label": [
            "title", "list of authors", "abstract", "figure", "table",
            "section title", "footnote", "Acknowledgements", "Reference"
        ],
        "figure label": [
            "title", "list of authors", "abstract", "table label", "figure",
            "table", "section title", "footnote", "Acknowledgements", "Reference"
        ],
        "figure": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "section title", "footnote", "Acknowledgements", "Reference"
        ],
        "table": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "figure", "section title", "footnote",
            "Acknowledgements", "Reference"
        ],
        "formula": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "figure", "table", "section title", "footnote",
            "Acknowledgements", "Reference"
        ],
        "section title": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "figure", "table", "footnote", "Reference"
        ],
        "Link": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "figure", "table", "section title"
        ],
        "footnote": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "figure", "table", "section title", "Acknowledgements"
        ],
        "Acknowledgements": [
            "title", "abstract", "table label", "figure label",
            "figure", "section title", "footnote", "Reference"
        ],
        "Reference": [
            "title", "list of authors", "abstract", "table label",
            "figure label", "figure", "table", "section title",
            "footnote", "Acknowledgements"
        ],
        "sentence": ["figure"]
    }

    for key, vals in categories.items():
        disjointWith[key].extend(vals)

    return disjointWith, subClassOf, equivalentClass

relations = ontology_relations_generator.extract_owl_rules(g)
disjoint, subclass, equivalent = process_relations_into_dicts(relations)

disjointWith = dict(disjointWith)
subClassOf = dict(subClassOf)
equivalentClass = dict(equivalentClass)

print('\nRelations extracted from the DoCO ontology:')
print("disjointWith: ", disjointWith)
print("subClassOf: ", subClassOf)
print("equivalentClass: ", equivalentClass)

def extract_coordinates_from_file(file_path):
    coordinates = []
    pattern = re.compile(
        r'([\w\s_]+)\s+Coords: \(page: (\d+), x: ([\d.]+), y: ([\d.]+), w: ([\d.]+), h: ([\d.]+)\)'
    )

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                class_name = match.group(1).strip()
                page = int(match.group(2))
                x = float(match.group(3))
                y = float(match.group(4))
                w = float(match.group(5))
                h = float(match.group(6))

                coordinates.append({
                    'class': class_name,
                    'page': page,
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h
                })
    return coordinates

def check_overlap(box1, box2):
    page1, x1, y1, w1, h1 = box1
    page2, x2, y2, w2, h2 = box2

    if page1 != page2:
        return False

    x_overlap = x1 < x2 + w2 and x2 < x1 + w1
    y_overlap = y1 < y2 + h2 and y2 < y1 + h1

    same_coordinates = (x1 == x2 and y1 == y2 and w1 == w2 and h1 == h2)
    return x_overlap and y_overlap and not same_coordinates

def check_validity(class1, class2):

    if class1 in disjointWith and class2 in disjointWith[class1]:
        return True

    if class1 in subClassOf and class2 in subClassOf[class1]:
        return False

    if class2 in subClassOf and class1 in subClassOf[class2]:
        return False
    else:
        print('Found an overlap between classes: ' + class1 + ' and ' + class2 + ' which is permitted by the ontology rules')
        return False

def process_coordinates(coordinates):
    classes_coordinates_to_print = []

    print('Among all overlapping bounding boxes:')

    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            class1 = coordinates[i]['class']
            class2 = coordinates[j]['class']

            box1 = (
                coordinates[i]['page'], coordinates[i]['x'], coordinates[i]['y'], coordinates[i]['w'], coordinates[i]['h'])
            box2 = (
                coordinates[j]['page'], coordinates[j]['x'], coordinates[j]['y'], coordinates[j]['w'], coordinates[j]['h'])

            if check_overlap(box1, box2):

                overlap_is_not_allowed = check_validity(class1, class2)

                if overlap_is_not_allowed:
                    classes_coordinates_to_print.append((
                        [class1, class2],
                        [box1, box2]
                    ))
    return classes_coordinates_to_print


def find_overlaps(file_path):
    coordinates = extract_coordinates_from_file(file_path)
    mapped_coordinates = []

    for coord in coordinates:

        mapped_class = map_classes([coord['class'], coord['class']])[0]
        new_coord = coord.copy()
        new_coord['class'] = mapped_class
        mapped_coordinates.append(new_coord)

    classes_coordinates_to_print = process_coordinates(mapped_coordinates)

    result = []
    for overlap in classes_coordinates_to_print:

        class_pair, coord_pair = overlap
        box1, box2 = coord_pair

        result.append({
            'classes': class_pair,
            'coordinates': [box1, box2]
        })

    return result

def map_classes(class_pair):

    class_mapping = {
        'Article_title': 'title',
        'Author': 'list of authors',
        'Abstract': 'abstract',
        'Caption': 'label',
        'Caption_Figure': 'figure label',
        'Caption_Table': 'table label',
        'Figure': 'figure',
        'Table': 'table',
        'Formula': 'formula',
        'Section': 'section title',
        'Link': 'Link',
        'Note': 'footnote',
        'Acknowledgements': 'Acknowledgements',
        'Reference': 'Reference',
        'phrase': 'sentence'
    }

    class1 = class_mapping.get(class_pair[0], class_pair[0])
    class2 = class_mapping.get(class_pair[1], class_pair[1])

    return [class1, class2]

def get_overlapping_classes_and_coords(file_path):
    overlaps = find_overlaps(file_path)

    for overlap in overlaps:
        class1, class2 = overlap['classes']
        box1, box2 = overlap['coordinates']
        print(f"Overlap not allowed between {class1} and {class2}: {box1}, {box2}")
    return overlaps

if __name__ == "__main__":
    file_path = Path(__file__).resolve().parent.parent / "uploads" / "to_process" / "pdf_processor_log.txt"
    get_overlapping_classes_and_coords(file_path)
