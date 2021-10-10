/*
Copyright 2008, 2013 bjweeks, MZMcBride, Tim Landscheidt
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
    count: u64,
}

pub struct TemplatesNonFree {}

#[async_trait::async_trait]
impl Report<Row> for TemplatesNonFree {
    fn title(&self) -> &'static str {
        "Templates containing non-free files"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* templatesnonfree.rs SLOW_OK */
SELECT
  imgtmp.page_title,
  COUNT(cl_to)
FROM
  page AS pg1
  JOIN categorylinks ON cl_from = pg1.page_id
  JOIN (
    SELECT
      pg2.page_namespace,
      pg2.page_title,
      il_to
    FROM
      page AS pg2
      JOIN imagelinks ON il_from = page_id
    WHERE
      pg2.page_namespace = 10
  ) AS imgtmp ON il_to = pg1.page_title
WHERE
  pg1.page_namespace = 6
  AND cl_to = 'All_non-free_media'
GROUP BY
  imgtmp.page_namespace,
  imgtmp.page_title
ORDER BY
  COUNT(cl_to) ASC;
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

    fn headings(&self) -> Vec<&'static str> {
        vec!["Template", "Non-free files"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[Template:{}|]]", row.page_title), row.count]
    }

    fn code(&self) -> &'static str {
        include_str!("templatesnonfree.rs")
    }
}
