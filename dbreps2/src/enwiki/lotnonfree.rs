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
use dbreps2::{linker, str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_namespace: u32,
    page_title: String,
    count: u64,
}

pub struct LotNonFree {}

#[async_trait::async_trait]
impl Report<Row> for LotNonFree {
    fn title(&self) -> &'static str {
        "Pages containing an unusually high number of non-free files"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* lotnonfree.rs SLOW_OK */
SELECT
  imgtmp.page_namespace,
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
  ) AS imgtmp ON il_to = pg1.page_title
WHERE
  pg1.page_namespace = 6
  AND cl_to = 'All_non-free_media'
GROUP BY
  imgtmp.page_namespace,
  imgtmp.page_title
HAVING
  COUNT(cl_to) > 6
ORDER BY
  COUNT(cl_to) DESC;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_namespace, page_title, count)| {
                Row {
                    page_namespace,
                    page_title,
                    count,
                }
            })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Non-free files"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![linker(row.page_namespace, &row.page_title), row.count]
    }

    fn code(&self) -> &'static str {
        include_str!("lotnonfree.rs")
    }
}
