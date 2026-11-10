import sys, pandas as pd
S=sys.argv[1]
d=pd.read_csv(S+'/cov_base.csv')
DET='Detailed table held'; HELD='Table held, detail not assessed'; IDN='Official source identified'
nat={
'USA':(DET,406,406,'BEA detail 2017 (NAICS-based); also 1997 benchmark ~490 industries'),
'CAN':(DET,473,220,'StatCan SUT 2022, SUPC products x NAICS industries'),
'JPN':(DET,445,391,'Basic table 2020; production file has 3,719 commodity rows'),
'KOR':(DET,380,278,'Bank of Korea basic table 2020'),
'TWN':(DET,484,163,'DGBAS 2021 (484 input rows x 163 columns)'),
'NZL':(DET,199,111,'Stats NZ IO 2020 (approx. counts)'),
'CHL':(DET,181,111,'Banco Central de Chile MIP 2018 / 2023'),
'IDN':(DET,185,None,'BPS 2016, product-by-product table'),
'PHL':(DET,None,240,'PSA 2018, industry-by-industry'),
'THA':(DET,None,180,'NESDC 2021, sector-by-sector'),
'DNK':(DET,None,117,'Statistics Denmark, industry-by-industry'),
'MEX':(HELD,None,None,'INEGI MIP 2018 (SCIAN), not counted'),
'DEU':(HELD,64,64,'Eurostat A*64 plus Destatis IO 2022/2023'),
'BRA':(HELD,None,67,'IBGE MIP 2015 (Nivel 67) and TRU 2023'),
'CHN':(HELD,None,17,'NBS yearbook IO tables (17 sectors)'),
}
for c in 'AUS ALB AUT AZE BOL HRV CYP ECU EST FRA GBR GEO IRL IND JOR KAZ PAK PER SWE SRB SGP SVN ESP TUN VEN ZAF ZMB'.split():
    nat.setdefault(c,(HELD,None,None,'Raw files held, detail not yet assessed'))
nat['MKD']=(HELD,88,None,'88 products (registry note)')
for c,p,n in [('SAU',299,'GASTAT SUT 2018-2023, 299 products x 298 activities (registry)'),('MLT',216,'NSO SUT 2019, 216 products x 95 industries (registry)'),('PRT',82,'INE IO 2013, 82 products (registry)'),('LVA',88,'CSB SUIOT, 88 products (registry)')]:
    nat.setdefault(c,(IDN,p,None,n))
for c in 'ARG COL URY CRI MAR EGY KEN TZA GHA VNM MYS TUR ISR HKG BGD LKA MNG ITA GRC CHE ISL CZE SVK POL HUN ROU BGR LTU RUS ARM LUX NGA ARE QAT OMN LBN IRN NPL KHM BRN FJI PNG RWA NAM MOZ BEL FIN'.split():
    nat.setdefault(c,(IDN,None,None,'Official page identified in SUT registry, not downloaded'))
d['national_status']=d.iso3.map(lambda c:nat.get(c,('None found',None,None,''))[0])
d['national_products']=d.iso3.map(lambda c:nat.get(c,(0,None,None,''))[1])
d['national_industries']=d.iso3.map(lambda c:nat.get(c,(0,None,None,''))[2])
d['national_note']=d.iso3.map(lambda c:nat.get(c,(0,None,None,''))[3])
d['national_products']=d.national_products.astype('Int64'); d['national_industries']=d.national_industries.astype('Int64')
d=d.rename(columns={'in_IEA':'iea','in_ICIO':'oecd_icio','in_FIGARO':'figaro','exiobase3_current':'in_exiobase3'})
d.to_csv(S+'/coverage_by_country.csv',index=False)
print(d.national_status.value_counts()); print(d.shape); print(set(nat)-set(d.iso3))
