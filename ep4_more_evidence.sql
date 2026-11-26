create table lock_monitor (
  sample_time  timestamp,
  sid          number,
  module       varchar2(64),
  object_name  varchar2(128),
  locked_mode  varchar2(20),
  rows_locked_since_sec number)
/
comment on table lock_monitor is 'Ops monitoring: every 5 seconds, which session holds a lock on which table. LOCKED_MODE 3 = row exclusive (rows being changed).'
/
create or replace procedure session_monitor_job(p_until timestamp with time zone) as
begin
  while systimestamp < p_until loop
    insert into session_monitor
    select ist_now, s.sid, s.module, s.action, s.status, s.event, s.wait_class, s.blocking_session,
           round(s.wait_time_micro / 1e6, 1), substr(q.sql_text, 1, 200)
      from v$session s left join v$sql q on q.sql_id = s.sql_id and q.child_number = 0
     where s.username = user and s.module in ('ORDER_APP', 'PRICE_BATCH');
    insert into lock_monitor
    select ist_now, l.session_id, s.module, o.object_name,
           decode(l.locked_mode, 3, 'ROW EXCLUSIVE', to_char(l.locked_mode)),
           round((sysdate - t.start_date) * 86400)
      from v$locked_object l
      join user_objects o on o.object_id = l.object_id
      join v$session s on s.sid = l.session_id
      left join v$transaction t on t.addr = s.taddr
     where s.module in ('ORDER_APP', 'PRICE_BATCH');
    commit;
    dbms_session.sleep(5);
  end loop;
end;
/
create or replace procedure price_batch_fixed as
  -- the fix: same repricing, but 5 orders per transaction, so each lock lives for milliseconds
begin
  dbms_application_info.set_module('PRICE_BATCH', 'REPRICE_CHUNKED');
  for c in (select order_id from orders order by order_id) loop
    update orders set amount = amount * 1.02, updated_at = systimestamp where order_id = c.order_id;
    if mod(c.order_id, 5) = 0 then
      commit;
      dbms_session.sleep(30);   -- same total run time as before (about 2 minutes), but no long locks
    end if;
  end loop;
  commit;
end;
/
create or replace procedure schedule_fixed_run(p_at timestamp with time zone) as
  -- same 4 app jobs + monitor, but the FIXED batch at p_at
begin
  for r in (select job_name from user_scheduler_jobs where job_name like 'APP_WORKER%' or job_name in ('OPS_MONITOR', 'PRICE_BATCH_JOB')) loop
    dbms_scheduler.drop_job(r.job_name, force => true);
  end loop;
  schedule_incident(p_at);
  dbms_scheduler.set_attribute('PRICE_BATCH_JOB', 'job_action', 'PRICE_BATCH_FIXED');
end;
/
select object_name, status from user_objects where object_type = 'PROCEDURE' order by 1
