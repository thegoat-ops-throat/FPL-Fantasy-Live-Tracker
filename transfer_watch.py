"""Non-transactional, data-backed transfer scouting for Fantasy PL Draft.

'Unrostered' means absent from the six tracked rosters; it is NOT a guarantee
of current free-agent/waiver availability. The league's official Transactions
page remains authoritative. No changes are posted to FPL Draft.
"""
import json
from pathlib import Path

POSITION = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
MANAGERS = {'Saul','Albert','Eddy','Daviel','Jaden','Andrew'}

def _num(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def safe_watch_file(path, gw):
    """Accept only clearly identified manually supplied previews.
    These never replace API-confirmed squad membership or scored lineups.
    """
    try:
        obj=json.loads(Path(path).read_text(encoding='utf8'))
    except (OSError,ValueError):
        return []
    if not isinstance(obj,dict) or int(obj.get('gameweek',0) or 0)!=gw:
        return []
    out=[]
    teams=obj.get('manager_lineups',{})
    if not isinstance(teams,dict):return []
    for name,info in teams.items():
        if name not in MANAGERS or not isinstance(info,dict):continue
        starters=info.get('starting_xi_ids',[])
        if not isinstance(starters,list) or len(starters)!=11:continue
        if not all(isinstance(n,int) and n>0 for n in starters) or len(set(starters))!=11:continue
        out.append({'name':name,'starting_xi_ids':starters,'note':str(info.get('note') or '')[:180],
                    'source':'Commissioner-entered prospective XI, not Draft-confirmed'})
    return out

def generate_watch(bootstrap, confirmed_rosters, gw, clubs, manual_file=None):
    """Return ten *scouting candidates*, not trades or claimed free agents.
    Scores are relative, estimated from available Draft-season public fields.
    """
    elements=bootstrap.get('elements',[])
    if isinstance(elements,dict):elements=list(elements.values())
    owners={}
    for manager,info in (confirmed_rosters or {}).items():
        for p in info.get('roster',[]):
            if isinstance(p,dict) and p.get('id'):
                owners[int(p['id'])]=manager
    ranked=[]
    for e in elements if isinstance(elements,list) else []:
        if not isinstance(e,dict):continue
        pid=e.get('id')
        if not isinstance(pid,int) or pid in owners:continue
        status=str(e.get('status') or 'a')
        position=e.get('element_type')
        if position not in POSITION:continue
        minutes=_num(e.get('minutes'),0) or 0
        form=_num(e.get('form'))
        ppg=_num(e.get('points_per_game'))
        total=_num(e.get('total_points'))
        if form is None and ppg is None and total is None:continue
        if minutes<45:continue
        # Exclude confirmed unavailable; leave doubts visible for informed users.
        if status in ('i','s','u'):continue
        f=max(0,min(12,form if form is not None else 0))
        g=max(0,min(12,ppg if ppg is not None else 0))
        reliability=max(0.2,min(1,minutes/(max(1,gw)*70)))
        score=round((.62*f+.38*g)*(.75+.25*reliability)*(0.78 if status=='d' else 1),2)
        if score<=0:continue
        club=clubs.get(e.get('team'),{}).get('short','—')
        reason=[]
        if form is not None:reason.append(f'Form {f:.1f}')
        if ppg is not None:reason.append(f'{g:.1f} pts/match')
        if status=='d':reason.append('Availability concern')
        if minutes<270:reason.append('Limited minutes sample')
        ranked.append({'id':pid,'name':str(e.get('web_name') or e.get('name') or f'Player {pid}'),
            'club':club,'position':POSITION[position], 'position_type':position,'scout_score':score,
            'form':round(f,1) if form is not None else None,'ppg':round(g,1) if ppg is not None else None,
            'availability':status, 'injury_news':str(e.get('news') or '')[:160],
            'reason':' · '.join(reason), 'verified_free_agent':False,
            'source':'FPL Draft public player form; NOT league availability verified'})
    ranked.sort(key=lambda p:(-p['scout_score'],-(p['form'] or 0),p['name']))
    previews=safe_watch_file(manual_file,gw) if manual_file else []
    return {'gameweek':gw,'generated_from':'Draft season form and points per game',
        'top10':ranked[:10], 'candidates':ranked[:80],
        'ownership_complete':False,'availability_note':
        'These players are not in the six tracked squads at the time checked. Official Draft availability, waiver status and other league teams must be verified before making a claim.',
        'manual_lineup_previews':previews,
        'status':'scouting suggestions only — no transactions submitted'}
