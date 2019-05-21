#!/home/philk/.virtualenvs/pdf-nlp/bin/python

import sys
import glob
import pdfminer.settings
import pdfminer.high_level
import pdfminer.layout
import io
import re
import ntpath
import sqlite3
pdfminer.settings.STRICT = False


def extract_text(inputfile=None, outfile='-',
            _py2_no_more_posargs=None,  # Python2 needs a shim
            no_laparams=False, all_texts=None, detect_vertical=None, # LAParams
            word_margin=None, char_margin=None, line_margin=None, boxes_flow=None, # LAParams
            output_type='text', codec='utf-8', strip_control=False,
            maxpages=0, page_numbers=None, password="", scale=1.0, rotation=0,
            layoutmode='normal', output_dir=None, debug=False,
            disable_caching=False, **other):
    if _py2_no_more_posargs is not None:
        raise ValueError("Too many positional arguments passed.")
    if not inputfile:
        raise ValueError("Must provide an input file")

    # If any LAParams group arguments were passed, create an LAParams object and
    # populate with given args. Otherwise, set it to None.
    if not no_laparams:
        laparams = pdfminer.layout.LAParams()
        for param in ("all_texts", "detect_vertical", "word_margin", "char_margin", "line_margin", "boxes_flow"):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)
    else:
        laparams = None

    outfp = io.StringIO()

    # print(locals())
    with open(inputfile, "rb") as fp:
        pdfminer.high_level.extract_text_to_fp(fp, **locals())
    return outfp.getvalue()


def format_text(fname, input_text):
    doc_headings = {'Investment objective': 'investment_objective',
                    'Investment strategy': 'investment_strategy',
                    'Performance (%)': 'performance_percentage',
                    'Performance review': 'performance_review',
                    'Market review': 'market_review',
                    'Outlook': 'outlook'}
    headings_found = []
    data_to_store = {'doc_name': '',
                     'doc_date': '',
                     'investment_objective': '',
                     'investment_strategy': '',
                     'performance_percentage': '',
                     'performance_review': '',
                     'market_review': '',
                     'outlook': ''}

    input_lines = input_text.splitlines()

    # for line in input_lines:
    #     print(line)

    # Check if any heading found
    for line in input_lines:
        if line in doc_headings.keys():
            headings_found.append(line)

    # print(headings_found)

    for heading, next_heading in pairwise(headings_found):
        # print("%s, %s" % (heading, next_heading))
        data_to_store[doc_headings[heading]] = get_paragraph(heading, next_heading, input_lines)

    # Get document date
    for line in input_lines:
        if line.startswith('Monthly factsheet - '):
            # print(re.search('(0[1-9]|[12][0-9]|3[01])[ ]'
            #                 '(January|February|March|April|May|June|July|August|September|October|November|December)'
            #                 '[ ](19|20)\d\d$', line)[0])

            data_to_store['doc_date'] = re.search('(0[1-9]|[12][0-9]|3[01])[ ]'
                                                  '(January|February|March|April|May|June|July'
                                                  '|August|September|October|November|December)'
                                                  '[ ](19|20)\d\d$', line)[0]
            # Stop once you get the first one
            break

    # Store document filename only
    data_to_store['doc_name'] = ntpath.basename(fname)

    # data to store
    print(data_to_store)
    return data_to_store




def pairwise(lst):
    """ yield item i and item i+1 in lst. e.g.
        (lst[0], lst[1]), (lst[1], lst[2]), ..., (lst[-1], None)
    """
    if not lst:
        return

    for i in range(len(lst)-1):
        yield lst[i], lst[i+1]

    yield lst[-1], None


def get_paragraph(heading, next_heading, input_lines):

    heading_pos = input_lines.index(heading)
    # print(heading_pos)

    # Handle the last paragraph
    if next_heading is None:
        end_paragraph_pos = input_lines[heading_pos + 1:].index('')
        # print(end_paragraph_pos)
        joined_paragraph = ''.join(input_lines[heading_pos + 1:heading_pos + end_paragraph_pos + 1])

    # This block should handle the cases when the paragraph is split across two pages
    else:
        # Figure out if the paragraph is split by looking for 'Monthly factsheet - '
        next_heading_pos = input_lines.index(next_heading)
        is_split = False

        for monthly_factsheet_pos in [i for i, line in enumerate(input_lines) if line.startswith('Monthly factsheet - ')]:
            # print(monthly_factsheet_pos)

            if monthly_factsheet_pos > heading_pos and monthly_factsheet_pos < next_heading_pos:
                is_split = True
                # print('Paragraph is split!')

        # Handle split paragraphs
        if is_split is True:
            # Get the first half of the paragraph
            first_end_paragraph_pos = input_lines[heading_pos + 1:].index('')
            # print(first_end_paragraph_pos)
            first_joined_paragraph = ''.join(input_lines[heading_pos + 1:heading_pos + first_end_paragraph_pos + 1])

            # Get the second half of the paragraph
            second_end_paragraph_pos = input_lines[monthly_factsheet_pos + 2:].index('')
            # print(second_end_paragraph_pos)
            second_joined_paragraph = ''.join(input_lines[monthly_factsheet_pos + 2:monthly_factsheet_pos + second_end_paragraph_pos + 2])

            # Concat first and second part
            joined_paragraph = ' '.join([first_joined_paragraph, second_joined_paragraph])

        # Handle paragraphs not split across two pages
        else:
            # print(next_heading_pos)
            joined_paragraph = ''.join(input_lines[heading_pos + 1:next_heading_pos - 1])

    # Clean up unwanted whitespaces
    cleaned_paragraph = ' '.join(joined_paragraph.split())
    # print(cleaned_paragraph)
    return cleaned_paragraph


def main():

    # Use all PDF files in data directory
    inputfiles = {'files': glob.glob("data/*.pdf")}
    # Use one PDF file for testing
    # inputfiles = {'files': ['data/active_index_income_fund.pdf']}

    # Store data into sqlite database
    conn = sqlite3.connect('pdf_text_extract.db')
    cur = conn.cursor()
    cur.execute('''
    DROP TABLE IF EXISTS extracts''')
    cur.execute('''
    CREATE TABLE extracts
    (doc_name TEXT,
    doc_date TEXT,
    investment_objective TEXT,
    investment_strategy TEXT,
    performance_percentage TEXT,
    performance_review TEXT,
    market_review TEXT,
    outlook TEXT)''')

    for fname in inputfiles['files']:
        extracted_text = extract_text(fname)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', extracted_text)
        formatted_text_dict = format_text(fname, cleaned_text)
        cur.execute('''
        INSERT INTO extracts VALUES (?,?,?,?,?,?,?,?)''', list(formatted_text_dict.values()))

    # Commmit and close database
    conn.commit()
    cur.close()

if __name__ == '__main__':
    sys.exit(main())
