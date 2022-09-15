# Author: Vinicius Alves <viniciusm.alves@gmail.com>
# Cheminformatics package v. 2.0
# License: BSD 3 clause

import pandas as pd
import numpy as np
from math import floor
#from rdkit import Chem
from scipy.spatial import distance_matrix
from sklearn import metrics
#from rdkit.Chem import Descriptors, Crippen, MolSurf, Lipinski, Fragments, EState, GraphDescriptors

#Define External Test Set
'''
def DefineExternalSet(df, act_column, sim_thresh):
    # Calculate descriptors
    def calcfp(mol,funcFPInfo=dict(radius=3, nBits=2048, useFeatures=False, useChirality=False)):
        fp = Chem.AllChem.GetMorganFingerprintAsBitVect(mol, **funcFPInfo)
        return fp
    df['fp'] = df['Mol'].apply(calcfp)
    df['Outcome'] = df[act_column].astype(int)
    dataset_size = df.size
'''
# Balance by Similarity
'''
def BalanceBySim(df, act_column, sim_thresh):
    # Calculate descriptors
    def calcfp(mol,funcFPInfo=dict(radius=3, nBits=2048, useFeatures=False, useChirality=False)):
        fp = Chem.AllChem.GetMorganFingerprintAsBitVect(mol, **funcFPInfo)
        return fp
    
    df['fp'] = df['Mol'].apply(calcfp)
    df['Outcome'] = df[act_column].astype(int)

    # Define larger class
    bigger_class = df.loc[df.Outcome == 0].copy()
    smaller_class = df.loc[df.Outcome == 1].copy()
    if len(smaller_class) > len(bigger_class):
        bigger_class, smaller_class = smaller_class, bigger_class

    comparison = smaller_class.fp.tolist()

    select_size = int(floor(len(smaller_class)/sim_thresh))

    bigger_class['Max_Tanimoto_Sim'] = bigger_class['fp'].apply(lambda x: max([Chem.DataStructs.TanimotoSimilarity(x, comparison[i]) for i in range(len(comparison))]))
    bigger_class.sort_values(by='Max_Tanimoto_Sim', ascending=False, inplace=True)
    bigger_class.reset_index(drop=False, inplace=True)

    bigger_closest = bigger_class.loc[:select_size,'index'].tolist()
    second_half_selection = np.linspace(start=select_size+1, stop=len(bigger_class), endpoint=False, num=select_size, dtype='int')
    bigger_linear = [int(_) for _ in bigger_class.loc[second_half_selection,'index'].tolist()]

    fp_bal = smaller_class.index.tolist() + bigger_closest + bigger_linear

    df = df.drop(['fp'], axis=1)
    df['Set'] = np.where(df.index.isin(fp_bal), 'train', 'ext')

    return df
'''

# Applicability Domain

def calc_dist_matrix(training_descriptors):
    return np.sort(distance_matrix(training_descriptors, training_descriptors), axis=1)[:,1:]
    
def calc_D_cutoff(distance_matrix, user_cutoff=0.5):
    average_dist = np.mean(distance_matrix, axis=None)
    std_dev = np.std(distance_matrix, axis=None)
    return (average_dist + user_cutoff * std_dev)

def calc_test_distances(testing_descriptors, training_descriptors):
    test_distances = np.sort(distance_matrix(testing_descriptors, training_descriptors), axis=1)[:,1:]
    average_test_dist = np.mean(test_distances, axis=1)
    return average_test_dist
    

# Calculate statistics

def binary_stats(y_train, y_pred):
    confusion_matrix = metrics.confusion_matrix(y_train, y_pred, labels=[0,1])
    Kappa = metrics.cohen_kappa_score(y_train, y_pred, weights='linear')
    # True and false values
    TN, FP, FN, TP = confusion_matrix.ravel()
    # Sensitivity, hit rate, recall, or true positive rate
    SE = TP/(TP+FN)
    # Specificity or true negative rate
    SP = TN/(TN+FP)
    # Precision or positive predictive value
    PPV = TP/(TP+FP)
    # Negative predictive value
    NPV = TN/(TN+FN)
    # Correct classification rate
    CCR = (SE + SP)/2
    d = dict({'Kappa': Kappa,
        'CCR': CCR,
        'Sensitivity': SE,
        'PPV': PPV,
        'Specificity': SP,
        'NPV': NPV})
    return pd.DataFrame(d, columns=d.keys(), index=[0]).round(2)
    
# Calculate continuous stats
def continuous_stats(y_train, y_pred):
    press = np.sum((y_pred - y_train)**2)
    tss = np.sum((y_train - y_train.mean())**2)
    return 1-(press/tss)
    

#pred_test = rf.predict(X_test)

#print("q2:", metrics.r2_score(y_test, pred_test).round(2))
#print("MSE:", metrics.mean_squared_error(y_test, pred_test).round(2))
#print("MAE:", metrics.mean_absolute_error(y_test, pred_test).round(2))

# Calculate RDKit descriptors
'''  
def calc_rdkit(mol):
    descriptors = pd.Series(np.array([Crippen.MolLogP(mol),
                                    Crippen.MolMR(mol),
                                    Descriptors.FpDensityMorgan1(mol),
                                    Descriptors.FpDensityMorgan2(mol),
                                    Descriptors.FpDensityMorgan3(mol),
                                    Descriptors.FractionCSP3(mol),
                                    Descriptors.HeavyAtomMolWt(mol),
                                    Descriptors.MaxAbsPartialCharge(mol),
                                    Descriptors.MaxPartialCharge(mol),
                                    Descriptors.MinAbsPartialCharge(mol),
                                    Descriptors.MinPartialCharge(mol),
                                    Descriptors.MolWt(mol),
                                    Descriptors.NumRadicalElectrons(mol),
                                    Descriptors.NumValenceElectrons(mol),
                                    EState.EState.MaxAbsEStateIndex(mol),
                                    EState.EState.MaxEStateIndex(mol),
                                    EState.EState.MinAbsEStateIndex(mol),
                                    EState.EState.MinEStateIndex(mol),
                                    EState.EState_VSA.EState_VSA1(mol),
                                    EState.EState_VSA.EState_VSA10(mol),
                                    EState.EState_VSA.EState_VSA11(mol),
                                    EState.EState_VSA.EState_VSA2(mol),
                                    EState.EState_VSA.EState_VSA3(mol),
                                    EState.EState_VSA.EState_VSA4(mol),
                                    EState.EState_VSA.EState_VSA5(mol),
                                    EState.EState_VSA.EState_VSA6(mol),
                                    EState.EState_VSA.EState_VSA7(mol),
                                    EState.EState_VSA.EState_VSA8(mol),
                                    EState.EState_VSA.EState_VSA9(mol),
                                    Fragments.fr_Al_COO(mol),
                                    Fragments.fr_Al_OH(mol),
                                    Fragments.fr_Al_OH_noTert(mol),
                                    Fragments.fr_aldehyde(mol),
                                    Fragments.fr_alkyl_carbamate(mol),
                                    Fragments.fr_alkyl_halide(mol),
                                    Fragments.fr_allylic_oxid(mol),
                                    Fragments.fr_amide(mol),
                                    Fragments.fr_amidine(mol),
                                    Fragments.fr_aniline(mol),
                                    Fragments.fr_Ar_COO(mol),
                                    Fragments.fr_Ar_N(mol),
                                    Fragments.fr_Ar_NH(mol),
                                    Fragments.fr_Ar_OH(mol),
                                    Fragments.fr_ArN(mol),
                                    Fragments.fr_aryl_methyl(mol),
                                    Fragments.fr_azide(mol),
                                    Fragments.fr_azo(mol),
                                    Fragments.fr_barbitur(mol),
                                    Fragments.fr_benzene(mol),
                                    Fragments.fr_benzodiazepine(mol),
                                    Fragments.fr_bicyclic(mol),
                                    Fragments.fr_C_O(mol),
                                    Fragments.fr_C_O_noCOO(mol),
                                    Fragments.fr_C_S(mol),
                                    Fragments.fr_COO(mol),
                                    Fragments.fr_COO2(mol),
                                    Fragments.fr_diazo(mol),
                                    Fragments.fr_dihydropyridine(mol),
                                    Fragments.fr_epoxide(mol),
                                    Fragments.fr_ester(mol),
                                    Fragments.fr_ether(mol),
                                    Fragments.fr_furan(mol),
                                    Fragments.fr_guanido(mol),
                                    Fragments.fr_halogen(mol),
                                    Fragments.fr_hdrzine(mol),
                                    Fragments.fr_hdrzone(mol),
                                    Fragments.fr_HOCCN(mol),
                                    Fragments.fr_imidazole(mol),
                                    Fragments.fr_imide(mol),
                                    Fragments.fr_Imine(mol),
                                    Fragments.fr_isocyan(mol),
                                    Fragments.fr_isothiocyan(mol),
                                    Fragments.fr_ketone(mol),
                                    Fragments.fr_ketone_Topliss(mol),
                                    Fragments.fr_lactam(mol),
                                    Fragments.fr_lactone(mol),
                                    Fragments.fr_methoxy(mol),
                                    Fragments.fr_morpholine(mol),
                                    Fragments.fr_N_O(mol),
                                    Fragments.fr_Ndealkylation1(mol),
                                    Fragments.fr_Ndealkylation2(mol),
                                    Fragments.fr_NH0(mol),
                                    Fragments.fr_NH1(mol),
                                    Fragments.fr_NH2(mol),
                                    Fragments.fr_Nhpyrrole(mol),
                                    Fragments.fr_nitrile(mol),
                                    Fragments.fr_nitro(mol),
                                    Fragments.fr_nitro_arom(mol),
                                    Fragments.fr_nitro_arom_nonortho(mol),
                                    Fragments.fr_nitroso(mol),
                                    Fragments.fr_oxazole(mol),
                                    Fragments.fr_oxime(mol),
                                    Fragments.fr_para_hydroxylation(mol),
                                    Fragments.fr_phenol(mol),
                                    Fragments.fr_phenol_noOrthoHbond(mol),
                                    Fragments.fr_phos_acid(mol),
                                    Fragments.fr_phos_ester(mol),
                                    Fragments.fr_piperdine(mol),
                                    Fragments.fr_piperzine(mol),
                                    Fragments.fr_priamide(mol),
                                    Fragments.fr_prisulfonamd(mol),
                                    Fragments.fr_pyridine(mol),
                                    Fragments.fr_quatN(mol),
                                    Fragments.fr_SH(mol),
                                    Fragments.fr_sulfide(mol),
                                    Fragments.fr_sulfonamd(mol),
                                    Fragments.fr_sulfone(mol),
                                    Fragments.fr_term_acetylene(mol),
                                    Fragments.fr_tetrazole(mol),
                                    Fragments.fr_thiazole(mol),
                                    Fragments.fr_thiocyan(mol),
                                    Fragments.fr_thiophene(mol),
                                    Fragments.fr_unbrch_alkane(mol),
                                    Fragments.fr_urea(mol),
                                    GraphDescriptors.BalabanJ(mol),
                                    GraphDescriptors.BertzCT(mol),
                                    GraphDescriptors.Chi0(mol),
                                    GraphDescriptors.Chi0n(mol),
                                    GraphDescriptors.Chi0v(mol),
                                    GraphDescriptors.Chi1(mol),
                                    GraphDescriptors.Chi1n(mol),
                                    GraphDescriptors.Chi1v(mol),
                                    GraphDescriptors.Chi2n(mol),
                                    GraphDescriptors.Chi2v(mol),
                                    GraphDescriptors.Chi3n(mol),
                                    GraphDescriptors.Chi3v(mol),
                                    GraphDescriptors.Chi4n(mol),
                                    GraphDescriptors.Chi4v(mol),
                                    GraphDescriptors.HallKierAlpha(mol),
                                    GraphDescriptors.Ipc(mol),
                                    GraphDescriptors.Kappa1(mol),
                                    GraphDescriptors.Kappa2(mol),
                                    GraphDescriptors.Kappa3(mol),
                                    Lipinski.HeavyAtomCount(mol),
                                    Lipinski.NHOHCount(mol),
                                    Lipinski.NOCount(mol),
                                    Lipinski.NumAliphaticCarbocycles(mol),
                                    Lipinski.NumAliphaticHeterocycles(mol),
                                    Lipinski.NumAliphaticRings(mol),
                                    Lipinski.NumAromaticCarbocycles(mol),
                                    Lipinski.NumAromaticHeterocycles(mol),
                                    Lipinski.NumAromaticRings(mol),
                                    Lipinski.NumHAcceptors(mol),
                                    Lipinski.NumHDonors(mol),
                                    Lipinski.NumHeteroatoms(mol),
                                    Lipinski.NumRotatableBonds(mol),
                                    Lipinski.NumSaturatedCarbocycles(mol),
                                    Lipinski.NumSaturatedHeterocycles(mol),
                                    Lipinski.NumSaturatedRings(mol),
                                    Lipinski.RingCount(mol),
                                    MolSurf.LabuteASA(mol),
                                    MolSurf.PEOE_VSA1(mol),
                                    MolSurf.PEOE_VSA10(mol),
                                    MolSurf.PEOE_VSA11(mol),
                                    MolSurf.PEOE_VSA12(mol),
                                    MolSurf.PEOE_VSA13(mol),
                                    MolSurf.PEOE_VSA14(mol),
                                    MolSurf.PEOE_VSA2(mol),
                                    MolSurf.PEOE_VSA3(mol),
                                    MolSurf.PEOE_VSA4(mol),
                                    MolSurf.PEOE_VSA5(mol),
                                    MolSurf.PEOE_VSA6(mol),
                                    MolSurf.PEOE_VSA7(mol),
                                    MolSurf.PEOE_VSA8(mol),
                                    MolSurf.PEOE_VSA9(mol),
                                    MolSurf.SlogP_VSA1(mol),
                                    MolSurf.SlogP_VSA10(mol),
                                    MolSurf.SlogP_VSA11(mol),
                                    MolSurf.SlogP_VSA12(mol),
                                    MolSurf.SlogP_VSA2(mol),
                                    MolSurf.SlogP_VSA3(mol),
                                    MolSurf.SlogP_VSA4(mol),
                                    MolSurf.SlogP_VSA5(mol),
                                    MolSurf.SlogP_VSA6(mol),
                                    MolSurf.SlogP_VSA7(mol),
                                    MolSurf.SlogP_VSA8(mol),
                                    MolSurf.SlogP_VSA9(mol),
                                    MolSurf.SMR_VSA1(mol),
                                    MolSurf.SMR_VSA10(mol),
                                    MolSurf.SMR_VSA2(mol),
                                    MolSurf.SMR_VSA3(mol),
                                    MolSurf.SMR_VSA4(mol),
                                    MolSurf.SMR_VSA5(mol),
                                    MolSurf.SMR_VSA6(mol),
                                    MolSurf.SMR_VSA7(mol),
                                    MolSurf.SMR_VSA8(mol),
                                    MolSurf.SMR_VSA9(mol),
                                    MolSurf.TPSA(mol)])).rename({0: 'MolLogP', 1: 'MolMR', 2: 'FpDensityMorgan1',
                                        3: 'FpDensityMorgan2',4: 'FpDensityMorgan3', 5: 'FractionCSP3',
                                        6: 'HeavyAtomMolWt', 7: 'MaxAbsPartialCharge',
                                        8: 'MaxPartialCharge', 9: 'MinAbsPartialCharge',
                                        10: 'MinPartialCharge', 11: 'MolWt', 12: 'NumRadicalElectrons',
                                        13: 'NumValenceElectrons', 14: 'MaxAbsEStateIndex',
                                        15: 'MaxEStateIndex', 16: 'MinAbsEStateIndex',
                                        17: 'MinEStateIndex', 18: 'EState_VSA1',19: 'EState_VSA10',
                                        20: 'EState_VSA11', 21: 'EState_VSA2', 22: 'EState_VSA3',
                                        23: 'EState_VSA4', 24: 'EState_VSA5', 25: 'EState_VSA6',
                                        26: 'EState_VSA7', 27: 'EState_VSA8', 28: 'EState_VSA9',
                                        29: 'fr_Al_COO', 30: 'fr_Al_OH', 31: 'fr_Al_OH_noTert',
                                        32: 'fr_aldehyde', 33: 'fr_alkyl_carbamate', 34: 'fr_alkyl_halide',
                                        35: 'fr_allylic_oxid', 36: 'fr_amide', 37: 'fr_amidine',
                                        38: 'fr_aniline', 39: 'fr_Ar_COO', 40: 'fr_Ar_N', 41: 'fr_Ar_NH',
                                        42: 'fr_Ar_OH', 43: 'fr_ArN',  44: 'fr_aryl_methyl',
                                        45: 'fr_azide', 46: 'fr_azo', 47: 'fr_barbitur',
                                        48: 'fr_benzene', 49: 'fr_benzodiazepine', 50: 'fr_bicyclic',
                                        51: 'fr_C_O',  52: 'fr_C_O_noCOO', 53: 'fr_C_S', 54: 'fr_COO',
                                        55: 'fr_COO2', 56: 'fr_diazo', 57: 'fr_dihydropyridine',
                                        58: 'fr_epoxide', 59: 'fr_ester', 60: 'fr_ether',  61: 'fr_furan',
                                        62: 'fr_guanido', 63: 'fr_halogen', 64: 'fr_hdrzine',
                                        65: 'fr_hdrzone', 66: 'fr_HOCCN', 67: 'fr_imidazole',
                                        68: 'fr_imide',  69: 'fr_Imine', 70: 'fr_isocyan',
                                        71: 'fr_isothiocyan', 72: 'fr_ketone',  73: 'fr_ketone_Topliss',
                                        74: 'fr_lactam', 75: 'fr_lactone', 76: 'fr_methoxy',
                                        77: 'fr_morpholine', 78: 'fr_N_O', 79: 'fr_Ndealkylation1',
                                        80: 'fr_Ndealkylation2', 81: 'fr_NH0', 82: 'fr_NH1',
                                        83: 'fr_NH2', 84: 'fr_Nhpyrrole', 85: 'fr_nitrile',
                                        86: 'fr_nitro', 87: 'fr_nitro_arom',  88: 'fr_nitro_arom_nonortho',
                                        89: 'fr_nitroso', 90: 'fr_oxazole', 91: 'fr_oxime',
                                        92: 'fr_para_hydroxylation', 93: 'fr_phenol',
                                        94: 'fr_phenol_noOrthoHbond', 95: 'fr_phos_acid',
                                        96: 'fr_phos_ester', 97: 'fr_piperdine', 98: 'fr_piperzine',
                                        99: 'fr_priamide',  100: 'fr_prisulfonamd', 101: 'fr_pyridine',
                                        102: 'fr_quatN',  103: 'fr_SH', 104: 'fr_sulfide',
                                        105: 'fr_sulfonamd', 106: 'fr_sulfone',  107: 'fr_term_acetylene',
                                        108: 'fr_tetrazole', 109: 'fr_thiazole',  110: 'fr_thiocyan',
                                        111: 'fr_thiophene', 112: 'fr_unbrch_alkane', 113: 'fr_urea',
                                        114: 'BalabanJ', 115: 'BertzCT', 116: 'Chi0', 117: 'Chi0n',
                                        118: 'Chi0v', 119: 'Chi1', 120: 'Chi1n', 121: 'Chi1v',
                                        122: 'Chi2n', 123: 'Chi2v', 124: 'Chi3n', 125: 'Chi3v',
                                        126: 'Chi4n', 127: 'Chi4v',  128: 'HallKierAlpha', 129: 'Ipc',
                                        130: 'Kappa1', 131: 'Kappa2', 132: 'Kappa3', 133: 'HeavyAtomCount',
                                        134: 'NHOHCount', 135: 'NOCount',  136: 'NumAliphaticCarbocycles',
                                        137: 'NumAliphaticHeterocycles',  138: 'NumAliphaticRings',
                                        139: 'NumAromaticCarbocycles',  140: 'NumAromaticHeterocycles',
                                        141: 'NumAromaticRings', 142: 'NumHAcceptors', 143: 'NumHDonors',
                                        144: 'NumHeteroatoms', 145: 'NumRotatableBonds',
                                        146: 'NumSaturatedCarbocycles', 147: 'NumSaturatedHeterocycles',
                                        148: 'NumSaturatedRings', 149: 'RingCount', 150: 'LabuteASA',
                                        151: 'PEOE_VSA1', 152: 'PEOE_VSA10', 153: 'PEOE_VSA11',
                                        154: 'PEOE_VSA12', 155: 'PEOE_VSA13',  156: 'PEOE_VSA14',
                                        157: 'PEOE_VSA2', 158: 'PEOE_VSA3', 159: 'PEOE_VSA4',
                                        160: 'PEOE_VSA5', 161: 'PEOE_VSA6', 162: 'PEOE_VSA7',
                                        163: 'PEOE_VSA8',  164: 'PEOE_VSA9', 165: 'SlogP_VSA1',
                                        166: 'SlogP_VSA10', 167: 'SlogP_VSA11', 168: 'SlogP_VSA12',
                                        169: 'SlogP_VSA2', 170: 'SlogP_VSA3', 171: 'SlogP_VSA4',
                                        172: 'SlogP_VSA5', 173: 'SlogP_VSA6', 174: 'SlogP_VSA7',
                                        175: 'SlogP_VSA8',  176: 'SlogP_VSA9', 177: 'SMR_VSA1',
                                        178: 'SMR_VSA10', 179: 'SMR_VSA2',  180: 'SMR_VSA3',
                                        181: 'SMR_VSA4', 182: 'SMR_VSA5', 183: 'SMR_VSA6',184: 'SMR_VSA7',
                                        185: 'SMR_VSA8', 186: 'SMR_VSA9', 187: 'TPSA'})
    return descriptors
    '''