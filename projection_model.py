"""Transparent Touchline projections.
Combines verified Draft history with optional commissioner-supplied external
context (FotMob/Premier League/Transfermarkt style notes) from
external_projection_inputs.json. No scraping is required for the website to run.
"""
from collections import defaultdict

def team_strength(state, gw):
    stats=defaultdict(lambda:{'games':0,'scored':0,'conceded':0})
    for wk, matches in state.get('club_results',{}).items():
        if int(wk)>=gw: continue
        for m in matches:
            if not m.get('finished'): continue
            h,a=m.get('home'),m.get('away')
            hs,ars=m.get('home_score'),m.get('away_score')
            if not h or not a or not isinstance(hs,int) or not isinstance(ars,int):
                continue
            stats[h]['games']+=1;stats[h]['scored']+=hs;stats[h]['conceded']+=ars
            stats[a]['games']+=1;stats[a]['scored']+=ars;stats[a]['conceded']+=hs
    teams={k:v for k,v in stats.items() if v['games']>=3}
    if len(teams)<10:return {},{}
    def rank(key, reverse):
        ranked=sorted(teams,key=lambda t: (teams[t][key]/teams[t]['games'])*(-1 if reverse else 1))
        return {t:i+1 for i,t in enumerate(ranked)}
    return rank('scored',True),rank('conceded',False)

def player_history(state,gw):
    hist=defaultdict(dict);pos={}
    for week,managers in state.get('players',{}).items():
        w=int(week)
        if w>=gw: continue
        for team in managers.values():
            for p in team.get('roster',[]):
                pid=p.get('id');pos[pid]=p.get('position_type')
                if isinstance(p.get('points'),int):hist[pid][w]=p['points']
    return hist,pos

def _ext_map(external_inputs):
    if not isinstance(external_inputs, dict):
        return {}
    data = external_inputs.get('players', external_inputs)
    if isinstance(data, list):
        out = {}
        for item in data:
            if isinstance(item, dict) and item.get('player_id'):
                out[int(item['player_id'])] = item
        return out
    if isinstance(data, dict):
        return {int(k):v for k,v in data.items() if str(k).isdigit() and isinstance(v, dict)}
    return {}

def _float(value):
    try:
        if value is None or isinstance(value, bool):return None
        out=float(value)
        return out if -10000<out<10000 else None
    except (ValueError, TypeError):
        return None


def previous_season_rates(history_past):
    """Most recent seasons first; rough points per 75 minutes from aggregate data.

    History-past from the standard Premier League Fantasy player summary contains
    season totals and minutes, not guaranteed per-appearance scores. No values
    are invented when either field is unavailable.
    """
    if not isinstance(history_past, list):return []
    valid=[]
    for season in history_past:
        if not isinstance(season,dict):continue
        pts=_float(season.get('total_points')); mins=_float(season.get('minutes'))
        if pts is None or mins is None or mins<180 or pts<0:continue
        rate=max(0,min(15.0, pts/(mins/75.0)))
        valid.append({'season':str(season.get('season_name') or 'Previous season'),
                      'per75':round(rate,2),'minutes':int(mins)})
    valid.sort(key=lambda x:x['season'],reverse=True)
    return valid[:4]


def blended_baseline(current, history_past):
    """Target weights: 75% current / 20% last year / 5% older years.
    Missing groups redistribute weight across available groups.
    """
    current_v=_float(current)
    prev=previous_season_rates(history_past)
    components=[]
    if current_v is not None:components.append(('current',.75,current_v))
    if prev:components.append(('last',.20,prev[0]['per75']))
    if len(prev)>1:
        older=prev[1:]; old_avg=sum(x['per75']*(0.5**i) for i,x in enumerate(older))/sum(0.5**i for i,_ in enumerate(older))
        components.append(('older',.05,old_avg))
    if not components:return None,{},prev
    weight=sum(c[1] for c in components)
    shares={c[0]:round(c[1]/weight*100) for c in components}
    result=sum(w*v for _,w,v in components)/weight
    return result,shares,prev


def projection_confidence(sample_count, historical_seasons, opponent_known,
                          availability_known, external_verified, baseline_known):
    """0-100 evidence-coverage index, not a calibrated chance of scoring points."""
    if not baseline_known:return 0
    score=24
    score+=min(30,int(sample_count)*6)
    score+=min(16,int(historical_seasons)*8)
    score+=12 if opponent_known else 0
    score+=8 if availability_known else 0
    score+=10 if external_verified else 0
    return max(0,min(95,score))


def prediction(state,gw,roster,external_inputs=None):
    hist,positions=player_history(state,gw)
    attack,defense=team_strength(state,gw)
    ext=_ext_map(external_inputs)
    past=state.get('historical_seasons',{})
    averages={pid:sum([v for _,v in sorted(weeks.items())][-5:])/len([v for _,v in sorted(weeks.items())][-5:]) for pid,weeks in hist.items() if weeks}
    position_rank={}
    for pos in [1,2,3,4]:
        ids=sorted([pid for pid in averages if positions.get(pid)==pos],key=lambda pid:-averages[pid])
        position_rank.update({pid:(idx+1,len(ids)) for idx,pid in enumerate(ids)})
    result=[]
    for player in roster:
        pid=player['id'];history=hist.get(pid,{})
        sample=[v for _,v in sorted(history.items())][-5:]
        fixture=player.get('opponent','')
        opp_id=None;team_id=player.get('club_id')
        fixtures=state.get('club_results',{}).get(str(gw),[])
        for f in fixtures:
            if f.get('home')==team_id:opp_id=f.get('away');break
            if f.get('away')==team_id:opp_id=f.get('home');break
        pos=player.get('position_type')
        opp_kind='defense' if pos in (3,4) else 'attack'
        opp_rank=(attack if opp_kind=='attack' else defense).get(opp_id)
        current_avg=sum(sample)/len(sample) if sample else None
        auto_fallback=False
        if current_avg is None:
            for key in ('auto_form','auto_points_per_game'):
                value=_float(player.get(key))
                if value is not None and 0<=value<=20:
                    current_avg=value;auto_fallback=True;break
        history_past=past.get(str(pid),[]) if isinstance(past,dict) else []
        baseline,weights,previous=blended_baseline(current_avg,history_past)
        ext_info=ext.get(pid,{})
        avail=player.get('chance_next')
        factor=1.0
        if isinstance(avail,(int,float)) and avail<100:factor=max(0,min(1,avail/100))
        elif player.get('injury_status') in ('i','s','u'):factor=0.5
        if isinstance(ext_info.get('availability_factor'),(int,float)):
            factor=max(0,min(1,float(ext_info['availability_factor'])))
        difficulty=1.0
        if opp_rank is not None:difficulty=max(0.85,min(1.15,0.85+(opp_rank-1)*.30/19))
        if isinstance(ext_info.get('fixture_adjustment'),(int,float)):
            difficulty=max(0.75,min(1.25,float(ext_info['fixture_adjustment'])))
        minutes_factor=1.0
        if isinstance(ext_info.get('predicted_minutes'),(int,float)):
            minutes_factor=max(0.35,min(1.05,float(ext_info['predicted_minutes'])/90))
        form_bump=0.0
        if isinstance(ext_info.get('form_adjustment'),(int,float)):
            form_bump=max(-2.5,min(2.5,float(ext_info['form_adjustment'])))
        # Optional FotMob observations, only when a real attributed source was entered.
        source_url=str(ext_info.get('source_url') or '')
        source_labels=['FPL Draft']
        external_verified=source_url.startswith('https://') and bool(ext_info.get('source_date'))
        if external_verified:
            for label in ext_info.get('sources',[]) if isinstance(ext_info.get('sources'),list) else []:
                if isinstance(label,str) and label and label not in source_labels:source_labels.append(label[:40])
            # FotMob form only modestly shifts a forecast; it never replaces points.
            rating=_float(ext_info.get('fotmob_avg_rating'))
            if rating is not None and 0<=rating<=10:
                form_bump+=max(-0.7,min(0.7,(rating-7.0)*0.35))
        expected=round(max(0,baseline*factor*difficulty*minutes_factor+form_bump),1) if baseline is not None else None
        if isinstance(ext_info.get('projected_points_override'),(int,float)):
            expected=round(max(0,float(ext_info['projected_points_override'])),1)
        confidence_pct=projection_confidence(len(sample),len(previous),opp_rank is not None,
              isinstance(avail,(int,float)) or bool(player.get('injury_news')),external_verified,baseline is not None)
        notes=['Recent verified FPL Draft points' if not auto_fallback else 'Current Draft-reported form']
        if previous:notes.append('prior-season Premier League Fantasy point totals weighted below current season')
        if opp_rank is not None:notes.append('verified opponent attack/defense trend')
        if external_verified:notes.append('dated external source inputs')
        result.append({'id':pid,'projected_points':expected,'sample_games':len(sample),
              'avg_recent':round(current_avg,1) if current_avg is not None else None,
              'position_rank':position_rank.get(pid,[None,None])[0],
              'position_rank_pool':position_rank.get(pid,[None,None])[1],
              'opponent_strength_rank':ext_info.get('opponent_rank_override') or opp_rank,
              'opponent_strength_kind':opp_kind,
              'opponent_rank_out_of':len(attack) if attack else None,
              'availability_factor':round(factor,2),'minutes_projection':ext_info.get('predicted_minutes'),
              'confidence_percent':confidence_pct,
              'confidence':f'{confidence_pct}%',
              'confidence_explanation':'Evidence-coverage index, not chance of scoring predicted points',
              'prior_seasons_used':len(previous),
              'prior_season_rates':previous[:3],
              'projection_weights_percent':weights,
              'fixture':fixture,'data_sources':source_labels,
              'auto_bootstrap_fallback':auto_fallback,
              'fotmob_avg_rating':ext_info.get('fotmob_avg_rating') if external_verified else None,
              'external_note':str(ext_info.get('note') or ext_info.get('headline') or '')[:320] if external_verified else '',
              'source_url':source_url[:600] if external_verified else '',
              'rationale':'; '.join(notes)+'.'})
    return result
