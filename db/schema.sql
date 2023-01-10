CREATE TABLE p1_channel_summary (channel int, tst text, tst_date text, tst_y int, tst_month int, tst_day int, tst_hr int, tst_m int, tst_s int, consumption_high real, consumption_low real, return_high real, return_low real, consumption_high_delta real, consumption_low_delta real, return_high_delta real, return_low_delta real);
CREATE TABLE p1_channel_detail (channel int, tst text, tst_date text, tst_y int, tst_month int, tst_day int, tst_hr int, tst_m int, tst_s int, consumption_high real, consumption_low real, return_high real, return_low real, consumption_actual real, return_actual real);
CREATE INDEX p1_channel_detail_idx_channel on p1_channel_detail (channel);
CREATE INDEX p1_channel_summary_idx_channel on p1_channel_summary (channel);
CREATE INDEX p1_channel_summary_idx_date on p1_channel_summary (tst_date);
CREATE INDEX p1_channel_detail_idx_date on p1_channel_detail (tst_date);
CREATE INDEX p1_channel_detail_idx_tst_hr on p1_channel_detail (tst_hr);
CREATE INDEX p1_channel_summary_idx_tst_hr on p1_channel_summary (tst_hr);
