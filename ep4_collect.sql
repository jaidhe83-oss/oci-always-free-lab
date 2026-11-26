create table ash_snapshot as
select cast(from_tz(sample_time, 'UTC') at time zone 'Asia/Kolkata' as timestamp) sample_time, session_id sid, module, action, session_state, event, wait_class,
       blocking_session, sql_id, time_waited / 1e6 time_waited_sec
  from v$active_session_history
 where module in ('ORDER_APP', 'PRICE_BATCH')
/
comment on table ash_snapshot is 'Copy of Oracle Active Session History (one sample per active session per second) for the application and batch sessions.'
/
select to_char(trunc(started_at, 'MI'), 'HH24:MI') minute,
       sum(case when status = 'OK' then 1 else 0 end) ok,
       sum(case when status = 'TIMEOUT' then 1 else 0 end) timeouts,
       max(elapsed_ms) max_ms
  from app_job_log group by trunc(started_at, 'MI') order by 1
/
select job_name, count(*) runs, sum(case when status = 'TIMEOUT' then 1 else 0 end) timeouts,
       to_char(min(case when status = 'TIMEOUT' then started_at end), 'HH24:MI:SS') first_timeout,
       to_char(max(case when status = 'TIMEOUT' then started_at end), 'HH24:MI:SS') last_timeout
  from app_job_log group by job_name order by 1
/
select job_name, to_char(actual_start_date, 'HH24:MI:SS') started, run_duration, status
  from job_history order by actual_start_date
/
select to_char(sample_time, 'HH24:MI:SS') t, sid, module, status, event, blocking_session, seconds_in_wait
  from session_monitor
 where blocking_session is not null or module = 'PRICE_BATCH'
 order by sample_time, sid fetch first 25 rows only
/
select to_char(sample_time, 'HH24:MI:SS') t, sid, module, object_name, locked_mode, rows_locked_since_sec
  from lock_monitor order by sample_time, sid fetch first 25 rows only
/
select event, module, count(*) ash_samples, count(distinct sid) sessions, min(blocking_session) blocker
  from ash_snapshot group by event, module order by 3 desc
/
select to_char(trunc(sample_time, 'MI'), 'HH24:MI') minute, count(*) active_samples,
       round(count(*) / 60, 1) avg_active_sessions
  from ash_snapshot group by trunc(sample_time, 'MI') order by 1
