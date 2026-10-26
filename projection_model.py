"""Deterministic, transparent projections from cached, verified Draft player points.
Not a betting model or official FPL prediction. Never invent opponent ranks.
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
            if not h or not a or not isinstance(hs,int) or not isinstance(ars,int):continue
            stats[h]['games']+=1;stats[h]['scored']+=hs;stats[h]['conceded']+=ars
            stats[a]['games']+=1;stats[a]['scored']+=ars;stats[a]['conceded']+=hs
    # Require 3 completed results to assign a rank; missing teams yield unknown.
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

def prediction(state,gw,roster):
    hist,positions=player_history(state,gw)
    attack,defense=team_strength(state,gw)
    # Rank observed players only: sample of tracked Touchline squads, not all EPL players.
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
        # Match opponents come from the fixture_results for selected gameweek.
        team_id=player.get('club_id')
        fixtures=state.get('club_results',{}).get(str(gw),[])
        for f in fixtures:
            if f.get('home')==team_id:opp_id=f.get('away');break
            if f.get('away')==team_id:opp_id=f.get('home');break
        pos=player.get('position_type')
        opp_kind='attack' if pos in (1,2) else 'defense'
        opp_rank=(attack if opp_kind=='attack' else defense).get(opp_id)
        baseline=sum(sample)/len(sample) if sample else None
        avail=player.get('chance_next')
        factor=1.0
        if isinstance(avail,(int,float)) and avail<100:factor=max(0,min(1,avail/100))
        elif player.get('injury_status') in ('i','s','u'):factor=0.5
        # Mild schedule adjustment, if robust opponent team rank available.
        difficulty=1.0
        if opp_rank is not None:
            # Rank 1 best defense/attack. Attackers face tough defense -> fewer pts.
            difficulty=max(0.85,min(1.15,0.85+(opp_rank-1)*.30/19))
        expected=round(max(0,baseline*factor*difficulty),1) if baseline is not None else None
        result.append({'id':pid,'projected_points':expected,'sample_games':len(sample),
                       'avg_recent':round(baseline,1) if baseline is not None else None,
                       'position_rank':position_rank.get(pid,[None,None])[0],
                       'position_rank_pool':position_rank.get(pid,[None,None])[1],
                       'opponent_strength_rank':opp_rank,'opponent_strength_kind':opp_kind,
                       'opponent_rank_out_of':len(attack) if attack else None,
                       'availability_factor':round(factor,2),
                       'confidence':'low' if len(sample)<3 else 'moderate',
                       'fixture':fixture,
                       'rationale':'Averages recent available Draft points, adjusts mildly for available opponent scoring/conceding data and availability; no verified press-conference report is assumed.'})
    return result
