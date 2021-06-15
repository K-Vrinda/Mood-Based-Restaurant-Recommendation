# -*- coding: utf-8 -*-
"""Mood Based Food Recommender.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18WLIKlJUPkVs3KvfLmQ4Koc7r7_eV8zb

# Recommending Restaurants based on User Moods

### User has to tell us his/her mood, we'll recommend him/her a restaurant according to the mood. The moods are stress, laziness, happy, depression, sick, cold weather, hunger, etc. The model works well for age range 15-30 due to the dataset.

### About the Dataset
We are using two datasets. First is Zomato Restaurants Dataset and Second is Food Choices of College Students Dataset.
"""

import nltk
nltk.download('stopwords')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
stopwords = set(STOPWORDS)
import seaborn as sns
from plotly.offline import init_notebook_mode, iplot
init_notebook_mode()
from collections import Counter
from nltk.corpus import stopwords
stop = set(stopwords.words('english'))
stop.update(['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}',''])
from nltk.stem import WordNetLemmatizer

"""## Zomato Restaurants Dataset Analysis (in New Delhi)


"""

res_data = pd.read_csv('/content/zomato.csv', encoding='latin-1')
countryCode_toName = {
    1: "India",
    14: "Australia",
    30: "Brazil",
    37: "Canada",
    94: "Indonesia",
    148: "New Zealand",
    162: "Phillipines",
    166: "Qatar",
    184: "Singapore",
    189: "South Africa",
    191: "Sri Lanka",
    208: "Turkey",
    214: "UAE",
    215: "United Kingdom",
    216: "United States",
}
res_data['Country'] = res_data['Country Code'].apply(lambda x: countryCode_toName[x])

res_data = res_data.loc[(res_data['Country Code'] == 1) & (res_data['City'] == 'New Delhi'), :]
res_data = res_data.loc[res_data['Longitude'] != 0, :]
res_data = res_data.loc[res_data['Latitude'] != 0, :]
res_data = res_data.loc[res_data['Latitude'] < 29] # clearing out invalid outlier
res_data = res_data.loc[res_data['Rating text'] != 'Not rated']
res_data['Cuisines'] = res_data['Cuisines'].astype(str)
res_data['fusion_num'] = res_data['Cuisines'].apply(lambda x: len(x.split(',')))
res_data.info()

"""### What are the most famous cuisines in CHOOSEN CITY?"""

lst_cuisine = set()
Cnt_cuisine = Counter()
for cu_lst in res_data['Cuisines']:
    cu_lst = cu_lst.split(',')
    lst_cuisine.update([cu.strip() for cu in cu_lst])
    for cu in cu_lst:
        Cnt_cuisine[cu.strip()] += 1

cnt = pd.DataFrame.from_dict(Cnt_cuisine, orient = 'index')
cnt.sort_values(0, ascending = False, inplace = True)


tmp_cnt = cnt.head(10)
tmp_cnt.rename(columns = {0:'cnt'}, inplace = True)
with plt.style.context('bmh'):
    f = plt.figure(figsize = (12, 8))
    ax = plt.subplot2grid((2,2), (0,0))
    sns.barplot(x = tmp_cnt.index, y = 'cnt', data = tmp_cnt, ax = ax, palette = sns.color_palette('Blues_d', 10))
    ax.set_title('# Cuisine')
    ax.tick_params(axis='x', rotation=70)
    ax = plt.subplot2grid((2,2), (0,1))
    sns.countplot(res_data['fusion_num'], ax=ax, palette = sns.color_palette('Blues_d', res_data.fusion_num.nunique()))
    ax.set_title('# Cuisine Provided')
    ax.set_ylabel('')
    plt.show()        
print('# Unique Cuisine: ', len(lst_cuisine))

"""### K-Means Clustering - Where are high-rated restaurants located?"""

res_data['Rating category'] = res_data['Rating text'].map({'Not rated': -1, 'Poor':0, 'Average':2, 'Good':3, 'Very Good':4, 'Excellent':5})
tmp = res_data['Aggregate rating'].map(np.round)
a = np.full(tmp.shape[0], False, dtype = bool)
((tmp - res_data['Rating category']).map(np.round)).value_counts()
sys_check = res_data[['Aggregate rating', 'Rating category', 'Votes']].copy()
sys_check['distorted'] = (res_data['Aggregate rating'] - res_data['Rating category']).map(np.round)
sys_check['diff'] = sys_check['Aggregate rating'] - sys_check['Rating category']
res_data = res_data.loc[sys_check['distorted'] != 2, :]
res_data['Rating category'] = res_data['Aggregate rating'].round(0).astype(int)

from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=7, random_state=0).fit(res_data[['Longitude', 'Latitude']])
res_data['pos'] = kmeans.labels_
pop_local = res_data.groupby('pos')['Longitude', 'Latitude', 'Aggregate rating'].agg({'Longitude':np.mean, 'Latitude':np.mean, 'Aggregate rating':np.median}).reset_index()

with plt.style.context('bmh', after_reset=True):
    pal = sns.color_palette('Spectral', 7)
    plt.figure(figsize = (8,6))
    for i in range(7):
        ix = res_data.pos == i
        plt.scatter(res_data.loc[ix, 'Latitude'], res_data.loc[ix, 'Longitude'], color = pal[i], label = str(i))
        plt.text(pop_local.loc[i, 'Latitude'], pop_local.loc[i, 'Longitude'], str(i) + ': '+str(pop_local.loc[i, 'Aggregate rating'].round(2)), fontsize = 14, color = 'black')
    plt.title('Location-wise Restaurant Median Rating in New Delhi')
    plt.legend()
    plt.show()

"""Here we can see that Central Delhi has slight better restaurants than North or South Suburb areas of Delhi.

## Food Choices Dataset Analysis
"""

food_data = pd.read_csv('/content/food_choices.csv')
food_data.info()

"""### What are some comfort food in various situations such as stress, boredom, hunger, happiness?"""

food_data[['comfort_food_reasons', 'comfort_food']]

def search_comfort(mood):
    lemmatizer = WordNetLemmatizer()
    foodcount = {}
    for i in range(124):
        temp = [temps.strip().replace('.','').replace(',','').lower() for temps in str(food_data["comfort_food_reasons"][i]).split(' ') if temps.strip() not in stop ]
        if mood in temp:
            foodtemp = [lemmatizer.lemmatize(temps.strip().replace('.','').replace(',','').lower()) for temps in str(food_data["comfort_food"][i]).split(',') if temps.strip() not in stop ]
            for a in foodtemp:
                if a not in foodcount.keys():
                    foodcount[a] = 1 
                else:
                    foodcount[a] += 1
    sorted_food = []
    sorted_food = sorted(foodcount, key=foodcount.get, reverse=True)
    return sorted_food


def find_my_comfort_food(mood):
    topn = []
    topn = search_comfort(mood) #function create dictionary only for particular mood
    print("5 Popular Comfort Foods in %s are:"%(mood))
    for i in range(5):
      print(topn[i])

    
    #print(topn[1])
    #print(topn[2])
    #print(topn[3])
    #print(topn[4])

import nltk
nltk.download('wordnet')
find_my_comfort_food('happy')

"""## Main Part of our Project: Suggesting Restaurants based on User Moods
##### Under Following Moods
* stress
* boredom
* depression/sadness
* hunger
* laziness
* cold weather
* happiness 
* watching tv

### Finding Restaurants based on cuisines
"""

res_data[res_data.Cuisines.str.contains('pizza', case=False)].sort_values(by='Aggregate rating', ascending=False).head(5)