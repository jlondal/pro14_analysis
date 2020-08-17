import os
import pyrugga as pgr
import pandas as pd

# define out zones of play
def Zones( x ): 
    x = 10 * round( x / 10) 
    if x > 95:
        x = 95
    if x < 5:
        x = 5
    return x

def scan_files(path):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    xml_files = []
    for f in files:
        if '.xml' in f.lower() :
            xml_files.append(f)

    return xml_files

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

def flatten_data(matches):


    # extract the features we interested in
    features = [
        'fixture_code',
        'team_name',
        'start_event',
        'end_event',
        'points',
        'length',
        'start',
        'x_coord',
        'x_coord_end',
        'y_coord',
        'y_coord_end',
        'pick_and_go',
        'one_out_drive',
        'penalty_try',
        'lineout_throw',
        'lineout',
        'scrum',
        'tap_pen',
        'try',
        'won_penalty_try',
        'conversion',
        'maul',
        'phases',
        'pass',
        'complete_pass',
        'incomplete_pass',
        'goal_kick',
        'goal_success',
        'goal_missed',     
        'throw_front',
        'throw_middle',
        'throw_back',
        'throw_15m_plus',
        'tackle',
        'missed_tackle',    
        'lost_in_ruck_or_maul',
        'sack',
        'jackal',
        'start_set_lineout_steal',
        'yellow_card',
        'red_card',
        'advantage',
        'pen_conceded',
        'penalty_won'
    ]

    df = pd.DataFrame()
    
    for match in matches:
        match.timeline['x_coord'] = (match.timeline['x_coord']*1.0).apply(match._Zones)
        match.timeline['y_coord'] = (match.timeline['y_coord']*1.0).apply(match._Zones)

        match.timeline['x_coord_end'] = (match.timeline['x_coord_end']*1.0).apply(match._Zones)
        match.timeline['y_coord_end'] = (match.timeline['y_coord_end']*1.0).apply(match._Zones)

        match.timeline['fixture_code'] = match.summary.fixture_code[0]


        try:
            df = pd.concat([df, match.timeline[features]], sort=False)
        except:
            df = match.timeline[features]
    
    return df


#functions we are going to need in this next section you can skip reading this part 
def empty_pitch():
    x_coord = np.linspace(0,100,100)
    tmp = pd.Series(x_coord)
    x_coord = np.unique(tmp.apply(Zones))

    y_coord = np.linspace(0,70,70)
    tmp = pd.Series(y_coord)
    y_coord = np.unique(tmp.apply(Zones))
    
    return (x_coord,y_coord)

def create_probs(x_coord, y_coord,kicking_rate_length,kicking_rate_width,points):
    rows = []
    for y in y_coord:
        row = []
        for x in x_coord:
            try:
                if x >= 95 and (y < 30 or y > 40) : 
                    row.append(0)
                elif x >= 90 and (y < 20 or y >= 60) : 
                    row.append(0)    
                elif x <= 50 and (y < 10 or y > 50) : 
                    row.append(0)  
                elif x <= 40 and (y < 10 or y > 50) : 
                    row.append(0)  
                else:
                    row.append(kicking_rate_length[x] * kicking_rate_width[y]*points)
            except:
                row.append(0)
        rows.append(row)

    tmp = pd.DataFrame(rows,columns=x_coord)
    tmp.index = y_coord

    return tmp    

def kicking_success(df,points=1):
    trys = df.query("end_event == 'End Try' ")
    conversions = df.query("end_event == 'End Try' and goal_success > 0")

    kicking_rate_width = ((conversions.groupby(['y_coord_end'])['team_name'].count())/\
     (trys.groupby(['y_coord_end'])['team_name'].count())).fillna(0)
    trys = df.query("end_event == 'End Pen Won' and goal_kick > 0 ")
    conversions = df.query("end_event == 'End Pen Won' and goal_success > 0")

    kicking_rate_length = ((conversions.groupby(['x_coord_end'])['team_name'].count())/\
     (trys.groupby(['x_coord_end'])['team_name'].count())).fillna(0)

    x_coord,y_coord = empty_pitch()
    
    tmp = create_probs(x_coord, y_coord,kicking_rate_length,kicking_rate_width,points)

    return tmp

def draw_line(x,y,ls='-',color='white'):
    line = plt.Line2D(x, y, lw=2.5,color=color,ls=ls)
    plt.gca().add_line(line)

def draw_pitch():

    Pitch = plt.Rectangle([0,0], width = 100, height = 70, fill = True,color='green')
    plt.gca().add_patch(Pitch)
        
    #halfway line
    draw_line((50, 50), (0, 70))

    #22m lines
    draw_line((22, 22), (0, 70))    
    draw_line((100-22, 100-22), (0, 70))
    
    #5m lines
    draw_line((5, 5), (2.5, 7.5))
    draw_line((5, 5), (62.5, 67.5))
    draw_line((95, 95), (2.5, 7.5))
    draw_line((95, 95), (62.5, 67.5))
    
    #10m lines
    draw_line((40, 40), (0, 70),ls='--')    
    draw_line((60, 60), (0, 70),ls='--')

    
    #15m lines
    draw_line((0, 100), (5, 5),ls='--')    
    draw_line((0, 100), (65, 65),ls='--')
    draw_line((0, 100), (15, 15), ls='--')
    draw_line((0, 100), (55, 55), ls='--')

    plt.ylim(0, 70)
    plt.xlim(0, 100)


def heatmap(hmap,title = "",negative=False):
    fig=plt.figure() #set up the figures
    fig.set_size_inches(17, 8)
    ax=fig.add_subplot(1,1,1)
    draw_pitch() #overlay our different objects on the pitch


    plt.title(title)

    scale = np.array([100,70])
    ax.imshow(hmap.values, zorder=1, aspect="auto", extent=(0,scale[0],0,scale[1]), 
              cmap=sns.palplot(sns.dark_palette("red", 50)),alpha=0.75,interpolation='lanczos')

    offs = np.array([scale[0]/hmap.values.shape[1], scale[1]/hmap.values.shape[0]])
    
    for pos, val in np.ndenumerate(hmap.values):
        ax.annotate(f"{val:.2f}", xy=np.array(pos)[::-1]*offs+offs/2, ha="center", va="center",color='black')


    plt.show()
            
    
