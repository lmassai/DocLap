from bs4 import Tag
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
import re

def get_title(soup_tag):
    title_tag = soup_tag.find('title')
    coords_value = title_tag.get('coords', '')

    if title_tag.get('type') == 'main':

        title_data = [title_tag.text]

        if coords_value:
            for title_coord in coords_value.split(';'):
                title_coord_vector = title_coord.split(',')

                page_n = int(title_coord_vector[0])
                x_axis = float(title_coord_vector[1])
                y_axis = float(title_coord_vector[2])
                width = float(title_coord_vector[3])
                height = float(title_coord_vector[4])

                coords_values = [page_n, x_axis, y_axis, width, height]
                title_data.append(coords_values)
        else:
            title_data.append('Not found')

        return title_data
    else:
        return "Not found"

def get_date_published(soup_tag):
    date_published_tag = soup_tag.find('date')
    if date_published_tag:
        return date_published_tag.text
    else:
        return "Not found"

def get_doi(soup_tag):
    idno_tags = soup_tag.find_all('idno')
    if idno_tags:
        for idno_tag in idno_tags:
            if idno_tag.get('type') == 'DOI':
                return idno_tag.text
            else:
                continue
        else:
            return "Not found"

def get_acknowledgement(soup_tag):
    ack_tag = soup_tag.find('div', {'type': re.compile(r'acknowledgement', re.I)})

    if ack_tag:
        acknowledgements_coords = []

        for tag in ack_tag.find_all(attrs={'coords': True}):
            coords_attr = tag['coords']
            for coord_set in coords_attr.split(';'):
                try:
                    coords = list(map(float, coord_set.split(',')))
                    acknowledgements_coords.append(coords)
                except ValueError:
                    continue

        acknowledged_persons = soup_tag.find_all('rs', {'type': 'person'})
        acknowledged_funders = soup_tag.find_all('rs', {'type': 'funder'})
        acknowledged_grant_names = soup_tag.find_all('rs', {'type': 'grantName'})
        acknowledged_grant_numbers = soup_tag.find_all('rs', {'type': 'grantNumber'})
        acknowledged_program_names = soup_tag.find_all('rs', {'type': 'programName'})
        acknowledged_names = [person.text for person in acknowledged_persons if person]
        funders_names = [funder.text for funder in acknowledged_funders if funder]
        grants_names = [grant.text for grant in acknowledged_grant_names if grant]
        programs_names = [program.text for program in acknowledged_program_names if program]
        grant_numbers = [grant_number.text for grant_number in acknowledged_grant_numbers if grant_number]
        acknowledgements_text = ack_tag.text if ack_tag else ""

        acknowledgement_data = [acknowledgements_text, acknowledged_names, funders_names, grants_names, programs_names,
            grant_numbers, acknowledgements_coords]

        return acknowledgement_data
    else:
        return 'Not found'

def get_email(header_tag, names_length):
    email_tags = header_tag.select('email')
    risultati_emails = []

    for i, email_tag in enumerate(email_tags):
        if i < names_length:
            email_text = email_tag.get_text(strip=True)
            if email_text != 'Not found':
                risultati_emails.append(email_text)

    return risultati_emails

def get_affiliation_data(header_tag, names_length):

    risultati_affiliations = []
    org_tags = header_tag.select('orgName')
    affiliation_tags = header_tag.select('affiliation')
    author_data = [''] * 6

    for i in range(names_length):

        try:
            full = org_tags[i].text
        except IndexError:
            full = 'Not found'
        author_data[0] = full

        try:
            department = org_tags[i].text
        except IndexError:
            department = 'Not found'
        author_data[1] = department

        try:
            institution = org_tags[i].text
        except IndexError:
            institution = 'Not found'
        author_data[2] = institution

        try:
            address_tag = affiliation_tags[i].find('address')
        except IndexError:
            address_tag = 'Not found'

        if address_tag:
            settlement_tag = address_tag.find('settlement')
            country_tag = address_tag.find('country')
            address_tag = address_tag.find('addrLine')

            if address_tag and address_tag != -1:
                address_text = address_tag.get_text(strip=True)
                author_data[3] = address_text
            else:
                author_data[3] = 'Not found'

            if settlement_tag and settlement_tag != -1:
                settlement_text = settlement_tag.get_text(strip=True)
                author_data[4] = settlement_text
            else:
                author_data[4] = 'Not found'

            if country_tag and country_tag != -1:
                country_text = country_tag.get_text(strip=True)
                author_data[5] = country_text
            else:
                author_data[5] = 'Not found'

        risultati_affiliations.append(list(author_data))

    return risultati_affiliations

def get_person_name_and_coords(header_tag):

    risultati_names = []
    pers_name_tags = header_tag.find_all('persName')
    author_name = [''] * 3

    if pers_name_tags:
        for i, pers_name_tag in enumerate(pers_name_tags):

            forename_tag = pers_name_tag.find('forename')
            surname_tag = pers_name_tag.find('surname')
            coords_value = pers_name_tag.get('coords', '')

            if forename_tag:
                forename_text = forename_tag.get_text(strip=True)
                author_name[0] = forename_text
            else:
                author_name[2] = 'Not found'

            if surname_tag:
                surname_text = surname_tag.get_text(strip=True)
                author_name[1] = surname_text
            else:
                author_name[2] = 'Not found'

            if coords_value:
                for author_coord in coords_value.split(';'):

                    author_coord_vector = author_coord.split(',')

                    page_n = int(author_coord_vector[0])
                    x_axis = float(author_coord_vector[1])
                    y_axis = float(author_coord_vector[2])
                    width = float(author_coord_vector[3])
                    height = float(author_coord_vector[4])

                coords_values = [page_n, x_axis, y_axis, width, height]
                author_name[2] = [coords_values]
            else:
                author_name[2] = 'Not found'

            risultati_names.append(list(author_name))

    return risultati_names

def get_keywords(soup_tag):
    keywords_tag = soup_tag.find('keywords')
    if keywords_tag:
        return keywords_tag.text
    else:
        return "Not found"

def get_keywords_with_PDFParser(filename):
    file = open(filename, "rb")
    parser = PDFParser(file)
    document = PDFDocument(parser)
    return str(document.info[0]['Keywords'])

def get_abstract_and_coords(soup_tag):
    abstract_data = []
    abstract_coords_set = []
    abstract_tag = soup_tag.find('abstract')

    abstract_data.append(abstract_tag.text)

    s_tags = soup_tag.select('abstract s')

    for s_tag in s_tags:

        abstract_coords_vector = s_tag['coords'].split(';')
        coords_set = []
        for coord_set in abstract_coords_vector:

            abstract_coords = coord_set.split(',')

            page_n = int(abstract_coords[0])
            x_axis = float(abstract_coords[1])
            y_axis = float(abstract_coords[2])
            width = float(abstract_coords[3])
            height = float(abstract_coords[4])

            lista = [page_n, x_axis, y_axis, width, height]
            coords_set.append(lista)

        abstract_coords_set.extend(coords_set)

    abstract_data.extend(list(abstract_coords_set))

    if abstract_data:
        return abstract_data

def get_header_data_and_coords(soup_tag):
    header_data = []
    header_tag = soup_tag.find('teiHeader')

    if header_tag:
        title = get_title(header_tag)
        date_published = get_date_published(header_tag)
        doi = get_doi(header_tag)
        keywords = get_keywords(header_tag)
        names = get_person_name_and_coords(header_tag)
        authors_data = get_affiliation_data(header_tag, len(names))
        emails = get_email(header_tag, len(names))
        abstract_data = get_abstract_and_coords(header_tag)

        header_data.extend([title, date_published, doi, keywords, list(names), list(authors_data), list(emails), list(abstract_data)])

        return header_data

    else:
        return 'Header not found'

def count_something(sub_tag, number_of_tags, main_grobid_tag):

    for child in main_grobid_tag.children:
        if child.name is not None:
            if child.name == sub_tag:
                if 'type' in child.attrs and sub_tag == 'figure' and child.attrs['type'] == 'table':
                    pass
                else:
                    number_of_tags[0] += 1

            count_something(sub_tag, number_of_tags, child)
    if number_of_tags[0]:
        return number_of_tags[0]
    else:
        return '0'

def get_figures_titles_and_coords(main_grobid_tag):

    figures_list = main_grobid_tag.select('figure[xml\\:id*=fig_]')
    figures_data = []

    for i, s_tag in enumerate(figures_list):
        figures_coords_set = []
        figure_caption = ''
        all_coords_for_this_figure = s_tag.figDesc.div.p.find_all('s')

        for fig_caption_period in all_coords_for_this_figure:
            figure_caption += ' ' + fig_caption_period.text

        figures_data.append([figure_caption])

        coords_set = []

        for multiple_coordinates in all_coords_for_this_figure:
            figure_and_caption_row_coordinates = multiple_coordinates['coords'].split(';')

            if s_tag.graphic is not None:
                figure_and_caption_row_coordinates.append(s_tag.graphic['coords'] + ',is_graphic')

            for coord_set in figure_and_caption_row_coordinates:
                figure_coords = coord_set.split(',')

                page_n = int(figure_coords[0])
                x_axis = float(figure_coords[1])
                y_axis = float(figure_coords[2])
                width = float(figure_coords[3])
                height = float(figure_coords[4])

                if len(figure_coords) > 5 and figure_coords[5]:
                    is_graphic = figure_coords[5]
                    lista = [page_n, x_axis, y_axis, width, height, is_graphic]
                else:
                    lista = [page_n, x_axis, y_axis, width, height]

                coords_set.append(lista)

        figures_coords_set.extend(coords_set)
        figures_data[i].extend(figures_coords_set)

    return figures_data

def get_table_titles_and_coords(main_grobid_tag):
    tables_data = []
    figures_list = main_grobid_tag.select('figure')

    for i, s_tag in enumerate(figures_list):
        if 'type' in s_tag.attrs and s_tag.attrs['type'] == 'table':
            all_caption_segments_for_this_table = s_tag.find('figDesc').find_all('s')
            coords_values = []

            for s in all_caption_segments_for_this_table:
                coords = s.get('coords')
                if coords:
                    coords_values.append(coords)

            table_caption_coords = []
            for coord_set in coords_values:
                for coord in coord_set.split(';'):
                    coord_parts = coord.split(',')
                    page_n = int(coord_parts[0])
                    coord_list = [page_n] + list(map(float, coord_parts[1:]))
                    table_caption_coords.append(coord_list)

            table_tag = s_tag.find('table')
            if table_tag and 'coords' in table_tag.attrs:
                attribute_value = table_tag['coords']
                table_coords = attribute_value.split(',')

                table_kind = s_tag.head.text if s_tag.head else 'Not found'
                table_title = s_tag.figDesc.text if s_tag.figDesc else 'Not found'

                page_n = int(table_coords[0])
                x_axis = float(table_coords[1])
                y_axis = float(table_coords[2])
                width = float(table_coords[3])
                height = float(table_coords[4])

                table_coords = [page_n, x_axis, y_axis, width, height]
                tables_data.append([table_kind, str(table_title), list(table_coords), table_caption_coords])
    return tables_data

def get_formulas_and_coords(main_grobid_tag):
    all_formulas = []
    formulas_list = main_grobid_tag.select('formula')

    for s_tag in formulas_list:

        attribute_value = s_tag['coords']
        formula_coords = attribute_value.split(',')

        formula_text = s_tag.contents[0].text

        page_n = int(formula_coords[0])
        x_axis = float(formula_coords[1])
        y_axis = float(formula_coords[2])
        width = float(formula_coords[3])
        height = float(formula_coords[4])

        formula_coords = [page_n, x_axis, y_axis, width, height]
        all_formulas.append([formula_text, list(formula_coords)])

    return all_formulas

def get_section_titles_and_coords(main_grobid_tag):
    all_section_titles = []
    section_titles_list = main_grobid_tag.select('head')

    for i, s_tag in enumerate(section_titles_list):
        if s_tag.get('coords', None):
            attribute_value = s_tag['coords']
            all_coords_for_this_block = attribute_value.split(';')

            section_title_text = s_tag.contents[0].text
            section_title_data = [section_title_text]

            for coord_set in all_coords_for_this_block:
                link_coords = coord_set.split(',')
                page_n = int(link_coords[0])
                x_axis = float(link_coords[1])
                y_axis = float(link_coords[2])
                width = float(link_coords[3])
                height = float(link_coords[4])

                section_title_data.append([page_n, x_axis, y_axis, width, height])

            all_section_titles.append(section_title_data)

    return all_section_titles

def get_links_and_coords(main_grobid_tag):
    all_links = []
    links_list = main_grobid_tag.select('ref')

    for i, s_tag in enumerate(links_list):
        if s_tag.get('coords', None):
            attribute_value = s_tag['coords']
            all_coords_for_this_block = attribute_value.split(';')

            link_text = s_tag.contents[0].text
            link_data = [link_text]

            for coord_set in all_coords_for_this_block:
                link_coords = coord_set.split(',')
                page_n = int(link_coords[0])
                x_axis = float(link_coords[1])
                y_axis = float(link_coords[2])
                width = float(link_coords[3])
                height = float(link_coords[4])

                link_data.append([page_n, x_axis, y_axis, width, height])

            all_links.append(link_data)

    return all_links

def get_p_and_coords(main_grobid_tag):
    all_p = []
    p_list = main_grobid_tag.select('p')

    for i, s_tag in enumerate(p_list):
        if s_tag.get('coords', None):
            attribute_value = s_tag['coords']
            all_coords_for_this_block = attribute_value.split(';')

            p_text = s_tag.contents[0].text
            p_data = [p_text]

            for coord_set in all_coords_for_this_block:
                link_coords = coord_set.split(',')
                page_n = int(link_coords[0])
                x_axis = float(link_coords[1])
                y_axis = float(link_coords[2])
                width = float(link_coords[3])
                height = float(link_coords[4])

                p_data.append([page_n, x_axis, y_axis, width, height])

            all_p.append(p_data)

    return all_p

def get_notes_and_coords(main_grobid_tag):
    all_notes = []
    notes_list = main_grobid_tag.select('note')

    for i, s_tag in enumerate(notes_list):
        if s_tag.get('coords', None):
            attribute_value = s_tag['coords']
            all_coords_for_this_block = attribute_value.split(';')

            note_text = s_tag.contents[0].text
            note_data = [note_text]

            for coord_set in all_coords_for_this_block:
                link_coords = coord_set.split(',')
                page_n = int(link_coords[0])
                x_axis = float(link_coords[1])
                y_axis = float(link_coords[2])
                width = float(link_coords[3])
                height = float(link_coords[4])

                note_data.append([page_n, x_axis, y_axis, width, height])

            all_notes.append(note_data)

    return all_notes

def get_phrases_and_coords(main_grobid_tag):
    text_block_list = main_grobid_tag.select('div s')
    all_text_blocks = []

    for i, s_tag in enumerate(text_block_list):
        phrases_coords_set = []
        text_value_in_this_block = s_tag.text
        all_text_blocks.append([text_value_in_this_block])
        coords_value_in_this_block = s_tag.get('coords', None)
        if coords_value_in_this_block:
            all_coords_for_this_text_block = coords_value_in_this_block.split(
                ';') if ';' in coords_value_in_this_block else [coords_value_in_this_block]
        else:
            print(f"WARNING: <s> tag has no 'coords'. Content: {s_tag}")
            all_coords_for_this_text_block = []

        coords_set = []
        for coord_set in all_coords_for_this_text_block:
            text_block_coords = coord_set.split(',')

            page_n = int(text_block_coords[0])
            x_axis = float(text_block_coords[1])
            y_axis = float(text_block_coords[2])
            width = float(text_block_coords[3])
            height = float(text_block_coords[4])

            lista = [page_n, x_axis, y_axis, width, height]
            coords_set.append(lista)

        phrases_coords_set.extend(coords_set)
        all_text_blocks[i].extend(phrases_coords_set)

    return all_text_blocks

def references(main_grobid_tag):
    references_data = []
    bibliographies = main_grobid_tag.find_all("listBibl")

    if not bibliographies:
        print("WARNING: No <listBibl> found in GROBID XML.")
        return []

    for bibItem, citation in enumerate(bibliographies[0].find_all("biblStruct")):
        references_coords_set = []
        references_partial_data = []
        references_partial_data.append(str(bibItem+1))

        if citation.analytic:
            analytic = citation.analytic

            if analytic.title:
                title = analytic.title.get_text()
            else:
                title = 'Not found'

            references_partial_data.append(title)

            references_authors = []
            for indice, author in enumerate(analytic.find_all("author")):
                author = author.persName
                if author is not None:
                    if author.forename:
                        author_forename = author.forename.contents[0]
                    else:
                        author_forename = 'Not found'

                    if author.surname:
                        author_surname = author.surname.contents[0]
                    else:
                        author_surname = 'Not found'
                else:
                    author_forename = 'Not found'
                    author_surname = 'Not found'
                references_authors.append([author_forename, author_surname])

            references_partial_data.append(list(references_authors))

            if analytic.ptr:
                link = analytic.ptr['target']
            else:
                link = 'Not found'

            references_partial_data.append(link)

            if analytic.ptr and 'type' in analytic.ptr.attrs:
                open_access = analytic.ptr['type']
            else:
                open_access = 'Not found'

            references_partial_data.append(open_access)

        else:
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')

        if citation.monogr:
            monogr = citation.monogr

            if monogr.title:
                journal = monogr.title.text
            else:
                journal = 'Not found'

            references_partial_data.append(journal)

            if monogr.publisher:
                publisher = getattr(monogr.publisher, 'text', 'Not found')
            else:
                publisher = 'Not found'

            references_partial_data.append(publisher)

            if monogr.date:
                publication_date = getattr(monogr.date, 'text', 'Not found')
            else:
                publication_date = 'Not found'

            references_partial_data.append(publication_date)

            if monogr.biblScope and isinstance(monogr.biblScope, Tag):

                publisher = monogr.biblScope if monogr.biblScope else 'Not found'

                if 'unit' in publisher.attrs:
                    references_partial_data.append(publisher.attrs['unit'] + ' ' + publisher.text if publisher.attrs['unit'] == 'volume' else 'Not found')
                else:
                    references_partial_data.append('Not found')

                if 'from' in publisher.attrs:
                    page_range_from = publisher.attrs['from']
                else:
                    page_range_from = 'Not found'
                if 'to' in publisher.attrs:
                    page_range_to = publisher.attrs['to']
                else:
                    page_range_to = 'Not found'
                if 'from' in publisher.attrs and 'to' in publisher.attrs:
                    references_partial_data.append([page_range_from, page_range_to])
                else:
                    references_partial_data.append('Not found')
            else:
                references_partial_data.append('Not found')
                references_partial_data.append('Not found')

            if monogr.editor:
                references_editors = []
                for indice, editor in enumerate(monogr.find_all("editor")):
                    editor = editor.persName

                    if editor is not None:
                        if editor.forename:
                            editor_forename = editor.forename.contents[0]
                        else:
                            editor_forename = 'Not found'

                        if editor.surname:
                            editor_surname = editor.surname.contents[0]
                        else:
                            editor_surname = 'Not found'
                    elif monogr.editor is not None:
                        editor_forename = monogr.editor.text
                        editor_surname = ''
                    else:
                        editor_forename = 'Not found'
                        editor_surname = 'Not found'

                    references_editors.append([editor_forename, editor_surname])

                references_partial_data.append(list(references_editors))
            else:
                references_partial_data.append('Not found')
        else:
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')
            references_partial_data.append('Not found')

        if citation.idno:
            doi = citation.idno.text
        else:
            doi = 'Not found'
        references_partial_data.append(doi)

        bibliography_ref_coords = citation.attrs['coords'].split(';') if citation.attrs else 'Not found'

        for coord_set in bibliography_ref_coords:
            coords_set = []
            reference_coords = coord_set.split(',')

            page_n = int(reference_coords[0])
            x_axis = float(reference_coords[1])
            y_axis = float(reference_coords[2])
            width = float(reference_coords[3])
            height = float(reference_coords[4])

            lista = [page_n, x_axis, y_axis, width, height]
            coords_set.append(lista)

            references_coords_set.extend(coords_set)

        if references_coords_set:
            references_partial_data.append(references_coords_set)
        else:
            references_partial_data.append('Not found')

        references_data.extend([references_partial_data])

        if citation.monogr and not citation.analytic:

            if references_data[bibItem][1] == 'Not found':
                references_data[bibItem][1] = journal
                references_data[bibItem][5] = 'Not found'

            if references_data[bibItem][2] == 'Not found':
                references_authors = []

                for indice, author in enumerate(monogr.find_all("author")):
                    if author is not None:
                        author = author.persName
                        author_forename = 'Not found'
                        author_surname = 'Not found'

                        if author and hasattr(author, 'forename') and author.forename is not None:
                            if author.forename.contents:
                                author_forename = author.forename.contents[0]

                        if author and hasattr(author, 'surname') and author.surname is not None:
                            if author.surname.contents:
                                author_surname = author.surname.contents[0]

                    else:
                        author_forename = 'Not found'
                        author_surname = 'Not found'

                    references_authors.append([author_forename, author_surname])

                references_data[bibItem][2] = list(references_authors)

            if references_data[bibItem][3] == 'Not found':
                if monogr.ptr:
                    link = monogr.ptr['target']
                else:
                    link = 'Not found'

                references_data[bibItem][3] = link

            if references_data[bibItem][4] == 'Not found':
                if monogr.ptr and 'type' in monogr.ptr.attrs:
                    open_access = monogr.ptr['type']
                else:
                    open_access = 'Not found'

                references_data[bibItem][4] = open_access

    return references_data

def get_hierarchy(tag, indent=0, hierarchy=''):

    hierarchy += '  ' * indent + tag.name + '\n'

    for child in tag.children:
        if child.name is not None:
            hierarchy = get_hierarchy(child, indent + 1, hierarchy)

    return hierarchy
