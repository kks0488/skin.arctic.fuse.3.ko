"""On-demand local movie/TV search. No network service or persistent index."""
import json
import unicodedata
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hangul_input import CHO, JUNG, compose, initials


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text or '').casefold() if c.isalnum())


def find_matches(records, query):
    term = normalize(query)
    if not term:
        return []
    scored = []
    for record in records:
        titles = [normalize(record.get(k, '')) for k in ('title', 'originaltitle', 'label')]
        if all(c in CHO or c.isspace() for c in query):
            titles += [normalize(initials(record.get('title', '')))]
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
        result = call(method, {'properties': ['title', 'originaltitle', 'year', 'plot', 'art', 'file', 'dateadded']})
        for row in result.get(key, []):
            row['_kind'] = kind
            records.append(row)
    return records


def create_window():
    import xbmc
    import xbmcgui

    class SearchWindow(xbmcgui.WindowXML):
        def onInit(self):
            if getattr(self, 'ready', False):
                return
            self.ready = True
            self.raw = ''; self.language = 'ko'; self.matches = []
            self.records = load_library()
            self.refresh_keys()
            self.refresh_results()
            self.setFocusId(100)

        def refresh_keys(self):
            self.keys = list(CHO + JUNG) if self.language == 'ko' else list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            for index in range(42):
                control = self.getControl(100+index)
                control.setLabel(self.keys[index] if index < len(self.keys) else '')
                control.setEnabled(index < len(self.keys))
            self.getControl(20).setLabel('영문/숫자' if self.language == 'ko' else '한글')

        def refresh_results(self):
            query = compose(self.raw)
            self.getControl(10).setLabel(query if query else '제목이나 초성으로 검색')
            self.matches = find_matches(self.records, query) if query.strip() else sorted(self.records, key=lambda r:r.get('dateadded',''), reverse=True)[:20]
            self.getControl(11).setLabel('검색 결과 ' + str(len(self.matches)) + '개' if query.strip() else '최근 추가한 작품')
            self.getControl(12).setLabel('결과가 없어요. 제목 일부나 영문 제목으로 찾아보세요.' if not self.matches else '오른쪽에서 작품을 선택하세요')
            panel = self.getControl(500); panel.reset()
            items = []
            for row in self.matches:
                item = xbmcgui.ListItem(label=row.get('title') or row['label'], label2=('영화' if row['_kind']=='movie' else '시리즈') + ' / ' + str(row.get('year') or ''))
                item.setArt(row.get('art', {})); items.append(item)
            panel.addItems(items)
            self.setProperty('Search.Query', query)
            self.setProperty('Search.Count', str(len(items)))

        def onClick(self, control):
            if 100 <= control < 142:
                index = control-100
                if index < len(self.keys):self.raw += self.keys[index]; self.refresh_results()
            elif control == 20:
                self.language = 'en' if self.language == 'ko' else 'ko'; self.refresh_keys()
            elif control == 21:self.raw += ' '; self.refresh_results()
            elif control == 22:self.raw = self.raw[:-1]; self.refresh_results()
            elif control == 23:self.raw = ''; self.refresh_results()
            elif control == 24:self.close()
            elif control == 25:
                if self.matches:self.setFocusId(500)
            elif control == 500:
                position = self.getControl(500).getSelectedPosition()
                if not 0 <= position < len(self.matches):return
                row = self.matches[position]
                if row['_kind'] == 'tvshow':
                    self.close()
                    xbmc.executebuiltin('ActivateWindow(Videos,videodb://tvshows/titles/' + str(int(row['tvshowid'])) + '/,return)')
                    return
                item = xbmcgui.ListItem(label=row.get('title') or row['label'], path=row.get('file',''))
                item.setArt(row.get('art', {})); tag=item.getVideoInfoTag()
                tag.setTitle(row.get('title') or row['label']); tag.setDbId(int(row['movieid'])); tag.setMediaType('movie')
                tag.setYear(row.get('year') or 0); tag.setPlot(row.get('plot') or '')
                xbmcgui.Dialog().info(item)
                if xbmc.Player().isPlaying():self.close()

        def onAction(self, action):
            if action.getId() in (9,10,92):
                if self.getFocusId() == 500:self.setFocusId(25)
                else:self.close()

    return SearchWindow('HomeKoSearch.xml', os.path.join(os.path.dirname(__file__), 'search-ui'), 'Default', '1080i')


def main():
    import xbmc
    import xbmcgui
    home = xbmcgui.Window(10000)
    if home.getProperty('HomeKo.SearchRunning'):return
    home.setProperty('HomeKo.SearchRunning', 'true')
    try:
        xbmc.executebuiltin('ReplaceWindow(Home)', True)
        window = create_window()
        window.doModal()
        del window
    except Exception as error:
        xbmc.log('HomeKo search failed: ' + type(error).__name__, xbmc.LOGERROR)
        xbmcgui.Dialog().notification('검색', '검색 화면을 열지 못했어요')
    finally:
        home.clearProperty('HomeKo.SearchRunning')


if __name__ == '__main__':
    main()
