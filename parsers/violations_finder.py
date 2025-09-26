import os
import sys
import shutil
import draw_utilities
import grobid_pdf_with_bb_generator
import overlapping_bb_coordinates_extractor
from logger import Logger
from collections import defaultdict

def main(pdf_path):
    directory      = os.path.dirname(os.path.abspath(pdf_path))
    out_dir        = os.path.join(directory, 'to_process')
    temp_folder    = os.path.join(out_dir, 'temp_pdf')
    overlapping_folder = os.path.join(temp_folder, 'overlapping')
    output_pdf_path    = os.path.join(out_dir, 'output_overlaps_with_bboxes.pdf')
    os.makedirs(overlapping_folder, exist_ok=True)
    page_width, page_height = draw_utilities.get_page_dimensions(pdf_path)
    pdf_log_file   = os.path.join(out_dir, 'overlap_errors.txt')
    csv_annotation = os.path.join(out_dir, 'semantic_overlap_annotations.csv')
    logger                  = Logger(pdf_log_file)
    logger_for_csv_annotation = Logger(csv_annotation)

    grobid_pdf_with_bb_generator.main(pdf_path)

    overlaps = overlapping_bb_coordinates_extractor.get_overlapping_classes_and_coords(
        os.path.join(out_dir, 'pdf_processor_log.txt')
    )

    all_classes, all_coordinates = [], []
    for ov in overlaps:
        all_classes.append(ov['classes'])
        all_coordinates.append(ov['coordinates'])
    all_coordinates = [list(t) for sub in all_coordinates for t in sub]

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

    logger.log(f'Number of overlap violations: {len(all_classes)}\n\n')
    logger.log('Class overlaps which are not allowed by ontology constraints:\n')

    log_txt, log_csv = '', ''
    for i, class_pair in enumerate(all_classes):
        coords_pair = all_coordinates[2 * i: 2 * i + 2]
        for j, class_name in enumerate(class_pair):
            mapped = class_mapping.get(class_name, class_name)
            page, x, y, w, h = coords_pair[j]

            log_txt += (
                f'{mapped} page: {page}\n'
                f'{mapped} coordinates: (page: {page}, x: {x}, y: {y}, w: {w}, h: {h})\n\n'
            )
            log_csv += f'{mapped},{page},{x},{y},{w},{h}\n'

    logger_for_csv_annotation.log(log_csv)
    logger.log(log_txt)

    associations, idx = defaultdict(list), 0
    for pair in all_classes:
        for cls in pair:
            associations[cls].append(all_coordinates[idx])
            idx += 1

    for cls, coords in associations.items():
        mapped = class_mapping.get(cls, cls)
        color  = color_map.get(mapped, (1, 0, 0))
        draw_utilities.create_pdf_with_bounding_boxes(
            pdf_path,
            os.path.join(overlapping_folder, f'overlapping_{cls}_bboxes.pdf'),
            page_width, page_height,
            coords, cls, color
        )

    try:
        if not os.listdir(overlapping_folder):
            print("[INFO] Empty folder, skipping layer merging.")
        else:
            first = True
            for filename in os.listdir(overlapping_folder):
                layer = os.path.join(overlapping_folder, filename)
                if os.path.isfile(layer):
                    if first:
                        draw_utilities.overlay_pdfs(pdf_path, layer, output_pdf_path)
                        first = False
                    else:
                        draw_utilities.overlay_pdfs(output_pdf_path, layer, output_pdf_path)

        if not os.listdir(overlapping_folder):
            shutil.copy(pdf_path, output_pdf_path)

    except FileNotFoundError:
        print(f"[INFO] Folder '{overlapping_folder}' not found. Skipping layer merging.")
    logger.close()

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

if __name__ == "__main__":
    pdf_path = sys.argv[1]
    print('Input file: ' + str(pdf_path))
    main(pdf_path)
