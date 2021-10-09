/*
Copyright 2011, 2013 bjweeks, MZMcBride, WOSlinker, Tim Landscheidt
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

pub struct PollTemps {}

#[async_trait::async_trait]
impl Report<Row> for PollTemps {
    fn title(&self) -> &'static str {
        "Template categories containing articles"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* polltemps.rs SLOW_OK */
SELECT
  page_title
FROM
  page AS pg1
  JOIN templatelinks AS tl ON pg1.page_id = tl.tl_from
WHERE
  pg1.page_namespace = 14
  AND tl.tl_namespace = 10
  AND tl.tl_title = 'Template_category'
  AND EXISTS (
    SELECT
      1
    FROM
      page AS pg2
      JOIN categorylinks AS cl ON pg2.page_id = cl.cl_from
    WHERE
      pg2.page_namespace = 0
      AND pg1.page_title = cl.cl_to
  );
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Template categories containing articles"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[:Category:{}]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("polltemps.rs")
    }
}
