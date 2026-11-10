import pandas as pd, numpy as np
Y=[str(y) for y in range(2018,2023)]
ax=pd.read_csv(r'D:\GitHub\EXIOBASE\00-class\class\country_axes\exiobase_rx2.csv')
ax=ax[ax.type=='country'].copy()
cm=pd.read_csv(r'D:\GitHub\EXIOBASE\00-class\class\country_axes\country_coverage_matrix.csv')
# FAO
f=pd.read_csv(r'D:\indecol\Data\fao\data\Production_Crops_Livestock_E_All_Data_NOFLAG.csv',encoding='latin-1',usecols=['Area Code','Item Code','Element','Y'+'2018','Y2019','Y2020','Y2021','Y2022'])
f=f[f.Element=='Production']
f=f[(f[['Y'+y for y in Y]].fillna(0)>0).any(axis=1)]
cmf=cm.dropna(subset=['FAOcode']).drop_duplicates('FAOcode'); fao2iso=dict(zip(cmf.FAOcode.astype(int),cmf.ISO3)); fao2iso.pop(351,None); fao2iso[41]='CHN'; fao2iso[276]='SDN'
f['iso3']=f['Area Code'].map(fao2iso)
fao=f.groupby('iso3')['Item Code'].nunique()
# PV
p=pd.read_parquet(r'D:\data\01-production_volumes\EXIOBASE_3_12_0\final\production_master_reconciled.parquet')
p=p[(p.quantity>0)&(p.year.between(2018,2022))]
p['pair']=p.commodity.astype(str)+'|'+p.sub_type.astype(str)
grp={'bgs_wms':'min','usgs_mcs':'min','usgs_myb':'min','usgs_myb_recycling':'min','worldsteel':'min','derived_clinker':'min','eurostat_prodcom':'prodcom','faostat_rfb':'fert'}
p['g']=p.source.map(grp)
pv=p.groupby(['country_iso3','g']).pair.nunique().unstack(fill_value=0)
pvall=p.groupby('country_iso3').pair.nunique()
eu=pd.read_csv(r'D:\GitHub\EXIOBASE\01-SUT_raw_data\sources\eu_country_native_source_matrix.csv')
import country_converter as coco
eu['iso3']=coco.convert(eu.eu_code.replace({'EL':'GR'}).tolist(),to='ISO3')
eurostat=set(eu[eu.eurostat_harmonised_time_series=='available'].iso3)
out=ax[['iso3','name','continent','exiobase3_current','in_IEA','in_ICIO','in_FIGARO']].copy()
out['fao_items']=out.iso3.map(fao).fillna(0).astype(int)
for g,c in [('min','pv_minerals_metals'),('prodcom','pv_prodcom'),('fert','pv_fertiliser')]:
    out[c]=out.iso3.map(pv[g] if g in pv else {}).fillna(0).astype(int)
out['pv_pairs_total']=out.iso3.map(pvall).fillna(0).astype(int)
out['eurostat_sut64']=out.iso3.isin(eurostat).astype(int)
out.to_csv(r'%s/cov_base.csv'%__import__('sys').argv[1],index=False)
print(out.describe().to_string()); print(len(out)); print(out.sort_values('pv_pairs_total').tail(5).to_string())
print('FAO unmapped areas sample', f[f.iso3.isna()]['Area Code'].unique()[:20])
