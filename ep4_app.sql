create table orders (order_id number primary key, status varchar2(12), amount number(10,2), updated_at timestamp)
/
insert into orders select level, 'NEW', 100 + level, systimestamp from dual connect by level <= 20
/
create or replace function ist_now return timestamp as
begin
  return cast(systimestamp at time zone 'Asia/Kolkata' as timestamp);  -- the database clock is UTC; log India time
end;
/
create table app_job_log (
  run_id      number generated always as identity primary key,
  job_name    varchar2(30),
  order_id    number,
  started_at  timestamp,
  elapsed_ms  number,
  status      varchar2(10),
  error_msg   varchar2(200))
/
comment on table app_job_log is 'One row per run of the order-processing application job. STATUS is OK or TIMEOUT. A job gives up after waiting 3 seconds for a row lock.'
/
create or replace procedure app_worker(p_name varchar2, p_first number, p_until timestamp with time zone) as
  -- the "application": every 10 s process one order; give up if the row is locked for more than 3 s
  busy exception;
  pragma exception_init(busy, -30006);   -- ORA-30006: what WAIT n raised in older releases
  busy26 exception;
  pragma exception_init(busy26, -54);    -- ORA-00054: what 26ai raises (with the blocking transaction id)
  t0 timestamp; id number := p_first; ms number; x number; err varchar2(200);
begin
  dbms_application_info.set_module('ORDER_APP', p_name);
  while systimestamp < p_until loop
    t0 := ist_now;
    begin
      select order_id into x from orders where order_id = id for update wait 3;
      update orders set status = 'PROCESSED', updated_at = systimestamp where order_id = id;
      commit;
      ms := round(extract(second from (ist_now - t0)) * 1000);
      insert into app_job_log (job_name, order_id, started_at, elapsed_ms, status) values (p_name, id, t0, ms, 'OK');
    exception when busy or busy26 then
      err := substr(sqlerrm, 1, 200);
      rollback;
      ms := round(extract(second from (ist_now - t0)) * 1000);
      insert into app_job_log (job_name, order_id, started_at, elapsed_ms, status, error_msg)
      values (p_name, id, t0, ms, 'TIMEOUT', err);
    end;
    commit;
    id := mod(id, 20) + 1;
    dbms_session.sleep(greatest(10 - ms / 1000, 1));
  end loop;
end;
/
create or replace procedure price_batch as
  -- the "batch" someone scheduled at the wrong time: reprices every order in ONE transaction, commits after 2 minutes
begin
  dbms_application_info.set_module('PRICE_BATCH', 'REPRICE_ALL');
  update orders set amount = amount * 1.02, updated_at = systimestamp;
  dbms_session.sleep(120);
  commit;
end;
/
create table session_monitor (
  sample_time       timestamp,
  sid               number,
  module            varchar2(64),
  action            varchar2(64),
  status            varchar2(8),
  event             varchar2(64),
  wait_class        varchar2(64),
  blocking_session  number,
  seconds_in_wait   number,
  sql_text          varchar2(200))
/
comment on table session_monitor is 'Ops monitoring: a snapshot of every application session, taken every 5 seconds. BLOCKING_SESSION is the SID of the session holding the lock this session waits for. MODULE shows which program the session belongs to.'
/
create or replace procedure session_monitor_job(p_until timestamp with time zone) as
begin
  while systimestamp < p_until loop
    insert into session_monitor
    select ist_now, s.sid, s.module, s.action, s.status, s.event, s.wait_class, s.blocking_session,
           round(s.wait_time_micro / 1e6, 1), substr(q.sql_text, 1, 200)
      from v$session s left join v$sql q on q.sql_id = s.sql_id and q.child_number = 0
     where s.username = user and s.module in ('ORDER_APP', 'PRICE_BATCH');
    commit;
    dbms_session.sleep(5);
  end loop;
end;
/
create or replace view job_history as
select job_name, cast(actual_start_date at time zone 'Asia/Kolkata' as timestamp) actual_start_date, run_duration, status from user_scheduler_job_run_details
/
comment on table job_history is 'History of scheduled jobs: when each job started, how long it ran and whether it succeeded. ORDER_JOB / APP_WORKER jobs are the application; other jobs are batches.'
/
create or replace procedure schedule_incident(p_at timestamp with time zone) as
  -- 4 app jobs run from p_at - 5 min to p_at + 6 min; the batch starts exactly at p_at
begin
  for i in 1 .. 4 loop
    dbms_scheduler.create_job(
      job_name   => 'APP_WORKER_' || i,
      job_type   => 'PLSQL_BLOCK',
      job_action => 'begin app_worker(''ORDER_JOB_' || i || ''', ' || (i * 5 - 4) || ', to_timestamp_tz(''' ||
                    to_char(p_at + interval '6' minute, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') || ''', ''YYYY-MM-DD HH24:MI:SS TZH:TZM'')); end;',
      start_date => p_at - interval '5' minute + numtodsinterval(i * 2, 'second'),
      enabled    => true);
  end loop;
  dbms_scheduler.create_job(
    job_name   => 'OPS_MONITOR',
    job_type   => 'PLSQL_BLOCK',
    job_action => 'begin session_monitor_job(to_timestamp_tz(''' ||
                  to_char(p_at + interval '6' minute, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') || ''', ''YYYY-MM-DD HH24:MI:SS TZH:TZM'')); end;',
    start_date => p_at - interval '5' minute,
    enabled    => true);
  dbms_scheduler.create_job(
    job_name   => 'PRICE_BATCH_JOB',
    job_type   => 'STORED_PROCEDURE',
    job_action => 'PRICE_BATCH',
    start_date => p_at,
    enabled    => true);
end;
