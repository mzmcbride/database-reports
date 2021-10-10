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
    count: u32,
}

pub struct OverusedNonFree {}

#[async_trait::async_trait]
impl Report<Row> for OverusedNonFree {
    fn title(&self) -> &'static str {
        "Overused non-free files"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* overusednonfree.rs SLOW_OK */
SELECT
  page_title,
  COUNT(*)
FROM
  imagelinks
  JOIN (
    SELECT
      page_id,
      page_title
    FROM
      page
      JOIN categorylinks ON cl_from = page_id
    WHERE
      cl_to = 'All_non-free_media'
      AND page_namespace = 6
  ) AS pgtmp ON pgtmp.page_title = il_to
GROUP BY
  il_to
HAVING
  COUNT(*) > 4
ORDER BY
  COUNT(*) DESC;
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
        "Non-free files used on more than four pages"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["File", "Uses"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("[[:File:{}|{}]]", row.page_title, row.page_title),
            row.count
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("overusednonfree.rs")
    }
}
