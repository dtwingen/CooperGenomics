import os 
import time 


key_file = 'key.key'
key_exp_start = time.time() 
cred_filename = 'CredFile.ini'

with open(cred_filename, 'r') as cred_in: 

	lines = cred_in.readlines() 
	config = {} 
	for line in lines: 
		tuples = line.rstrip('\n').split('=', 1) 
		
		if tuples[0] in ('Expiry '): 
			config[tuples[0]] = tuples[1] 
			
	if not(config['Expiry '] == -1): 

		# Time below is in seconds. 
		time_for_exp = int(config['Expiry ']) * 60
		
		while(os.path.isfile(key_file)): 
			time.sleep(10) 
			
			if (not(time.time() - key_exp_start <= time_for_exp) 
				and os.path.isfile(key_file)): 
				os.remove(key_file) 
