/*
Public domain; bjweeks, MZMcBride, CBM, Tim Landscheidt; 2012, 2013
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
    page_title: String,
}

pub struct Pollcats {}

#[async_trait::async_trait]
impl Report<Row> for Pollcats {
    fn title(&self) -> &'static str {
        "Polluted categories"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn query(&self) -> &'static str {
        r#"
/* pollcats.rs SLOW_OK */
SELECT
  p1.page_title
FROM
  page AS p1
WHERE
  p1.page_namespace = 14
  AND NOT EXISTS(
    SELECT
      1
    FROM
      templatelinks
    WHERE
      tl_from = p1.page_id
      AND tl_namespace = 10
      AND tl_title = 'Polluted_category'
  )
  AND EXISTS(
    SELECT
      1
    FROM
      page AS p2
      JOIN categorylinks ON cl_from = p2.page_id
    WHERE
      cl_to = p1.page_title
      AND p2.page_namespace IN (2, 3)
  )
  AND EXISTS(
    SELECT
      1
    FROM
      page AS p3
      JOIN categorylinks ON cl_from = p3.page_id
    WHERE
      cl_to = p1.page_title
      AND p3.page_namespace = 0
  )
LIMIT
  1000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title,)| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Categories that contain pages in the (Main) namespace and the user namespaces (limited to the first 1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        vec![format!("{{{{dbr link|1={}}}}}", &row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("pollcats.rs")
    }
}
