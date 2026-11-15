-- CYF production schema only. Install once after inventory/backup; no DROP/REPLACE.
-- core_log.create_time is Unix milliseconds. NULL/nonpositive timestamps stay.
-- Run through the authorized local MySQL client; credentials never belong here.
USE `jia`;
DELIMITER $$
CREATE PROCEDURE `cyf_core_log_retention_7d`(
    IN p_cutoff_ms BIGINT,
    IN p_upper_id BIGINT,
    OUT p_deleted BIGINT
)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_cutoff BIGINT;
    DECLARE v_upper BIGINT;
    DECLARE v_cursor BIGINT DEFAULT 0;
    DECLARE v_end BIGINT;
    DECLARE v_locked INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        IF v_locked = 1 THEN
            DO RELEASE_LOCK('jia.core_log.retention_7d');
        END IF;
        RESIGNAL;
    END;

    SET p_deleted = 0;
    -- Dedicated autocommit session only: never accumulate millions of row locks
    -- in one transaction. Each ID window is atomic and safely resumable.
    IF @@session.autocommit <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit retention requires autocommit';
    END IF;
    SELECT GET_LOCK('jia.core_log.retention_7d', 0) INTO v_locked;
    IF COALESCE(v_locked, 0) <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit retention already running';
    END IF;
    SET v_cutoff = CAST(UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3) - INTERVAL 7 DAY) * 1000 AS UNSIGNED);
    -- Optional older cutoff/ID ceiling binds the first run to its exact backup.
    -- Callers cannot shorten the seven-day retention window.
    IF p_cutoff_ms IS NOT NULL THEN
        SET v_cutoff = LEAST(v_cutoff, p_cutoff_ms);
    END IF;
    SELECT MAX(id) INTO v_upper FROM `jia`.`core_log`;
    IF p_upper_id IS NOT NULL THEN
        SET v_upper = LEAST(v_upper, p_upper_id);
    END IF;

    windows: LOOP
        SET v_end = NULL;
        SELECT MAX(window_ids.id) INTO v_end
        FROM (
            SELECT id FROM `jia`.`core_log` FORCE INDEX (PRIMARY)
            WHERE id > v_cursor AND id <= v_upper
            ORDER BY id LIMIT 5000
        ) AS window_ids;
        IF v_end IS NULL THEN
            LEAVE windows;
        END IF;
        -- Fixed primary-key windows avoid repeated full-table scans without
        -- adding an index/rebuilding this multi-GB live table. No DELETE LIMIT
        -- or skipped binlogging: recovery/replication behavior stays intact.
        DELETE FROM `jia`.`core_log`
        WHERE id > v_cursor AND id <= v_end
          AND create_time > 0 AND create_time < v_cutoff;
        SET p_deleted = p_deleted + ROW_COUNT();
        SET v_cursor = v_end;
    END LOOP;
    DO RELEASE_LOCK('jia.core_log.retention_7d');
END$$

CREATE EVENT `cyf_core_log_retention_7d`
    ON SCHEDULE EVERY 1 DAY
    STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Rolling seven-day core_log retention; unknown timestamps preserved'
    DO CALL `jia`.`cyf_core_log_retention_7d`(NULL, NULL, @cyf_audit_deleted)$$
DELIMITER ;
