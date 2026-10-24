"""Touchline local server. Run with Python 3.10+; no dependencies."""
import json, os, threading, time, urllib.request, urllib.error
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STATE=ROOT/'scores.json'
IDS={'Saul':393832,'Albert':365375,'Eddy':372793,'Daviel':372999,'Jaden':365166,'Andrew':372608}
GW7={'Saul':61,'Albert':54,'Eddy':43,'Daviel':34,'Jaden':46,'Andrew':37}
DEFAULT={'updated_at':None,'status':'Waiting for verified Draft API data','source':'Fantasy Premier League Draft','gameweek':8,'scores':{},'rounds':{},'history':[]}
lock=threading.Lock()

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'TouchlineBiweekly/1.0 (personal league scoreboard)','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=12) as r:
        return json.load(r)

def load():
    if STATE.exists():
        try: return json.loads(STATE.read_text(encoding='utf8'))
        except (OSError,ValueError): pass
    return dict(DEFAULT)

def save(state):
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding='utf8');tmp.replace(STATE)

def poll():
    with lock:
        state=load()
        try:
            # Draft's API is separate from standard Fantasy Premier League.
            # Never substitute standard FPL scores for Draft scores.
            bootstrap=fetch('https://draft.premierleague.com/api/bootstrap-static')
            events=bootstrap.get('events', {})
            # Official Draft bootstrap: events = {'current': 8, 'data': [...]}.
            if isinstance(events, dict) and isinstance(events.get('current'), int):
                current=events['current']
            else:
                event_list=events.get('data', []) if isinstance(events, dict) else events
                if not isinstance(event_list, list):
                    raise ValueError('Unexpected Draft events format')
                now=datetime.now(timezone.utc)
                parsed=[]
                for event in event_list:
                    if not isinstance(event, dict): continue
                    deadline=event.get('deadline_time')
                    if not isinstance(deadline, str): continue
                    try:
                        parsed.append((datetime.fromisoformat(deadline.replace('Z','+00:00')),int(event['id'])))
                    except (ValueError,TypeError,KeyError): continue
                if not parsed: raise ValueError('Draft API did not supply usable Gameweek deadlines')
                past=[item for item in parsed if item[0]<=now]
                current=max(past)[1] if past else min(parsed)[1]
            live=fetch(f'https://draft.premierleague.com/api/event/{current}/live')
            elements=live.get('elements') if isinstance(live,dict) else None
            if not isinstance(elements,dict): raise ValueError('Draft live API has no player elements')
            scores={}; players={}; provisional={}
            for name,entry in IDS.items():
                payload=fetch(f'https://draft.premierleague.com/api/entry/{entry}/event/{current}')
                picks=payload.get('picks') if isinstance(payload,dict) else None
                if not isinstance(picks,list) or len(picks)!=15:
                    raise ValueError(f'Expected 15 picks for {name}')
                total=0; roster=[]
                for pick in sorted(picks,key=lambda x:x['position']):
                    pid=str(pick['element'])
                    stats=elements.get(pid,{}).get('stats',{})
                    pts=stats.get('total_points')
                    if not isinstance(pts,int): raise ValueError(f'No points for player {pid} on {name}')
                    position=int(pick['position'])
                    multiplier=int(pick.get('multiplier',1))
                    if position<=11: total+=pts*multiplier
                    roster.append({'id':int(pid),'position':position,'points':pts,'minutes':stats.get('minutes',0),'multiplier':multiplier})
                # Provisional: automatic substitutions and late corrections can change final score.
                scores[name]=total
                players[name]=roster
                provisional[name]=True
            state['scores'][str(current)]=scores
            state.setdefault('players',{})[str(current)]=players
            state['gameweek']=current
            state['updated_at']=datetime.now(timezone.utc).isoformat()
            state['status']='Live Draft player points loaded — starting XI totals provisional'
            state['provisional']=True
            # Archive only completed two-week rounds, using final GW totals when available.
            # GW7 is a screenshot baseline, not a verified final API result.
            for gw in range(8,current,2):
                first=state['scores'].get(str(gw-1),GW7 if gw==8 else None)
                second=state['scores'].get(str(gw))
                if first and second:
                    key=f'GW{gw-1}–GW{gw}'
                    state.setdefault('rounds',{})[key]={name:first[name]+second[name] for name in IDS if name in first and name in second}
            save(state)
        except Exception as e:
            state['status']='Live refresh unavailable: '+str(e)[:160]
            # Keep old verified data and timestamps, never label stale data as freshly updated.
            save(state)

def loop():
    while True:
        poll();time.sleep(300)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        if self.path.split('?')[0]=='/api/status':
            data=json.dumps(load(),ensure_ascii=False).encode()
            self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        else:super().do_GET()

if __name__=='__main__':
    threading.Thread(target=loop,daemon=True).start()
    print('Open http://localhost:8000 (Ctrl+C to stop)')
   ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8000))), Handler).serve_forever()
