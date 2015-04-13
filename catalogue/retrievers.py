
'''
A contentmine Retriever template
At the bottom the Retriever object type is defined, the main task of it is run()
Other classes should inherit from the Retriever object template, and overwrite 
_cmd to show what command they need to run.
Then they can optionally overwrite before, after, store and save - do actions corresponding to the run
By default before, after, store and save are executed by run, but they can be disabled on any default run call
by sending before=False etc
However of course the default action of these methods is pass. So unless they are overwritten in the defined Retrievers 
with something useful, nothing would happen anyway.
Retrievers can also overwrite run if necessary
Each Retriever class should be able to be called and return output and delete anything it put on disk by default
It can also be programmed using the available overwriteable methods to store the stuff it put on disk somewhere else

Make sure to use class names that start with one upper case letter and the rest lower case.
'''

import uuid, subprocess, os, shutil, json, requests, time
from flask import current_app


class Retriever(object):
    def __init__(self):
        self.output = {
            "records": []
        }
    
    def store(self, reclist=[], idkey='id'):
        if len(reclist) > 0:
            recs = reclist
        else:
            recs = self.output["records"]
        data = ''
        for r in recs:
            data += json.dumps( {'index':{'_id':r[idkey]}} ) + '\n'
            data += json.dumps( r ) + '\n'
        r = requests.post(current_app.config['INDEX_URL'] + '_bulk', data=data)
        self.output["store"] = r.json()

    def _cmd(self, **kwargs):
        self.output['command'] = []
        for key in kwargs.keys():
            self.output['command'].append(key)
            self.output['command'].append(kwargs[key])
    
    def before(self, **kwargs):
        pass
    
    def after(self, **kwargs):
        pass
    
    def meta(self):
        return {} # a method to return any metadata that may be needed by UI to build user options
        
    def run(self, before=True,after=True,store=True,save=True,**kwargs):
        # check for dodgy characters in the kwargs
        if 'callback' in kwargs: del kwargs['callback']
        if '_' in kwargs: del kwargs['_']
        for k in kwargs.keys():
            if ';' in k or ';' in kwargs[k]:
                self.output['errors'] = ['Sorry, illegal character found in args.']
                return self.output
        if before: self.before(**kwargs)
        self._cmd(**kwargs)
        try:
            p = subprocess.Popen(self.output['command'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.output['output'], self.output['errors'] = p.communicate()
        except Exception, e:
            self.output['output'] = {}
            self.output['errors'] = [str(e)]
        if after: self.after(**kwargs)
        if not isinstance(self.output['errors'],dict) and not isinstance(self.output['errors'],list):
            self.output['errors'] = [i for i in self.output['errors'].split('\n') if len(i) > 0]
        if not isinstance(self.output['output'],dict) and not isinstance(self.output['output'],list) and '\n' in self.output['output']:
            self.output['output'] = [i for i in self.output['output'].split('\n') if len(i) > 0]
        if store: self.store(**kwargs)
        return self.output

    

'''        
class core(Retriever):
    def _cmd(self, **kwargs):
        self.output['command'] = ['quickscrape']
        if len(kwargs) > 0:
            for key in kwargs.keys():
                k = key
                if not key.startswith('-'): k = '-' + k
                if len(key) > 2: k = '-' + k
                if k not in ['-d','--scraperdir','-o','--output','-f','--outformat']:
                    self.output['command'].append(k)
                    self.output['command'].append(kwargs[key])
            self.output['command'].append('--scraperdir')
            self.output['command'].append(current_app.config['QS_JS_DIR'])

            
            
class doaj(Retriever):
    
    
class opendoar(Retriever):
    

class crossref(Retriever):
    
    
class arxiv(Retriever):
    
    
class journaltocs(Retriever):
'''

