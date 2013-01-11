#!/usr/bin/env python
# encoding: utf-8
"""
gus.py

Created by virtualastronomer on 2013-01-10.
Copyright (c) 2013 Smithsonian Astrophysical Observatory. All rights reserved.

History:
    10 Jan 2013
    
    Good news: My bibcode pyparser still works. I understand sorting and
    can pass stuff in and get junk out. I can run it in ipython notebook...
    
    I rooted around for a straight text to PDF formatter and ended up with 
    reportlab. It works, but I fear that full format control will require
    a fair bit of low lever hacking...  
    
    Even so I remembered that latex "writing" (tabs, etc) is a total fucking
    mess too, and prone to pain for anyone wanting to write a "latex" document
    that can be converted to toher formats.  A better solution would be to 
    template the whole thing (write template, apply inputs, export output).
    
    A better solution is then write out ReST templates, import the json and
    write out to ReST and convert to (? HTML PDF etc) using the templating.
"""

import os
import sys
import simplejson
import requests
import pyparsing as pp

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# base API search url
BASE_URL = 'http://adslabs.org/adsabs/api/search/'

# developer API access key
DEV_KEY = 'RNXwVjVrpaXez8fh'

def pub_map(pub):
    # function to lookup shortnames for publication names
    return pub

def pub_filter(properties,filters):
    """ Return true false if *any* of a set of paper parameters are returned.
    """
    return len(set(properties).intersection(set(filters))) > 0 
    
def ppBibCode(content):
    """ ADS bibcode parser

        See:

        Grammar:
            YYYYJJJJJVVVVMPPPPA
    """
    y_grm = pp.nums
    j_grm = pp.alphas + '.&'
    v_grm = pp.alphanums + '.'
    m_grm = "iDELPQRSTUV" + '.' # restricting this is prob a bad idea
    p_grm = pp.alphanums + '.'
    a_grm = pp.alphas + '.'

    noper = lambda t: [x.replace('.', '') for x in t]

    y = pp.Word(y_grm, exact=4).setResultsName('Y')
    j = pp.Word(j_grm, exact=5).setResultsName('J')
    j.setParseAction(noper)
    v = pp.Word(v_grm, exact=4).setResultsName('V')
    v.setParseAction(noper)
    m = pp.Word(m_grm, exact=1).setResultsName('M')
    m.setParseAction(noper)
    p = pp.Word(p_grm, exact=4).setResultsName('P')
    p.setParseAction(noper)
    a = pp.Word(a_grm, exact=1).setResultsName('A')
    a.setParseAction(noper)
    bibp = y + j + v + m + p + a
    bib = bibp.parseString(content)

    return (bib.Y, bib.J, bib.V, bib.M, bib.P, bib.A)

def testppBibCode():
    """ test function for bibcode parser
    """
    tests = [['2009AJ....137....1F', '2009', 'AJ', '137', '', '1', 'F']]
    tests.append(['2001A&A...365L...1J', '2001', 'A&A', '365', 'L', '1', 'J'])
    tests.append(['1910YalRY...1....1E', '1910', 'YalRY', '1', '', '1', 'E'])
    tests.append(['1998bllp.confE...1U', '1998', 'bllp', 'conf', 'E', '1', 'U'])

    for test in tests:
        assert ppBibCode(test[0]) == tuple(test[1:])

def main():
    author = "Muench, A."
    filters = ['REFEREED']
    
    params = {}
    
    # basic author search
    params['q'] = "author:^%s" % author

    # the fields we want back
    params['fl'] = 'bibcode,title,pub,author'
    
    # process N results at a time
    params['rows'] = '5'
    
    # include our access key
    params['dev_key'] = DEV_KEY
    
    params['sort'] = "CITED desc"
    
    # first N
    start = 0
    processed = 0    
    params['start'] = start
    
    r = requests.get(BASE_URL, params=params)
    
    if r.status_code != requests.codes.ok:
        # hopefully if something went wrong you'll get a json error message
        e = simplejson.loads(r.text)
        sys.stderr.write("error retrieving results for author %s: %s\n" % (author, e['error']))

    data = simplejson.loads(r.text.decode('utf-8'))
    hits = data['meta']['hits'] #total possible records for query
    count = data['meta']['count'] #records in this return

    c = canvas.Canvas("hello.pdf", pagesize=letter)
    pdfx = 30
    pdfy = 750
    lits = 80
    litd = 10
    for d in data['results']['docs']:
        title = d.get('title','notitle')
        c.drawString(pdfx, pdfy, title)
        year, journal, volume, m, page, acroynm = ppBibCode(d.get('bibcode'))
        print pdfx, pdfy, year, title
        print "   ", year, journal, volume, m, page, acroynm
        pdfy = pdfy - lits
        
    c.save()
    pass

if __name__ == '__main__':
    main()

