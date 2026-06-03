# -*- coding: utf-8 -*-
import re
s=open('C:/Users/andra/claude/geo-quiz.html',encoding='utf-8').read()
blocks=re.findall(r'<script>(.*?)</script>',s,re.S)

def balance(code):
    i=0; n=len(code)
    par=0; sq=0; cur=0
    # mode stack: each entry is a delimiter we're inside: '"', "'", '`'
    mode=None
    tmpl_stack=[]   # when we enter ${ inside a template, push the template delim
    while i<n:
        c=code[i]
        if mode in ('"',"'",'`'):
            if c=='\\':
                i+=2; continue
            if mode=='`' and c=='$' and i+1<n and code[i+1]=='{':
                tmpl_stack.append(('`',cur)); mode=None; cur+=1; i+=2; continue
            if c==mode:
                mode=None
            i+=1; continue
        # not in a string
        if c=='/' and i+1<n and code[i+1]=='/':
            j=code.find('\n',i); i=(n if j<0 else j); continue
        if c=='/' and i+1<n and code[i+1]=='*':
            j=code.find('*/',i); i=(n if j<0 else j+2); continue
        if c in '"\'`':
            mode=c; i+=1; continue
        if c=='(' : par+=1
        elif c==')': par-=1
        elif c=='[': sq+=1
        elif c==']': sq-=1
        elif c=='{': cur+=1
        elif c=='}':
            cur-=1
            if tmpl_stack and cur==tmpl_stack[-1][1]:
                mode=tmpl_stack.pop()[0]
        i+=1
    return dict(par=par,sq=sq,cur=cur,mode=mode,tmpl=len(tmpl_stack))

for idx,b in enumerate(blocks):
    print('block',idx,'len',len(b),balance(b))
