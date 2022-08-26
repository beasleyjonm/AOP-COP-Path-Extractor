import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

def performPCA(df,dimensions):
    print(df.columns)
    cols=df.columns
    df['target'] = df[[cols[0], cols[1]]].apply("-".join, axis=1)
    features = [x for x in cols if "|" in x]# Separating out the features
    x = df.loc[:, features].values# Separating out the target
    y = df.loc[:,['target']].values# Standardizing the features
    x = StandardScaler().fit_transform(x)

    pca = PCA(n_components=dimensions)
    principalComponents = pca.fit_transform(x)
    expVariance = pca.explained_variance_ratio_

    principalDf = pd.DataFrame(data=principalComponents,columns=['principal component 1','principal component 2'])
    finalDf = pd.concat([principalDf,df[['target']]],axis = 1)

    return [finalDf,expVariance]

def visualizePCA(pcaData,expVariance):
    fig = plt.figure(figsize = (8,8))
    ax = fig.add_subplot(1,1,1) 
    ax.set_xlabel(f"Principal Component 1; Variance:{expVariance[0]}", fontsize = 15)
    ax.set_ylabel(f"Principal Component 2; Variance:{expVariance[1]}", fontsize = 15)
    ax.set_title('2 component PCA', fontsize = 20)
    targets = [x for x in pcaData['target']]
    color = cm.rainbow(np.linspace(0, 1, len(targets)))
    for target, color in zip(targets,color):
        indicesToKeep = pcaData['target'] == target
        ax.scatter(pcaData.loc[indicesToKeep, 'principal component 1']
                , pcaData.loc[indicesToKeep, 'principal component 2']
                , c = color
                , s = 50)
    ax.legend(targets)
    ax.grid()

    buf = io.BytesIO() # in-memory files
    plt.savefig(buf, format = "png") # save to the above file object
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements

    return "data:image/png;base64,{}".format(data)