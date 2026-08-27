#TODO: Add units, make sure this is working with duplicate entries
import argparse
from types import NoneType
import numpy as np
import plotly.express as px
from    plotly.offline      import  plot
from    plotly.graph_objs   import  Figure
import pandas as pd
from bobcat_db_interface.communications import db_comms
import plotly.io as pio
pio.renderers.default = "browser"

def plotter(param1, param2, param3=None, 
            color=None, filter_by=None, 
            no_duplicate_x=True, no_duplicate_y=True, 
            no_duplicate_z=True, saveto=None,
            log_x=False, log_y=False):
    
    #establishing the connection
    cur, conn = db_comms.db_connect()

    # retrieve column names to make sure the parameters are valid
    query = "SELECT column_name FROM information_schema.columns WHERE table_name='binary_model';"
    bm_cols = pd.read_sql(query, conn)
    query = "SELECT column_name FROM information_schema.columns WHERE table_name='candidate';"
    c_cols = pd.read_sql(query, conn)

    # Retrieve the data
    #   1. Get only data which passes the parameter filter(s)
    #       - Check that the filter is in the evidence_subcategory table
    #       - If so, get all subcategory ids for that filter and pass it to model_evidence for the binary model ids
    #       - Later, use those binary_model ids to filter df1, df2, etc.

    query = "SELECT binary_model_id FROM binary_model;"
    binary_model_ids = pd.read_sql(query, conn)['binary_model_id'].tolist() # No filter

    if filter_by is not None:

        query = "SELECT * FROM evidence_subcategory;"
        evidence_subcategory_table = pd.read_sql(query, conn)
        ev_cols = evidence_subcategory_table[["evidence_category_type", "evidence_subcategory_type"]].drop_duplicates()

        query = "SELECT binary_model_id, evidence_subcategory_id FROM model_evidence;"
        model_evidence_table = pd.read_sql(query, conn)

        if type(filter_by) in [list, tuple]:
            pass # TODO: Implement list/tuple filtering
        elif type(filter_by) == str:
            filter = filter_by
            if filter not in ev_cols.values:
                raise ValueError("Filter by not found in evidence_subcategory_type.")
            else:
                filtered_table = evidence_subcategory_table[(evidence_subcategory_table['evidence_subcategory_type'] == filter) | (evidence_subcategory_table['evidence_category_type'] == filter)]
                evidence_ids = filtered_table['evidence_subcategory_id'].tolist()
                binary_model_ids = model_evidence_table[model_evidence_table['evidence_subcategory_id'].isin(evidence_ids)]['binary_model_id'].tolist()

        else:
            raise ValueError("Filter by must be a string, list, or tuple.")
        
    #   2. From the filtered data, select the columns for param1, param2, and param3
    if param1 in bm_cols['column_name'].values:
        query = "SELECT candidate_name AS name, binary_model_id, " + param1 + " FROM binary_model"
        df1 = pd.read_sql(query, conn)
        df1 = df1[df1['binary_model_id'].isin(binary_model_ids)] # Filter
    elif param1 in c_cols['column_name'].values:
        query = "SELECT name, binary_model_id, " + param1 + " FROM candidate"
        df1 = pd.read_sql(query, conn)
        df1 = df1[df1['binary_model_id'].isin(binary_model_ids)]
    else:
        raise ValueError("Parameter 1 not found in either table.")
    if param2 in bm_cols['column_name'].values:
        query = "SELECT candidate_name AS name, binary_model_id, " + param2 + " FROM binary_model"
        df2 = pd.read_sql(query, conn)
        df2 = df2[df2['binary_model_id'].isin(binary_model_ids)]
        hist = False
    elif param2 in c_cols['column_name'].values:
        query = "SELECT name, binary_model_id, " + param2 + " FROM candidate"
        df2 = pd.read_sql(query, conn)
        df2 = df2[df2['binary_model_id'].isin(binary_model_ids)]
        hist = False
    elif param2 == "hist":
        hist = True
    else:
        raise ValueError("Parameter 2 not found in either table.")
    # Optional z data
    if param3 != None:
        if param3 in bm_cols['column_name'].values:
            query = "SELECT candidate_name AS name, binary_model_id, " + param3 + " FROM binary_model"
            df3 = pd.read_sql(query, conn)
            df3 = df3[df3['binary_model_id'].isin(binary_model_ids)]
        elif param3 in c_cols['column_name'].values:
            query = "SELECT name, binary_model_id, " + param3 + " FROM candidate"
            df3 = pd.read_sql(query, conn)
            df3 = df3[df3['binary_model_id'].isin(binary_model_ids)]
        else:
            raise ValueError("Parameter 3 not found in either table.")
    # Optional color data
    if color != None:
        if color in bm_cols['column_name'].values:
            query = "SELECT candidate_name AS name, binary_model_id, " + color + " FROM binary_model"
            df_color = pd.read_sql(query, conn)
            df_color = df_color[df_color['binary_model_id'].isin(binary_model_ids)]
        elif color in c_cols['column_name'].values:
            query = "SELECT name, binary_model_id, " + color + " FROM candidate"
            df_color = pd.read_sql(query, conn)
            df_color = df_color[df_color['binary_model_id'].isin(binary_model_ids)]
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

    # get units
    if param1 == 'eccentricity' or param1 == 'q':
        unit1 = 'unitless'
    elif param1 in ['m1', 'm2', 'mtot', 'mc', 'mu']:
        unit1 = 'Msun'
    elif param1 == 'semimajor_axis' or param1 == 'seperation':
        unit1 = 'pc'
    elif param1 == 'inclination':
        unit1 = 'deg'
    elif param1 == 'period_epoch':
        unit1 = 'MJD'
    elif param1 == 'orb_freq':
        unit1 = 'Hz'
    elif param1 == 'orb_period':
        unit1 = 'yr'

    if param2 == 'eccentricity' or param2 == 'q':
        unit2 = 'unitless'
    elif param2 in ['m1', 'm2', 'mtot', 'mc', 'mu']:
        unit2 = 'Msun'
    elif param2 == 'semimajor_axis' or param2 == 'seperation':
        unit2 = 'pc'
    elif param2 == 'inclination':
        unit2 = 'deg'
    elif param2 == 'period_epoch':
        unit2 = 'MJD'
    elif param2 == 'orb_freq':
        unit2 = 'Hz'
    elif param2 == 'orb_period':
        unit2 = 'yr'

    if param3 != None:
        if param3 == 'eccentricity' or param3 == 'q':
            unit3 = 'unitless'
        elif param3 in ['m1', 'm2', 'mtot', 'mc', 'mu']:
            unit3 = 'Msun'
        elif param3 == 'semimajor_axis' or param3 == 'seperation':
            unit3 = 'pc'
        elif param3 == 'inclination':
            unit3 = 'deg'
        elif param3 == 'period_epoch':
            unit3 = 'MJD'
        elif param3 == 'orb_freq':
            unit3 = 'Hz'
        elif param3 == 'orb_period':
            unit3 = 'yr'
        
    if color != None:
        if color == 'eccentricity' or color == 'q':
            unit_color = 'unitless'
        elif color in ['m1', 'm2', 'mtot', 'mc', 'mu']:
            unit_color = 'Msun'
        elif color == 'semimajor_axis' or color == 'seperation':
            unit_color = 'pc'
        elif color == 'inclination':
            unit_color = 'deg'
        elif color == 'period_epoch':
            unit_color = 'MJD'
        elif color == 'orb_freq':
            unit_color = 'Hz'
        elif color == 'orb_period':
            unit_color = 'yr'

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
    fig.update_yaxes(title=str(param2 + ' (' + unit2 + ')'))
    fig.update_xaxes(title=str(param1 + ' (' + unit1 + ')'))
    if param3 != None:
        fig.update_layout(scene=dict(
            xaxis=dict(title=str(param1 + ' (' + unit1 + ')')),
            yaxis=dict(title=str(param2 + ' (' + unit2 + ')')),
            zaxis=dict(title=str(param3 + ' (' + unit3 + ')'))))
    if color != None:
        fig.update_layout(coloraxis_colorbar=dict(title=str(color + ' (' + unit_color + ')')))

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
    parser.add_argument("-filter_by", "--filter_by", type=str, required=False)
    parser.add_argument("-no_dup_x", "--no_dup_x", type=bool, required=False)
    parser.add_argument("-no_dup_y", "--no_dup_y", type=bool, required=False)
    parser.add_argument("-no_dup_z", "--no_dup_z", type=bool, required=False)
    parser.add_argument("-saveto", "--saveto", type=str, required=False)
    parser.add_argument("-log_x", "--log_x", type=bool, required=False)
    parser.add_argument("-log_y", "--log_y", type=bool, required=False)
    args = parser.parse_args()
    plotter(args.param1, args.param2, args.param3, args.color, args.no_dup_x, args.no_dup_y, args.no_dup_z, args.saveto, args.log_x, args.log_y)
    #python plotter.py -x param1 -y param2 [hist] -z param3 -color color -no_dup_x True -no_dup_y True -no_dup_z True -saveto path -log_x True -log_y True
