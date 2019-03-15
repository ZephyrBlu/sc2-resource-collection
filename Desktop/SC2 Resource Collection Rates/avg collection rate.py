import mpyq
from s2protocol_py3 import versions
import json
import os
import csv
import math

def write2file(data, filename):
	with open(filename, 'w', encoding='utf-8') as output:
		writer = csv.writer(output, lineterminator='\n')
		writer.writerows(data)

def setup(filename):
	archive = mpyq.MPQArchive(filename)
	
	# getting correct game version and protocol
	contents = archive.header['user_data_header']['content']

	header = versions.latest().decode_replay_header(contents)

	baseBuild = header['m_version']['m_baseBuild']
	protocol = versions.build(baseBuild)

	metadata = json.loads(archive.read_file('replay.gamemetadata.json'))

	# accessing neccessary parts of file for data
	contents = archive.read_file('replay.tracker.events')

	# translating data into dict format info
	trackerEvents = protocol.decode_replay_tracker_events(contents)

	players = metadata['Players']
	game_length = metadata['Duration']
	collection_rates = {}
	races = {}

	for player in players:
		collection_rates[player['PlayerID']] = {'mineral': [(0, 0)], 'gas': [(0, 0)]}
		races[player['PlayerID']] = player['SelectedRace']

	return trackerEvents, collection_rates, races, game_length

def main():

	fileList = os.listdir('PvT') # dir is your directory path
	number_files = len(fileList)

	avg_protoss_collection_rates = {'mineral': {}, 'gas': {}}
	avg_terran_collection_rates = {'mineral': {}, 'gas': {}}

	game_lengths = {}

	for i in range(0, number_files):
		filename = f'PvT/replay{i}.SC2Replay'

		events, collection_rates, races, game_length = setup(filename)

		for event in events:
			if event['_event'] == 'NNet.Replay.Tracker.SPlayerStatsEvent':
				player = collection_rates[event['m_playerId']]

				mineral_rate = event['m_stats']['m_scoreValueMineralsCollectionRate']
				gas_rate = event['m_stats']['m_scoreValueVespeneCollectionRate']

				count = len(player['mineral'])
				time = event['_gameloop']
				avg_mineral_rate = ((player['mineral'][-1][1]*count)+mineral_rate)/(count+1)
				avg_gas_rate = ((player['gas'][-1][1]*count)+gas_rate)/(count+1)

				player['mineral'].append((time, avg_mineral_rate))
				player['gas'].append((time, avg_gas_rate))

		for playerId, rates in collection_rates.items():
			player = collection_rates[playerId]
			for pair in rates['mineral']:
				if races[playerId] == 'Prot':
					if pair[0] in avg_protoss_collection_rates['mineral'].keys():
						avg_protoss_collection_rates['mineral'][pair[0]].append(pair[1])
					else:
						avg_protoss_collection_rates['mineral'][pair[0]] = [pair[1]]
				else:
					if pair[0] in avg_terran_collection_rates['mineral'].keys():
						avg_terran_collection_rates['mineral'][pair[0]].append(pair[1])
					else:
						avg_terran_collection_rates['mineral'][pair[0]] = [pair[1]]
				
			for pair in rates['gas']:
				if races[playerId] == 'Prot':
					if pair[0] in avg_protoss_collection_rates['gas'].keys():
						avg_protoss_collection_rates['gas'][pair[0]].append(pair[1])
					else:
						avg_protoss_collection_rates['gas'][pair[0]] = [pair[1]]
				else:
					if pair[0] in avg_terran_collection_rates['gas'].keys():
						avg_terran_collection_rates['gas'][pair[0]].append(pair[1])
					else:
						avg_terran_collection_rates['gas'][pair[0]] = [pair[1]]

		if game_length in game_lengths.keys():
			game_lengths[game_length] += 1
		else:
			game_lengths[game_length] = 1

		# for p, c in collection_rates.items():
		# 	for n, v in c.items():
		# 		for num in v:
		# 			print(num)
		# 		print('\n')
		# 	print('\n\n')

		print(f'done replay {i+1}\n')

	final_avg_protoss = {'mineral': {}, 'gas': {}}
	final_avg_terran = {'mineral': {}, 'gas': {}}

	for resource, values in avg_protoss_collection_rates.items():
		for time, v in values.items():
			if len(v) > 2:
				avg = sum(v)/len(v)
				final_avg_protoss[resource][time] = avg

	for resource, values in avg_terran_collection_rates.items():
		for time, v in values.items():
			if len(v) > 2:
				avg = sum(v)/len(v)
				final_avg_terran[resource][time] = avg

	count_t = 0
	small_t = 0
	sum_t = 0
	terran_stddev = []
	size_t = []
	for k,v in sorted(avg_terran_collection_rates['mineral'].items()):
		avg = sum(v)/len(v)
		size = len(v)
		variance_sum = 0
		for val in v:
			variance_sum += (val-avg)**2

		if size > 2:
			terran_stddev.append(math.sqrt(variance_sum/(size-1)))
			sum_t += len(v)
			size_t.append(len(v))
			if size > 30:
				count_t += 1
			print(k/22.4,v)
			print('\n')
		else:
			small_t += 1
			# terran_variance.append(0)
		

	count_p = 0
	small_p = 0
	sum_p = 0
	protoss_stddev = []
	size_p = []
	for k,v in sorted(avg_protoss_collection_rates['mineral'].items()):
		avg = sum(v)/len(v)
		size = len(v)
		variance_sum = 0
		for val in v:
			variance_sum += (val-avg)**2

		if size > 2:
			protoss_stddev.append(math.sqrt(variance_sum/(size-1)))
			sum_p += len(v)
			size_p.append(len(v))
			if size > 30:
				count_p += 1
			print(k/22.4,v)
			print('\n')
		else:
			small_p += 1
			# protoss_variance.append(0)
		
	t = avg_terran_collection_rates['mineral']
	p = avg_protoss_collection_rates['mineral']
	print(f'size terran: {len(t)}')
	print(f'size toss: {len(p)}')

	print(f'terran: {count_t}')
	print(f'toss: {count_p}')

	print(f'terran discarded: {small_t}')
	print(f'toss discarded: {small_p}')

	print('avg length')

	print(f'terran: {sum_t/(len(t)-small_t)}')
	print(f'toss: {sum_p/(len(t)-small_p)}')

	# write2file(zip(terran_stddev, protoss_stddev), 'Std Dev.csv')
	write2file(zip(size_t, size_p), 'Sizes.csv')

	protoss_min = []
	for k, v in sorted(final_avg_protoss['mineral'].items()):
		protoss_min.append((k,v))
	# write2file(protoss_min, 'ProtossMineral.csv')

	protoss_gas = []
	for k, v in sorted(final_avg_protoss['gas'].items()):
		protoss_gas.append((k,v))
	# write2file(protoss_gas, 'ProtossGas.csv')

	terran_min = []
	for k, v in sorted(final_avg_terran['mineral'].items()):
		terran_min.append((k,v))
	# write2file(terran_min, 'TerranMineral.csv')

	terran_gas = []
	for k, v in sorted(final_avg_terran['gas'].items()):
		terran_gas.append((k,v))
	# write2file(terran_gas, 'TerranGas.csv')

	mineral_diff = []
	for i in range(0, len(protoss_min)):
		diff = protoss_min[i][1]-terran_min[i][1]
		mineral_diff.append(diff)

	gas_diff = []
	for i in range(0, len(protoss_gas)):
		diff = protoss_gas[i][1]-terran_gas[i][1]
		gas_diff.append(diff)

	# write2file(zip(mineral_diff, gas_diff), 'Resource Collection Diff.csv')

	lengths = []
	for k, v in sorted(game_lengths.items()):
		lengths.append((k, v))

	# write2file(lengths, 'Game Lengths.csv')

main()