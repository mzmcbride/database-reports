/*
Copyright 2023 Kunal Mehta <legoktm@debian.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

use anyhow::Result;
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;
use time::format_description::FormatItem;
use time::macros::format_description;
use time::{Date, Duration, OffsetDateTime};

const TIMESTAMP_DB: &[FormatItem] =
    format_description!("[year][month][day]000000");
const TIMESTAMP_LIKE: &[FormatItem] =
    format_description!("[year][month][day]%");
const TIMESTAMP_HUMAN: &[FormatItem] =
    format_description!("[month repr:long] [day padding:none], [year]");

pub struct Row {
    user_name: String,
    days: u64,
    start: Date,
}

pub struct UserStreaks {}

impl Report<Row> for UserStreaks {
    fn title(&self) -> &'static str {
        "Longest active user editing streaks"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* userstreaks.rs SLOW_OK */
SELECT
  actor_name,
  COUNT(DISTINCT substring(rev_timestamp, 1, 8)) as days
FROM
  revision_userindex
  JOIN actor_revision ON rev_actor = actor_id
WHERE
  rev_timestamp < ?
  AND rev_timestamp >= ?
GROUP BY
  actor_name
HAVING
  COUNT(DISTINCT substring(rev_timestamp, 1, 8)) > 364
ORDER BY
  days DESC
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let today = OffsetDateTime::now_utc().date();
        let one_year_ago = today - Duration::days(365);
        let mut rows = conn
            .exec_map(
                self.query(),
                (
                    today.format(TIMESTAMP_DB).unwrap(),
                    one_year_ago.format(TIMESTAMP_DB).unwrap(),
                ),
                |(user_name, days)| Row {
                    user_name,
                    days,
                    start: one_year_ago,
                },
            )
            .await?;
        for row in &mut rows {
            loop {
                let yesterday = row.start - Duration::days(1);
                let made_edit: Option<usize> = conn
                    .exec_first(
                        r#"
/* userstreaks.rs SLOW_OK */
SELECT
  1
FROM
  revision_userindex
  JOIN actor_revision ON rev_actor = actor_id
WHERE
  actor_name = ?
  AND rev_timestamp LIKE ?
LIMIT 1"#,
                        (
                            &row.user_name,
                            yesterday.format(TIMESTAMP_LIKE).unwrap(),
                        ),
                    )
                    .await?;
                if made_edit.is_some() {
                    /*println!(
                        "{} edited on {:?} (len: {})",
                        &row.user_name, &row.start, row.days
                    );*/
                    row.days += 1;
                    row.start = yesterday;
                } else {
                    dbg!((&row.user_name, row.days));
                    break;
                }
            }
        }
        rows.sort_by_key(|row| row.days);
        rows.reverse();
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Users who have an active streak of at least one edit per day (minimum 365 days listed)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["User", "Consecutive days", "Start of streak"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("[[User:{}]]", row.user_name),
            //format!("{} ({})", format_days(row.days), row.days),
            row.days,
            row.start.format(TIMESTAMP_HUMAN).unwrap()
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("userstreaks.rs")
    }
}

/* FIXME: support leap years
fn format_days(days: u64) -> String {
    let years = days / 365;
    let rem = days % 365;
    let day_part = if rem == 1 {
        " and 1 day".to_string()
    } else if rem == 0 {
        "".to_string()
    } else {
        format!(" and {rem} days")
    };
    if years > 1 {
        format!("{years} years{day_part}")
    } else {
        format!("{years} year{day_part}")
    }
}


#[test]
fn test_format_days() {
    assert_eq!("33 years and 300 days", &format_days(12345));
    assert_eq!("1 year and 2 days", &format_days(367));
    assert_eq!("1 year and 1 day", &format_days(366));
    assert_eq!("2 years", &format_days(730));
} */

#[test]
fn test_format() {
    use time::macros::date;
    assert_eq!(
        "20230115000000",
        &date!(2023 - 01 - 15).format(TIMESTAMP_DB).unwrap()
    );
    assert_eq!(
        "20230115%",
        &date!(2023 - 01 - 15).format(TIMESTAMP_LIKE).unwrap()
    );
    assert_eq!(
        "January 15, 2023",
        &date!(2023 - 01 - 15).format(TIMESTAMP_HUMAN).unwrap()
    );
}
