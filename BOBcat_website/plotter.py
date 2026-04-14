#TODO: Add units, make sure this is working with duplicate entries
import argparse
import numpy as np
import plotly.express as px
from    plotly.offline      import  plot
from    plotly.graph_objs   import  Figure
import pandas as pd
from bobcat_db_interface.communications import db_comms
import plotly.io as pio
pio.renderers.default = "browser"

def plotter(param1, param2, param3=None, color=None, no_duplicate_x=True, no_duplicate_y=True, no_duplicate_z=True, saveto=None, log_x=False, log_y=False):
    
    #establishing the connection
    cur, conn = db_comms.db_connect()

    # retrieve column names to make sure the parameters are valid
    query = "SELECT column_name FROM information_schema.columns WHERE table_name='binary_model';"
    bm_cols = pd.read_sql(query, conn)
    query = "SELECT column_name FROM information_schema.columns WHERE table_name='candidate';"
    c_cols = pd.read_sql(query, conn)

    # retrieve the data
    if param1 in bm_cols['column_name'].values:
        query = "SELECT candidate_name AS name, " + param1 + " FROM binary_model"
        df1 = pd.read_sql(query, conn)
    elif param1 in c_cols['column_name'].values:
        query = "SELECT name, " + param1 + " FROM candidate"
        df1 = pd.read_sql(query, conn)
    else:
        raise ValueError("Parameter 1 not found in either table.")
    if param2 in bm_cols['column_name'].values:
        query = "SELECT candidate_name AS name, " + param2 + " FROM binary_model"
        df2 = pd.read_sql(query, conn)
        hist = False
    elif param2 in c_cols['column_name'].values:
        query = "SELECT name, " + param2 + " FROM candidate"
        df2 = pd.read_sql(query, conn)
        hist = False
    elif param2 == "hist":
        hist = True
    else:
        raise ValueError("Parameter 2 not found in either table.")
    # Optional z data
    if param3 != None:
        if param3 in bm_cols['column_name'].values:
            query = "SELECT candidate_name AS name, " + param3 + " FROM binary_model"
            df3 = pd.read_sql(query, conn)
        elif param3 in c_cols['column_name'].values:
            query = "SELECT name, " + param3 + " FROM candidate"
            df3 = pd.read_sql(query, conn)
        else:
            raise ValueError("Parameter 3 not found in either table.")
    # Optional color data
    if color != None:
        if color in bm_cols['column_name'].values:
            query = "SELECT candidate_name AS name, " + color + " FROM binary_model"
            df_color = pd.read_sql(query, conn)
        elif color in c_cols['column_name'].values:
            query = "SELECT name, " + color + " FROM candidate"
            df_color = pd.read_sql(query, conn)
        else:
            raise ValueError("Color not found in either table.")
    conn.close() # close the connection
    
    # remove duplicates
    if no_duplicate_x == True:
        df1.drop_duplicates(subset='name', inplace=True)
    if no_duplicate_y == True:
        df2.drop_duplicates(subset='name', inplace=True)

    # merge the dataframes
    if hist == True:
        df = df1
    else:
        df = df1.merge(df2, how='inner', on='name').drop_duplicates()

    # add z data if it exists
    if param3 != None:
        if no_duplicate_z == True:
            df3.drop_duplicates(subset='name', inplace=True)
        df = df.merge(df3, how='inner', on='name').drop_duplicates()

    # add color data if it exists
    if color != None:
        df_color.drop_duplicates(subset='name', inplace=True)
        df = df.merge(df_color, how='inner', on='name').drop_duplicates()

    # plot the data
    if log_x == True:
        df[param1] = np.log10(df[df[param1] != 0][param1])
    if log_y == True:
        df[param2] = np.log10(df[df[param2] != 0][param2])
    if hist == True:
        fig = px.histogram(df, x=df[param1], hover_name='name', hover_data=[param1])
    elif param3 == None and color == None:
        fig = px.scatter(df, x=df[param1], y=df[param2], hover_name='name', hover_data=[param1, param2])
    elif param3 == None and color != None:
        fig = px.scatter(df, x=df[param1], y=df[param2], color=df[color], hover_name='name', hover_data=[param1, param2, color])
    elif param3 != None and color == None:
        fig = px.scatter_3d(df, x=df[param1], y=df[param2], z=df[param3], hover_name='name', hover_data=[param1, param2, param3])
    elif param3 != None and color != None:
        fig = px.scatter_3d(df, x=df[param1], y=df[param2], z=df[param3], color=df[color], hover_name='name', hover_data=[param1, param2, param3, color])
    
    # update the layout
    fig.update_layout(title='{} vs {}'.format(param1, param2))
    fig.update_yaxes(title=param2)
    fig.update_xaxes(title=param1)
    
    # show the plot
    if saveto != None:
        fig.write_html(str(saveto)+'/'+str(param1)+'_'+str(param2)+'.html')
    fig.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--param1", type=str, required=True)
    parser.add_argument("-y", "--param2", type=str, required=True)
    parser.add_argument("-z", "--param3", type=str, required=False)
    parser.add_argument("-color", "--color", type=str, required=False)
    parser.add_argument("-no_dup_x", "--no_dup_x", type=bool, required=False)
    parser.add_argument("-no_dup_y", "--no_dup_y", type=bool, required=False)
    parser.add_argument("-no_dup_z", "--no_dup_z", type=bool, required=False)
    parser.add_argument("-saveto", "--saveto", type=str, required=False)
    parser.add_argument("-log_x", "--log_x", type=bool, required=False)
    parser.add_argument("-log_y", "--log_y", type=bool, required=False)
    args = parser.parse_args()
    plotter(args.param1, args.param2, args.param3, args.color, args.no_dup_x, args.no_dup_y, args.no_dup_z, args.saveto, args.log_x, args.log_y)
    #plotter -x param1 -y param2 [hist] -z param3 -color color -no_dup_x True -no_dup_y True -no_dup_z True -saveto path -log_x True -log_y True
