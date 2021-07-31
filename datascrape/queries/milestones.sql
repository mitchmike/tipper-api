-- milestones pivot table
select
pivtab.match_mode,
pivtab.request_finish - pivtab.request_start as "req",
pivtab.match_finish - pivtab.match_start as "scrape_full",
pivtab.process_row_finish_0 - pivtab.process_row_start_0 as "scrape_process_row_0",
pivtab.process_row_finish_1 - pivtab.process_row_start_1 as "scrape_process_row_1",
pivtab.persist_finish_0 - pivtab.process_row_finish_0 as "scrape_persist_0",
pivtab.persist_finish_1 - pivtab.process_row_finish_1 as "scrape_persist_1",
pivtab.match_start - pivtab.request_finish as "time_in_queue"
from (select * from crosstab(
$$select concat(run_id,'_',match_id,'_',mode) as match_mode,
	milestone,
	milestone_time
	from milestones
	where mode is not null
	and milestone_time > (now() - interval '1 day')
	order by concat(run_id,'_',match_id,'_',mode), milestone_time$$
) as milestone_interval ("match_mode" text,
						 "request_start" timestamp,
						 "request_finish" timestamp,
						 "match_start" timestamp,
						 "process_row_start_0" timestamp, "process_row_finish_0" timestamp,
						 "persist_finish_0" timestamp,
						 "process_row_start_1" timestamp, "process_row_finish_1" timestamp,
						 "persist_finish_1" timestamp,
						 "match_finish" timestamp)) as pivtab;