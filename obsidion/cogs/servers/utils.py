import json
from bs4 import BeautifulSoup


async def get_html(url, session):
    async with session.get(url) as resp:
        if resp.status == 200:
            html = await resp.text()
            return html
        return False


async def get_json(url, session):
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data
        return False


async def hiveMCAchievements(username, session):
    url = f"http://api.hivemc.com/v1/player/{username}"
    json_data = await get_json(url, session)
    str_json = json.dumps(json_data)
    json_new = json.loads(str_json)
    data = {"all_achievements": []}
    for ach in json_new["achievements"]:
        data["all_achievements"].append(ach)
    return data


async def hiveMCStatus(username, session):
    url = f"http://api.hivemc.com/v1/player/{username}"
    json_data = await get_json(url, session)
    str_json = json.dumps(json_data)
    json_new = json.loads(str_json)
    data = {"status": []}
    for _ in json_new["status"]:
        thing = json_new["status"]
        data["status"].append(thing)
    return data


async def hiveMCGameStats(username, game, session):
    url = f"http://api.hivemc.com/v1/player/{username}/{game}"
    json_data = await get_json(url, session)
    str_json = json.dumps(json_data)
    json_new = json.loads(str_json)
    data = {"stats": [json_new]}
    return data


async def hiveMCRank(username, session):
    url = f"http://api.hivemc.com/v1/player/{username}"
    json_data = await get_json(url, session)
    str_json = json.dumps(json_data)
    json_new = json.loads(str_json)
    rank = json_new["rankName"]
    data = {"rank": [rank]}
    return data


async def manacube(username, session, game):
    url = f"https://manacube.com/stats_data/fetch.php?username={username}"
    json_data = await get_json(url, session)
    str_json = json.dumps(json_data)
    json_new = json.loads(str_json)
    game_stat = json_new[game]
    data = {"game_stats": [game_stat]}
    return data


async def wyncraftClasses(username, session):
    url = f"https://api.wynncraft.com/v2/player/{username}/stats"
    json_data = await get_json(url, session)
    str_json = json.dumps(json_data)
    json_new = json.loads(str_json)
    data = {"classes": []}
    if json_new["code"] == 400:
        return False
    wynClasses = json_new["data"][0]["classes"]
    data["classes"].append(wynClasses)
    return data


async def blocksmc(username, session):
    url = f"https://blocksmc.com/player/{username}"
    html = await get_html(url, session)
    soup = BeautifulSoup(html, "lxml")
    if not soup.find("h1", {"class": "profile-header"}):
        return False
    rank = (
        soup.find("p", {"class": ["profile-rank"]}).get_text().replace("\n", "").strip()
    )
    timeplayed = soup.find("h1", {"dir": ["ltr"]}).get_text().replace("\n", "").strip()
    data = {"rank": rank, "timeplayed": timeplayed, "game_stats": []}

    for game in soup.find_all("div", {"class": "col-xl-4"}):
        stats = {}
        game_name = (
            game.find("div", {"class": "title"}).get_text().replace("\n", "").strip()
        )
        for stat in game.find_all("ul"):
            stat_name = (
                stat.find("div", {"class": "key"}).get_text().replace("\n", "").strip()
            )
            stat_val = int(stat.find("div", {"class": "val"}).get_text())
            stats[stat_name] = stat_val
        data["game_stats"].append({game_name: stats})
    return data


# a bit of a time consumer will do later not finished yet


async def universocraft(username, session):
    url = f"https://stats.universocraft.com/stats.php?player={username}"
    html = await get_html(url, session)
    soup = BeautifulSoup(html, "lxml")
    data = {"game_stats": []}
    for game in soup.find_all("div", {"class": "game"}):
        stats = {}
        game_name = game.find("h2").get_text().replace("\n", "").strip()
        for stat in soup.find_all("div", {"class": "game-stat"}):
            stat_val = stat.find("p", {"class": "game-stat-count"}).get_text()
            stat_name = stat.find("p", {"class": "game-stat-title"}).get_text()
            stats[stat_name] = stat_val
            data["game_stats"].append({stat_name: stat_val})
    return data


async def minesaga(username, session):
    url = f"https://www.minesaga.org/player/{username}"
    html = await get_html(url, session)
    soup = BeautifulSoup(html, "lxml")
    main_info = soup.find("div", {"class": ["dd-profile-details"]})
    try:
        joined = main_info.find("h4").get_text().strip()
    except:
        return False
    last_seen = main_info.findAll("span")[1].get_text().strip()
    play_time = main_info.findAll("span")[2].get_text().strip()
    data = {
        "joined": joined,
        "last_seen": last_seen,
        "play_time": play_time,
        "game_stats": [],
    }

    for game in soup.find_all("div", {"class": "dd-section col-md-4"}):
        stats = {}
        game_name = (
            game.find("div", {"class": "dd-box-title"})
            .get_text()
            .replace("\n", "")
            .strip()
        )
        for stat in game.find_all("dl"):
            stat_name = stat.find("dt").get_text().replace("\n", "").strip()
            stat_val = stat.find("dd").get_text()
            stats[stat_name] = stat_val
        data["game_stats"].append({game_name: stats})

    return data


async def gommehd(username, session):
    url = f"https://www.gommehd.net/player/index?playerName={username}"
    html = await get_html(url, session)
    soup = BeautifulSoup(html, "lxml")
    data = {"game_stats": []}
    for game in soup.find_all("div", {"class": "stat-table"}):
        stats = {}
        game_name = game.find("h5").get_text().replace("\n", "").strip()
        for stat in game.find_all("li"):
            stat_val = stat.find("span", {"class": "score"}).get_text()
            stat_name = stat.get_text().replace("\n", "").strip().replace(stat_val, "")
            stats[stat_name] = stat_val
        data["game_stats"].append({game_name: stats})
    return data


async def veltpvp(username, session):
    url = f"https://www.veltpvp.com/u/{username}"
    html = await get_html(url, session)
    soup = BeautifulSoup(html, "lxml")
    rank = soup.find("div", {"id": "profile"}).find("h2").get_text().strip()
    last_seen = (
        soup.find("div", {"class": "bottom"})
        .get_text()
        .split("\n")[2]
        .replace("\xa0", " ")
        .strip()
    )
    current_status = soup.find("div", {"class": "top"}).get_text().strip()
    info = soup.find_all("div", {"class": "element"})[1].get_text().split("\n")
    first_joined = info[3].strip()
    time_played = info[5].replace("\xa0", " ").strip()
    monthly_views = info[7].strip()
    data = {
        "rank": rank,
        "last_seen": last_seen,
        "current_status": current_status,
        "first_joined": first_joined,
        "time_played": time_played,
        "monthly_views": monthly_views,
        "game_stats": [],
    }

    # first stat is special
    first_game = soup.find("a", {"class": "server"})
    game_name = first_game.find("div", {"class": "server-header"}).get_text().strip()
    stats = {}
    for stat in first_game.find_all("div", {"class": "server-stat"}):
        stat_name = (
            stat.find("div", {"class": "server-stat-description"}).get_text().strip()
        )
        stat_val = stat.find("div", {"class": "server-stat-number"}).get_text().strip()
        stats[stat_name] = stat_val
    data["game_stats"].append({game_name: stats})

    for game in soup.find_all("div", {"class": "server"}):
        if not game.find("div", {"class": "server unknown"}):
            break
        game_name = game.find("div", {"class": "server-header"}).get_text().strip()
        stats = {}
        for stat in game.find_all("div", {"class": "server-stat"}):
            stat_name = (
                stat.find("div", {"class": "server-stat-description"})
                .get_text()
                .strip()
            )
            stat_val = (
                stat.find("div", {"class": "server-stat-number"}).get_text().strip()
            )
            stats[stat_name] = stat_val
        data["game_stats"].append({game_name: stats})
    return data

