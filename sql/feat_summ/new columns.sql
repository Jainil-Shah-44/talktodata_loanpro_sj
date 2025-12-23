alter table loan_records
add city varchar(150) NULL;

alter table loan_records
add current_bureau_score INT NULL;

alter table loan_records
add claim_info varchar(150) NULL;

alter table loan_records
add category varchar(150) NULL;

alter table loan_records
add sarfesi_applicable varchar(50) NULL;

alter table loan_records
add legal_action1 varchar(150) NULL;

alter table loan_records
add legal_action2 varchar(150) NULL;

alter table loan_records
add asset_type_detail varchar(200) NULL;

alter table loan_records
add recovery_timeline_range_by_skc varchar(100) NULL;

alter table loan_records
add auctions_cnt int NULL;







