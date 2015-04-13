
import os, requests, json, uuid, inspect
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, request, make_response, current_app, abort, render_template
from flask.ext.login import LoginManager, current_user, login_user

from catalogue import settings, retrievers

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    # parent directory
    here = os.path.dirname(os.path.abspath( __file__ ))
    config_path = os.path.join(os.path.dirname(here), 'app.cfg')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)
    login_manager.setup_app(app)
    if app.config.get('WITH_ES',False):
        if requests.head(app.config['INDEX_URL']).status_code != 200:
            requests.post(app.config['INDEX_URL'])
            requests.put(app.config['MAPPING_URL'], json.dumps(app.config['MAPPING']))
    return app

app = create_app()

@login_manager.user_loader
def load_account_for_login_manager(userid):
    # TODO should actually get a user somehow here or return anonymous user
    # connect to separate CL user auth tool
    return {}

'''
TODO: auth against CL accounts system - get user, their rights on this service, and the group they are in
then get details about this service from the CL services system - to work out what the user is allowed to do

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = models.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values or 'api_key' in request.headers:
        apik = request.values['api_key'] if 'api_key' in request.values else request.headers['api_key']
        res = models.Account.query(q='api_key:"' + apik + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)
'''


@app.errorhandler(404)
def page_not_found(e):
    return 'File Not Found', 404

@app.errorhandler(401)
def page_not_found(e):
    return 'Unauthorised', 401
        
        
def rjson(f):
    # wraps output as a JSON response, with JSONP if necessary
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            print raw
        except:
            raw = False
        callback = request.args.get('callback', False)
        if raw:
            return f(*args,**kwargs)
        elif callback:
            content = str(callback) + '(' + str(f(*args,**kwargs)) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            res = f(*args, **kwargs)
            if not isinstance(res,dict) and not isinstance(res,list): res = [i for i in str(res).split('\n') if len(i) > 0]
            resp = make_response( json.dumps( res, sort_keys=True ) )
            resp.mimetype = "application/json"
            return resp
    return decorated_function


# add checks once account auth in place    

@app.route('/', methods=['GET','POST'])
@app.route('/<procname>', methods=['GET','POST'])
@rjson
def proc(procname=None):
    if procname is None:
        return {
            "title": "Cottage Labs Catalogue",
            "version": "0.1",
            "README": "A catalogue of articles.",
            "retrievers": [name.lower() for name, obj in inspect.getmembers(retrievers) if inspect.isclass(obj) and name != 'Retriever'],
            "routes": ['record','query','filter','daily']
        }
    else:
        pr = getattr(retrievers, procname[0].capitalize() + procname[1:].lower() )
        params = request.json if request.json else request.values
        params = {k:params[k] for k in params.keys()}
        return pr().run(**params)
    
    

@app.route('/record', methods=['GET','POST'])
@app.route('/record/<ident>', methods=['GET','POST'])
@rjson
def record(ident=None):
    if ident is not None:
        try:
            f = requests.get(app.config['INDEX_URL'] + ident)
            rec = f.json()['_source']
        except:
            abort(404)
    else:
        rec = {"record":{},"meta":{}}
    if request.method == 'GET':
        if ident is not None:
            return rec['record'] # TODO show full record with meta info depending on user permission
        else:
            return 'Cottage Labs Catalogue' # instructions
    elif request.method in ['PUT','POST']:
        inp = {}
        if request.json:
            for k in request.json.keys():
                if k.lower() not in ['submit','api_key']:
                    inp[k] = request.json[k]
        else:
            for k, v in request.values.items():
                if k.lower() not in ['submit','api_key']:
                    inp[k] = v
        if request.method == 'PUT':
            if "meta" in inp: # TODO and if user has permission to update meta
                rec = inp
            else:
                rec["record"] = inp
        else:
            for k in inp.keys():
                if "meta" in inp: # TODO and if user has permission to update meta
                    rec[k] = inp[k]
                else:
                    rec["record"][k] = inp[k]
        if 'id' not in rec:
            if 'id' in rec['record']:
                rec['id'] = rec['record']['id']
            else:
                rec['id'] = uuid.uuid4().hex
                rec['record']['id'] = rec['id']
        rec['updated_date'] = datetime.now().strftime("%Y-%m-%d %H%M")
        rec['updated_by'] = 'anon_UI' # TODO change this depending on username, method, etc. Store changes to history if necessary
        if 'created_date' not in rec:
            rec['created_date'] = datetime.now().strftime("%Y-%m-%d %H%M")
        # TODO: save user doing this action
        return requests.post(app.config['INDEX_URL'] + rec['id'], data=json.dumps(rec))


@app.route('/query', methods=['GET','POST'])
@rjson
def fquery():
    # NOTE tried streaming response with context here through requests but it was very slow
    if request.method == 'GET':
        return requests.get(app.config['INDEX_URL'] + '_search?' + "&".join([k + '=' + request.args[k] for k in request.args.keys()])).json()
    elif request.method == 'POST':
        params = request.json if request.json else request.values
        params = {k:params[k] for k in params.keys()}
        return requests.post(app.config['INDEX_URL'] + '_search', data=json.dumps(params)).json()

    
@app.route('/filter', methods=['GET','POST'])
@app.route('/filter/<valstr>', methods=['GET','POST'])
@rjson
def find(valstr=None):
    # NOTE tried streaming response with context here through requests but it was very slow
    params = request.json if request.json else request.values
    qry = {
        "query" : {
            "filtered": {
                "filter": {
                    "bool" : {
                        "must" : []
                    }
                }
            }
        }
    }
    if 'values' in params or valstr is not None:
        if valstr:
            vals = valstr
        elif not isinstance(params['values'],list) and ',' in params['values']:
            vals = params['values'].split(',')
        else:
            vals = params['values']
        if isinstance(params['values'],list):
            for val in vals:
                qry['query']['filtered']['filter']['bool']['must'].append({'query':{'query_string': val}})
        else:
            qry['query']['filtered']['filter'] = {'query':{'query_string': params['values']}}
    else:
        for k, v in params.items():
            if k.lower() not in ['submit','api_key','from','size']:
                tq = {}
                tq[k] = v
                qry['query']['filtered']['filter']['bool']['must'].append({'term':tq})
    if 'from' in request.values:
        qry['from'] = request.values['from']
    if 'size' in request.values:
        qry['size'] = request.values['size']    
    r = requests.post(app.config['INDEX_URL'] + '_search', data=json.dumps(qry)).json()
    return [i['_source']['record'] for i in r.json().get('hits',{}).get('hits',[])]


@app.route('/daily')
@app.route('/daily/<start>')
@app.route('/daily/<start>/<end>')
@rjson
def daily(start=None,end=None):
    # TODO: this should be a filtered query
    if start is None:
        start = datetime.now().strftime("%Y-%m-%d") + ' 0000'
    else:
        try:
            startcheck = start.strptime("%Y-%m-%d %H%M")
        except:
            abort(404)
    if end is None:
        end = (start.strptime("%Y-%m-%d %H%M") + timedelta(days=1)).strftime("%Y-%m-%d %H%M")
    else:
        try:
            endcheck = end.strptime("%Y-%m-%d %H%M")
        except:
            abort(404)
    qry = {
        "query" : {
            "filtered": {
                "filter": {
                    "range": {
                        "created_date": {
                            "gte": start,
                            "lt": end
                        }
                    }
                }
            }
        },
        'sort': [{"created_date.exact":{"order":"desc"}}]
    }
    if 'from' in request.values:
        qry['from'] = request.values['from']
    if 'size' in request.values:
        qry['size'] = request.values['size']
    r = requests.post(app.config['INDEX_URL'] + '_search', data=json.dumps(qry))
    return [i['_source']['record'] for i in r.json().get('hits',{}).get('hits',[])]
   

@app.route('/title', methods=['GET','POST'])
@app.route('/title/<title>', methods=['GET','POST'])
@rjson
def title(title=None):
    # NOTE tried streaming response with context here through requests but it was very slow
    params = request.json if request.json else request.values
    if title is None:
        title = params.get('title','*')
    # TODO: this should be some sort of smart search for a single record with similar title
    qry = {
        "query" : {
            "filtered": {
                "filter": {
                    "flt" : {
                        "fields": ["record.title"],
                        "like_text" : title
                    }
                }
            }
        },
        "size":1
    }
    r = requests.post(app.config['INDEX_URL'] + '_search', data=json.dumps(qry)).json()
    return [i['_source']['record'] for i in r.json().get('hits',{}).get('hits',[])]


@app.route('/browse', methods=['GET','POST'])
def browse():
    return render_template('browse.html')

@app.route('/graph', methods=['GET','POST'])
def graph():
    return render_template('graph.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

