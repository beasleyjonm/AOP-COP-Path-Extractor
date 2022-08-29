import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
#from matplotlib.pyplot import cm
#import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import numpy as np
#import io
#import base64
import plotly.express as px
import math

def first_n_digits(num, n):
    return num // 10 ** (int(math.log(num, 10)) - n + 1)

def performPCA(df,positives,dimensions):
    print(positives)
    pos_length=len(positives)
    target_length=df.shape[0]
    cols=df.columns
    df['Target'] = df[[cols[0], cols[1]]].apply("-".join, axis=1)
    if pos_length>0:
        df['outcome'] = ["1" if x in positives else "0" for x in df['Target']]
    features = [x for x in cols if "|" in x]# Separating out the features
    x = df.loc[:, features].values# Standardizing  the features
    #y = df.loc[:,['target']].values# Separating out the target
    x = StandardScaler().fit_transform(x)

    pca = PCA(n_components=dimensions)
    principalComponents = pca.fit_transform(x)
    expVariance = pca.explained_variance_ratio_
    if dimensions==2:
        pc1_var="{:.2f}".format(expVariance[0])
        pc2_var="{:.2f}".format(expVariance[1])
        principalDf = pd.DataFrame(data=principalComponents,columns=['PC1','PC2'])
        if pos_length>0:
            pcaData = pd.concat([principalDf,df[['Target','outcome']]],axis = 1)
        else:
            pcaData = pd.concat([principalDf,df[['Target']]],axis = 1)
        print(pcaData)
        plotly_fig = px.scatter(data_frame=pcaData,
                                x=f"PC1",
                                y=f"PC2",
                                color="outcome" if pos_length>0 else "Target",
                                hover_data={"Target":True},
                                labels=dict(PC1=f"PC1 (Variance:{pc1_var})",
                                            PC2=f"PC2 (Variance:{pc2_var})",
                                            outcome="Target Class"))
    if target_length<=1000:
        if dimensions==3:        
            pc1_var="{:.2f}".format(expVariance[0])
            pc2_var="{:.2f}".format(expVariance[1])
            pc3_var="{:.2f}".format(expVariance[2])
            principalDf = pd.DataFrame(data=principalComponents,columns=['PC1','PC2','PC3'])
            if pos_length>0 == False:
                pcaData = pd.concat([principalDf,df[['Target','outcome']]],axis = 1)
            else:
                pcaData = pd.concat([principalDf,df[['Target']]],axis = 1)
            print(pcaData)
            plotly_fig = px.scatter_3d(data_frame=pcaData,
                                    x=f"PC1",
                                    y=f"PC2",
                                    z=f"PC3",
                                    color="outcome" if pos_length>0 else "Target",
                                    hover_data={"Target":True},
                                    labels=dict(PC1=f"PC1 (Variance:{pc1_var})",
                                                PC2=f"PC2 (Variance:{pc2_var})",
                                                PC3=f"PC3 (Variance:{pc3_var})",
                                                outcome="Target Class"))
    else:
        return ""
    if target_length>10:
        plotly_fig.update_layout(showlegend=False)
    return plotly_fig
    # fig = plt.figure(figsize = (8,8))
    # ax = fig.add_subplot(1,1,1) 
    # ax.set_xlabel(f"Principal Component 1; Variance:{expVariance[0]}", fontsize = 15)
    # ax.set_ylabel(f"Principal Component 2; Variance:{expVariance[1]}", fontsize = 15)
    # ax.set_title('2 component PCA', fontsize = 20)
    # targets = [x for x in pcaData['target']]
    # colors = cm.rainbow(np.linspace(0, 1, len(targets)))
    # for target, color in zip(targets,colors):
    #     indicesToKeep = pcaData['target'] == target
    #     ax.scatter(pcaData.loc[indicesToKeep, 'principal component 1']
    #             , pcaData.loc[indicesToKeep, 'principal component 2']
    #             , color = color
    #             , s = 50)
    #     if use_labels==True:
    #         plt.text(pcaData.loc[indicesToKeep, 'principal component 1']
    #                 , pcaData.loc[indicesToKeep, 'principal component 2']
    #                 , target
    #                 , fontsize=10)
    # ax.legend(targets)#, loc='center left', bbox_to_anchor=(1, 0.5))
    # ax.grid()
    
    # buf = io.BytesIO() # in-memory files
    # plt.savefig(buf, format = "png") # save to the above file object
    # plt.close()
    # data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements

    # return "data:image/png;base64,{}".format(data)