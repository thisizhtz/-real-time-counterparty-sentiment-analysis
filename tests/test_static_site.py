from html.parser import HTMLParser
from pathlib import Path


class StaticSiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.scripts = []
        self.stylesheets = []
        self.title_parts = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"])
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.stylesheets.append(attributes["href"])
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data.strip())


def test_static_webpage_has_required_sections_and_assets():
    parser = StaticSiteParser()
    parser.feed(Path("index.html").read_text(encoding="utf-8"))

    assert "实时交易对手方情绪分析" in "".join(parser.title_parts)
    assert {"overview", "demo", "workflow", "deployment"}.issubset(parser.ids)
    assert parser.stylesheets == ["web/styles.css"]
    assert parser.scripts == ["web/app.js"]

    for asset in [*parser.stylesheets, *parser.scripts]:
        assert Path(asset).exists()


def test_frontend_demo_contains_local_analysis_logic():
    index_html = Path("index.html").read_text(encoding="utf-8")
    app_js = Path("web/app.js").read_text(encoding="utf-8")

    assert "function analyzeEvent" in app_js
    assert "missed payment" in app_js
    assert "credit_default" in app_js
    assert "systemic financial risks" in app_js
    assert "dimensionScores" in app_js
    assert "color-scheme: light" in Path("web/styles.css").read_text(encoding="utf-8")
    assert "所有计算都在本地浏览器完成" in index_html
