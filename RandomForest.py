import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn import metrics
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.model_selection import permutation_test_score, StratifiedKFold
from scipy.spatial import distance_matrix
import matplotlib.pyplot as plt
plt.switch_backend('agg')

from cheminformatics import calc_dist_matrix, calc_D_cutoff, calc_test_distances, binary_stats
from collections import Counter
#from matplotlib.pyplot import cm
#import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import numpy as np
import io
import base64
import plotly.express as px
import math

def RandomForestClassifierTrain(df, positives, balance_data=False):
#X = dataset.iloc[:, 0:4].values
#y = dataset.iloc[:, 4].values
   
    print(positives)
    pos_length=len(positives)
    target_length=df.shape[0]
    cols=df.columns
    df['Target'] = df[[cols[0], cols[1]]].apply("-".join, axis=1)
    if pos_length>0:
        df['outcome'] = [1 if x in positives  else 0 for x in df['Target']]
    features = [x for x in cols if "|" in x]# Separating out the features
    X_train = df.loc[:, features].values# Standardizing  the features
    #X_train = StandardScaler().fit_transform(x)# Fit Transform features
    #y_train = df.loc[:,['outcome']].values# Separating out the target
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    X_train = StandardScaler().fit_transform(X_train)# Fit Transform features(X_train)
    y_train = df['outcome'].to_numpy()
    print(y_train)
    # X_test = StandardScaler().transform(X_test)# Transform features(X_test)
    print('Training set shape: %s' % Counter(y_train))
    # classifier = RandomForestClassifier(n_estimators=20, random_state=0)
    # classifier.fit(X_train, y_train)
    # y_pred = classifier.predict(X_test)

    # print(confusion_matrix(y_test,y_pred))
    # print(classification_report(y_test,y_pred))
    # print(accuracy_score(y_test, y_pred))



    ######

    ##%%time
    # Number of trees in random forest
    n_estimators = [100, 250, 500, 750, 1000]
    max_features = ['auto', 'sqrt']
    criterion = ['gini', 'entropy']
    if balance_data == True:
        class_weight = [None]
    else:
        class_weight = [None,'balanced',
                        {0:.9, 1:.1}, {0:.8, 1:.2}, {0:.7, 1:.3}, {0:.6, 1:.4},
                        {0:.4, 1:.6}, {0:.3, 1:.7}, {0:.2, 1:.8}, {0:.1, 1:.9}]
    random_state = [24]

    # Create the random grid
    param_grid = {'n_estimators': n_estimators,
                'max_features': max_features,
                'criterion': criterion,
                'random_state': random_state,
                'class_weight': class_weight}

    # setup model building
    rf = GridSearchCV(RandomForestClassifier(), param_grid, n_jobs=-1, cv=5, verbose=1)
    rf.fit(X_train, y_train)
    print()
    print('Best params: %s' % rf.best_params_)
    print('Score: %.2f' % rf.best_score_)

    rf_best = RandomForestClassifier(**rf.best_params_, n_jobs=-1)
    rf_best.fit(X_train, y_train)

    # Applicability Domain
    training_distances = calc_dist_matrix(X_train)
    D_cutoff = calc_D_cutoff(training_distances)

    # Params
    cross_val = StratifiedKFold(n_splits=5)
    index = []
    pred = []
    prob = []
    ad = []

    # 5-fold external loop
    for train_index, test_index in cross_val.split(X_train, y_train):
        
        fold_model = rf_best.fit(X_train[train_index], y_train[train_index])
        fold_pred = rf_best.predict(X_train[test_index])
        fold_prob = rf_best.predict_proba(X_train[test_index])
        pred.append(fold_pred)
        prob.append(fold_prob)
        index.append(test_index)
        
        # Estimate AD for each fold
        fold_distances_train = calc_dist_matrix(X_train[train_index])
        fold_D_cutoff = calc_D_cutoff(fold_distances_train)
        fold_distances_test = calc_test_distances(X_train[test_index], X_train[train_index])
        
        fold_cpd_ad = []
        for i in np.arange(0, len(fold_distances_test), 1):
            if fold_distances_test[i] < fold_D_cutoff:
                fold_cpd_ad.append('Inside')
            else:
                fold_cpd_ad.append('Outside')
            
        ad.append(fold_cpd_ad)

    # Prepare results 
    fold_index = np.concatenate(index)    
    fold_pred = np.concatenate(pred)
    print(fold_pred)
    fold_prob = np.concatenate(prob)
    fold_prob = np.amax(fold_prob, axis=1).round(2)
    fold_ad = np.concatenate(ad)
    print('ok1')
    five_fold_dwpc = pd.DataFrame({'Prediction': fold_pred, 'Confidence': fold_prob, 'AD': fold_ad}, index=list(fold_index))
    five_fold_dwpc.AD[five_fold_dwpc.AD == 'Outside'] = np.nan
    five_fold_dwpc.AD[five_fold_dwpc.AD == 'Inside'] = five_fold_dwpc.Prediction
    five_fold_dwpc.sort_index(inplace=True)
    five_fold_dwpc['y_train'] = pd.DataFrame(y_train)

    five_fold_ad = five_fold_dwpc.dropna().astype(int)
    coverage_5f = len(five_fold_ad) / len(five_fold_dwpc)

    # Stats
    dwpc = pd.DataFrame(binary_stats(five_fold_dwpc['y_train'], five_fold_dwpc['Prediction']))
    dwpc['Coverage'] = 1.0
    
    # AD stats
    dwpc_ad = five_fold_dwpc.dropna(subset=['AD']).astype(int)
    coverage_dwpc_ad = len(dwpc_ad['AD']) / len(five_fold_dwpc['y_train'])
    dwpc_ad = pd.DataFrame(binary_stats(dwpc_ad['y_train'], dwpc_ad['AD']))
    dwpc_ad['Coverage'] = round(coverage_dwpc_ad, 2)

    # Print stats
    print('\033[1m' + '5-fold External Cross Validation Statistical Characteristics' + '\n' + '\033[0m')
    dwpc_5f_stats = dwpc.append(dwpc_ad)
    dwpc_5f_stats.set_index([['DWPC', 'DWPC AD']], drop=True, inplace=True)
    print(dwpc_5f_stats)

    permutations = 20
    score, permutation_scores, pvalue = permutation_test_score(rf_best, X_train, y_train,
                                                           cv=5, scoring='balanced_accuracy',
                                                           n_permutations=permutations,
                                                           n_jobs=-1,
                                                           verbose=1,
                                                           random_state=24)
    print('True score = ', score.round(2),
      '\nY-randomization = ', np.mean(permutation_scores).round(2),
      '\np-value = ', pvalue.round(4))

    report = f"5-fold External Cross Validation Statistical Characteristics\n\n\
        True score = {score.round(2)}, \n\
        Y-randomization = {np.mean(permutation_scores).round(2)}, \n\
        p-value = {pvalue.round(4)}"

    # Export stats
    #if len(dwpc_ext) > 0: # If testing on true external set.
        # morgan_stats = pd.concat([morgan, morgan_ad, ext_set_stats, ext_set_stats_ad], axis=0)
        # morgan_stats.set_index([['5-fold CV', '5-fold CV AD', 'Ext. Withheld Set', 'Ext. Withheld Set AD']], drop=True, inplace=True)
        # morgan_stats
    #else:
    dwpc_stats = dwpc_5f_stats.copy()
    dwpc_stats.drop('Kappa', axis=1, inplace=True)
    
    # Transpose morgan_stats
    dwpc_stats_t = dwpc_stats.T
    dwpc_stats_t = dwpc_stats_t.reset_index()
    dwpc_stats_t = dwpc_stats_t.rename(columns={'index': 'Stats'})

    # Make plot
    plt.style.use('seaborn-colorblind')
    fig, ax1 = plt.subplots(figsize=(8,5), dpi=90)

    dwpc_stats_t.plot(kind='bar', ax=ax1, width=0.8)
    ax1.set_xticklabels(labels=dwpc_stats_t['Stats'].tolist(), fontsize=14, rotation=0)
    ax1.axhline(y=.6, color='indianred', ls='dashed')
    #ax1.axhline(y=.4, xmax=0.16, color='indianred', ls='dashed')
    ax1.legend_.remove()
    plt.title('Statistical Characteristics of DWPC Random Forest', fontsize=16)
    ax1.set_yticks(np.arange(0, 1.1, 0.1))
    ax1.tick_params(labelsize=12)

    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, fontsize=12,
            loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=4)
    fig.tight_layout()

    buf = io.BytesIO() # in-memory files
    plt.savefig(buf, bbox_inches='tight', transparent=False, format='png', dpi=300) # save to the above file object
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements

    return "data:image/png;base64,{}".format(data),report