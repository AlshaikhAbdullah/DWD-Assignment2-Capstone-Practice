# Checkpoint B scouting probe output (read-only, nothing loaded)

### New Registration Of Motor Vehicles Under VQS, Monthly
`d_529752a3d78beb78bd4f38e3be37f1b6`
- resolves: yes · total rows: **10** · sampled: 10 (FULL)
- **WIDE format**: 429 month columns 1990May → 2026Jan; other columns: `DataSeries` (text)
- distinct `DataSeries` values (10): ['        Category C: Goods Vehicles & Buses Not Under ETS', '        Category C: Goods Vehicles & Buses Under ETS', '    Category A: Cars', '    Category B: Cars', '    Category C: Goods Vehicles & Buses', '    Category D: Motorcycles & Scooters', '    Taxis', '    Vehicles Exempted From VQS', '    Weekend Cars/Off Peak Cars', 'Total New Motor Vehicles Registered']
- export/scrap/disposal signal: **NONE found**

### New Registration Of Motor Vehicles Under VQS , Monthly (dup?)
`d_d94cf5d839fc11a144f24ef971705d3e`
- resolves: yes · total rows: **10** · sampled: 10 (FULL)
- **WIDE format**: 432 month columns 1990May → 2026Apr; other columns: `DataSeries` (text)
- distinct `DataSeries` values (10): ['        Category C: Goods Vehicles & Buses Not Under ETS', '        Category C: Goods Vehicles & Buses Under ETS', '    Category A: Cars', '    Category B: Cars', '    Category C: Goods Vehicles & Buses', '    Category D: Motorcycles & Scooters', '    Taxis', '    Vehicles Exempted From VQS', '    Weekend Cars/Off Peak Cars', 'Total New Motor Vehicles Registered']
- export/scrap/disposal signal: **NONE found**

### New Registration of Motor Vehicles Under VQS
`d_06c3969c73ac5ba2d059cf39491ce048`
- resolves: yes · total rows: **532** · sampled: 532 (FULL)
- columns: `month` (text), `category` (text), `number` (numeric)
- `month` coverage in sample: 2014-01 → 2020-04 (76 distinct)
- distinct `category` values (7): ['Category A', 'Category B', 'Category C', 'Category C-ETS', 'Category D', 'Taxis', 'Vehicles Exempted From VQS']
- export/scrap/disposal signal: **NONE found**

### New Registration of Motor Vehicles under VQS (verified CP A)
`d_f52d6995ea85ad8d5088906d7a24d5df`
- resolves: yes · total rows: **91** · sampled: 91 (FULL)
- columns: `year` (numeric), `category` (text), `number` (numeric)
- `year` coverage in sample: 2005 → 2017 (13 distinct)
- distinct `category` values (7): ['Category A', 'Category B', 'Category C', 'Category C-ETS', 'Category D', 'Taxis', 'Vehicles Exempted From VQS']
- export/scrap/disposal signal: **NONE found**

### Quarterly New Registration of Vehicle Population
`d_f8408eaf8ecf45adae760a035b8d850d`
- resolves: yes · total rows: **412** · sampled: 412 (FULL)
- columns: `period` (numeric), `category` (text), `type` (text), `cumulative_number` (numeric)
- `period` coverage in sample: 2016-Q1 → 2020-Q4 (20 distinct)
- distinct `category` values (6): ['Buses', 'Cars and Station-wagons', 'Goods and Other Vehicles', 'Motorcycles and Scooters', 'Tax Exempted Vehicles', 'Taxis']
- distinct `type` values (25): ['Buses', 'Cars and Station-wagons', 'Company', 'Company cars', 'Excursion Buses', 'Goods and Other Vehicles', 'Goods-cum-passengers', 'HGVs ( mlw >3.5 - 16 mt)', 'LGVs ( mlw <= 3.5 mt)', 'Motorcycles and Scooters', 'Off peak cars', 'Off peak/Weekend cars', 'Private', 'Private Buses', 'Private Hire (Chauffeur) cars', 'Private Hire (Rental)', 'Private Hire (Self-Drive) cars', 'Private Hire Buses', 'Private cars', 'Public Buses', 'School Buses', 'Taxis', 'Tuition', 'Tuition cars', 'VHGVs ( mlw > 16 mt)']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicles De-Registered Under VQS, Monthly
`d_d520d6034b5e0c4f883b4e480de28f97`
- resolves: yes · total rows: **8** · sampled: 8 (FULL)
- **WIDE format**: 432 month columns 1990May → 2026Apr; other columns: `DataSeries` (text)
- distinct `DataSeries` values (8): ['    Category A: Cars', '    Category B: Cars', '    Category C: Goods Vehicles & Buses', '    Category D: Motorcycles & Scooters', '    Taxis', '    Vehicles Exempted From VQS', '    Weekend Cars/Off Peak Cars', 'Total Motor Vehicles De-Registered']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicles De-registered under VQS
`d_1332f905376c3848bdcc032423ca5563`
- resolves: yes · total rows: **456** · sampled: 456 (FULL)
- columns: `month` (text), `category` (text), `number` (numeric)
- `month` coverage in sample: 2014-01 → 2020-04 (76 distinct)
- distinct `category` values (6): ['Category A', 'Category B', 'Category C', 'Category D', 'Taxis', 'Vehicles Exempted from VQS']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicle De-registration under VQS
`d_6e50d957520951abb4083d2b2bd0ae90`
- resolves: yes · total rows: **78** · sampled: 78 (FULL)
- columns: `year` (numeric), `category` (text), `number` (numeric)
- `year` coverage in sample: 2005 → 2017 (13 distinct)
- distinct `category` values (6): ['Category A', 'Category B', 'Category C', 'Category D', 'Taxis', 'Vehicles Exempted From VQS']
- export/scrap/disposal signal: **NONE found**

### Quarterly Deregistration of Vehicle Population
`d_5a32a72cbc741ecfda152c20677f0f3d`
- resolves: yes · total rows: **412** · sampled: 412 (FULL)
- columns: `period` (numeric), `category` (text), `type` (text), `number` (numeric)
- `period` coverage in sample: 2016-Q1 → 2020-Q4 (20 distinct)
- distinct `category` values (6): ['Buses', 'Cars and Station-wagons', 'Goods and Other Vehicles', 'Motorcycles and Scooters', 'Tax Exempted Vehicles', 'Taxis']
- distinct `type` values (25): ['Buses', 'Cars and Station-wagons', 'Company', 'Company cars', 'Excursion Buses', 'Goods and Other Vehicles', 'Goods-cum-passengers', 'HGVs ( mlw >3.5 - 16 mt)', 'LGVs ( mlw <= 3.5 mt)', 'Motorcycles and Scooters', 'Off peak cars', 'Off peak/Weekend cars', 'Private', 'Private Buses', 'Private Hire (Chauffeur) cars', 'Private Hire (Rental)', 'Private Hire (Self-Drive) cars', 'Private Hire Buses', 'Private cars', 'Public Buses', 'School Buses', 'Taxis', 'Tuition', 'Tuition cars', 'VHGVs ( mlw > 16 mt)']
- export/scrap/disposal signal: **NONE found**

### Monthly Motor Vehicle Population by Vehicle Type
`d_2ecb009f1e1ec5a816a454944dec4022`
- resolves: yes · total rows: **444** · sampled: 444 (FULL)
- columns: `month` (text), `vehicle_type` (text), `number` (numeric)
- `month` coverage in sample: 2012-01 → 2018-02 (74 distinct)
- distinct `vehicle_type` values (9): ['Buses', 'Car', 'Cars', 'Goods & Other Vehicles', 'Motorcycle and Scooter', 'Motorcycles', 'Rental Cars', 'Rental cars', 'Taxi']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicle Population By Type Of Vehicle (End Of Period), Monthly
`d_206838bdc92c07ab495af49475563da5`
- resolves: yes · total rows: **8** · sampled: 8 (FULL)
- **WIDE format**: 772 month columns 1962Jan → 2026Apr; other columns: `DataSeries` (text)
- distinct `DataSeries` values (8): ['    Buses', '    Cars', '    Goods & Other Vehicles', '    Motorcycles & Scooters', '    Private Hire Cars', '    Public Motor Cars', '    Taxis', 'Total']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicle Population By Type Of Vehicle (End Of Period), Annual
`d_aa457c0abaacccefd238c31cfed211d9`
- resolves: yes · total rows: **7** · sampled: 7 (FULL)
- columns: `DataSeries` (text), `2025` (numeric), `2024` (numeric), `2023` (numeric), `2022` (numeric), `2021` (numeric), `2020` (numeric), `2019` (numeric), `2018` (numeric), `2017` (numeric), `2016` (numeric), `2015` (numeric), `2014` (numeric), `2013` (numeric), `2012` (numeric), `2011` (numeric), `2010` (numeric), `2009` (numeric), `2008` (numeric), `2007` (numeric), `2006` (numeric), `2005` (numeric), `2004` (numeric), `2003` (numeric), `2002` (numeric), `2001` (numeric), `2000` (numeric), `1999` (numeric), `1998` (numeric), `1997` (numeric), `1996` (numeric), `1995` (numeric), `1994` (numeric), `1993` (numeric), `1992` (numeric), `1991` (numeric), `1990` (numeric), `1989` (numeric), `1988` (numeric), `1987` (numeric), `1986` (numeric), `1985` (numeric), `1984` (numeric), `1983` (numeric), `1982` (numeric), `1981` (numeric), `1980` (text), `1979` (text), `1978` (text), `1977` (text), `1976` (text), `1975` (text), `1974` (text), `1973` (text), `1972` (text), `1971` (text), `1970` (text), `1969` (text), `1968` (text), `1967` (text), `1966` (text), `1965` (text), `1964` (text), `1963` (text), `1962` (text), `1961` (text)
- distinct `DataSeries` values (7): ['    Buses', '    Goods & Other Vehicles', '    Motorcycles & Scooters', '    Private & Company Cars', '    Private Hire Cars', '    Taxis', 'Total']
- distinct `1980` values (5): ['118345', '152574', '371341', '6512', 'na']
- distinct `1979` values (5): ['108051', '143402', '338729', '6217', 'na']
- distinct `1978` values (5): ['137240', '309384', '5874', '98248', 'na']
- distinct `1977` values (5): ['134903', '289954', '5442', '89840', 'na']
- distinct `1976` values (5): ['135499', '279864', '5217', '84016', 'na']
- distinct `1975` values (5): ['142045', '280378', '4935', '83145', 'na']
- distinct `1974` values (5): ['142674', '276866', '4779', '84849', 'na']
- distinct `1973` values (5): ['122714', '187972', '367737', '4775', 'na']
- distinct `1972` values (5): ['115619', '168991', '2936', '337147', 'na']
- distinct `1971` values (5): ['109655', '155956', '2681', '313907', 'na']
- distinct `1970` values (5): ['105214', '142568', '2298', '290208', 'na']
- distinct `1969` values (5): ['130088', '2096', '267582', '99265', 'na']
- distinct `1968` values (5): ['121106', '1907', '246427', '90283', 'na']
- distinct `1967` values (5): ['116097', '1821', '229544', '80940', 'na']
- distinct `1966` values (5): ['113287', '1660', '211735', '68746', 'na']
- distinct `1965` values (5): ['104729', '1617', '192422', '60838', 'na']
- distinct `1964` values (5): ['1586', '171502', '52412', '95349', 'na']
- distinct `1963` values (5): ['1492', '153004', '44926', '85668', 'na']
- distinct `1962` values (5): ['133645', '1433', '35336', '77379', 'na']
- distinct `1961` values (5): ['117936', '1375', '28205', '70108', 'na']
- export/scrap/disposal signal: **NONE found**

### Annual Motor Vehicle Population by Vehicle Type
`d_2873f3b1b2a836103f51f696350b98fa`
- resolves: yes · total rows: **412** · sampled: 412 (FULL)
- columns: `year` (numeric), `category` (text), `type` (text), `number` (numeric)
- `year` coverage in sample: 2005 → 2024 (20 distinct)
- distinct `category` values (6): ['Buses', 'Cars and Station-wagons', 'Goods and Other Vehicles', 'Motorcycles and Scooters', 'Tax Exempted Vehicles', 'Taxis']
- distinct `type` values (22): ['Buses', 'Cars and Station-wagons', 'Company cars', 'Excursion buses', 'Goods and Other Vehicles', 'Goods-cum-passenger vehicles (GPVs)', 'Heavy Goods Vehicles (HGVs)', 'Light Goods Vehicles (LGVs)', 'Motorcycles and Scooters', 'Motorcycles and scooters', 'Off peak cars', 'Omnibuses', 'Private Hire (Chauffeur) cars', 'Private Hire (Self-Drive) cars', 'Private buses', 'Private cars', 'Private hire buses', 'Rental cars', 'School buses (CB)', 'Taxis', 'Tuition cars', 'Very Heavy Goods Vehicles (VHGVs)']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicle Population Under VQS (End Of Period), Monthly
`d_ede1a559013d10f234d209ac5e9fd9b4`
- resolves: yes · total rows: **8** · sampled: 8 (FULL)
- **WIDE format**: 433 month columns 1990May → 2026May; other columns: `DataSeries` (text)
- distinct `DataSeries` values (8): ['    Category A: Cars', '    Category B: Cars', '    Category C: Goods Vehicles & Buses', '    Category D: Motorcycles & Scooters', '    Taxis', '    Vehicles Exempted From VQS', '    Weekend Cars/Off Peak Cars', 'Total Motor Vehicles']
- export/scrap/disposal signal: **NONE found**

### Annual Motor Vehicle Population by Vehicle Quota Categories
`d_cc30f50369bcd6b6f848a586bded2290`
- resolves: yes · total rows: **78** · sampled: 78 (FULL)
- columns: `year` (numeric), `category` (text), `number` (numeric)
- `year` coverage in sample: 2005 → 2017 (13 distinct)
- distinct `category` values (6): ['Category A', 'Category B', 'Category C', 'Category D', 'Taxis', 'Vehicles Exempted From VQS']
- export/scrap/disposal signal: **NONE found**

### Motor Vehicle Population under VQS
`d_f8876e8c0959ba5bcfa2c40cf6d25dab`
- resolves: yes · total rows: **300** · sampled: 300 (FULL)
- columns: `month` (text), `category` (text), `number` (numeric)
- `month` coverage in sample: 2014-01 → 2018-02 (50 distinct)
- distinct `category` values (6): ['Category A', 'Category B', 'Category C', 'Category D', 'Taxis', 'Vehicles Exempted From VQS']
- export/scrap/disposal signal: **NONE found**
