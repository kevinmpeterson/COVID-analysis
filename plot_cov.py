import matplotlib.pyplot as plt
import datetime as dt
import dateutil as du
import csv
import os
import numpy as np

COVDIR_BASE="COVID-19"
COVDIR_SUB="/csse_covid_19_data/csse_covid_19_daily_reports/"
COVDIR_FULL=COVDIR_BASE+COVDIR_SUB

# Magic factor to convert from reported to estimated infections
REP_TO_INFECT=6.9

class Stats():
	def __init__(self, deaths=0, confirmed=0, state="", date=""):
		self.deaths = deaths
		self.confirmed = confirmed
		self.state = state
		self.date = date


def aggregate_stats(stats):
	all_stats = Stats(0, 0, "", "")
	if len(stats) > 0:
		all_stats.date = stats[0].date
	
	for stat in stats:
		all_stats.deaths += stat.deaths
		all_stats.confirmed += stat.confirmed
	
	return all_stats

def checkint(st):
	val = 0
	try:
		val = int(st)
	except ValueError:
		val = 0
	
	return val

def angle_diff(a1, a2):
	da = a2 - a1
	while da > 180:
		da -= 360

	while da <= -180:
		da += 360

	return da

def collect_stats_ll(file_name, lat, lon, dlat, dlon):
	stats = []
	with open(file_name, 'r') as csvfile:
		all_data = csv_reader(csvfile, delimiter=',')
		for row in all_data:
			data_lat = float(row[6])
			data_lon = float(row[7])
			
			lat_diff = angle_diff(data_lat, lat)
			lon_diff = angle_diff(data_lon, lon)

			if(abs(lat_diff) < dlat and abs(lon_diff) < dlon):
				s = Stats(checkint(row[4]), checkint(row[3]), row[0], row[2])
				stats.append(s)

def collect_stats(file_name, country, region=None):
	stats = []
	with open(file_name, 'r') as csvfile:
		all_data = csv.reader(csvfile, delimiter=',')
		for row in all_data:
			if row[1].lower() == country.lower():
				if region == None or region.lower() == row[0].lower():
					s = Stats(checkint(row[4]), checkint(row[3]), row[0], row[2])
					stats.append(s)
	return stats			

def datestr_to_doy(ds):
	date_time_obj = du.parser.parse(ds)
	jan1 = dt.date(year=2020, day=1, month=1)
	diff = date_time_obj.date() - jan1
	doy = diff.days
	
	return doy

def get_timeseries(country, region=[]):
	all_stats = []
	min_doy = 365
	max_doy = -1
	for filename in os.listdir(COVDIR_FULL):
		if filename.endswith(".csv"):
			cur_stats = []
			if len(region) > 0:
				for r in region:
					addl_stats = collect_stats(os.path.join(COVDIR_FULL,filename), country, r)
					cur_stats = cur_stats + addl_stats
			else:
				cur_stats = collect_stats(os.path.join(COVDIR_FULL,filename), country, None)
				
			#cur_stats = collect_stats(os.path.join(COVDIR_FULL, filename), 

			if(len(cur_stats) > 0):
				agg_stats = aggregate_stats(cur_stats)
				cur_doy = datestr_to_doy(agg_stats.date)
				all_stats.append(agg_stats)
				if(cur_doy < min_doy): min_doy = cur_doy
				if(cur_doy > max_doy): max_doy = cur_doy

	#dates = list(range(min_doy, max_doy+1))
	#deaths = np.zeros(max_doy - min_doy + 1)
	#confirmed = np.zeros(max_doy - min_doy + 1)
	#for stat in all_stats:
	#	doy = datestr_to_doy(stat.date)
	#	deaths[doy - min_doy] = stat.deaths
	#	confirmed[doy - min_doy] = stat.confirmed

	dates = np.zeros(len(all_stats))
	deaths = np.zeros(len(all_stats))
	confirmed = np.zeros(len(all_stats))
	
	for idx,stat in enumerate(all_stats):
		doy = datestr_to_doy(stat.date)
		dates[idx] = doy
		deaths[idx] = stat.deaths
		confirmed[idx] = stat.confirmed

	inds = dates.argsort()
	dates = dates[inds]
	deaths = deaths[inds]
	confirmed = confirmed[inds]
	
	estimated = REP_TO_INFECT * confirmed	
	cum_deaths = np.cumsum(deaths)
	cum_confirmed = np.cumsum(confirmed)
	cum_estimated = REP_TO_INFECT * cum_confirmed

	ts = {
		'dates': dates, 
		'deaths' : deaths,
		'confirmed' : confirmed,
		'estimated' : estimated,
		'cum_deaths' : cum_deaths,
		'cum_confirmed' : cum_confirmed,
		'cum_estimated' : cum_estimated
	}

	return ts

def plot_data(ts, location_str):
	plt.clf()
	plt.plot(ts['dates'], ts['deaths'], 'r-', ts['dates'], ts['confirmed'], 'g-', ts['dates'], ts['estimated'], 'k-.')
	plt.hlines(100, ts['dates'][0], ts['dates'][len(ts['dates'])-1], 'k', 'dotted')
	plt.hlines(1000, ts['dates'][0], ts['dates'][len(ts['dates'])-1], 'r', 'dotted')
	plt.hlines(5000, ts['dates'][0], ts['dates'][len(ts['dates'])-1], 'r')


	# Get most recent numbers	
	max_est = np.amax(ts['estimated'])
	plot_max = 1.25 * max_est

	last_reported = ts['confirmed'][len(ts['confirmed'])-1]
	last_date = np.amax(ts['dates'])
	
	plt.annotate(last_reported, (last_date, last_reported))


	# Make sure timeline is up to date
	now = dt.datetime.now()
	today = now.strftime("%m-%d-%Y, %H:%M:%S")
	doy_today = datestr_to_doy(today)

	plt.xlim(0, doy_today)
	plt.ylim(0, plot_max)
	plt.xlabel("Day of Year")
	plt.ylabel("# People")
	plt.legend(['Deaths', 'Confirmed Cases', 'Estimated Cases'])
	plt.title(location_str+" - day "+str(doy_today)+" - @ "+str(last_reported))

	return plt

if __name__ == "__main__":
	bay_area_cities = ["Santa Clara County, CA", "Solano, CA", "Santa Cruz, CA", "Alameda County, CA", "Santa Clara, CA", "San Francisco County, CA", "San Mateo, CA", "Sonoma County, CA", "Marin, CA", "Berkeley, CA"] 


	ts_US = get_timeseries("US")
	ts_IT = get_timeseries("Italy")
	ts_CA = get_timeseries("US", ["California"])
	ts_Bay = get_timeseries("US", bay_area_cities)
	ts_NY = get_timeseries("US", ["New York"])

	plt_US = plot_data(ts_US, "US")
	plt_US.savefig("US.jpeg", dpi=300)

	plt_IT = plot_data(ts_IT, "Italy")
	plt_IT.savefig("Italy.jpeg", dpi=300)	
	
	plt_CA = plot_data(ts_CA, "US, CA")
	plt_CA.savefig("CA.jpeg", dpi=300)
	
	plt_NY = plot_data(ts_NY, "US, NY")
	plt_NY.savefig("NY.jpeg", dpi=300)
	

	plt_Bay = plot_data(ts_Bay, "US, Bay Area")
	plt_Bay.savefig("Bay.jpeg", dpi=300)

	#plt.subplot(311)
	#plt_US.show()
	#plt.subplot(312)
	#plt_CA.show()
	#plt.subplot(313)
	#plt_Bay.show()
