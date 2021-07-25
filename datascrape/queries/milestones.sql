-- milestones pivot table
select * from crosstab(
$$select concat(run_id,'_',match_id,'_',mode) as match_mode,
	milestone,
	milestone_time - lag(milestone_time) over (order by milestone_time) as delta_time
	from milestones
	where mode is not null
	order by milestone_time$$
) as milestone_interval ("match_mode" text, "request_start" interval,
					 "request_finished" interval, "process_row_start_0" interval,
					 "process_row_finished_0" interval, "persist_finished_0" interval,
					 "process_row_start_1" interval, "process_row_finished_1" interval,
					 "persist_finished_1" interval);