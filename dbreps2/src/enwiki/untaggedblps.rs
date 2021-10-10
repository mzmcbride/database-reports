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
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
}

pub struct UntaggedBLPs {}

#[async_trait::async_trait]
impl Report<Row> for UntaggedBLPs {
    fn title(&self) -> &'static str {
        "Untagged biographies of living people"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* untaggedblps.rs SLOW_OK */
SELECT
  p1.page_title
FROM
  page AS p1
  JOIN categorylinks ON cl_from = p1.page_id
WHERE
  cl_to = 'Living_people'
  AND p1.page_namespace = 0
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS p2
    WHERE
      p2.page_title = p1.page_title
      AND p2.page_namespace = 1
  )
LIMIT
  1000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Pages in [[:Category:Living people]] missing WikiProject tags \
        (limited to the first 1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("untaggedblps.rs")
    }
}
