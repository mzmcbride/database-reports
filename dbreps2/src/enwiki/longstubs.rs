/*
Copyright 2008, 2013 bjweeks, MZMcBride, CBM, Tim Landscheidt
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
    page_len: u64,
}

pub struct LongStubs {}

#[async_trait::async_trait]
impl Report<Row> for LongStubs {
    fn title(&self) -> &'static str {
        "Long stubs"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* longstubs.rs SLOW_OK */
SELECT
  page_title,
  page_len
FROM
  page
  JOIN categorylinks ON cl_from = page_id
WHERE
  cl_to LIKE '%stubs'
  AND page_namespace = 0
  AND page_len > 2000
GROUP BY
  page_title
ORDER BY
  page_len DESC
LIMIT
  1000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title, page_len)| Row {
                page_title,
                page_len,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Long pages in categories that end in \"stubs\" (limited to the first 1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Length"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title), row.page_len]
    }

    fn code(&self) -> &'static str {
        include_str!("longstubs.rs")
    }
}
