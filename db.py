from pony.orm import *
from datetime import datetime
from ussoccer_scrape import * 
import os

db = Database()

class Game(db.Entity):
    id = PrimaryKey(int, auto=True)
    attendence = Required(int)
    date = Required(datetime)
    competition = Required(str)
    link = Required(str)
    opponent = Required(str)
    usa_one = Required(int)
    usa_two = Required(int)
    usa_fin = Required(int)
    opp_one = Required(int)
    opp_two = Required(int)
    opp_fin = Required(int)
    goals = Set("Goal")
    players = Set("Player")
    venue = Required(str)
    weather = Required(str)

class Goal(db.Entity):
	id = PrimaryKey(int, auto=True)
	scored_by = Required(str)
	minute = Required(int)
	assist = Optional(str)
	stoppage = Required(int)
	team = Required(str)
	game = Required(Game)

class Player(db.Entity):
	id = PrimaryKey(int, auto=True)
	name = Required(str)
	start = Required(int)
	end = Required(int)
	game = Required(Game)

def instantiate():
	db.bind('sqlite', 'data/scraped.sqlite', create_db=True)
	db.generate_mapping(create_tables=True)

def refresh():
    os.remove('data/scraped.sqlite')
    instantiate()
    matches = get_matches()
    print("got matches")

    for match in matches:
        with db_session:
            g = Game(attendence = match['attendence'],
                date = match['date'],
                competition = match['competition'],
                link = match['link'],
                opponent = match['opponent'],
                usa_one = match['usa_one'],
                usa_two = match['usa_two'],
                usa_fin = match['usa_fin'],
                opp_one = match['opp_one'],
                opp_two = match['opp_two'],
                opp_fin = match['opp_fin'],
                goals = [],
                players = [],
                venue = match['venue'],
                weather = match['weather'],
            )
            for goal in match['goals']:
                g.goals.add(
                    Goal(scored_by=goal['scored_by'],
                        minute=goal['minute'],
                        assist=goal['assist'],
                        stoppage=goal['stoppage'],
                        team=goal['team'],
                        game = g
                        ))

            for player in match['players']:
                g.players.add(
                        Player(name = player['name'],
                            start = player['start'],
                            end = player['end'],
                            game = g
                        )
                    )
