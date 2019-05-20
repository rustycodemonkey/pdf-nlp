#!/home/philk/.virtualenvs/pdf-nlp/bin/python

import sys
# import glob
import pdfminer.settings
import pdfminer.high_level
import pdfminer.layout
import io
import re
from itertools import tee
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

def store_text(input_text):
    doc_headings = {'Investment objective': 'objective',
                    'Investment strategy': 'strategy',
                    'Performance review': 'performance',
                    'Market review': 'market',
                    'Outlook': 'outlook'}
    headings_found = []
    data_to_store = {'doc_date': '',
                     'objective': '',
                     'strategy': '',
                     'performance': '',
                     'market': '',
                     'outlook': ''}

    input_lines = input_text.splitlines()

    # for line in input_lines:
    #     print(line)

    # Check if any heading found
    for line in input_lines:
        if line in doc_headings.keys():
            headings_found.append(line)

    print(headings_found)

    for heading, next_heading in pairwise(headings_found):
        print(heading, next_heading)
        data_to_store[doc_headings[heading]] = get_paragraph(heading, next_heading, input_lines)

    # Get document date
    for line in input_lines:
        if line.startswith('Monthly factsheet'):
            print(re.search('(0[1-9]|[12][0-9]|3[01])[ ]'
                            '(January|February|March|April|May|June|July|August|September|October|November|December)'
                            '[ ](19|20)\d\d$', line)[0])

            data_to_store['doc_date'] = re.search('(0[1-9]|[12][0-9]|3[01])[ ]'
                                                  '(January|February|March|April|May|June|July'
                                                  '|August|September|October|November|December)'
                                                  '[ ](19|20)\d\d$', line)[0]
            # Stop once you get the first one
            break

    # data to store
    print(data_to_store)

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
    print(heading_pos)

    if next_heading is None:
        paragraph_num_lines = input_lines[heading_pos + 1:].index('')
        # print(paragraph_num_lines)
        joined_paragraph = ''.join(input_lines[heading_pos + 1:heading_pos + paragraph_num_lines + 1])
    else:
        # TODO: Think about this part more and then code
        next_heading_pos = input_lines.index(next_heading)
        print(next_heading_pos)
        joined_paragraph = ''.join(input_lines[heading_pos + 1:next_heading_pos - 1])

    print(joined_paragraph)

    # TODO: Add other text cleaning smarts here.
    return joined_paragraph

def main():

    # inputfiles = {'files': glob.glob("data/*.pdf")}
    inputfiles = {'files': ['data/active_index_income_fund.pdf']}

    for fname in inputfiles['files']:
        extracted_text = extract_text(fname)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', extracted_text)
        store_text(cleaned_text)

if __name__ == '__main__':
    sys.exit(main())
