create table events (
	id integer,
	event_name text,
	guest_count integer,
	event_date text,
	setup_time text,
	start_time text,
	end_time text,
	crdate text,
	bldg_name text,
	room_name text,
	client_name text,
	event_is_for text
	);
	
insert into events values (1, 'My First Event', 150, '2011-08-11', null, null, null,
 '2011-07-20', 'South Building', 'Main Room', 'Sheffield Family', 'Active');

 
-- add checklist for events
create table chklist_items (
	id integer,
	itm_name text
);

insert into chklist_items values (1,'Color Scheme');
insert into chklist_items values (2,'Guest Count');
insert into chklist_items values (3,'Choose Band');
insert into chklist_items values (4,'Choose DJ');
insert into chklist_items values (5,'Choose Florist');
insert into chklist_items values (6,'Choose Photographer');
insert into chklist_items values (7,'Choose Videographer');
insert into chklist_items values (8,'Choose Baker');
insert into chklist_items values (9,'Choose Invitations');
insert into chklist_items values (10,'Send Invitations');
insert into chklist_items values (11,'Choose Liqour');
insert into chklist_items values (12,'Choose Wine');
insert into chklist_items values (13,'Choose Champagne');
insert into chklist_items values (14,'Purchase Guest Book');
insert into chklist_items values (15,'Finalize Seating Plan');
insert into chklist_items values (16,'Finalize Place Cards');
insert into chklist_items values (17,'Choose Caterer');
insert into chklist_items values (18,'Choose Menu');
insert into chklist_items values (19,'Send Thank Yous');
insert into chklist_items values (20,'Send Invoices');



create table chklist (
	event_id integer,
	chk_id integer,
	chk_value text,
	updt_date text,
	note text
	);
	
insert into chklist values (1,1, 'Blue and Gold', '2012-08-30', 'May change soon. Possibly to Blue and Red');

 
 --===================================================================================
create table client_info (
	id integer,
	client_name text,
	con_1 text,
	phn_1 text,
	con_2 text,
	phn_2 text,
	con_3 text,
	phn_3 text,
	address1 text,
	address2 text,
	city text,
	st_abbv text,
	zip text,
	email_1 text,
	email_2 text
	);
	
insert into contact_info values (1, 'Sheffield Family', 'Jesse Sheffield', 'c720-837-1133', 'Rosalie Sheffield', 'c720-837-1122', 'Main Number', 'h303-604-6058', '203 Lois Dr', Null, 'Louisville', 'CO', '80027',xxx@xxx.com)
--===========================================================
create table buildings (
	id integer,
	name text,
	address1 text,
	address2 text,
	address3 text,
	city text,
	st_abbv text,
	zip text,
	cont1_name text,
	cont1_phone text,
	cont2_name text,
	cont2_phone text
	);
	
insert into buildings values (1, 'North Building', 'xxx Baseline', null, null, 'Boulder', 'CO', '80303', 'Gary', null, null, null);
insert into buildings values (2, 'South Building', 'xxx Baseline', null, null, 'Boulder', 'CO', '80303', 'Gary', null, null, null);
--===================================================================================
create table rooms (
	id integer,
	name text,
	bldg_id integer,
	sq_ft integer,
	max_standing integer,
	max_seated integer
	);
	
insert into rooms values (1, 'Social Hall', 2, 1600, 160, 125);
--===================================================================================
create table catered_items (
	id integer,
	name text,
	category text,
	amnt_per_container integer,
	amnt_per_person real,
	amnt_units text,
	container_price real,
	sold_by text,
	allergy_info text,
	prep_minutes integer,
	prep_notes text,
	req_oven text,
	notes text
	);
	
insert into catered_items values (1, 'Paper Package Gold', 'Other', 1, 1, 'pcs', 2.50, 'Har HaShem', null, null, null, null, null);
insert into catered_items values (2, 'Paper Package White', 'Other', 1, 1, 'pcs', 2.00, 'Har HaShem', null, null, null, null, null);

--===================================================================================
-- Stores all catering worksheet line items for a given event
create table budget_items (
		id integer,
		event_id integer,
		item_id integer,
	guest_cnt_ovride integer,
	ENCR_ovride intege
		);
		
--===========================================================================
-- Stores all staffing worksheet line items for a given event		
create table budget_staffing (
		id integer,
		event_id integer,
		staff_id integer,
		hrs real
		);
--===========================================
create table staff (
	id integer,
	name text,
	hr_rate real,
	def_hrs real
	);
	
insert into staff values (1, 'Rosalie', 30.0, 4);
insert into staff values (2, 'Brittany', 15.0, 4);
insert into staff values (3, 'NewHelp', 20.0, 4);
insert into staff values (4, 'Becca', 15.0, 4);
--============================================	
create table weeks(
wk_yr integer,
wk_strt_date text
);

insert into weeks values (2013,2,'2013-01-07');


create table invoices(
	id integer,
	cust_name text,
	event_id integer,
	payment_id integer,
	tax_id integer,
	invoice_title text,
	invoice_num integer,
	late_fee real,
	inv_issue_date text,
	inv_due_date text,
	inv_description text,
	inv_created text,
	inv_updated text
	);
	
create table inv_items(
	id integer,
	inv_id integer,
	product_name text,
	unit_cost real,
	quantity real,
	discount real,
	description text
	);
	
create table payments(
	id integer,
	event_id integer,
	payment_method text,
	payment_amnt real,
	payment_date text
	);
	
create table taxes(
	id integer,
	tax_name text,
	tax_caption text,
	tax_pct real);
	
insert into taxes values (1,'Colorado State Tax 2015','StateTax2015',2.9);
insert into taxes values (2,'Local Sales Tax 2015','StateTax2015',4.54);


--========================================================
create table billable_items(
	id integer,
	item_type text,
	name text,
	cost_type text,
	cost real
	);
	
insert into billable_items values (10,'Room','Rental Charge North Bldg','Fixed',450.00);
insert into billable_items values (20,'Room','Rental Charge South Bldg','Fixed',500.00);
insert into billable_items values (30,'Paper Package','Paper Pkg Gold','PerPerson',3.00);
insert into billable_items values (40,'Paper Package','Paper Pkg White','PerPerson',2.50);

insert into billable_items values (100,'Staff','Rosalie','HrRate',30.00);
insert into billable_items values (110,'Staff','Emma','HrRate',20.00);
insert into billable_items values (120,'Staff','Heather','HrRate',20.00);









	
	
	
	
-- Need to add a table for storing the text from emails tied to each event.
-- Need to add table for storing billing, invoicing, payment data.
-- Need to add table to store event followup data (how much food was left, what went well, what did't)
-- Need to add table for storing data to recreate room/table/seating layouts
-- for example divide a room into grid and table is assigned to a grid number then stored.
--



	
	
	
	

	
	



