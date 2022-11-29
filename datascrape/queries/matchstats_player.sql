select * from (select game_id, player_name, team, CAST(disposals as float) / CASt(time_on_ground_pcnt as float) as "efficiency", disposals, time_on_ground_pcnt from matchstats_player where time_on_ground_pcnt > 30) e
order by efficiency desc;

-- game ids from game table
select distinct id, year, round_number from games_footywire
where year=2021 and (home_team = 'richmond-tigers' or away_team = 'richmond-tigers');

-- sum disposals by game,team
select game_id, team, sum(disposals) as disposals from matchstats_player
where game_id in (10355,10450,10443)  group by game_id, team;