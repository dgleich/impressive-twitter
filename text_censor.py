#!/usr/bin/env python

"""
text_censor.py
==============

Censor, flag, or filter short segments of text.  Needs a list of
bad words to definitely filter on.

Designed to be used the with list of words from:
http://urbanoalvarez.es/blog/2008/04/04/bad-words-list/`
"""

import os
import string

import unac

def remove_accents(s):
    #return unicodedata.normalize('NFKD',u).encode('ascii','ignore')
    return unac.unac_string(s)

def remove_punctuation(str, delete=False, punct=string.punctuation):
    if type(str)==type('str'):
        if delete:        
            return string.translate(str, string.maketrans('', ''), punct)
        else:
            return string.translate(str, string.maketrans(punct, ' '*len(punct)))
    else:
        tab = {}
        if delete:        
            tab.update( (ord(c),None) for c in punct )
            return str.translate(tab)
        else:
            tab.update( (ord(c),u' ') for c in punct )
            return str.translate(tab)

def punct_ratio(str,punct=set(string.punctuation)):
    """ Return the ratio of punctuation to letters """
    
    pchar = 0
    chars = 0
    for s in str:
        chars += 1
        if s in punct:
            pchar += 1
    return (pchar,chars)

class ShortTextCensor:
    def __init__(self,badwordlist=[],
        badwordlistfile=os.path.join(
                            os.path.split(os.path.abspath( __file__ ))[0],
                            'badwords.txt')):
        self.badwords = set()
        self.add_badwords(badwordlist)
        self.add_badword_file(badwordlistfile)
    
    def add_badwords(self,list):
        """  Add words from a python list to the database of badwords. """
        for b in list:
            self.badwords.add(b)
            self.badwords.add(b.lower())
            
    def add_badword_file(self,filename):
        """ Add words from a newline delimited file """
        f = open(filename)
        for line in f:
            line = line.rstrip()
            self.badwords.add(line)
            self.badwords.add(line.lower())
            
    def check(self,text):
        parts = text.split()
        for p in parts:
            pl = p.lower()
            if p in self.badwords or pl in self.badwords:
                return True
        for p in parts:
            p = remove_accents(p)
            p = remove_punctuation(p)
            p = p.lower()
            if p in self.badwords:
                return True
        
        # now text generic regexes
        tlower = text.lower()
        for w in self.badwords:
            if w in tlower:
                return True
        tlower = remove_accents(tlower)
        for w in self.badwords:
            if w in tlower:
                return True
        tlower = remove_punctuation(tlower)
        for w in self.badwords:
            if w in tlower:
                return True
        
        # now look for weird words
        urlparts = []
        for p in parts:
            if p.startswith('http://'):
                urlparts.append(p)
                continue
            else:
                p = remove_accents(p)
                (pchar,chars) = punct_ratio(p)
                if chars>5 and pchar>3:
                    return True
                
        return False
            
            
            
if __name__=='__main__':
    C = ShortTextCensor()
    print C.check("fuck")
    
            
