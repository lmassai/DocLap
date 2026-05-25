import os
import shutil
import subprocess
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import xml_from_PDF_functions
import draw_utilities
import sys
from logger import Logger

def safe_overlay(pdf1, pdf2, output):
    try:
        draw_utilities.overlay_pdfs(pdf1, pdf2, output)
    except OSError:
        print("Layer not merged")

def main(pdf_path):

    directory = os.path.dirname(os.path.abspath(pdf_path))
    out_dir = directory + '\\to_process\\'
    pdf_log_file = out_dir + 'pdf_processor_log.txt'
    csv_annotation = out_dir + 'csv_annotations.csv'
    logger = Logger(pdf_log_file)
    logger_for_csv_annotation = Logger(csv_annotation)

    try:
        if not os.path.exists(out_dir + os.path.splitext(os.path.basename(pdf_path))[0] + '_grobid_output.xml'):
            subprocess.run(
                ["curl", "--insecure", "-v", "--form", f"input=@{pdf_path}",
                 "--form", "teiCoordinates=ref",
                 "--form", "teiCoordinates=biblStruct",
                 "--form", "teiCoordinates=persName",
                 "--form", "teiCoordinates=figure",
                 "--form", "teiCoordinates=formula",
                 "--form", "teiCoordinates=head",
                 "--form", "teiCoordinates=s",
                 "--form", "segmentSentences=1",
                 "--form", "teiCoordinates=p",
                 "--form", "teiCoordinates=note",
                 "--form", "teiCoordinates=title",
                 "--form", "teiCoordinates=affiliation",
                 "https://grobidorg-grobid-full2.hf.space/api/processFulltextDocument",
                 ">", f"{out_dir}{os.path.splitext(os.path.basename(pdf_path))[0]}_grobid_output.xml"], shell=True)

        print(out_dir + 'grobid_output.xml created.')
    except subprocess.CalledProcessError as e:
        print('Error creating' + out_dir + 'grobid_output.xml')

    grobid_file_path = out_dir + os.path.splitext(os.path.basename(pdf_path))[0] + '_grobid_output.xml'

    if not os.path.exists(directory + '\\to_process\\'):
        os.makedirs(directory + '\\to_process\\')
    temp_folder = os.path.dirname(os.path.abspath(pdf_path)) + '\\to_process\\' + 'temp_pdf\\'
    output_pdf_path = os.path.dirname(os.path.abspath(pdf_path)) + '\\to_process\\' + 'output_with_bboxes.pdf'

    page_width, page_height = draw_utilities.get_page_dimensions(pdf_path)

    with open(grobid_file_path, 'r', encoding='utf-8') as grobid_xml_file:
        grobid_content = grobid_xml_file.read()

    if "Error 503 Service Unavailable" in grobid_content:
        logger.log('Cannot process pdf')
        logger.close()
        shutil.copy(pdf_path, output_pdf_path)
        sys.exit('\n\nCannot process pdf, Grobid service is DOWN\n\n')

    if grobid_content == '[NO_BLOCKS] PDF parsing resulted in empty content':
        logger.log('Cannot process pdf')
        logger.close()
        shutil.copy(pdf_path, output_pdf_path)

    main_grobid_tag = BeautifulSoup(grobid_content, 'xml')

    figures_data = xml_from_PDF_functions.get_figures_titles_and_coords(main_grobid_tag)
    temp_lists = []

    for i, figure in enumerate(figures_data):
        for caption_block in figures_data[i][1:]:
            temp_lists.extend([caption_block])

    figures_image_bounding_boxes = []
    figures_captions_bounding_boxes = []

    for graphic_coordinates in temp_lists:
        if len(graphic_coordinates) > 5:
            figures_image_bounding_boxes.append(graphic_coordinates[:-1])
        else:
            figures_captions_bounding_boxes.append(graphic_coordinates)

    header_data = xml_from_PDF_functions.get_header_data_and_coords(main_grobid_tag)
    formulas_data = xml_from_PDF_functions.get_formulas_and_coords(main_grobid_tag)
    links_data = xml_from_PDF_functions.get_links_and_coords(main_grobid_tag)
    notes_data = xml_from_PDF_functions.get_notes_and_coords(main_grobid_tag)
    section_titles_data = xml_from_PDF_functions.get_section_titles_and_coords(main_grobid_tag)
    acknowledgement_data = xml_from_PDF_functions.get_acknowledgement(main_grobid_tag)
    phrases_data = xml_from_PDF_functions.get_phrases_and_coords(main_grobid_tag)
    tables_data = xml_from_PDF_functions.get_table_titles_and_coords(main_grobid_tag)
    references_data = xml_from_PDF_functions.references(main_grobid_tag)

    logger.log('Number of authors: ' + str(xml_from_PDF_functions.count_something('persName', [0], main_grobid_tag.find('teiHeader'))))
    logger.log('Number of emails: ' + str(xml_from_PDF_functions.count_something('email', [0], main_grobid_tag.find('teiHeader'))))
    logger.log('Number of tables: ' + str(xml_from_PDF_functions.count_something('table', [0], main_grobid_tag)))
    logger.log('Number of figures: ' + str(xml_from_PDF_functions.count_something('figure', [0], main_grobid_tag)))
    logger.log('Number of formulas: ' + str(xml_from_PDF_functions.count_something('formula', [0], main_grobid_tag)))
    logger.log('Number of dates: ' + str(xml_from_PDF_functions.count_something('date', [0], main_grobid_tag)))
    logger.log('Number of sections and subsections: ' + str(xml_from_PDF_functions.count_something('head', [0], main_grobid_tag)))
    logger.log('Number of bibliographic entries: ' + str(xml_from_PDF_functions.count_something('biblStruct', [0], main_grobid_tag.find('listBibl'))))
    logger.log('Number of pages: ' + str(len(PdfReader(pdf_path).pages)))
    logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Article_title'

    try:
        if len(header_data[0]) > 1 and not isinstance(header_data[0][1], str):
            logger.log(element_kind + ' page: ' + str(header_data[0][1][0]))
            logger.log(element_kind + ' text: ' + header_data[0][0])
            for coord_block_for_ref in header_data[0][1:]:
                logger.log(element_kind + ' Coords: (page: ' + str(coord_block_for_ref[0]) + ', x: ' + str(coord_block_for_ref[1]) + ', y: ' + str(coord_block_for_ref[2]) + ', w: ' + str(coord_block_for_ref[3]) + ', h: ' + str(coord_block_for_ref[4]) + ')')
                logger_for_csv_annotation.log(
                    element_kind + ',' + str(coord_block_for_ref[0]) + ',' + str(coord_block_for_ref[1]) + ',' + str(
                        coord_block_for_ref[2]) + ',' + str(coord_block_for_ref[3]) + ',' + str(coord_block_for_ref[4]))
                bbox_lists.extend([coord_block_for_ref])
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
            draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'title_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0.8, 0.6, 1))

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Author'

    try:
        for i in range(len(header_data[4])):
            logger.log(element_kind + ' text: ' + header_data[4][i][0] + ' ' + header_data[4][i][1])
            logger.log(element_kind + ' name: ' + header_data[4][i][0])
            logger.log(element_kind + ' surname: ' + header_data[4][i][1])

            if header_data[4][i][2] != 'Not found':
                for author_coord in header_data[4][i][2]:

                    page, x, y, w, h = author_coord
                    coord_string = f'{element_kind} Coords: (page: {page}, x: {x}, y: {y}, w: {w}, h: {h})'
                    coord_string_for_csv = f'{element_kind},{page},{x},{y},{w},{h}'
                    logger.log(f'{element_kind} page: {page}')
                    logger.log(coord_string)
                    logger_for_csv_annotation.log(coord_string_for_csv)
                    bbox_lists.append(author_coord)

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'authors_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0.7, 0.7, 1))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Abstract'

    try:
        logger.log(element_kind + ' page: ' + str(header_data[7][1][0]))
        logger.log(element_kind + ' text: ' + str(header_data[7][0]))

        for abstract_block in header_data[7][1:]:
            logger.log(element_kind + ' Coords: (page: ' + str(header_data[7][1][0]) + ', x: ' + str(abstract_block[1]) + ', y: ' + str(abstract_block[2]) + ', w: ' + str(abstract_block[3]) + ', h: ' + str(abstract_block[4]) + ')')
            logger_for_csv_annotation.log(element_kind + ',' + str(header_data[7][1][0]) + ',' + str(abstract_block[1]) + ',' + str(
                abstract_block[2]) + ',' + str(abstract_block[3]) + ',' + str(abstract_block[4]))
            bbox_lists.extend([abstract_block])

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'abstract_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (1, 0.5, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Figure'

    try:
        for i, figure in enumerate(figures_data):
            if any(figure):
                logger.log(element_kind + ' page: ' + str(figure[1][0]))
                logger.log(element_kind + ' text: ' + str(figure[0]))

                for figure_block in figures_image_bounding_boxes:
                    if figure_block[0] == figure[1][0]:
                        logger.log(element_kind + ' Coords: (page: ' + str(figure[1][0]) + ', x: ' + str(
                            figure_block[1]) + ', y: ' + str(figure_block[2]) + ', w: ' + str(
                            figure_block[3]) + ', h: ' + str(figure_block[4]) + ')')
                        logger_for_csv_annotation.log(element_kind + ',' + str(figure[1][0]) + ',' + str(
                            figure_block[1]) + ',' + str(figure_block[2]) + ',' + str(
                            figure_block[3]) + ',' + str(figure_block[4]))
                        bbox_lists.extend([figure_block])

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'figures_bboxes.pdf', page_width, page_height,
                                                      figures_image_bounding_boxes, element_kind, (1, 0, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")


    bbox_lists = []
    element_kind = 'Table'

    try:
        for i, table in enumerate(tables_data):
            logger.log(element_kind + ' page: ' + str(table[2][0]))
            logger.log(element_kind + ' text: ' + table[1])
            logger.log(
                element_kind + ' Coords: (page: ' + str(table[2][0]) + ', x: ' + str(table[2][1]) + ', y: ' + str(
                    table[2][2]) + ', w: ' + str(table[2][3]) + ', h: ' + str(table[2][4]) + ')')
            logger_for_csv_annotation.log(
                element_kind + ',' + str(table[2][0]) + ',' + str(table[2][1]) + ',' + str(
                    table[2][2]) + ',' + str(table[2][3]) + ',' + str(table[2][4]))
            bbox_lists.extend([table[2]])

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'tables_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0, 1, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")


    bbox_lists = []
    element_kind = 'Caption_Figure'

    try:
        for i, caption in enumerate(figures_data):
            if any(caption):
                logger.log(element_kind + ' page: ' + str(caption[1][0]))
                logger.log(element_kind + ' text: ' + str(caption[0]))

                for caption_block in figures_captions_bounding_boxes:
                    if caption_block[0] == caption[1][0]:
                        logger.log(element_kind + ' Coords: (page: ' + str(caption[1][0]) + ', x: ' + str(
                            caption_block[1]) + ', y: ' + str(caption_block[2]) + ', w: ' + str(
                            caption_block[3]) + ', h: ' + str(caption_block[4]) + ')')
                        logger_for_csv_annotation.log(element_kind + ',' + str(caption[1][0]) + ',' + str(
                            caption_block[1]) + ',' + str(caption_block[2]) + ',' + str(
                            caption_block[3]) + ',' + str(caption_block[4]))
                        bbox_lists.append(caption_block)

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'captions_bboxes.pdf', page_width,
                                                      page_height, figures_captions_bounding_boxes, element_kind,
                                                      (0.6, 0, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind_caption = 'Caption_Table'

    try:
        for i, table_data in enumerate(tables_data):
            if any(table_data):
                table_title = table_data[1]
                table_caption_coords = table_data[3]

                logger.log(element_kind_caption + ' page: ' + str(table_data[2][0]))
                logger.log(element_kind_caption + ' text: ' + str(table_title))

                for caption_block in table_caption_coords:
                    if caption_block[0] == table_data[2][0]:
                        logger.log(element_kind_caption + ' Coords: (page: ' + str(caption_block[0]) + ', x: ' + str(
                            caption_block[1]) + ', y: ' + str(caption_block[2]) + ', w: ' + str(
                            caption_block[3]) + ', h: ' + str(caption_block[4]) + ')')
                        logger_for_csv_annotation.log(element_kind_caption + ',' + str(caption_block[0]) + ',' + str(
                            caption_block[1]) + ',' + str(caption_block[2]) + ',' + str(
                            caption_block[3]) + ',' + str(caption_block[4]))
                        bbox_lists.append(caption_block)

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'table_captions_bboxes.pdf', page_width, page_height, bbox_lists, element_kind_caption, (0.6, 0, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")


    bbox_lists = []
    element_kind = 'Formula'

    try:
        for i, formula in enumerate(formulas_data):

            logger.log(element_kind + ' page: ' + str(formula[1][0]))
            logger.log(element_kind + ' text: ' + formula[0])
            logger.log(element_kind + ' Coords: (page: ' + str(formula[1][0]) + ', x: ' + str(formula[1][1]) + ', y: ' + str(formula[1][2]) + ', w: ' + str(formula[1][3]) + ', h: ' + str(formula[1][4]) + ')')

            logger_for_csv_annotation.log(element_kind + ',' + str(formula[1][0]) + ',' + str(formula[1][1]) + ',' + str(
                formula[1][2]) + ',' + str(formula[1][3]) + ',' + str(formula[1][4]))

            bbox_lists.extend([formula[1]])
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'formulas_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0, 0, 1))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Section'

    try:
        for i, section_title in enumerate(section_titles_data):
            logger.log(element_kind + ' page: ' + str(section_title[1][0]))
            logger.log(element_kind + ' text: ' + section_title[0])
            logger.log(element_kind + ' Coords: (page: ' + str(section_title[1][0]) + ', x: ' + str(section_title[1][1]) + ', y: ' + str(section_title[1][2]) + ', w: ' + str(section_title[1][3]) + ', h: ' + str(section_title[1][4]) + ')')
            logger_for_csv_annotation.log(element_kind + ',' + str(section_title[1][0]) + ',' + str(section_title[1][1]) + ',' + str(
                section_title[1][2]) + ',' + str(section_title[1][3]) + ',' + str(section_title[1][4]))

            bbox_lists.extend([section_title[1]])
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'section_titles_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0.7, 0, 1))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Link'

    try:
        for i, link in enumerate(links_data):
            logger.log(element_kind + ' page: ' + str(link[1][0]))
            logger.log(element_kind + ' text: ' + link[0])
            logger.log(element_kind + ' Coords: (page: ' + str(link[1][0]) + ', x: ' + str(link[1][1]) + ', y: ' + str(link[1][2]) + ', w: ' + str(link[1][3]) + ', h: ' + str(link[1][4]) + ')')

            logger_for_csv_annotation.log(element_kind + ',' + str(link[1][0]) + ',' + str(link[1][1]) + ',' + str(link[1][2]) + ',' + str(
                link[1][3]) + ',' + str(link[1][4]))

            for coord_block_for_ref in link[1:]:
                bbox_lists.extend([coord_block_for_ref])
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'links_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0, 1, 1))

        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Note'

    try:
        for i, note in enumerate(notes_data):
            logger.log(element_kind + ' page: ' + str(note[1][0]))
            logger.log(element_kind + ' text: ' + note[0])

            logger.log(element_kind + ' Coords: (page: ' + str(note[1][0]) + ', x: ' + str(note[1][1]) + ', y: ' + str(note[1][2]) + ', w: ' + str(
                note[1][3]) + ', h: ' + str(note[1][4]) + ')')

            logger_for_csv_annotation.log(element_kind + ',' + str(note[1][0]) + ',' + str(note[1][1]) + ',' + str(note[1][2]) + ',' + str(
                note[1][3]) + ',' + str(note[1][4]))

            bbox_lists.extend([note[1]])

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'notes_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0, 0, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Acknowledgements'

    try:
        if acknowledgement_data[6][0][0] != 'u':
            page_number = int(acknowledgement_data[6][0][0])
        else:
            page_number = 0
        logger.log(element_kind + ' page: ' + str(page_number))

        if acknowledgement_data != 'Not found':
            for i, acknowledged_person in enumerate(acknowledgement_data[1]):
                logger.log(element_kind + ' person: ' + acknowledgement_data[1][i])

            for i, acknowledged_funder in enumerate(acknowledgement_data[2]):
                logger.log(element_kind + ' funder: ' + acknowledgement_data[2][i])

            for i, acknowledged_grant in enumerate(acknowledgement_data[3]):
                logger.log(element_kind + ' grant: ' + acknowledgement_data[3][i])

            for i, acknowledged_program in enumerate(acknowledgement_data[4]):
                logger.log(element_kind + ' program: ' + acknowledgement_data[4][i])

            for i, acknowledged_grant_number in enumerate(acknowledgement_data[5]):
                logger.log(element_kind + ' grant number: ' + acknowledgement_data[5][i])

            logger.log(element_kind + ' text: ' + acknowledgement_data[0])

            for index, coords in enumerate(acknowledgement_data[6]):
                if len(coords) >= 5 and index > 0:
                    logger.log(element_kind + ' Coords: (page: ' + str(page_number) + ', x: ' + str(
                        coords[1]) + ', y: ' + str(coords[2]) + ', w: ' + str(coords[3]) + ', h: ' + str(coords[4]) + ')')

                    logger_for_csv_annotation.log(
                        element_kind + ',' + str(page_number) + ',' + str(coords[1]) + ',' + str(coords[2]) + ',' + str(
                            coords[3]) + ',' + str(coords[4]))

                    bbox_lists.append(coords)

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'acknowledgements_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (1, 0, 1))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'Reference'

    try:
        for reference in references_data:
            logger.log(element_kind + ' page: ' + str(reference[12][0][0]))
            logger.log(element_kind + ' title: ' + reference[1])

            for i, reference_author in enumerate(reference[2]):
                if reference[2] != 'Not found':
                    logger.log(element_kind + ' author ' + str(i + 1) + ': ' + reference_author[0] + ' ' + reference_author[1])
                else:
                    logger.log(element_kind + ' author ' + str(i + 1) + ': Not found')
            logger.log(element_kind + ' link: ' + reference[3])
            logger.log(element_kind + ' availability: ' + reference[4])
            logger.log(element_kind + ' journal/conference: ' + reference[5])
            logger.log(element_kind + ' publisher:' + str(reference[6]))
            logger.log(element_kind + ' date:' + str(reference[7]))
            logger.log(element_kind + ' volume:' + str(reference[8]))

            if reference[9] != 'Not found':
                logger.log(element_kind + ' page range: from ' + reference[9][0] + ' to ' + reference[9][1])
            else:
                logger.log(element_kind + ' page range: Not found')

            if reference[10] != 'Not found':
                for j, reference_editor in enumerate(reference[10]):
                    if reference[10] != 'Not found':
                        logger.log(element_kind + ' editor ' + str(j + 1) + ': ' + reference_editor[0] + ' ' + reference_editor[1])
                    else:
                        logger.log(element_kind + ' editor ' + str(j + 1) + ': Not found')
            else:
                logger.log(element_kind + ' editor : Not found')

            logger.log(element_kind + ' DOI: ' + str(reference[11]))

            for coord in reference[12]:
                logger.log(element_kind + ' Coords: (page: ' + str(reference[12][0][0]) + ', x: ' + str(coord[1]) + ', y: ' + str(coord[2]) + ', w: ' + str(
                    coord[3]) + ', h: ' + str(coord[4]) + ')')

                logger_for_csv_annotation.log(element_kind + ',' + str(reference[12][0][0]) + ',' + str(coord[1]) + ',' + str(
                    coord[2]) + ',' + str(coord[3]) + ',' + str(coord[4]))

                bbox_lists.extend([coord])

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'references_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (1, 1, 0))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    bbox_lists = []
    element_kind = 'phrase'

    try:
        for i, phrases in enumerate(phrases_data):
            logger.log('phrase ' + str(i + 1) + ' (page ' + str(phrases[1][0]) + ')')
            logger.log('Text: ' + str(phrases[0]))
            logger_for_csv_annotation.log('phrase ' + str(i + 1) + ' (page ' + str(phrases[1][0]) + ')')
            logger_for_csv_annotation.log('Text: ' + str(phrases[0]))

            for phrase in phrases_data[i][1:]:
                logger.log('Coords: (x: ' + str(phrase[1]) + ', y: ' + str(phrase[2]) + ', w: ' + str(
                    phrase[3]) + ', h: ' + str(phrase[4]) + ')')
                logger_for_csv_annotation.log(
                    element_kind + ',' + str(phrase[1]) + ',' + str(phrase[2]) + ',' + str(phrase[3]) + ',' + str(phrase[4]))
                bbox_lists.extend([phrase])

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        draw_utilities.create_pdf_with_bounding_boxes(pdf_path, temp_folder + 'phrases_bboxes.pdf', page_width, page_height, bbox_lists, element_kind, (0.5, 0.5, 0.5))
        logger.log("\nend_section\n")

    except IndexError as e:
        print('Error on ' + element_kind + ' processing: ' + str(e))
        logger.log("\nend_section\n")

    layers = [
        (temp_folder + 'phrases_bboxes.pdf', temp_folder + 'authors_bboxes.pdf'),
    ]

    layers += [
        (output_pdf_path, temp_folder + 'title_bboxes.pdf') if (
                    len(header_data[0]) > 1 and not isinstance(header_data[0][1], str)) else None,
        (output_pdf_path, temp_folder + 'section_titles_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'abstract_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'figures_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'captions_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'tables_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'table_captions_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'formulas_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'links_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'acknowledgements_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'references_bboxes.pdf'),
        (output_pdf_path, temp_folder + 'notes_bboxes.pdf'),
    ]

    layers = [layer for layer in layers if layer is not None]

    for pdf1, pdf2 in layers:
        safe_overlay(pdf1, pdf2, output_pdf_path)

    safe_overlay(pdf_path, output_pdf_path, output_pdf_path)

    logger.close()

    if os.path.exists(temp_folder):
        for item in os.listdir(temp_folder):
            item_path = os.path.join(temp_folder, item)
            if item == "overlapping" and os.path.isdir(item_path):
                continue
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    pass

if __name__ == "__main__":
    pdf_path = sys.argv[1]
    print('Input file: ' + str(pdf_path))
    main(pdf_path)
    command = f'python parsers/violations_finder_and_correct.py "{pdf_path}"'
    os.system(command)
