#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 15:15:05 2022

@author: jotape42p
"""

### For ILCD Structure

import re

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

def split_into_sentences(text):
    """Splits text into sentences. 
        from: https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
    """
    
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(";",";<stop>")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1] if sentences[-1]=="  " else sentences
    sentences = [s.strip() for s in sentences]
    
    return sentences

def text_to_list(text, limit):
    def optimize(n, s='; '):
        f=''
        for x in n:
            if f == '':
                f = x
            elif len(f+'; '+x) > limit:
                yield f.strip()
                f = x
            else:
                if x.isspace(): pass
                elif f.strip().endswith(('.', ';')): f+=' '+x
                else: f+=s+x
        yield f.strip()
    n = split_into_sentences(text)
    if max([len(x) for x in n]) < limit:
        return list(optimize(n))
    else:
        m, s = [], '; '
        for x in n:
            if len(x) > limit:
                b, s = '', ' '
                for i in range(0, len(x), limit-50):
                    if len(x[i:i+limit-50]+b) > limit:
                        m.append(b)
                        c = x[i:i+limit-50].split(' ')
                    else:
                        c = (b+x[i:i+limit-50]).split(' ')
                    if len(c[:-1]) > 0:
                        a, b = c[:-1], c[-1]
                    else:
                        a, b, s = x[i:i+limit-50], '', ''
                    m.append(' '.join(a) if isinstance(a, list) else a)
            else:
                m.append(x)
        return list(optimize(m, s))
