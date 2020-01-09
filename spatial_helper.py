import threading
import pandas as pd
import reverse_geocoder as rg
from geopy.distance import vincenty


class GeoReverseThread (threading.Thread):
    def __init__(self, threadID, name, counter, ds, min, max):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.min = min
        self.max = max
        self.ds = ds

    def run(self):
        print ("Starting " + self.name)
        for i in range(self.min, self.max):
            lat = self.ds.get_value(i, 'latitude')
            lon = self.ds.get_value(i, 'longitude')

            self.counter += 1
            if self.counter % 1000 == 0:
                print('getting geoinfo: {} counter: {}'.format(self.name, self.counter))

            results = rg.get((lat, lon), mode=1)
            self.ds.set_value(i, 'geocc', results['cc'])
            self.ds.set_value(i, 'geoname', results['name'])
            self.ds.set_value(i, 'geoadmin1', results['admin1'])


class DistanceCalcThread (threading.Thread):
    def __init__(self, threadID, name, counter, ds, min, max):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.min = min
        self.max = max
        self.ds = ds

    def run(self):
        print ("Starting " + self.name)

        for i in range(self.min, self.max):
            lat = self.ds.get_value(i, 'latitude')
            lon = self.ds.get_value(i, 'longitude')
            homelat = self.ds.get_value(i, 'homelat')
            homelon = self.ds.get_value(i, 'homelon')

            home = (homelat, homelon)
            poi = (lat, lon)

            self.counter += 1
            if self.counter % 1000 == 0:
                print('calculating dist from home: {} counter: {}'.format(self.name, self.counter))

            dist = vincenty(home, poi).meters
            self.ds.set_value(i, 'dist_from_home', dist)


class DataEnrichmentSpatial():
    def __init__(self):
        self.counter = 0

    def get_geoinfo(self, row):

        self.counter += 1
        if self.counter % 1000 == 0:
            print('geoinfo counter: {}'.format(self.counter))

        results = rg.get((row['latitude'], row['longitude']), mode=1)
        return results['cc'], results['name'], results['admin1']

    def set_geo_loc_mt(self, ds_ori):

        self.counter = 0
        # TODO: review performance issue
        ds_ori.loc[:, 'geocc'] = ''
        ds_ori.loc[:, 'geoname'] = ''
        ds_ori.loc[:, 'geoadmin1'] = ''
        ds_ori.reset_index(inplace=True, drop=True)
        threads = []
        total =len(ds_ori)
        step = int(total /16)
        #dummy call to load singleton
        results = rg.get((0.1, 0.1), mode=1)

        for i in range(0, total, step):
            min = i
            max = i + step-1
            max = max if max < total else total
            thread1 = GeoReverseThread(1, str(i), 1, ds_ori, min, max)
            thread1.start()
            threads.append(thread1)

        # Wait for all threads to complete
        for t in threads:
            t.join()
        print("Exiting Main Thread")
        return ds_ori

    def set_geo_loc_fast(self, ds_ori):

        self.counter = 0
        # TODO: review performance issue
        ds_ori.loc[:,'geocc'] = ''
        ds_ori.loc[:, 'geoname'] = ''
        ds_ori.loc[:, 'geoadmin1'] = ''
        ds_ori.reset_index(inplace=True)

        min = 0
        max = len(ds_ori)

        self.set_geo_loc_task(ds_ori, max, min)
        # geo_coder
        print('load geo info!')
        return ds_ori

    def set_geo_loc_task(self, ds_ori, max, min):
        for i in range(min, max):
            lat = ds_ori.get_value(i, 'latitude')
            lon = ds_ori.get_value(i, 'longitude')

            self.counter += 1
            if self.counter % 1000 == 0:
                print('geoinfo counter: {}'.format(self.counter))

            results = rg.get((lat, lon), mode=1)
            ds_ori.set_value(i, 'geocc', results['cc'])
            ds_ori.set_value(i, 'geoname', results['name'])
            ds_ori.set_value(i, 'geoadmin1', results['admin1'])

            # ds_ori[['geocc', 'geoname', 'geoadmin1']] = ds_ori.apply(lambda row: self.get_geoinfo(row), axis=1)

    def set_geo_loc(self, ds_ori):

        self.counter = 0
        # TODO: review performance issue
        ds_ori.loc[:,'geocc'] = ''
        ds_ori.loc[:, 'geoname'] = ''
        ds_ori.loc[:, 'geoadmin1'] = ''

        for i , row in ds_ori.iterrows():
            r = row
            geocc, geoname, geoadmin1 =self.get_geoinfo(r)
            ds_ori.set_value(i, 'geocc', geocc)
            ds_ori.set_value(i, 'geoname', geoname)
            ds_ori.set_value(i, 'geoadmin1', geoadmin1)

        #ds_ori[['geocc', 'geoname', 'geoadmin1']] = ds_ori.apply(lambda row: self.get_geoinfo(row), axis=1)
        # geo_coder
        print('load geo info!')
        return ds_ori

    def set_geo_location(self, ds_ori):
        m = ds_ori.as_matrix(columns=['latitude', 'longitude'])
        coordinates = zip(m[:,0], m[:,1])
        results = rg.search(list(coordinates), mode=1)
        len(results)
        dsloc = pd.DataFrame(results)
        print(dsloc.columns)
        dsloc.rename(columns={'name': 'geoname', 'cc': 'geocc', 'admin1': 'geoadmin1', 'admin2': 'geoadmin2'}, inplace=True)
        print(dsloc.shape)
        #ds_ori = pd.concat([ds_ori, dsloc], axis=1, copy=False)
        ds_ori['geocc'] = dsloc.geocc
        ds_ori['geoname'] = dsloc.geoname
        ds_ori['geoadmin1'] = dsloc.geoadmin1
        ds_ori['geolat'] = dsloc.lat
        ds_ori['geolon'] = dsloc.lon
        print(ds_ori.shape)
        print('load geo info!')
        return ds_ori

    def calc_distance(self, row):
        home = (row['homelat'], row['homelon'])
        poi = (row['latitude'], row['longitude'])
        self.counter += 1
        if self.counter % 1000 == 0:
            print('calculating distance from home {}'.format(self.counter))
        return vincenty(home, poi).kilometers

    def set_home_location(self, ds):
        print('setting home location...')
        userhome = ds[['id', 'screen_name', 'latitude', 'longitude', 'geocc', 'geoadmin1']].round(3).groupby(
            ['screen_name', 'latitude', 'longitude', 'geocc', 'geoadmin1']).size().reset_index()
        userhome.rename(columns={0: 'count','latitude':'homelat', 'longitude':'homelon', 'geocc':'homecc', 'geoadmin1':'homeadmin1'}, inplace=True)
        userhome.sort_values(by=['screen_name', 'count'], ascending=False, inplace=True)
        userhome.drop_duplicates(subset=['screen_name'], keep='first', inplace=True)
        ds = ds.merge(userhome, on='screen_name')
        ds.loc[:, 'tourist'] = 0
        ds.loc[(ds.homecc != ds.geocc), 'tourist'] = 1
        return ds

    def calc_distances(self, ds):
        print('calculating distances from home...')
        self.counter = 0
        ds['dist_from_home'] = ds.apply(lambda row: self.calc_distance(row), axis=1)
        print('calculating distances from home done!')
        return ds

    def calc_distances_mt(self, ds_ori):

        self.counter = 0
        # TODO: review performance issue
        ds_ori.loc[:, 'dist_from_home'] = 0
        threads = []
        total =len(ds_ori)
        step = int(total /16)

        for i in range(0, total, step):
            min = i
            max = i + step-1
            max = max if max < total else total
            thread1 = DistanceCalcThread(1, str(i), 1, ds_ori, min, max)
            thread1.start()
            threads.append(thread1)

        # Wait for all threads to complete
        for t in threads:
            t.join()
        print("Exiting Main Thread")
        return ds_ori


if __name__ == "__main__":
    dataset_filename = '/Users/john/projects/fittur/dataset/fitness/tweets.csv'
    output_filename = '/Users/john/projects/fittur/dataset/fitness/tweets_spatial.csv'
    enricher = DataEnrichmentSpatial()
    ds = pd.read_csv(dataset_filename)
    ds = enricher.set_geo_location(ds)
    ds = enricher.set_home_location(ds)
    #DataWriter.save_dataset(ds, output_filename)

