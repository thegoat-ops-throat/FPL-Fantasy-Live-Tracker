"""Touchline 2.0 — FPL Draft public tracker (standard library only).

Run: python server.py. On Render: Start Command = python server.py.
No FPL account password or API key is needed for public Draft endpoints.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'scores.json'
CONFIG = ROOT / 'config.json'
BASE = 'https://draft.premierleague.com/api'
MANAGERS = [
    {'name': 'Saul', 'team': 'Saulitos', 'id': 393832},
    {'name': 'Albert', 'team': 'gospurs', 'id': 365375},
    {'name': 'Eddy', 'team': "It's called soccer", 'id': 372793},
    {'name': 'Daviel', 'team': 'LIVERPOOL', 'id': 372999},
    {'name': 'Jaden', 'team': 'gooner', 'id': 365166},
    {'name': 'Andrew', 'team': 'Bleed Blue', 'id': 372608},
]
# Only used if the old GW7 public API is inaccessible; clearly identified as a snapshot.
GW7_SCREENSHOT = {'Saul': 61, 'Albert': 54, 'Eddy': 43, 'Daviel': 34, 'Jaden': 46, 'Andrew': 37}
REFRESH_SECONDS = 300
HISTORY_REFRESH_SECONDS = 6 * 3600
FETCH_TIMEOUT = 16
state_lock = threading.RLock()


def default_state():
    return {
        'updated_at': None, 'status': 'Connecting to Fantasy Premier League Draft…',
        'source': 'Fantasy Premier League Draft', 'gameweek': 8,
        'managers': MANAGERS, 'scores': {}, 'players': {},
        'score_sources': {}, 'week_status': {}, 'rounds': {}, 'history': [],
        'provisional': True, 'waivers': {'source': 'unavailable', 'order': []},
        'history_updated_at': None, 'history_errors': [],
    }


def load():
    if STATE.exists():
        try:
            result = json.loads(STATE.read_text(encoding='utf-8'))
            if isinstance(result, dict):
                merged = default_state()
                merged.update(result)
                return merged
        except (OSError, ValueError):
            pass
    return default_state()


def save(data):
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    tmp.replace(STATE)


def fetch(path):
    req = urllib.request.Request(
        BASE + path, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; Touchline/2.0; personal-league)',
            'Accept': 'application/json',
        }
    )
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
        return json.load(response)


def rows(value):
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        return [x for x in value.values() if isinstance(x, dict)]
    return []


def safe_int(value, fallback=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def event_info(bootstrap):
    raw = bootstrap.get('events', {})
    data = rows(raw.get('data', [])) if isinstance(raw, dict) else rows(raw)
    current = safe_int(raw.get('current')) if isinstance(raw, dict) else 0
    if not current:
        now = datetime.now(timezone.utc)
        passed = []
        for e in data:
            deadline = e.get('deadline_time')
            if not deadline:
                continue
            try:
                if datetime.fromisoformat(deadline.replace('Z', '+00:00')) <= now:
                    passed.append(safe_int(e.get('id')))
            except ValueError:
                continue
        current = max(passed or [1])
    current = max(1, min(current, 38))
    return current, {safe_int(e.get('id')): e for e in data}


def player_index(bootstrap):
    result = {}
    for p in rows(bootstrap.get('elements', [])):
        pid = safe_int(p.get('id'))
        if not pid:
            continue
        name = p.get('web_name') or p.get('name') or ' '.join(
            str(p.get(k, '')).strip() for k in ('first_name', 'second_name')
        ).strip() or f'Player {pid}'
        result[pid] = {
            'name': name,
            'club_id': safe_int(p.get('team')),
            'position_type': safe_int(p.get('element_type')),
            'shirt_number': safe_int(p.get('shirt_number')),
        }
    return result


def club_index(bootstrap):
    return {safe_int(t.get('id')): {
        'short': t.get('short_name') or t.get('name') or '—',
        'name': t.get('name') or '',
    } for t in rows(bootstrap.get('teams', []))}


def fixtures_index(live, gw):
    fixtures = rows(live.get('fixtures', [])) if isinstance(live, dict) else []
    if not any('team_h' in f and 'team_a' in f for f in fixtures):
        try:
            response = fetch(f'/fixtures/?event={gw}')
            fixtures = rows(response.get('fixtures', [])) if isinstance(response, dict) else rows(response)
        except (urllib.error.URLError, ValueError, TypeError):
            pass
    result = {}
    for f in fixtures:
        home, away = safe_int(f.get('team_h')), safe_int(f.get('team_a'))
        if not home or not away:
            continue
        info = {
            'home': home, 'away': away,
            'started': bool(f.get('started')),
            'finished': bool(f.get('finished') or f.get('finished_provisional')),
            'kickoff': f.get('kickoff_time'),
        }
        result.setdefault(home, []).append(info)
        result.setdefault(away, []).append(info)
    return result


def fixture_display(club_id, by_club, clubs):
    items = by_club.get(club_id, [])
    if not items:
        return {'opponent': 'Fixture TBD', 'match_status': 'unknown'}
    texts = []
    for f in items:
        opponent = f['away'] if f['home'] == club_id else f['home']
        venue = 'H' if f['home'] == club_id else 'A'
        texts.append(f"{clubs.get(opponent, {}).get('short', '—')} ({venue})")
    if any(f['started'] and not f['finished'] for f in items):
        status = 'live'
    elif all(f['finished'] for f in items):
        status = 'finished'
    elif not any(f['started'] for f in items):
        status = 'upcoming'
    else:
        status = 'upcoming'  # One match finished, another still upcoming (double GW)
    return {'opponent': ' · '.join(texts), 'match_status': status}


def extract_confirmed_subs(payload):
    raw = payload.get('subs', [])
    if not isinstance(raw, list):
        return []
    result = []
    for sub in raw:
        if not isinstance(sub, dict):
            continue
        incoming = safe_int(sub.get('element_in') or sub.get('in'))
        outgoing = safe_int(sub.get('element_out') or sub.get('out'))
        if incoming and outgoing:
            result.append({'in_id': incoming, 'out_id': outgoing, 'type': 'confirmed'})
    return result


def projected_subs(roster):
    """Formation-aware possibilities only when both involved fixtures have ended.

    Follow bench order. 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD.
    Do not treat this estimate as the Draft engine's final decision.
    """
    starters = [p for p in roster if p['position'] <= 11]
    bench = sorted((p for p in roster if p['position'] > 11), key=lambda x: x['position'])
    counts = {k: sum(p['position_type'] == k for p in starters) for k in range(1, 5)}
    taken = set()
    output = []
    for original in starters:
        if original['minutes'] != 0 or original['match_status'] != 'finished':
            continue
        typ = original['position_type']
        if typ not in (1, 2, 3, 4):
            continue
        for candidate in bench:
            new_type = candidate['position_type']
            if candidate['id'] in taken or candidate['minutes'] <= 0 or candidate['match_status'] != 'finished':
                continue
            if typ == 1 and new_type != 1:
                continue
            if typ != 1 and new_type == 1:
                continue
            test = dict(counts)
            test[typ] -= 1
            test[new_type] += 1
            if not (test[1] == 1 and 3 <= test[2] <= 5 and 2 <= test[3] <= 5 and 1 <= test[4] <= 3):
                continue
            taken.add(candidate['id'])
            counts = test
            output.append({'in_id': candidate['id'], 'out_id': original['id'], 'type': 'projected'})
            break
    return output


def week_data(gw, bootstrap, events, players_db, clubs_db):
    live = fetch(f'/event/{gw}/live')
    elements = live.get('elements', {}) if isinstance(live, dict) else {}
    if not isinstance(elements, (list, dict)):
        raise ValueError(f'GW{gw}: no Draft live player points')
    if isinstance(elements, list):
        elements = {str(item.get('id')): item for item in elements if isinstance(item, dict)}
    by_club = fixtures_index(live, gw)
    scores = {}
    player_lists = {}
    sources = {}
    for m in MANAGERS:
        name = m['name']
        payload = fetch(f"/entry/{m['id']}/event/{gw}")
        picks = payload.get('picks') if isinstance(payload, dict) else None
        if not isinstance(picks, list) or len(picks) != 15:
            raise ValueError(f'GW{gw}: {name} lineup not yet available')
        roster = []
        for pick in sorted(picks, key=lambda p: safe_int(p.get('position'))):
            pid = safe_int(pick.get('element'))
            pos = safe_int(pick.get('position'))
            details = players_db.get(pid, {})
            live_stats = elements.get(str(pid), {}).get('stats', {})
            pts = live_stats.get('total_points')
            if not isinstance(pts, int):
                raise ValueError(f'GW{gw}: no Draft points for player {pid}')
            fixture = fixture_display(details.get('club_id'), by_club, clubs_db)
            roster.append({
                'id': pid, 'position': pos,
                'name': details.get('name', f'Player {pid}'),
                'club': clubs_db.get(details.get('club_id'), {}).get('short', '—'),
                'position_type': details.get('position_type', 0),
                'shirt_number': details.get('shirt_number', 0),
                'points': pts,
                'minutes': safe_int(live_stats.get('minutes')),
                'multiplier': safe_int(pick.get('multiplier', 1)),
                **fixture,
            })
        substitutions = extract_confirmed_subs(payload)
        xi_total = sum(p['points'] for p in roster if p['position'] <= 11)
        if substitutions:
            indexed = {p['id']: p for p in roster}
            total = xi_total + sum(
                indexed[s['in_id']]['points'] - indexed[s['out_id']]['points']
                for s in substitutions if s['in_id'] in indexed and s['out_id'] in indexed
            )
            source = 'confirmed_substitutions'
        else:
            total = xi_total
            source = 'starting_xi'
        history = payload.get('entry_history') or {}
        official_points = history.get('points') if isinstance(history, dict) else None
        if isinstance(official_points, int) and not isinstance(official_points, bool):
            total = official_points
            source = 'official_entry_history'
        if not substitutions and source != 'official_entry_history':
            substitutions = projected_subs(roster)
        scores[name] = total
        sources[name] = source
        player_lists[name] = {'roster': roster, 'subs': substitutions}
    meta = events.get(gw, {})
    return scores, player_lists, sources, {
        'finished': bool(meta.get('finished')),
        'deadline': meta.get('deadline_time'),
        'fixtures_known': bool(by_club),
    }


def update_summaries(state):
    # GW1-2, GW3-4, ... independent of the GW7-8 starting point for the original scoreboard.
    max_week = max(1, safe_int(state.get('gameweek'), 1))
    rounds = []
    for first in range(1, max_week + 1, 2):
        second = first + 1
        week1 = state['scores'].get(str(first), {})
        week2 = state['scores'].get(str(second), {})
        completed = bool(state['week_status'].get(str(second), {}).get('finished'))
        verified = all(
            state['score_sources'].get(str(w), {}).get(m['name']) in
            ('official_entry_history', 'confirmed_substitutions')
            for w in (first, second) for m in MANAGERS
        )
        standings = []
        for manager in MANAGERS:
            name = manager['name']
            a = week1.get(name)
            b = week2.get(name)
            available = int(isinstance(a, int)) + int(isinstance(b, int))
            standings.append({
                'name': name, 'team': manager['team'], 'gw1': a, 'gw2': b,
                'total': (a or 0) + (b or 0) if available else None,
                'complete': available == 2,
            })
        standings.sort(key=lambda x: (not x['complete'], -(x['total'] or 0), x['name']))
        rounds.append({
            'label': f'GW{first}–GW{second}', 'first': first, 'second': second,
            'finished': completed, 'verified': verified,
            'has_both': all(x['complete'] for x in standings),
            'standings': standings,
        })
    state['rounds'] = {r['label']: r for r in rounds}
    state['history'] = [r['label'] for r in rounds if r['finished'] and r['has_both']]
    overall = []
    for manager in MANAGERS:
        name = manager['name']
        vals = [state['scores'].get(str(g), {}).get(name) for g in range(1, max_week + 1)]
        count = sum(isinstance(value, int) for value in vals)
        overall.append({
            'name': name, 'team': manager['team'], 'total': sum(v for v in vals if isinstance(v, int)),
            'weeks_found': count, 'weeks_expected': max_week, 'complete': count == max_week,
        })
    overall.sort(key=lambda x: (-x['total'], x['name']))
    state['overall'] = overall


def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def waiver_data(config):
    # Do not invent an official waiver order from league rank: priority shifts on successful claims.
    manual = config.get('waiver_order', [])
    names = {m['name'] for m in MANAGERS}
    if (isinstance(manual, list) and len(manual) == len(names)
            and set(manual) == names):
        return {'source': 'manual', 'order': manual}
    league_id = safe_int(config.get('league_id'))
    if league_id:
        try:
            data = fetch(f'/league/{league_id}/details')
            candidate = data.get('waiver_order') or data.get('waiver_priority')
            if isinstance(candidate, list):
                by_entry = {m['id']: m['name'] for m in MANAGERS}
                mapped = []
                for value in candidate:
                    entry = safe_int(value.get('entry_id', value.get('entry')) if isinstance(value, dict) else value)
                    if entry in by_entry:
                        mapped.append(by_entry[entry])
                if len(mapped) == len(names) and set(mapped) == names:
                    return {'source': 'league_api', 'order': mapped}
        except (urllib.error.URLError, ValueError, TypeError):
            pass
    return {'source': 'unavailable', 'order': []}


def refresh_one(gw, bootstrap, events, player_db, clubs):
    scores, players, sources, info = week_data(gw, bootstrap, events, player_db, clubs)
    with state_lock:
        state = load()
        state['scores'][str(gw)] = scores
        state['players'][str(gw)] = players
        state['score_sources'][str(gw)] = sources
        state['week_status'][str(gw)] = info
        update_summaries(state)
        save(state)


def worker():
    last_history = 0
    while True:
        try:
            bootstrap = fetch('/bootstrap-static')
            current, events = event_info(bootstrap)
            player_db, clubs = player_index(bootstrap), club_index(bootstrap)
            with state_lock:
                state = load()
                state['gameweek'] = current
                state['managers'] = MANAGERS
                state['waivers'] = waiver_data(load_config())
                update_summaries(state)
                save(state)
            # Current first: all six managers appear quickly after a Render cold start.
            refresh_one(current, bootstrap, events, player_db, clubs)
            with state_lock:
                state = load()
                state['updated_at'] = datetime.now(timezone.utc).isoformat()
                state['status'] = 'Live Draft data loaded (scores may be provisional)'
                state['provisional'] = not bool(state['week_status'].get(str(current), {}).get('finished'))
                save(state)
            if time.time() - last_history >= HISTORY_REFRESH_SECONDS:
                errors = []
                # Rebuild archives from the public API on cold start, no permanent disk required.
                # Recheck only missing/unfinished weeks on later passes.
                for gw in range(1, current):
                    with state_lock:
                        state = load()
                        already_final = bool(state['week_status'].get(str(gw), {}).get('finished'))
                        populated = bool(state['scores'].get(str(gw)))
                    if already_final and populated:
                        continue
                    try:
                        refresh_one(gw, bootstrap, events, player_db, clubs)
                    except Exception as exc:
                        errors.append(f'GW{gw}: {str(exc)[:90]}')
                with state_lock:
                    state = load()
                    state['history_updated_at'] = datetime.now(timezone.utc).isoformat()
                    state['history_errors'] = errors
                    update_summaries(state)
                    save(state)
                last_history = time.time()
        except Exception as exc:
            with state_lock:
                state = load()
                state['status'] = f'Update failed; showing last available data: {str(exc)[:140]}'
                save(state)
        time.sleep(REFRESH_SECONDS)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/status':
            with state_lock:
                payload = json.dumps(load(), ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)
        elif path == '/':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()


if __name__ == '__main__':
    threading.Thread(target=worker, daemon=True).start()
    port = int(os.environ.get('PORT', '8000'))
    print(f'Touchline 2.0 listening on 0.0.0.0:{port}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
