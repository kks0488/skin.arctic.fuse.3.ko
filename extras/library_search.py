"""On-demand local movie/TV search. No network service or persistent index."""
import json
import unicodedata


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text or '').casefold() if c.isalnum())


def find_matches(records, query):
    term = normalize(query)
    if not term:
        return []
    scored = []
    for record in records:
        titles = [normalize(record.get(k, '')) for k in ('title', 'originaltitle', 'label')]
        matches = [s for s in titles if term in s]
        if matches:
            rank = min(0 if s == term else 1 if s.startswith(term) else 2 for s in matches)
            scored.append((rank, normalize(record.get('title', '')), record))
    return [r for _, _, r in sorted(scored, key=lambda value: value[:2])]


def call(method, params=None):
    import xbmc
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    if 'error' in reply:
        raise RuntimeError(reply['error'].get('message', 'Kodi library error'))
    return reply['result']


def load_library():
    records = []
    for kind, method, key in [('movie', 'VideoLibrary.GetMovies', 'movies'), ('tvshow', 'VideoLibrary.GetTVShows', 'tvshows')]:
        result = call(method, {'properties': ['title', 'originaltitle', 'year', 'plot', 'art', 'file']})
        for row in result.get(key, []):
            row['_kind'] = kind
            records.append(row)
    return records


def main():
    import xbmc
    import xbmcgui
    home = xbmcgui.Window(10000)
    if home.getProperty('HomeKo.SearchRunning'):
        return
    home.setProperty('HomeKo.SearchRunning', 'true')
    try:
        xbmc.executebuiltin('ReplaceWindow(Home)', True)
        dialog = xbmcgui.Dialog()
        query = ''
        records = None
        while True:
            keyboard = xbmc.Keyboard(query, '우리 영화·시리즈 검색')
            keyboard.doModal()
            if not keyboard.isConfirmed():
                return
            query = keyboard.getText().strip()
            if not normalize(query):
                return
            if records is None:
                records = load_library()
            matches = find_matches(records, query)
            if not matches:
                dialog.ok('검색 결과 없음', '보유한 영화·시리즈에서 찾지 못했어요.\n제목 일부나 영문 제목으로 다시 검색해 주세요.')
                continue
            while True:
                items = []
                for row in matches:
                    kind = '영화' if row['_kind'] == 'movie' else '시리즈'
                    year = str(row.get('year') or '')
                    item = xbmcgui.ListItem(label=row.get('title') or row['label'], label2=kind + (' · ' + year if year else ''))
                    item.setArt(row.get('art', {}))
                    items.append(item)
                selected = dialog.select('“' + query + '” · ' + str(len(matches)) + '개', items, useDetails=True)
                if selected < 0:
                    break  # Back returns to the prefilled search input.
                row = matches[selected]
                if row['_kind'] == 'tvshow':
                    xbmc.executebuiltin('ActivateWindow(Videos,videodb://tvshows/titles/' + str(int(row['tvshowid'])) + '/,return)')
                    return
                item = xbmcgui.ListItem(label=row.get('title') or row['label'], path=row.get('file', ''))
                item.setArt(row.get('art', {}))
                tag = item.getVideoInfoTag()
                tag.setTitle(row.get('title') or row['label'])
                tag.setDbId(int(row['movieid']))
                tag.setMediaType('movie')
                tag.setYear(row.get('year') or 0)
                tag.setPlot(row.get('plot') or '')
                dialog.info(item)
                if xbmc.Player().isPlaying():
                    return
    except Exception as error:
        xbmc.log('HomeKo local search failed: ' + type(error).__name__, xbmc.LOGERROR)
        xbmcgui.Dialog().ok('검색 오류', '라이브러리를 읽지 못했어요. 잠시 후 다시 시도해 주세요.')
    finally:
        home.clearProperty('HomeKo.SearchRunning')


if __name__ == '__main__':
    main()
