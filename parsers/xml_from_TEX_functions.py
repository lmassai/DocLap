import re
from bs4 import NavigableString

def get_title(main_latexml_tag):
    title = main_latexml_tag.find('title').text
    return title

def get_keywords(main_latexml_tag):
    keywords = main_latexml_tag.find('keywords').text.strip()
    keywords_list = keywords.split(',')
    for i in range(len(keywords_list)):
        keywords_list[i] = re.sub(r'[^\w\s]', '', keywords_list[i].strip())
    return ''

def get_abstract(main_latexml_tag):
    abstract = ''
    abstract_element = main_latexml_tag.find('abstract')
    for a in abstract_element.contents:
        try:
            for b in a.contents:
                if isinstance(b, NavigableString):
                    abstract += b.text
        except AttributeError:
            continue
        return abstract

def get_acknowledgements(main_latexml_tag):
    acknowledgements = main_latexml_tag.find('acknowledgements').text.strip()
    return acknowledgements

def get_dates(main_latexml_tag):
    dates_list = []
    dates = main_latexml_tag.find_all('date')
    for date in dates:
        dates_list.append(date.text.strip())
    return dates_list

def get_authors(main_latexml_tag):
    authors_list = []
    authors = main_latexml_tag.find_all('creator')
    for author in authors:
        person_names = author.find_all('personname')
        for j, person_name in enumerate(person_names):
            for k in person_name.contents:
                if isinstance(k, NavigableString):
                    if any(c.isalpha() for c in k):
                        if 'Comment' not in str(type(k)):
                            authors_list.append(re.sub(r'[^a-zA-Z\s]', '', k).strip())
    return authors_list

def get_affiliations(main_latexml_tag):
    affiliations_list = []
    creators = main_latexml_tag.find_all('creator')
    for creator in creators:
        contacts = creator.find_all('contact', {'role': 'affiliation'})
        for affiliation in contacts:
            if affiliation:
                affiliation_text = affiliation.find_all('text', {'class': 'ltx_affiliation_institution'})
                for affiliation_text_tag in affiliation_text:
                    institution_names = [name.strip() for name in affiliation_text_tag.contents if
                                         isinstance(name, NavigableString)]
                    for institution_name in institution_names:
                        affiliations_list.append(re.sub(r'[^\w\s]', '', institution_name.strip()))
    return affiliations_list

def get_emails(main_latexml_tag):
    emails_list = []
    email_contact_tags = main_latexml_tag.find('creator').find_all('contact', {'role': 'email'})
    for email_contact_tag in email_contact_tags:
        email_text = email_contact_tag.text.strip()
        emails_list.append(email_text)
    return emails_list

def get_chapter_titles(main_latexml_tag):
    chapters_list = []
    chapter_titles = main_latexml_tag.find_all('section')
    for chapter in chapter_titles:
        try:
            chapters_list.append((chapter.title.contents[0].text, chapter.title.contents[1].text))
        except IndexError:
            try:
                chapters_list.append(('Un-numbered', chapter.title.contents[0].text))
            except IndexError:
                chapters_list.append('Not found')
    return chapters_list

def get_subsections(main_latexml_tag, chapter_titles):
    subsections_list = []
    chapter_titles_strings = [chapter[1] for chapter in chapter_titles]
    subsection_titles = main_latexml_tag.find_all('title')
    for subsection_title in subsection_titles:
        try:
            if subsection_title.contents[1].text not in chapter_titles_strings:
                subsections_list.append((subsection_title.contents[0].text, subsection_title.contents[1].text))
        except IndexError:
            continue
    return subsections_list

def get_figures(main_latexml_tag):
    fig_captions_list = []
    figures = main_latexml_tag.find_all('figure')

    for figure in figures:
        fig_captions = figure.find_all('caption')
        for fig_caption in fig_captions:
            fig_caption_elements = []
            for element in fig_caption.contents:
                fig_caption_elements.append(element.text.strip())
            fig_captions_list.append(fig_caption_elements)
    return fig_captions_list

def get_tables(main_latexml_tag):
    tab_captions_list = []
    tables = main_latexml_tag.find_all('table')

    for table in tables:
        tab_captions = table.find_all('caption')
        for tab_caption in tab_captions:
            tab_caption_elements = []
            for element in tab_caption.contents:
                tab_caption_elements.append(element.text.strip())
            tab_captions_list.append(tab_caption_elements)
    return tab_captions_list

def get_formulas(main_latexml_tag):
    formulas_list = []
    for j, math_tag in enumerate(main_latexml_tag.find_all('Math', mode='display')):
        tex = math_tag['tex']
        formula_tex = tex.replace('%', '').replace('\n', '')
        formulas_list.append(formula_tex)
    return formulas_list

def get_links(main_latexml_tag):
    links_list = []
    ref_tags = main_latexml_tag.find_all('ref')
    bib_refs = main_latexml_tag.find_all('bibref')

    for ref_tag in ref_tags:
        href = ref_tag.get('href')
        labelref = ref_tag.get('labelref')
        if href:
            links_list.append(['URL', href])
        if labelref:
            if 'tab:' in labelref:
                links_list.append(['table', labelref.replace('LABEL:', '')])
            if 'fig:' in labelref:
                links_list.append(['figure', labelref.replace('LABEL:', '')])
            if 'sec:' in labelref:
                links_list.append(['section', labelref.replace('LABEL:', '')])
            if 'appendix:' in labelref:
                links_list.append(['appendix', labelref.replace('LABEL:', '')])
            else:
                if 'tab:' not in labelref and 'fig:' not in labelref and 'sec:' not in labelref and 'appendix:' not in labelref:
                    links_list.append(['label', labelref.replace('LABEL:', '')])
    for bibref_tag in bib_refs:
        bibrefs = bibref_tag['bibrefs']
        links_list.append(['bibliography', bibrefs])
    return links_list

def get_bibliography(bib_elements):
    references_list = []

    for element in bib_elements:
        reference = {}
        lines = element.strip().split('\n')
        for line in lines[1:]:
            if line.strip():
                match = re.match(r'\s*([^=]+)\s*=\s*{(.+)}', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    reference[key] = value
        references_list.append(reference)
    return references_list