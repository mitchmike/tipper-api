from datascrape.scrapers.fantasyScrape import FantasyScraper
from datascrape.scrapers.gameScrape import GameScraper
from datascrape.scrapers.match_statsScrape import MatchStatsScraper
from datascrape.scrapers.playerScrape import PlayerScraper


def test_model_mgmt_home(app, client, admin_user):
    with client:
        response = client.get("/admin/scrape", follow_redirects=True)
        assert response.status_code == 200
        assert '<title>Tipper - Datascrape Controls</title>' in response.text


def test_trigger_player_scrape(app, client, admin_user, monkeypatch):
    with client:
        monkeypatch.setattr(PlayerScraper, "scrape_entities", lambda *args: 10)
        response = client.get("/admin/scrape/players", follow_redirects=True)
        assert response.status_code == 200
        assert b'Scrape successful' in response.data
        assert '''<td>Player</td>
                    <td>Success</td>''' in response.text
        assert b'<td>10</td>' in response.data  # mocked count


def test_trigger_game_scrape(app, client, admin_user, monkeypatch):
    with client:
        monkeypatch.setattr(GameScraper, "scrape_entities", lambda *args: 10)
        response = client.get("/admin/scrape/games?from_year=1963&to_year=2035", follow_redirects=True)
        assert response.status_code == 200
        assert b'Scrape successful' in response.data
        assert '''<td>Game</td>
                    <td>Success</td>''' in response.text
        assert b'<td>10</td>' in response.data  # mocked count


def test_trigger_fantasy_scrape(app, client, admin_user, monkeypatch):
    with client:
        monkeypatch.setattr(FantasyScraper, "scrape_entities", lambda *args: 10)
        response = client.get("/admin/scrape/fantasies?from_year=1963&to_year=2035&from_round=1&to_round=25", follow_redirects=True)
        assert response.status_code == 200
        assert b'Scrape successful' in response.data
        assert '''<td>Fantasy</td>
                    <td>Success</td>''' in response.text
        assert b'<td>10</td>' in response.data  # mocked count


def test_trigger_match_stats_scrape(app, client, admin_user, monkeypatch):
    with client:
        monkeypatch.setattr(MatchStatsScraper, "scrape_entities", lambda *args: 10)
        response = client.get("/admin/scrape/match_stats?from_year=1963&to_year=2035&from_round=1&to_round=25", follow_redirects=True)
        assert response.status_code == 200
        assert b'Scrape successful' in response.data
        assert '''<td>MatchStats</td>
                    <td>Success</td>''' in response.text
        assert b'<td>10</td>' in response.data  # mocked count
