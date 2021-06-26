/*
Copyright 2009-2010 bjweeks, MZMcBride, svick
Copyright 2021 Kunal Mehta <legoktm@debian.org>

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
use dbreps2::{Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    rc_timestamp: String,
    rc_title: String,
    page_is_redirect: u32,
}

pub struct NewProjects {}

#[async_trait::async_trait]
impl Report<Row> for NewProjects {
    fn title(&self) -> &'static str {
        "New WikiProjects"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Fortnightly
    }

    fn query(&self) -> &'static str {
        r#"
/* newprojects.rs SLOW_OK */
SELECT
  rc_timestamp,
  rc_title,
  page_is_redirect
FROM
  recentchanges
  LEFT JOIN page ON rc_cur_id = page_id
WHERE
  rc_new = 1
  AND rc_namespace = 4
  AND rc_title LIKE 'WikiProject%'
  AND rc_title NOT LIKE '%/%'
ORDER BY
  rc_timestamp DESC
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(rc_timestamp, rc_title, page_is_redirect)| Row {
                    rc_timestamp,
                    rc_title,
                    page_is_redirect,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "List of created WikiProject pages that aren't subpages from the past 30 days"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Date", "WikiProject page"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        let page = if row.page_is_redirect == 1 {
            format!("''[[Project:{}|]]''", &row.rc_title)
        } else {
            format!("[[Project:{}|]]", &row.rc_title)
        };
        vec![row.rc_timestamp.to_string(), page]
    }

    fn code(&self) -> &'static str {
        include_str!("newprojects.rs")
    }
}
