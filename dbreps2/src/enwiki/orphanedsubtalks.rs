/*
Copyright 2010, 2013 bjweeks, MZMcBride, Tim Landscheidt
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
use dbreps2::{str_vec, Frequency, Linker, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_namespace: u32,
    page_title: String,
}

pub struct OrphanedSubTalks {}

#[async_trait::async_trait]
impl Report<Row> for OrphanedSubTalks {
    fn title(&self) -> &'static str {
        "Orphaned talk subpages"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* orphanedsubtalks.rs SLOW_OK */
SELECT
  pg1.page_namespace,
  pg1.page_title
FROM
  page AS pg1
WHERE
  pg1.page_title LIKE '%/%'
  AND pg1.page_namespace IN (1, 5, 7, 9, 11, 13, 15, 101, 103, 119, 711, 829)
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg2
    WHERE
      pg2.page_namespace = pg1.page_namespace
      AND pg2.page_title = SUBSTRING_INDEX(pg1.page_title, '/', 1)
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg3
    WHERE
      pg3.page_namespace = pg1.page_namespace - 1
      AND pg3.page_title = pg1.page_title
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg4
    WHERE
      pg4.page_namespace = pg1.page_namespace - 1
      AND pg4.page_title = SUBSTRING_INDEX(pg1.page_title, '/', 1)
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      templatelinks
    JOIN linktarget ON tl_target_id = lt_id
    WHERE
      tl_from = pg1.page_id
      AND lt_namespace = 10
      AND lt_title = 'G8-exempt'
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg5
    WHERE
      pg5.page_namespace = pg1.page_namespace
      AND pg5.page_title = LEFT(
        pg1.page_title,
        LENGTH(pg1.page_title) - INSTR(REVERSE(pg1.page_title), '/')
      )
  );
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_namespace, page_title)| Row {
                page_namespace,
                page_title,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Talk pages that don't have a root page and do not have a \
        corresponding subject-space page"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![Linker::new(row.page_namespace, &row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("orphanedsubtalks.rs")
    }
}
