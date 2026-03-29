import re, warnings, numpy as np, pandas as pd, joblib
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import f1_score, balanced_accuracy_score, classification_report

ANTIB_COLS = ['AMX/AMP','AMC','CZ','FOX','CTX/CRO','IPM','GEN','AN',
    'Acide nalidixique','ofx','CIP','C','Co-trimoxazole','Furanes','colistine']
ANTIBIOTIC_CLASS = {
    'AMX/AMP':'Penicillin','AMC':'Beta-lactam+inhibitor',
    'CZ':'Cephalosporin-1G','FOX':'Cephalosporin-2G',
    'CTX/CRO':'Cephalosporin-3G','IPM':'Carbapenem',
    'GEN':'Aminoglycoside','AN':'Aminoglycoside',
    'Acide nalidixique':'Quinolone','ofx':'Fluoroquinolone',
    'CIP':'Fluoroquinolone','C':'Phenicol',
    'Co-trimoxazole':'Sulfonamide','Furanes':'Nitrofuran','colistine':'Polymyxin'
}
VALID_SPECIES = {
    'Escherichia coli','Klebsiella pneumoniae','Proteus mirabilis',
    'Enterobacteria spp.','Morganella morganii','Serratia marcescens',
    'Pseudomonas aeruginosa','Acinetobacter baumannii','Citrobacter spp.'
}
RES_GROUPS = {
    'beta_lactam':['AMX/AMP','AMC','CZ','FOX','CTX/CRO'],
    'carbapenem':['IPM'],'aminoglycoside':['GEN','AN'],
    'fluoroquinolone':['Acide nalidixique','ofx','CIP'],
    'other':['C','Co-trimoxazole','Furanes','colistine'],
}

def clean_species(s):
    if pd.isna(s): return np.nan
    s = re.sub(r'^S\d+[-\s]+','',str(s).strip())
    if s in ('?','missing',''): return np.nan
    for o,n in [('E.coli','Escherichia coli'),('E. coli','Escherichia coli'),
                ('E.coi','Escherichia coli'),('Klbsiella','Klebsiella'),
                ('Prot.eus','Proteus'),('Proeus','Proteus'),('Enteobacteria','Enterobacteria')]:
        s=s.replace(o,n)
    return s

def clean_ab(v):
    if pd.isna(v): return np.nan
    v=str(v).strip().lower()
    if v in ('?','missing',''): return np.nan
    if v in ('r','i','intermediate'): return 1  # I merged into R
    if v=='s': return 0
    return np.nan

def parse_year(d):
    m=re.search(r'(20\d{2})',str(d)) if not pd.isna(d) else None
    return int(m.group(1)) if m else np.nan

def load_clean(path):
    df=pd.read_csv(path); df.columns=df.columns.str.strip()
    if 'age/gender' in df.columns:
        sp=df['age/gender'].astype(str).str.split('/',expand=True)
        df['Age']=pd.to_numeric(sp[0],errors='coerce')
        df['Gender']=sp[1].str.strip() if sp.shape[1]>1 else np.nan
        df.drop(columns=['age/gender'],inplace=True)
    df['Souches']=df['Souches'].apply(clean_species)
    df=df[df['Souches'].isin(VALID_SPECIES)].copy()
    for col in ANTIB_COLS: df[col]=df[col].apply(clean_ab)
    for col in ['Diabetes','Hypertension','Hospital_before']:
        df[col]=df[col].apply(lambda x:1 if str(x).strip().lower() in ('yes','true','1')
                              else(0 if str(x).strip().lower() in ('no','false','0') else np.nan))
    df['Infection_Freq']=pd.to_numeric(
        df['Infection_Freq'].replace(['unknown','error','missing','?'],np.nan),errors='coerce')
    df['Infection_Freq']=df.groupby('Souches')['Infection_Freq'].transform(
        lambda x:x.fillna(x.median() if x.notna().any() else 0)).fillna(0)
    df=df[df['Age'].notna()&(df['Age']>0)].copy()
    df['Age']=df['Age'].clip(1,110)
    if 'Collection_Date' in df.columns:
        df['Collection_Year']=df['Collection_Date'].apply(parse_year)
    return df

def engineer(df, sp_rate=None):
    df=df.copy()
    df['Age_sq']=df['Age']**2
    df['Is_Child']=(df['Age']<18).astype(int)
    df['Is_Elderly']=(df['Age']>=65).astype(int)
    df['Age_Group']=pd.cut(df['Age'],[0,18,40,65,120],labels=['young','adult','senior','elderly']).astype(str)
    for c in ['Diabetes','Hypertension','Hospital_before']: df[c]=df[c].fillna(0)
    df['Comorbidity_Score']=df['Diabetes']+df['Hypertension']+df['Hospital_before']
    df['High_Risk']=((df['Comorbidity_Score']>=2)|(df['Is_Elderly']==1)).astype(int)
    for grp,cols in RES_GROUPS.items():
        present=[c for c in cols if c in df.columns]
        df[f'res_{grp}']=df[present].mean(axis=1) if present else 0
    df['Resistance_Count']=df[ANTIB_COLS].sum(axis=1)
    df['MDR_Flag']=(df['Resistance_Count']>=3).astype(int)
    df['XDR_Flag']=(df['Resistance_Count']>=10).astype(int)
    df['Resistance_Rate']=df['Resistance_Count']/len(ANTIB_COLS)
    df['Species_R_Rate']=df['Souches'].map(sp_rate if sp_rate else {}).fillna(0.4)
    df['Years_Since_2019']=(df['Collection_Year'].fillna(2022)-2019).clip(0,10) if 'Collection_Year' in df.columns else 3
    df['Freq_x_Comorbidity']=df['Infection_Freq']*df['Comorbidity_Score']
    df['Age_x_Comorbidity']=df['Age']*df['Comorbidity_Score']
    df['HighRisk_x_Species']=df['High_Risk']*df['Species_R_Rate']
    return df

FEAT_NUM=['Age','Age_sq','Infection_Freq','Comorbidity_Score','Resistance_Count',
          'MDR_Flag','XDR_Flag','Resistance_Rate','Species_R_Rate','Is_Elderly',
          'Is_Child','High_Risk','Years_Since_2019','Freq_x_Comorbidity',
          'Age_x_Comorbidity','HighRisk_x_Species',
          'res_beta_lactam','res_carbapenem','res_aminoglycoside','res_fluoroquinolone','res_other']
FEAT_CAT=['Souches','Gender','Age_Group']

def build_pipeline():
    prep=ColumnTransformer([
        ('num',StandardScaler(),FEAT_NUM),
        ('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1),FEAT_CAT)
    ])
    rf=RandomForestClassifier(n_estimators=300,max_depth=14,min_samples_leaf=2,
        max_features='sqrt',class_weight='balanced',random_state=42,n_jobs=-1)
    hgb=HistGradientBoostingClassifier(max_iter=200,max_depth=8,learning_rate=0.05,
        min_samples_leaf=20,l2_regularization=0.1,class_weight='balanced',random_state=44)
    voting=VotingClassifier([('rf',rf),('hgb',hgb)],voting='soft')
    return Pipeline([('prep',prep),('model',MultiOutputClassifier(voting,n_jobs=1))])

def tune_thresholds(pipe, X_val, y_val):
    thresholds={}
    try: proba_list=pipe.predict_proba(X_val)
    except: return {col:0.5 for col in ANTIB_COLS}
    for i,col in enumerate(ANTIB_COLS):
        p=proba_list[i]
        if p.shape[1]<2: thresholds[col]=0.5; continue
        p_r=p[:,1]; best_t,best_f=0.5,0.0
        for t in np.arange(0.25,0.75,0.025):
            s=f1_score(y_val.iloc[:,i],(p_r>=t).astype(int),average='weighted',zero_division=0)
            if s>best_f: best_f,best_t=s,t
        thresholds[col]=best_t
    return thresholds

def predict_thresh(pipe, X, thresholds):
    try:
        pl=pipe.predict_proba(X)
        out=np.zeros((len(X),len(ANTIB_COLS)),dtype=int)
        for i,col in enumerate(ANTIB_COLS):
            out[:,i]=(pl[i][:,1]>=thresholds.get(col,0.5)).astype(int)
        return out
    except: return pipe.predict(X)

DRUG_ALT={'AMX/AMP':['AMC','CTX/CRO','IPM'],'AMC':['CTX/CRO','IPM','GEN'],
    'CZ':['FOX','CTX/CRO','IPM'],'FOX':['CTX/CRO','IPM','GEN'],
    'CTX/CRO':['IPM','GEN','AN'],'IPM':['GEN','AN','colistine'],
    'GEN':['AN','CIP','IPM'],'AN':['GEN','CIP','IPM'],
    'Acide nalidixique':['CIP','ofx'],'ofx':['CIP','GEN'],
    'CIP':['GEN','AN','IPM'],'C':['Co-trimoxazole','CIP'],
    'Co-trimoxazole':['CIP','GEN','C'],'Furanes':['Co-trimoxazole','CIP'],
    'colistine':['IPM','GEN']}

def suggest_treatment(pred_dict):
    resistant=[ab for ab,v in pred_dict.items() if v==1]
    sensitive=[ab for ab,v in pred_dict.items() if v==0]
    n=len(resistant); out=[]
    if n==0:
        out.append("No resistance — standard empiric therapy.")
        out.append(f"Sensitive: {', '.join(sensitive[:5])}")
    elif n>=12:
        out.append("PDR — infectious disease specialist required.")
        last=[a for a in sensitive if a in ['colistine','IPM']]
        if last: out.append(f"Last-resort options: {', '.join(last)}")
    elif n>=3:
        out.append(f"MDR ({n} classes resistant).")
        pref=[a for a in sensitive if a in ['IPM','GEN','AN','colistine']]
        if pref: out.append(f"Preferred: {', '.join(pref)}")
    else:
        for rab in resistant:
            alts=[a for a in DRUG_ALT.get(rab,[]) if pred_dict.get(a)==0]
            if alts: out.append(f"Replace {rab} → {', '.join(alts)}")
    return out

def predict_patient(arts, patient_data):
    pipe=arts['pipeline']; sp_map=arts.get('species_r_rate',{})
    row=patient_data.copy()
    age=float(row.get('Age',40)); inf=float(row.get('Infection_Freq',1))
    comb=int(row.get('Diabetes','No')=='Yes')+int(row.get('Hypertension','No')=='Yes')+int(row.get('Hospital_before','No')=='Yes')
    row.update({'Age':age,'Age_sq':age**2,'Infection_Freq':inf,'Comorbidity_Score':comb,
        'Is_Elderly':int(age>=65),'Is_Child':int(age<18),'High_Risk':int(comb>=2 or age>=65),
        'Resistance_Count':0,'MDR_Flag':0,'XDR_Flag':0,'Resistance_Rate':0,
        'Species_R_Rate':sp_map.get(row.get('Souches',''),0.4),'Years_Since_2019':3,
        'Freq_x_Comorbidity':inf*comb,'Age_x_Comorbidity':age*comb,
        'HighRisk_x_Species':int(comb>=2 or age>=65)*sp_map.get(row.get('Souches',''),0.4),
        'res_beta_lactam':0,'res_carbapenem':0,'res_aminoglycoside':0,'res_fluoroquinolone':0,'res_other':0,
        'Age_Group':'elderly' if age>=65 else('senior' if age>=40 else('adult' if age>=18 else 'young'))})
    X=pd.DataFrame([row])[FEAT_NUM+FEAT_CAT]
    for c in FEAT_CAT: X[c]=X[c].fillna('Unknown').astype(str)
    for c in FEAT_NUM: X[c]=pd.to_numeric(X[c],errors='coerce').fillna(0)
    preds=predict_thresh(pipe,X,arts['thresholds'])
    pred_dict={ab:int(preds[0,i]) for i,ab in enumerate(ANTIB_COLS)}
    return {ab:('R' if v==1 else 'S') for ab,v in pred_dict.items()}, suggest_treatment(pred_dict)

if __name__=='__main__':
    DATA='/Users/yuvi/Desktop/VS Code/langchain/models/antibiotic-resistance-predictor/dataset/raw/Bacteria_dataset_Multiresictance.csv'
    print("="*60)
    print("  ANTIBIOTIC RESISTANCE — SECONDARY MODEL")
    print("="*60)

    print("\n[1/6] Loading data...")
    df=load_clean(DATA)
    print(f"      Valid rows: {len(df):,}")

    print("[2/6] Species resistance rates...")
    sp_rate={sp: float(np.nanmean(df.loc[df['Souches']==sp,ANTIB_COLS].values))
             for sp in df['Souches'].unique()}

    print("[3/6] Feature engineering...")
    df=engineer(df, sp_rate=sp_rate)
    df.to_csv("cleaned_clinical_data.csv", index=False)

    y=df[ANTIB_COLS].copy()
    for col in ANTIB_COLS:
        mv=int(y[col].mode().iloc[0]) if y[col].notna().any() else 1
        y[col]=y[col].fillna(mv).astype(int)

    X=df[FEAT_NUM+FEAT_CAT].copy()
    for c in FEAT_CAT: X[c]=X[c].fillna('Unknown').astype(str)
    for c in FEAT_NUM: X[c]=pd.to_numeric(X[c],errors='coerce').fillna(0)

    X_tmp,X_test,y_tmp,y_test=train_test_split(X,y,test_size=0.15,random_state=42,stratify=X['MDR_Flag'])
    X_train,X_val,y_train,y_val=train_test_split(X_tmp,y_tmp,test_size=0.176,random_state=42,stratify=X_tmp['MDR_Flag'])
    print(f"      Train:{len(X_train):,} | Val:{len(X_val):,} | Test:{len(X_test):,}")

    print("[4/6] Training (RF + HGB voting ensemble)...")
    pipe=build_pipeline()
    pipe.fit(X_train,y_train)
    print("      Done!")

    print("[5/6] Threshold tuning on validation set...")
    thresholds=tune_thresholds(pipe,X_val,y_val)

    print("[6/6] Evaluating on test set...")
    y_pred=predict_thresh(pipe,X_test,thresholds)

    print("\n"+"="*65)
    print(f"  {'Antibiotic':<22} {'Class':<22} {'W-F1':>6} {'M-F1':>6} {'Bal':>6}")
    print("  "+"-"*60)
    f1r={}
    for i,col in enumerate(ANTIB_COLS):
        wf=f1_score(y_test.iloc[:,i],y_pred[:,i],average='weighted',zero_division=0)
        mf=f1_score(y_test.iloc[:,i],y_pred[:,i],average='macro',zero_division=0)
        ba=balanced_accuracy_score(y_test.iloc[:,i],y_pred[:,i])
        f1r[col]={'weighted':wf,'macro':mf,'bal_acc':ba}
        cls=ANTIBIOTIC_CLASS.get(col,'')
        print(f"  {col:<22} {cls:<22} {wf:>6.4f} {mf:>6.4f} {ba:>6.4f}")

    ow=np.mean([v['weighted'] for v in f1r.values()])
    om=np.mean([v['macro'] for v in f1r.values()])
    print("  "+"-"*60)
    print(f"  {'OVERALL AVERAGE':<44} {ow:>6.4f} {om:>6.4f}")
    print("="*65)

    print("\n  CLASSIFICATION REPORTS")
    print("="*60)
    for i,col in enumerate(ANTIB_COLS):
        print(f"\n  --- {col} ({ANTIBIOTIC_CLASS.get(col,'')}) ---")
        print(classification_report(y_test.iloc[:,i],y_pred[:,i],
              target_names=['S','R'],zero_division=0))

    print("  TOP FEATURES (RF, first antibiotic):")
    try:
        cat_enc=pipe.named_steps['prep'].named_transformers_['cat']
        all_names=FEAT_NUM+list(cat_enc.get_feature_names_out())
        rf_est=pipe.named_steps['model'].estimators_[0].estimators_[0]
        imp=rf_est.feature_importances_
        imp_df=pd.DataFrame({'Feature':all_names[:len(imp)],'Importance':imp}).sort_values('Importance',ascending=False).head(15)
        for _,r in imp_df.iterrows():
            print(f"    {r['Feature']:<32} {r['Importance']:.4f} {'█'*int(r['Importance']*300)}")
    except Exception as e:
        print(f"  skipped: {e}")
        imp_df=pd.DataFrame()

    arts={'pipeline':pipe,'feature_cols_num':FEAT_NUM,'feature_cols_cat':FEAT_CAT,
          'antib_cols':ANTIB_COLS,'thresholds':thresholds,'label_map':{'S':0,'R':1},
          'inv_label_map':{0:'S',1:'R'},'f1_results':f1r,'feature_importance':imp_df,
          'species_r_rate':sp_rate,'overall_weighted_f1':ow,'overall_macro_f1':om}
    out = "secondarymodel.pkl"
     
    joblib.dump(arts, out)
    print(f"\n  Model saved: {out}")
    print(f"\n  FINAL COMPETITION F1 (weighted) → {ow:.4f}")
    print(f"  FINAL COMPETITION F1 (macro)    → {om:.4f}")


