import os
import pyrugga as pgr
import pandas as pd 
from sqlalchemy import create_engine
import psycopg2 as pg

#database connection
connection_local = pg.connect("host=postgres port=5433 dbname=postgres user=postgres")
engine = create_engine('postgresql://postgres:@postgres:5433/postgres')


# define our zones to count events in
##################################################################
def Zones( x ): 
    #     x = 10 * round( x / 10) 
    #     if x > 95:
    #         x = 95
    #     if x < 5:
    #         x = 5
    return x

# scans a folder and returns a list of all the XML files we want to convert
##################################################################
def scan_files(path):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    xml_files = []
    for f in files:
        if '.xml' in f.lower() :
            xml_files.append(f)

    return xml_files

# opens each XML file and converts it to a Match object in PyRugga
##################################################################
def get_matches(FILES_LOC):
    matches = []
    for fn in scan_files(FILES_LOC):
        #print(FILES_LOC + fn)
        matches.append(pgr.Match(FILES_LOC + fn,zones=Zones))


    #Check stats
    dates = []
    for match in matches:
        dates.append(match.summary['fixture_date'][0])

    print("Number of Matches : %s" % str(len(matches)))
    print("First game : " + str(pd.to_datetime(pd.DataFrame(dates,columns=['dte'])['dte']).min()))
    print("Last game : " + str(pd.to_datetime(pd.DataFrame(dates,columns=['dte'])['dte']).max()))
    
    return matches


# Extracts the sequences we are interested in from a match object
##################################################################
def get_Sequences(FOLDER,event,outcome,start_zone):

    #get out matches
    matches = get_matches(FOLDER)

    copy_rows = False
    first = True
    set_intrest = -1
    df = pd.DataFrame()
    last_phases = -1

    for match in matches:
        copy_rows = False
        first = True
        set_intrest = -1

        for index, row in match.events.iterrows():
            #trigger start of sequence
            if  row['event'] == event and row['outcome'] == outcome and row['x_coord'] >= start_zone and first == True:
                copy_rows = True
                set_intrest = row['set_num']
                first == False
                last_phases = row['phases']

            #trigger end of sequence
            if (set_intrest != row['set_num']  or last_phases > row['phases']) and  copy_rows == True:
                copy_rows = False
                first = True

            if copy_rows == True:
                #axis = 0 to append rows, axis = 1 to append columns
                df = pd.concat([df,row],axis=1) 
                last_phases = row['phases']

    # I am sure I have to do this because I never learnt to use concat properly, or concat is not 
    # the correct why to do this. Regardless this is a lazy hack becuase I was not bothered to 
    # read the documentation so just guessed.
    df = df.T
    
    #remove the last entery which tells us possession has changed. I know its changed the phases reset to 1 you dont need this row
    df = df.query('event != "Possession"')
    
    return df

def get_Timelines(FOLDER):
    # creates an empty dataframe
    df = pd.DataFrame()

    # Convert to Match Object
    matches = get_matches(FOLDER)

    for match in matches:
        match.timeline['x_coord'] = (match.timeline['x_coord']*1.0).apply(match._Zones)
        match.timeline['y_coord'] = (match.timeline['y_coord']*1.0).apply(match._Zones)

        match.timeline['x_coord_end'] = (match.timeline['x_coord_end']*1.0).apply(match._Zones)
        match.timeline['y_coord_end'] = (match.timeline['y_coord_end']*1.0).apply(match._Zones)

        match.timeline['fixture_code'] = match.summary.fixture_code[0]

        df = pd.concat([df, match.timeline], sort=False)

    # Prints the first 10 rows
    return df
    
    
   

