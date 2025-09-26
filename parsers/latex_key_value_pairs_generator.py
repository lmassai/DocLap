import os
import subprocess
from bs4 import BeautifulSoup
import xml_from_TEX_functions
import sys
from logger import Logger
from pathlib import Path
import shutil

def main(tex_path):
    directory = os.path.dirname(os.path.abspath(tex_path))
    out_dir = directory + '\\to_process\\'
    xml_log_file = out_dir + 'latex_processor_log.txt'

    print('TeX file path: ' + xml_log_file)

    logger = Logger(xml_log_file)
    
    if not os.path.exists(directory + '\\to_process\\'):
        os.makedirs(directory + '\\to_process\\')

    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-include-directory", directory, "-output-directory", directory + '\\to_process', tex_path])
        print(tex_path + " compiled.")
    except subprocess.CalledProcessError as e:
        print('Error compiling ' + tex_path)
    pdf_path = directory + '\\to_process\\' + os.path.basename(tex_path).replace('.tex', '.pdf')
    out_file = out_dir + os.path.basename(tex_path).replace('.tex', '_latexml.xml')
    try:
        subprocess.run(["latexml", tex_path, ">", out_file], shell=True)
        print(directory + '\latexml_output.xml' + " created.")
    except subprocess.CalledProcessError as e:
        print('Error creating' + directory + 'latexml_output.xml')
    latexml_file_path = out_file

    with open(latexml_file_path, 'r', encoding='utf-8') as latexml_file:
        latexml_content = latexml_file.read()

    main_latexml_tag = BeautifulSoup(latexml_content, 'xml')

    defaults = {
        "title_from_latex": ('get_title', ''),
        "keywords_list_from_latex": ('get_keywords', []),
        "abstract_from_latex": ('get_abstract', ''),
        "acknowledgements_from_latex": ('get_acknowledgements', ''),
        "dates_from_latex": ('get_dates', []),
        "authors_list_from_latex": ('get_authors', []),
        "affiliations_list_from_latex": ('get_affiliations', []),
        "emails_list_from_latex": ('get_emails', []),
        "chapter_titles_from_latex": ('get_chapter_titles', []),
        "subsections_list_from_latex": ('get_subsections', []),
        "figure_captions_list_from_latex": ('get_figures', []),
        "table_captions_list_from_latex": ('get_tables', []),
        "formulas_list_from_latex": ('get_formulas', []),
        "links_list_from_latex": ('get_links', [])
    }

    results = {}
    for var_name, (func_name, default) in defaults.items():
        try:
            if var_name == "subsections_list_from_latex":
                results[var_name] = getattr(xml_from_TEX_functions, func_name)(main_latexml_tag,
                                                                               results["chapter_titles_from_latex"])
            else:
                results[var_name] = getattr(xml_from_TEX_functions, func_name)(main_latexml_tag)
        except AttributeError:
            results[var_name] = default

    title_from_latex = results["title_from_latex"]
    keywords_list_from_latex = results["keywords_list_from_latex"]
    abstract_from_latex = results["abstract_from_latex"]
    acknowledgements_from_latex = results["acknowledgements_from_latex"]
    dates_from_latex = results["dates_from_latex"]
    authors_list_from_latex = results["authors_list_from_latex"]
    affiliations_list_from_latex = results["affiliations_list_from_latex"]
    emails_list_from_latex = results["emails_list_from_latex"]
    chapter_titles_from_latex = results["chapter_titles_from_latex"]
    subsections_list_from_latex = results["subsections_list_from_latex"]
    figure_captions_list_from_latex = results["figure_captions_list_from_latex"]
    table_captions_list_from_latex = results["table_captions_list_from_latex"]
    formulas_list_from_latex = results["formulas_list_from_latex"]
    links_list_from_latex = results["links_list_from_latex"]

    logger.log('Number of authors:' + str(len(authors_list_from_latex)))
    logger.log('Number of emails:' + str(len(emails_list_from_latex)))
    logger.log('Number of tables:' + str(len(table_captions_list_from_latex)))
    logger.log('Number of figures:' + str(len(figure_captions_list_from_latex)))
    logger.log('Number of formulas:' + str(len(formulas_list_from_latex)))
    logger.log('Number of dates:' + str(len(dates_from_latex)))
    logger.log('Number of chapters:' + str(len(chapter_titles_from_latex)))
    logger.log('Number of subsections (including Appendixes):' + str(len(subsections_list_from_latex)))
    logger.log('Number of sections and subsections:' + str(len(chapter_titles_from_latex) + len(subsections_list_from_latex)))
    logger.log("\nend_section")

    logger.log('\nTitle:')
    if title_from_latex != '':
        logger.log(title_from_latex)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nKeywords:')
    if len(keywords_list_from_latex) > 0:
        for j, keyword in enumerate(keywords_list_from_latex):
            logger.log('Keyword ' + str(j+1) + ': ' + keyword)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nAbstract:')
    if abstract_from_latex != '':
        logger.log(abstract_from_latex)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nAcknowledgements:')
    if acknowledgements_from_latex != '':
        logger.log(acknowledgements_from_latex)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nDates:')
    if len(dates_from_latex) > 0:
        for j, date in enumerate(dates_from_latex):
            logger.log('Date ' + str(j+1) + ': ' + date)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nAuthors:')
    if len(authors_list_from_latex) > 0:
        for j, author in enumerate(authors_list_from_latex):
            logger.log('Author ' + str(j+1) + ': ' + author)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nAffiliations:')
    if len(affiliations_list_from_latex) > 0:
        for j, affiliation in enumerate(affiliations_list_from_latex):
            logger.log('Affiliation ' + str(j+1) + ': ' + affiliation)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nEmails:')
    if len(emails_list_from_latex) > 0:
        for j, email in enumerate(emails_list_from_latex):
            logger.log('Email ' + str(j+1) + ': ' + email)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nChapter titles:')
    if len(chapter_titles_from_latex) > 0:
        for chapter in chapter_titles_from_latex:
            logger.log(f"Section {chapter[0]}: {chapter[1]}")
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nSubsections:')
    if len(subsections_list_from_latex) > 0:
        for subsection in subsections_list_from_latex:
            logger.log(f"Subsection {subsection[0]}: {subsection[1]}")
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nFigure captions:')
    if len(figure_captions_list_from_latex) > 0:
        for figure_caption in figure_captions_list_from_latex:
            logger.log(f"Caption {figure_caption[0]}: {figure_caption[1]}")
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nTables:')
    if len(table_captions_list_from_latex) > 0:
        for table_caption in table_captions_list_from_latex:
            logger.log(f"Caption {table_caption[0]}: {table_caption[1]}")
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nFormulas:')
    if len(formulas_list_from_latex) > 0:
        for j, formula in enumerate(formulas_list_from_latex):
            logger.log('Formula ' + str(j+1) + ': ' + formula)
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.log('\nLinks:')
    if len(links_list_from_latex) > 0:
        for ref_tag in links_list_from_latex:
            logger.log('Link to ' + ref_tag[0] + ': ' + ref_tag[1])
    else:
        logger.log('Not found')
    logger.log("\nend_section")

    logger.close()

    p = Path(pdf_path)
    super_folder = p.parent.parent
    dest = super_folder / p.name
    aux_file = p.parent / (p.stem + ".aux")
    log_file = p.parent / (p.stem + ".log")

    shutil.copy2(p, dest)

    command = f'python parsers/violations_finder_and_correct.py "{dest}"'
    os.system(command)

    if dest.exists():
        dest.unlink()

    if aux_file.exists():
        aux_file.unlink()

    if log_file.exists():
        log_file.unlink()

    temp_pdf_dir = p.parent / "temp_pdf"
    if temp_pdf_dir.exists() and temp_pdf_dir.is_dir():
        shutil.rmtree(temp_pdf_dir)
    pass

if __name__ == "__main__":
    tex_path = sys.argv[1]
    print('Input file: ' + tex_path)
    main(tex_path)
