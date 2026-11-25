select model_name, algorithm, mining_function from user_mining_models where model_name = 'ALL_MINILM_L12_V2'
/
select vector_dimension_count(vector_embedding(all_minilm_l12_v2 using 'hello' as data)) dims from dual
/
create table dba_notes (id number primary key, note varchar2(200), emb vector(384, float32))
/
insert into dba_notes (id, note) select 1, 'Node was evicted from the cluster after interconnect heartbeat loss' from dual union all
select 2, 'Increase ipfrag_high_thresh when packet reassembly failures climb' from dual union all
select 3, 'Switchover to the standby database completed with no data loss' from dual union all
select 4, 'Tablespace is full: add a datafile or enable autoextend' from dual union all
select 5, 'Slow query fixed by gathering optimizer statistics on the table' from dual union all
select 6, 'Backup failed because the recovery area ran out of space' from dual union all
select 7, 'User account locked after too many failed login attempts' from dual union all
select 8, 'Apply the latest release update with a rolling patch' from dual
/
update dba_notes set emb = vector_embedding(all_minilm_l12_v2 using note as data)
/
select count(*) notes_with_vectors from dba_notes where emb is not null
/
select id, note from dba_notes where lower(note) like '%kicked out%'
/
select id, note, round(vector_distance(emb, vector_embedding(all_minilm_l12_v2 using 'my server got kicked out of the cluster' as data), cosine), 3) distance from dba_notes order by distance fetch first 3 rows only
/
select id, note, round(vector_distance(emb, vector_embedding(all_minilm_l12_v2 using 'cannot sign in, password tried too many times' as data), cosine), 3) distance from dba_notes order by distance fetch first 3 rows only
/
select id, note, round(vector_distance(emb, vector_embedding(all_minilm_l12_v2 using 'disk space problem' as data), cosine), 3) distance from dba_notes order by distance fetch first 3 rows only
/
create vector index dba_notes_ivf on dba_notes (emb) organization neighbor partitions distance cosine
/
select index_name, index_type from user_indexes where table_name = 'DBA_NOTES' and index_name = 'DBA_NOTES_IVF'
/
