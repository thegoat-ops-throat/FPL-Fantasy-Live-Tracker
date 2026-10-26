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

def prediction(state,gw,roster,external_inputs=None):
    hist,positions=player_history(state,gw)
    attack,defense=team_strength(state,gw)
    ext=_ext_map(external_inputs)
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
        opp_id=None
        team_id=player.get('club_id')
        fixtures=state.get('club_results',{}).get(str(gw),[])
        for f in fixtures:
            if f.get('home')==team_id:opp_id=f.get('away');break
            if f.get('away')==team_id:opp_id=f.get('home');break
        pos=player.get('position_type')
        opp_kind='defense' if pos in (3,4) else 'attack'  # defenders/GKs care about opponent attack; mids/fwds about opponent defense
        opp_rank=(attack if opp_kind=='attack' else defense).get(opp_id)
        baseline=sum(sample)/len(sample) if sample else None
        auto_fallback=False
        if baseline is None:
            for key in ('auto_form','auto_points_per_game'):
                try:
                    value=float(player.get(key))
                    if 0 <= value <= 20:
                        baseline=value
                        auto_fallback=True
                        break
                except (ValueError,TypeError):
                    continue
        ext_info = ext.get(pid, {})
        avail=player.get('chance_next')
        factor=1.0
        if isinstance(avail,(int,float)) and avail<100:
            factor=max(0,min(1,avail/100))
        elif player.get('injury_status') in ('i','s','u'):
            factor=0.5
        if isinstance(ext_info.get('availability_factor'), (int,float)):
            factor=max(0,min(1,float(ext_info['availability_factor'])))
        difficulty=1.0
        if opp_rank is not None:
            difficulty=max(0.85,min(1.15,0.85+(opp_rank-1)*.30/19))
        if isinstance(ext_info.get('fixture_adjustment'), (int,float)):
            difficulty=max(0.75,min(1.25,float(ext_info['fixture_adjustment'])))
        minutes_factor=1.0
        if isinstance(ext_info.get('predicted_minutes'), (int,float)):
            minutes_factor=max(0.35,min(1.05,float(ext_info['predicted_minutes'])/90))
        form_bump=0.0
        if isinstance(ext_info.get('form_adjustment'), (int,float)):
            form_bump=max(-2.5,min(2.5,float(ext_info['form_adjustment'])))
        expected=round(max(0,(baseline*factor*difficulty*minutes_factor)+form_bump),1) if baseline is not None else None
        if isinstance(ext_info.get('projected_points_override'), (int,float)):
            expected=round(max(0,float(ext_info['projected_points_override'])),1)
        source_labels=['FPL Draft']
        for label in ext_info.get('sources',[]) if isinstance(ext_info.get('sources'), list) else []:
            if isinstance(label, str) and label and ext_info.get('source_url') and label not in source_labels:
                source_labels.append(label[:40])
        rationale_parts=[
            'Uses recent verified Draft points' if not auto_fallback else 'Uses Draft-supplied player form / points-per-game',
            'availability and likely minutes',
            'opponent strength from completed fixtures' if opp_rank is not None else 'limited opponent-strength data',
        ]
        if ext_info:
            rationale_parts.append('commissioner-supplied external context')
        note = ext_info.get('note') or ext_info.get('headline') or ''
        result.append({'id':pid,'projected_points':expected,'sample_games':len(sample),
                       'avg_recent':round(baseline,1) if baseline is not None else None,
                       'position_rank':position_rank.get(pid,[None,None])[0],
                       'position_rank_pool':position_rank.get(pid,[None,None])[1],
                       'opponent_strength_rank':ext_info.get('opponent_rank_override') or opp_rank,
                       'opponent_strength_kind':opp_kind,
                       'opponent_rank_out_of':len(attack) if attack else None,
                       'availability_factor':round(factor,2),'minutes_projection': ext_info.get('predicted_minutes'),
                       'confidence':ext_info.get('confidence') or ('low' if len(sample)<3 else 'moderate'),
                       'fixture':fixture,'data_sources':source_labels,
                       'auto_bootstrap_fallback':auto_fallback,
                       'external_note': str(note)[:320] if note else '',
                       'source_url': str(ext_info.get('source_url') or '')[:600],
                       'rationale':'; '.join(rationale_parts)+'.'})
    return result
