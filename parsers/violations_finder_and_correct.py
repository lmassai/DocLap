import os
import re
import sys
import shutil
import draw_utilities
import grobid_pdf_with_bb_generator
import overlapping_bb_coordinates_extractor
import correct_with_LLM
import DocLap_pdf_without_errors_generator
from collections import Counter
from logger import Logger
from collections import defaultdict
from pdf2image import convert_from_path
from pathlib import Path

LABEL_MAPPING = {
    'list of authors': 'Author',
    "figure label": "Caption_Figure",
    "table label": "Caption_Table",
    'title': 'Article_title',
    "label": "Caption",
    'abstract': 'Abstract',
    'figure': 'Figure',
    'table': 'Table',
    'formula': 'Formula',
    'section title': 'Section',
    'Link': 'Link',
    'footnote': 'Note',
    'Acknowledgements': 'Acknowledgements',
    'Reference': 'Reference',
    'sentence': 'phrase'
}

def extract_overlap_pairs_by_page(overlaps):
    result = defaultdict(list)

    for item in overlaps:
        class1, class2 = item["classes"]
        (p1, x1, y1, w1, h1), (p2, x2, y2, w2, h2) = item["coordinates"]

        if p1 != p2:
            continue

        page = p1
        row1 = f"{class1},{page},{x1},{y1},{w1},{h1}"
        row2 = f"{class2},{page},{x2},{y2},{w2},{h2}"
        result[page].append([row1, row2])
    return dict(result)

def extract_images_from_pdf_with_overlaps_already_on_them(pdf_path):
    output_dir = os.path.dirname(os.path.abspath(pdf_path)) + "\\pdf_images"
    os.makedirs(output_dir, exist_ok=True)

    pages = convert_from_path(pdf_path)
    image_info = []

    for i, img in enumerate(pages):
        img_path = os.path.join(output_dir, f"page_{i+1}.png")
        img.save(img_path, "PNG")

def group_lines_by_page(log_output_for_csv_annotation):
    blocks = defaultdict(list)

    lines = log_output_for_csv_annotation.strip().splitlines()
    for line in lines:
        parts = line.split(",")
        page = parts[1]
        blocks[page].append(line)

    return blocks

def apply_replacements_to_file(filepath, replacements):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        for old, new in sorted(replacements.items(), key=lambda x: -len(x[0])):
            pattern = r'\b' + re.escape(old) + r'\b'
            content, count = re.subn(pattern, new, content)
            if count:
                print(f"Replaced '{old}' with '{new}' ({count} occurrences)")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("\n" + filepath + " does not exist!\n")

def apply_label_mapping_to_lines(lines, label_mapping):
    updated_lines = []
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) != 6:
            continue
        label = parts[0].lower()
        mapped_label = label_mapping.get(label, None)
        if mapped_label:
            parts[0] = mapped_label
            updated_lines.append(",".join(parts))
    return updated_lines

def main(pdf_path):
    directory = pdf_path.parent
    out_dir = directory / "to_process"
    out_dir.mkdir(exist_ok=True)

    temp_folder = os.path.join(out_dir, 'temp_pdf')
    output_pdf_path = os.path.join(out_dir, "output_overlaps_with_bboxes.pdf")
    overlapping_folder = os.path.join(temp_folder, 'overlapping')

    page_width, page_height = draw_utilities.get_page_dimensions(pdf_path)

    pdf_log_file = os.path.join(out_dir, 'overlap_errors.txt')
    csv_annotation = os.path.join(out_dir, 'semantic_overlap_annotations.csv')
    overlaps_to_remove_per_LLaVA = os.path.join(out_dir, 'overlaps_to_remove.csv')

    logger = Logger(pdf_log_file)
    logger_for_csv_annotation = Logger(csv_annotation)
    logger_for_overlaps_to_remove = Logger(overlaps_to_remove_per_LLaVA)

    grobid_pdf_with_bb_generator.main(pdf_path)

    overlaps = overlapping_bb_coordinates_extractor.get_overlapping_classes_and_coords(
        os.path.join(out_dir, 'pdf_processor_log.txt')
    )

    all_classes = []
    all_coordinates = []

    for overlap in overlaps:
        all_classes.append(overlap['classes'])
        all_coordinates.append(overlap['coordinates'])

    all_coordinates = [list(tupla) for sotto_lista in all_coordinates for tupla in sotto_lista]

    os.makedirs(overlapping_folder, exist_ok=True)

    class_mapping = {
        'Caption_Figure': 'figure label',
        'Caption_Table': 'table label',
        'Section': 'section title',
        'Author': 'list of authors',
        'Abstract': 'abstract',
        'Caption': 'label',
        'Article_title': 'title',
        'Figure': 'figure',
        'Table': 'table',
        'Formula': 'formula',
        'Link': 'Link',
        'Note': 'footnote',
        'Acknowledgements': 'Acknowledgements',
        'Reference': 'Reference',
        'phrase': 'sentence'
    }

    color_map = {
        'title': (0.8, 0.6, 1),
        'list of authors': (0.7, 0.7, 1),
        'abstract': (1, 0.5, 0),
        'label': (0.6, 0, 0),
        'figure label': (0.6, 0, 0),
        'table label': (0.6, 0, 0),
        'figure': (1, 0, 0),
        'table': (0, 1, 0),
        'formula': (0, 0, 1),
        'section title': (0.7, 0, 1),
        'Link': (0, 1, 1),
        'footnote': (0, 0, 0),
        'Acknowledgements': (1, 0, 1),
        'Reference': (1, 1, 0),
        'sentence': (0.5, 0.5, 0.5)
    }

    associations = defaultdict(list)
    coord_index = 0

    for class_pair in all_classes:
        for class_name in class_pair:
            associations[class_name].append(all_coordinates[coord_index])
            coord_index += 1

    logger.log('Number of overlap violations: ' + str(len(all_classes)) + '\n\n')
    logger.log('Class overlaps which are not allowed by ontology constraints:\n')

    log_output = ''
    log_output_for_csv_annotation = ''

    for i in range(len(all_classes)):
        class_pair = all_classes[i]
        coordinates_pair = all_coordinates[2 * i:2 * i + 2]

        for j in range(len(class_pair)):
            class_name = class_pair[j]
            mapped_class_name = class_mapping.get(class_name, class_name)
            page, x, y, w, h = coordinates_pair[j]

            log_output += f'{mapped_class_name} page: {page}\n'
            log_output += f'{mapped_class_name} coordinates: (page: {page}, x: {x}, y: {y}, w: {w}, h: {h})\n\n'
            log_output_for_csv_annotation += f'{mapped_class_name},{page},{x},{y},{w},{h}\n'

    replacements_for_csv_annotation = {
        "section title": "Section",
        "figure label": "Caption_Figure",
        "table label": "Caption_Table",
        "list of authors": "Author",
        "abstract": "Abstract",
        "title": "Article_title",
        "label": "Caption",
        "figure": "Figure",
        "table": "Table",
        "formula": "Formula",
        "Link": "Link",
        "footnote": "Note",
        "Acknowledgements": "Acknowledgements",
        "Reference": "Reference",
        "sentence": "phrase",
    }

    for old, new in replacements_for_csv_annotation.items():
        log_output_for_csv_annotation = log_output_for_csv_annotation.replace(old, new)

    log_output_for_csv_annotation = log_output_for_csv_annotation.replace(" ", "")
    logger_for_csv_annotation.log(log_output_for_csv_annotation)

    replacements_log_output = {
        "section title": "Section",
        "list of authors": "Author",
        "figure label": "Caption_Figure",
        "table label": "Caption_Table",
        "abstract": "Abstract",
        "title": "Article_title",
        "label": "Caption",
        "figure": "Figure",
        "table": "Table",
        "formula": "Formula",
        "Link": "Link",
        "footnote": "Note",
        "Acknowledgements": "Acknowledgements",
        "Reference": "Reference",
        "sentence": "phrase",
    }

    for old, new in replacements_log_output.items():
        log_output = log_output.replace(old, new)

    logger.log(log_output)

    for class_name, coordinates in associations.items():
        mapped_label = class_mapping.get(class_name, class_name)
        color = color_map.get(mapped_label, (1, 0, 0))
        draw_utilities.create_pdf_with_bounding_boxes(
            pdf_path,
            os.path.join(overlapping_folder, f'overlapping_{class_name}_bboxes.pdf'),
            page_width, page_height,
            coordinates, class_name, color
        )

    first_iteration = True
    for filename in os.listdir(overlapping_folder):
        overlapping_file_path = os.path.join(overlapping_folder, filename)
        if os.path.isfile(overlapping_file_path):
            if first_iteration:
                draw_utilities.overlay_pdfs(pdf_path, overlapping_file_path, output_pdf_path)
                first_iteration = False
            else:
                draw_utilities.overlay_pdfs(output_pdf_path, overlapping_file_path, output_pdf_path)

    if os.path.isdir(overlapping_folder) and not os.listdir(overlapping_folder):
        shutil.copy(pdf_path, output_pdf_path)

    logger.close()

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    pdf_with_just_overlapping_bb_on_it_path = output_pdf_path

    extract_images_from_pdf_with_overlaps_already_on_them(
        pdf_with_just_overlapping_bb_on_it_path)

    output_dir = os.path.dirname(os.path.abspath(pdf_with_just_overlapping_bb_on_it_path)) + "\\pdf_images"
    overlaps_by_page = extract_overlap_pairs_by_page(overlaps)

    all_rows_that_LLaVA_says_to_remove = ""

    for page, overlap_pairs in overlaps_by_page.items():
        image_path = os.path.join(output_dir, f"page_{int(page)}.png")
        print(f"\n--- Page {page} ---")
        print(f"Image: {image_path}")

        for bbox_pair in overlap_pairs:
            print(f"\nBounding boxes to evaluate (original): {bbox_pair}")

            mapped_pair = apply_label_mapping_to_lines(bbox_pair, LABEL_MAPPING)
            print(f"Bounding boxes with mapped labels: {mapped_pair}")

            lines = "\n".join(mapped_pair)
            coords_to_remove = correct_with_LLM.ask_to_LLaVA(lines, image_path)

            print(f"→ LLaVA suggests to remove:\n{coords_to_remove}")
            all_rows_that_LLaVA_says_to_remove += "\n" + coords_to_remove

    all_lines = log_output_for_csv_annotation.strip().splitlines()
    line_counts = Counter(all_lines)

    duplicate_lines = []
    for line, count in line_counts.items():
        if count > 1:
            duplicate_lines.extend([line] * (count - 1))

    replacements_for_duplicates = {
        "list of authors": "Author",
        "section title": "Section",
        "figure label": "Caption_Figure",
        "table label": "Caption_Table",
        "abstract": "Abstract",
        "title": "Article_title",
        "label": "Caption",
        "figure": "Figure",
        "table": "Table",
        "formula": "Formula",
        "Link": "Link",
        "footnote": "Note",
        "Acknowledgements": "Acknowledgements",
        "Reference": "Reference",
        "sentence": "phrase",
    }

    duplicate_lines = [
        line if not replacements_for_duplicates else
        (lambda l: [(l := l.replace(old, new)) for old, new in replacements_for_duplicates.items()] and l)(line)
        for line in duplicate_lines
    ]

    all_rows_that_LLaVA_says_to_remove = "\n".join(
        line for line in (all_rows_that_LLaVA_says_to_remove.strip().splitlines() + duplicate_lines)
        if line.strip() != "Invalid output"
    )

    if all_rows_that_LLaVA_says_to_remove == "":
        all_rows_that_LLaVA_says_to_remove = "None"
    print("\nAll rows that LLaVA says to remove, including the duplicates:\n" + str(all_rows_that_LLaVA_says_to_remove) + "\n")

    replacements_back = {
        'list of authors': 'Author',
        "figure label": "Caption_Figure",
        "table label": "Caption_Table",
        'title': 'Article_title',
        "label": "Caption",
        'abstract': 'Abstract',
        'figure': 'Figure',
        'table': 'Table',
        'formula': 'Formula',
        'section title': 'Section',
        'Link': 'Link',
        'footnote': 'Note',
        'Acknowledgements': 'Acknowledgements',
        'Reference': 'Reference',
        'sentence': 'phrase'
    }

    for human_label, internal_label in replacements_back.items():
        all_rows_that_LLaVA_says_to_remove = all_rows_that_LLaVA_says_to_remove.replace(human_label, internal_label)

    logger_for_overlaps_to_remove.log(all_rows_that_LLaVA_says_to_remove)
    logger_for_overlaps_to_remove.close()

    apply_replacements_to_file(str(out_dir) + '\\' + 'overlap_errors.txt', replacements_back)
    apply_replacements_to_file(str(out_dir) + '\\' + 'pdf_processor_log.txt', replacements_back)
    apply_replacements_to_file(str(out_dir) + '\\' + 'semantic_overlap_annotations.csv', replacements_back)

    for old, new in replacements_back.items():
        all_rows_that_LLaVA_says_to_remove = all_rows_that_LLaVA_says_to_remove.replace(old, new)

    DocLap_pdf_without_errors_generator.main(pdf_path, all_rows_that_LLaVA_says_to_remove)

if __name__ == "__main__":
    pdf_path   = Path(sys.argv[1]).resolve()
    print('Input file: ' + str(pdf_path))
    main(pdf_path)
