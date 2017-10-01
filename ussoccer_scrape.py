import csv
import urllib
from bs4 import BeautifulSoup
import re
from pprint import pprint
from dateutil import parser

url = 'https://www.ussoccer.com/womens-national-team/results-statistics'
root = 'https://www.ussoccer.com'

def get_matches():
	matches = []
	soup = BeautifulSoup(urllib.request.urlopen(url).read(), 'html.parser')
	rows = soup.select('table.card-table tr')
	for row in rows:
		cells = row.findAll('td')
		if len(cells) > 0:
			m = cells[1].text.strip().replace('\n', ' ').replace('WNT vs ', '')
			print(m)
			l = cells[1].find('a')['href']
			d = cells[0].text.strip()
			dt = parser.parse(d)
			year = to_int(d.split(",")[1])
			if year < 2014: 
				break
			v = cells[3].text.strip().split('\n')[0].strip()
			if has_int(cells[4].text.strip()):
				a = to_int(cells[4].text.strip())
			else:
				a = -1
			match = get_match_data(l)
			if match is not None:
				match['date'] = dt 
				match['opponent'] = m
				match['venue'] = v
				match['attendence'] = a
				match['link'] = l
				matches.append(match)
	return matches


def get_match_data(link):
	match = {}
	soup = BeautifulSoup(urllib.request.urlopen(root+link).read(), 'html.parser')
	paras = soup.find(id='tab-1')
	if paras is not None and len(paras) > 1:
		match['competition'] = re.sub('<[^<]+?>|\xa0|\n', '', str(paras).split('Competition:')[1].split('<br/>')[0]).strip()
		match['weather'] = re.sub('<[^<]+?>|\xa0|\n', '', str(paras).split('Weather:')[1].split('<br/>')[0]).strip().split('Scoring Summary:')[0]
		paras_index = 1
		if len(paras) > 2:
			paras_index = 2
		scoring = str(paras).split('Scoring Summary:')[1].split("Lineups")[0].strip()
		br_index = 0
		scorelines_to_mod = re.split('<br*>|\n', scoring)
		scorelines = []
		for line in scorelines_to_mod:
			scorelines.append(re.sub('<[^<]+?>|\xa0|\n|\t', ' ', line).strip())

		while scorelines[br_index]=="" or scorelines[br_index].split()[0] != "USA":
			br_index += 1
		us_score = scorelines[br_index].split()
		match['usa_one'] = to_int(us_score[1])
		match['usa_two'] = to_int(us_score[2])
		match['usa_fin'] = to_int(us_score[-1])

		br_index += 1
		while scorelines[br_index].split()[0].strip() == "":
			br_index += 1
		opp_score = scorelines[br_index].split()
		match['opp_one'] = to_int(opp_score[1])
		match['opp_two'] = to_int(opp_score[2])
		match['opp_fin'] = to_int(opp_score[-1])

		score_list = scorelines[(br_index+1):]
		match['goals'] = extract_goals(score_list)
	
		lineup = str(paras).split("Lineups")[1].strip()
		match['players'] = extract_lineup(lineup)

		return match
	else:
		return None


def extract_goals(score_list):
	goals = []
	for score in score_list:
		if len(score.split(":")) > 1:
			break
		if score.strip()!="":
			goal = {}
			dashsplit = re.split("–|-",score)
			noteam = re.sub(dashsplit[0], '', score).strip()
			goal['team'] = dashsplit[0].strip()

			if len(dashsplit[1].split('+')) > 1:
				goal['minute'] = to_int(noteam.split('+')[0])
				goal['stoppage'] = to_int(noteam.split('+')[1])
			else:
				goal['minute'] = to_int(noteam)
				goal['stoppage'] =  -1

			combo = noteam.split(str(goal['minute']))[0].strip()
			if len(combo.split('(')) > 1:
				goal['scored_by'] = re.sub('–', '', combo.split('(')[0]).strip()
				goal['assist'] = combo.split('(')[1].split(')')[0].strip()
			else:
				goal['scored_by'] = re.sub("–|-", '', combo).strip()
				goal['assist'] = ""

			goals.append(goal)
	return(goals)

def extract_lineup(lineup):
	lineup =  re.split("[Hh]ead [Cc]oach|[Nn]ot [Aa]vailable", lineup)[0]
	lineup = re.sub('USA','', lineup)
	lineup = re.sub('<[^<]+?>|\xa0|\n|\t|:', ' ', lineup)
	
	did_not_play = []
	if len(re.split('Subs not used|Substitutions Not Used', lineup)) > 1:
		not_subbed = re.split('Subs not used|Substitutions Not Used', lineup)[1]
		not_subbed_names = re.split("–|-", not_subbed)
		for name in not_subbed_names:
			name = re.sub(',|;','', name)
			if re.match('.*[0-9].*', name):
				next_num = to_int(name)
				name = re.sub(str(next_num), '', name)
			if name.strip() != "":
				did_not_play.append(name.strip())

	players = []
	for player in did_not_play:
		players.append({'name': player, 'start': -1, 'end':-1})
			

	who_played = re.sub('\([Cc]apt[^)]+\)', '', re.split('Subs not used|Substitutions Not Used', lineup)[0])

	subs = []
	#check if there were any subs
	if(re.match('.*\([^)]+\).*', who_played)):
		#recursively search for subs, then strip them out of the string and clean the starters
		depth = 0
		paren_indicies = []
		subbed_indicies = []
		char = 0
		dash_index = 0
		while char < len(who_played):
			if who_played[char] == '(':
				depth += 1
				paren_indicies.append(char)
			if who_played[char] == ')':
				depth -= 1
				open_paren = paren_indicies[depth]
				substitute = who_played[open_paren:(char+1)]
				who_played = re.sub(re.escape(substitute), '', who_played)
				char = open_paren - 1
				subs.append({'player': substitute.strip(), 'for': re.split("–|-", who_played[:char])[-1].strip()})
				paren_indicies.remove(open_paren)
			char += 1
		starters = who_played
	else:
		starters = who_played


	starters_list = []
	for name in re.split("–|-", starters):
		name = re.sub(',|;','', name)
		if re.match('.*[0-9].*', name):
			next_num = to_int(name)
			name = re.sub(str(next_num), '', name)
		if name.strip() != "":
			starters_list.append({'name': name.strip(), 'start':0, 'end':-1})

	subs_list = []	
	double_subs = []	
	for sub in subs:
		if has_int(sub['for']):
			double_subs.append(sub)
		else:
			if len(re.split("–|-", sub['player']))>1:
				name = re.split("–|-", sub['player'])[1]
			else:
				name = sub['player']
			minute_string = int_string(name)
			name = re.sub(re.escape(minute_string)+'|,|;|\)', '', name).strip()

			if len(minute_string.split('+'))>1:
				minute = to_int(minute_string.split('+')[0])
			else:
				minute = to_int(minute_string)

			for starter in starters_list:
				if starter['name'] == sub['for']:
					starter['end'] = minute
					subs_list.append({'name': name.strip(), 'start':minute, 'end':-1})

	players = players + subs_list + starters_list

	doubles = []
	for sub in double_subs:
		name = re.split("–|-", sub['player'])[1]
		in_minute_string = int_string(name)
		name = re.sub(re.escape(minute_string)+'|,|;|\)', '', name).strip()

		if len(minute_string.split('+'))>1:
			in_minute = to_int(in_minute_string.split('+')[0])
		else:
			in_minute = to_int(in_minute_string)
		sub_in_minute = to_int(sub['for'])
		subbed_for = re.sub(str(sub_in_minute)+'|,|;|\)', '', sub['for']).strip()
		for player in players:
			if player['name'] == subbed_for:
				player['start'] = sub_in_minute
				player['end'] = in_minute
				doubles.append({'name': name.strip(), 'start':in_minute, 'end':-1})
	players += doubles
	return players


def to_int(s):
	try: 
		num = int(s)
		return num
	except ValueError:
		num = int(re.sub(r'[^\d-]+', '', s))
		return num

def has_int(s):
	num = re.sub(r'[^\d-]+', '', s)
	try: 
		num = int(num)
		return True
	except ValueError:
		return False

def int_string(s):
	first = -1
	last = 0

	for char in range(0, len(s)):
		if re.match('[0-9]', s[char]):
			if first == -1:
				first = char
			last = char
	return s[first:last+1]
