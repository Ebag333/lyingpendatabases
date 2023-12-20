import matplotlib.colors as mplc
import numpy as np
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Post-2002 Dead Sea Scrolls-like Fragments",
    page_icon='assets/Icon.png'
)

def five_colors():
    return ['#262622', '#D98E32', '#8C503A', '#D98162', '#D9AB9A']

def align(text, alignment='left'):
    return '<div style="text-align:' + alignment + '>' + text + '</div>'

def format_markdown_list(col, cell, delimiter='', ordered=False):
    items = cell.split(delimiter)
    output = ''
    if len(items) > 1:
        output = '<ol>' if ordered else '<ul>'
        for item in items:
            if not item.isspace():
                output += '<li>' + item + '</li>'
        output += '</ol>' if ordered else '</ul>'
    else:
        output = items[0]
    format_markdown_longline(col, output)

def format_markdown_longline(col, cell):
    st.markdown('**' + col + ':** <br>' + str(cell), unsafe_allow_html=True)

def format_markdown_shortline(col, cell):
    st.markdown('**' + col + ':** ' + str(cell), unsafe_allow_html=True)

def format_markdown_purchase(col, cell):
    bold, reg = col.split('\n')
    st.markdown(
        '**' + bold + '** (' + reg + ')**:** <br>' + str(cell), 
        unsafe_allow_html=True)
    
def format_markdown_orcid(orcid):
    return '<sup>[![](https://info.orcid.org/wp-content/uploads/2019/11/'\
        'orcid_16x16.png)](https://orcid.org/' + orcid + ')</sup>'

def format_markdown(col_names, row, skip=0, searchres=False):
    col_stop = -2 # To not include content and canonical grouping information
    sale_exist = False
    for col, cell in zip(col_names[skip:col_stop], row[skip+1:col_stop]):
        if not pd.isna(cell):
            cell = cell.replace('$', '\$')
            if col.lower().startswith('purchase'):
                format_markdown_purchase(col, cell)
            elif col.lower().startswith('asking'):
                format_markdown_longline(col, cell)
            elif col.lower().startswith('sale'):
                format_markdown_longline(col, cell)
                sale_exist = True
            elif col.lower() == 'sources':
                format_markdown_list(
                    col, cell, delimiter='\n\n', ordered=False)
            else:
                if len(cell) < 50:
                    format_markdown_shortline(col, cell)
                else:
                    format_markdown_longline(col, cell)
        else:
            if col.lower().startswith('purchase') and sale_exist:
                format_markdown_purchase(col, 'Unknown')
            elif col.lower().startswith('asking') and sale_exist:
                format_markdown_longline(col, 'Unknown')


def content(df):
    groups = [g.split(', ') for g in df['Composition'].unique()]
    groups.sort(key=lambda x: int(x[1]))

    # content_histogram(sub_df, groups)

    options = [x[0] for x in groups]
    content_selected = st.selectbox(
        'Select a composition', options=options)
    st.write('##')
    hits = st.empty()

    results = df.loc[df['Composition'].str.startswith(content_selected)]
    for row in results.itertuples():
        with st.expander(row.Content):
            format_markdown(list(df.columns.values), row, skip=2)
            
    counter = len(results)
    if counter == 0:
        txt = ':red[No entries found]'
    else:
        txt = ':blue[' + str(counter) + ' of ' + str(len(df)) + ' hits]'
    hits.markdown(txt, unsafe_allow_html=True)
                

def search(df):
    df1 = df.copy()

    post_query = str(st.text_input('Enter query', ''))
    st.write('##')
    hits = st.empty()

    txt = ''
    counter = 0
    if len(post_query) > 0:
        mask = np.column_stack(
            [df1[col].str.contains(post_query, case=False, na=False) \
             for col in df1])
        print(mask)
        results = df1.loc[mask.any(axis=1)]
        counter = len(results)

        for res in results.itertuples():
            with st.expander(res.Content):
                format_markdown(df1.columns.values, res, skip=2)

        if counter == 0:
            txt = ':red[No entries found]'
        else:
            txt = ':blue[' + str(counter) + ' of ' + str(len(df1)) + ' hits]'

    hits.markdown(txt, unsafe_allow_html=True)


def get_rgba_hex(color_array, alpha=.8):
    '''
    To convert add transparencies to given color array
    '''
    ishex = True if color_array[0].startswith('#') else False
    rgba_tuples, hex = [], []
    rgb = None
    if ishex:
        rgb = np.array([mplc.to_rgb(x) for x in color_array]) * 255
        hex = color_array.copy()
    else:
        rgblist = []
        for rgbstr in color_array:
            rgblist.append([int(x)/255. for x in rgbstr[4:-1].split(', ')])
        rgb = np.array(rgblist) * 255.
        hex = [mplc.to_hex(x).upper() for x in rgblist]

    for x in rgb:
        rgba_tuples.append(
            'rgba(' + ','.join([str(int(i)) for i in x[:3]]) + \
            ',' + str(alpha) + ')')
        
    return rgba_tuples, hex


def gallery_histogram(sub_df, groups):
    data = []
    for val, cnt in df['Composition'].value_counts().items():
        label, order = val.split(', ')
        canon = sub_df[sub_df['Composition'] == val].iloc[0]['Canonical Categorisation']
        data.append([int(order), label, cnt, canon])
    data.sort(key=lambda x: int(x[0]))
    data = np.array(data)[:, 1:]
    
    # Plot chart
    bar = pd.DataFrame(
        {'Composition':data[:, 0], 'Number of fragments':data[:, 1],
         'Canonical Categorisation':data[:, 2]})
    fig = px.bar(
        bar, x='Composition', y='Number of fragments', 
        color='Canonical Categorisation', title='Textual distribution of Post-2002 Fragments',
        color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(range=[0, 13])
    fig.update_layout(font_family='sans-serif')
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        'This diagram shows the distribution of the post-2002 fragments according to '\
        'their textual content. Nearly 90\% of fragments with recognisable content fe'\
        'ature text found in the Old Testament. There are also fragments which have b'\
        'een identified with non-biblical Qumran manuscripts. 11 fragments have text '\
        'that is not identified.'
    )
    st.write('##')


def gallery_sankey(sankeydf):
    # The operation '|' is a set union
    set_nodes = set(sankeydf['Seller']) | set(sankeydf['Buyer'])
    dict_nodes = dict(zip(set_nodes, np.arange(len(set_nodes))))

    cmap_colors = [x for x in px.colors.qualitative.T10_r]
    rgba, hex = get_rgba_hex(cmap_colors, alpha=0.8)

    source, target, count = [], [], []
    sankeynp = sankeydf.to_numpy()
    for i in range(len(sankeynp)):
        row = sankeynp[i, :]
        source.append(dict_nodes[row[0]])
        target.append(dict_nodes[row[1]])
        count.append(int(row[2]))
    fig = go.Figure(data=[go.Sankey(
        arrangement = 'snap',
        node = {"label": list(set_nodes), "thickness":35, "pad":10,
                "color": [hex[i % len(hex)] for i in np.arange(len(set_nodes))],},
        link = {"source": source, "target": target, "value": count,#}
                "color": [rgba[i % len(hex)] for i in source],
                "sourcesrc": 'Seller'}
    )])
    fig.update_layout(
        title_text='Flow diagram of sales and donations of Post-2002 Fragments', 
        font_family='sans-serif', height=600)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        'This diagram visualizes the change of hands of Post-2002 Fragments, including s'\
        'ales and donations. For example, hovering the flow between William Kando and Sc'\
        'høyen Collection will show the number 22.0, "source: William Kando", and "targe'\
        't: Schøyen Collection". This means that there has been 22 purchases from the Sc'\
        'høyen Collection from William Kando. Note that this visualisation emphasizes fl'\
        'ow and not time. Representatives in a sale is also not visualised in this diagr'\
        'am. Hovering over the node of William Kando, we can see the number 55.0, "incom'\
        'ing flow count: 0", and "outgoing flow count: 12". This is to be interpreted as'\
        ' Kando has sold or donated 55 times, to 12 different people and/or institutions'\
        '. Zero incoming flow count means that all the 55 items were traced back to him.'
    )
    st.caption(
        '**Abbreviations:** \n - APU: Azusa Pacific University \n - ATS: Ashland Theolog'\
        'ical Seminary \n - FJCO: Foundation on Judaism and Christian Origin \n - LMI: L'\
        'egacy Ministries International \n - NCF: National Christian Foundation \n - SWB'\
        'TS: Southwestern Baptist Theological Seminary', unsafe_allow_html=True)
    st.write('##')


def gallery():
    sub_df = df[['Composition', 'Canonical Categorisation']]
    groups = [g.split(', ') for g in df['Composition'].unique()]
    groups.sort(key=lambda x: int(x[1]))
    gallery_histogram(sub_df, groups)

    st.divider()

    sankeyf = os.getcwd() + '/data/post2002-sankeyvis-changeofhands.csv'
    sankeydf = pd.read_csv(sankeyf, sep=';', encoding='utf-8')
    gallery_sankey(sankeydf)

    st.divider()
    

def overview(df):
    st.markdown(
        'In the table below, you can browse our database in its entirety. Note that an'\
        ' option to view the table as a full page will show up on the top right of the'\
        ' table when you hover the table.', unsafe_allow_html=True)
    df1 = df.copy()
    st.dataframe(df1.iloc[:, :-2], hide_index=True)


dbf = os.getcwd() + '/data/post2002DB-v3.xlsx'
df = pd.read_excel(dbf, dtype=str)

# Selection of columns to show and process in this page
cols = list(range(0, 21))
cols = [x for x in cols if x not in [1]]
df = df.iloc[:, cols]

st.header('The Post-2002 Dead Sea Scrolls-like fragments')

authors = 'Ludvik A. Kjeldsberg ' + format_markdown_orcid('0000-0001-5268-4983') + ', '
authors += 'Årstein Justnes ' + format_markdown_orcid('0000-0001-6448-0507') + ', and '
authors += 'Hilda Deborah ' + format_markdown_orcid('0000-0003-3779-2569')
st.markdown('By ' + authors, unsafe_allow_html=True)
st.markdown('##')

ftitle = open('assets/texts/lp_post_intro.txt', 'r')
st.markdown(
    '<div style="text-align: justify;">'+ftitle.read()+'</div>', unsafe_allow_html=True)
st.markdown('##')

tabs = st.tabs(['Overview', 'Filter textual content', 'Visualisation gallery', 'Search'])


tab_overview = tabs[0]
with tab_overview:
    st.write('##')
    overview(df)

tab_content = tabs[1]
with tab_content:
    st.write('##')
    content(df)

tab_gallery = tabs[2]
with tab_gallery:
    st.write('##')
    gallery()

tab_search = tabs[3]
with tab_search:
    st.write('##')
    search(df)