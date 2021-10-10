/*
Copyright 2012-2013 MZMcBride, Tim Landscheidt
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
use dbreps2::{str_vec, DbrLink, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
    count: u32,
}

pub struct LinkedMisspellings {}

#[async_trait::async_trait]
impl Report<Row> for LinkedMisspellings {
    fn title(&self) -> &'static str {
        "Linked misspellings"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Daily
    }

    fn query(&self) -> &'static str {
        r#"
/* linkedmisspellings.rs SLOW_OK */
SELECT
  p1.page_title,
  COUNT(*)
FROM
  page AS p1
  JOIN categorylinks ON p1.page_id = cl_from
  JOIN pagelinks ON p1.page_title = pl_title
  AND pl_namespace = 0
  JOIN page AS p2 ON pl_from = p2.page_id
  AND p2.page_namespace = 0
WHERE
  p1.page_namespace = 0
  AND p1.page_is_redirect = 1
  AND cl_to = 'Redirects_from_misspellings'
GROUP BY
  1
LIMIT
  1000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title, count)| Row {
                page_title,
                count,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Linked misspellings (limited to the first 1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Article", "Incoming links"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![DbrLink::new(&row.page_title), row.count]
    }

    fn code(&self) -> &'static str {
        include_str!("linkedmisspellings.rs")
    }
}
