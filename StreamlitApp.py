# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# Import required packages
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Define required function to find steps in data
def find_steps(data):
    data['diff'] = np.gradient(data[1])
    data['diffmagnitude'] = np.absolute(df['diff'])
    max_step = data['diffmagnitude'].max()
    #step_position = data[data['diffmagnitude'] == max_step]
    step_positions = data[data['diffmagnitude'] >= 0.85 * max_step]
    return step_positions

def find_steps_max(data):
    step_positions = find_steps(data)
    if len(step_positions) > 1:
        order = 0
        step_positions['order_list'] = np.nan
        for x in range (1, len(step_positions)):
            compare = step_positions.iloc[x,0] - step_positions.iloc[x-1,0]
            if compare >= 0.004:
                order += 1
            step_positions['order_list'].iloc[x] = order
        median = []
        for x in step_positions['order_list'].unique():
            subset_median = step_positions[step_positions['order_list'] == x][0].median()
            median.append(round(subset_median,3))
        steps = step_positions[step_positions[0].isin(median)]
        return steps
    else:
        return step_positions

def detect_step_error(data):
    steps = find_steps_max(data)
    for x in range(0, len(steps)-1):
        compare = steps.iloc[x+1,0] - steps.iloc[x,0]
        if compare <= 0.02:
            steps = steps.iloc[x:x+2,0:2]
    return steps

def level_data(data):
    steps = find_steps_max(data)
    fitline = data[data[0]<=(0.75*steps.iloc[0,0])]
    equationofline = np.polyfit(fitline[0], fitline[1], 1)
    data['fitlinedata'] = (equationofline[0]*df[0])+equationofline[1]
    data['leveldata'] = data[1]-data['fitlinedata']
    return data['leveldata']

# App initialize
st.title('Profilometry Data')
uploaded_file = st.file_uploader("Choose a file", type=['txt'])
chart = st.empty()


if uploaded_file is not None:
    
    # Import data
    df = pd.read_csv(uploaded_file, header = None, delimiter='\t')
    #st.dataframe(df.head()) - print first 5 lines of data

    # Plot raw data
    fig, ax = plt.subplots()
    ax.plot(df[0], df[1])
    ax.set_title('Raw Data')
    ax.set_xlabel('Position (mm)')
    ax.set_ylabel('Step height (um)')
    chart.pyplot(fig)
    
    # Detect steps
    steps = find_steps_max(df)
    ax.set_title('Steps Detected')
    for i in range(0, len(steps)):
        ax.axvline(x=steps.iloc[i,0], color = 'r')
    chart.pyplot(fig)
    error_steps = detect_step_error(df)
    if not steps.equals(error_steps):
        st.warning('Some steps are too close for an accurate step height to be determined.')
        st.dataframe(error_steps)
    
    # Level data
    df['leveldata'] = level_data(df)
    fig, ax = plt.subplots()
    ax.plot(df[0], df['leveldata'])
    ax.set_title('Levelled Data')
    ax.set_xlabel('Position (mm)')
    ax.set_ylabel('Step height (um)')
    st.pyplot(fig)
        
    # Calculate step height of levelled data
    percent_data = st.slider('% Step for calculation', 0.0, 1.0, 0.75)
    if len(steps) > 1:
        step1 = df[df['Position'] <= (0.75*steps.iloc[0,0])]
        step2 = df[(df['Position'] >= (1.25*steps.iloc[0,0])) & (df['Position'] <= (0.75*steps.iloc[1,0]))]
        parameters = {'Step Height 0': np.absolute(step1['leveldata'].mean() - step2['leveldata'].mean())}
        for i in range(1, len(steps)):
            if i == len(steps)-1:
                st.write(i)
                stepx = df[(df['Position'] >= (1.25*steps.iloc[i,0])) & (df['Position'] <= (0.75*steps.iloc[i+1,0]))]
                stepy = df[df['Position'] >= (1.25*steps.iloc[i+1,0])]
                parameters["Step Height {0}".format(i)] = np.absolute(stepx['leveldata'].mean() - stepy['leveldata'].mean())
            else:
                st.write(i)
                stepx = df[(df['Position'] >= (1.25*steps.iloc[i-1,0])) & (df['Position'] <= (0.75*steps.iloc[i,0]))]
                stepy = df[(df['Position'] >= (1.25*steps.iloc[i,0])) & (df['Position'] <= (0.75*steps.iloc[i+1,0]))]
                parameters["Step Height {0}".format(i)] = np.absolute(stepx['leveldata'].mean() - stepy['leveldata'].mean())

    else:
        step1 = df[df[0] <= (percent_data*steps.iloc[0,0])]
        step2 = df[df[0] >= ((2-percent_data)*steps.iloc[0,0])]
        stepheight = np.absolute(step1['leveldata'].mean() - step2['leveldata'].mean())
        parameters = {'Step height 1': stepheight}
    parameterdf = pd.DataFrame(data= parameters, columns = ['Parameter', 'Value (um)'])
    average_step_height = parameterdf['Value (um)'].mean()
    parameterdf.loc[len(parameterdf)] = ['Average Step Height', average_step_height]
      
      
    # Calculate surface roughness - TIR
    TIR1 = step1['leveldata'].max() - step1['leveldata'].min()
    TIR2 = step2['leveldata'].max() - step2['leveldata'].min()
    parameterdf.loc[len(parameterdf)] = ['TIR level 1', TIR1]
    parameterdf.loc[len(parameterdf)] = ['TIR Level 2', TIR2]
    
    # Calculate surface roughness - Ra
    for i in range(len(step1)):
        step1['deviation'] = np.absolute(step1['leveldata'] - step1['leveldata'].mean())
    Ra1 = step1['deviation'].mean()
    for i in range(len(step2)):
        step2['deviation'] = np.absolute(step2['leveldata'] - step2['leveldata'].mean())
    Ra2 = step2['deviation'].mean()
    parameterdf.loc[len(parameterdf)] = ['Ra 1', Ra1]
    parameterdf.loc[len(parameterdf)] = ['Ra 2', Ra2]
    
    # Calculate surface roughness - RMS
    step1['leveldatasquare'] = step1['leveldata']**2
    RMS1 = np.sqrt(step1['leveldatasquare'].mean())
    step2['leveldatasquare'] = step2['leveldata']**2
    RMS2 = np.sqrt(step2['leveldatasquare'].mean())
    parameterdf.loc[len(parameterdf)] = ['RMS 1', RMS1]
    parameterdf.loc[len(parameterdf)] = ['RMS 2', RMS2]
    
    # Add sidebar with parameter list
    st.sidebar.subheader('Parameters')
    st.sidebar.dataframe(parameterdf)    

    
else:
    st.write('Please Select a File')

   
