#!/home/philk/.virtualenvs/pdf-nlp/bin/python

import sys
# import glob
import pdfminer.settings
import pdfminer.high_level
import pdfminer.layout
import io
import re
pdfminer.settings.STRICT = False


def extract_text(inputfiles=[], outfile='-',
            _py2_no_more_posargs=None,  # Bloody Python2 needs a shim
            no_laparams=False, all_texts=None, detect_vertical=None, # LAParams
            word_margin=None, char_margin=None, line_margin=None, boxes_flow=None, # LAParams
            output_type='text', codec='utf-8', strip_control=False,
            maxpages=0, page_numbers=None, password="", scale=1.0, rotation=0,
            layoutmode='normal', output_dir=None, debug=False,
            disable_caching=False, **other):
    if _py2_no_more_posargs is not None:
        raise ValueError("Too many positional arguments passed.")
    if not inputfiles:
        raise ValueError("Must provide files to work upon!")

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
    for fname in inputfiles['files']:
        with open(fname, "rb") as fp:
            pdfminer.high_level.extract_text_to_fp(fp, **locals())
    return outfp.getvalue()


def store_text(input_text):
    paragraph_headings = ['Investment objective', 'Investment strategy', 'Performance review', 'Market review',
                          'Outlook']
    data_to_store = dict()

    input_lines = input_text.splitlines()

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

    # Check if any heading found
    for line in input_lines:
        if line in paragraph_headings:
            print(line)


    # data to store
    print(data_to_store)


def main(args=None):
    # inputfiles = {'files': glob.glob("data/*.pdf")}
    inputfiles = {'files': ['data/active_index_income_fund.pdf']}
    extracted_text = extract_text(inputfiles)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', extracted_text)
    print(cleaned_text.splitlines())
    store_text(extracted_text)

if __name__ == '__main__':
    sys.exit(main())
