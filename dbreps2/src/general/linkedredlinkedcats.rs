/*
Public domain; MZMcBride, Tim Landscheidt; 2012, 2013
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
    cl_to: String,
    count: u64,
}

pub struct LinkedRedlinkedCats {}

#[async_trait::async_trait]
impl Report<Row> for LinkedRedlinkedCats {
    fn title(&self) -> &'static str {
        "Red-linked categories with incoming links"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* linkedredlinkedcats.rs SLOW_OK */
SELECT
  cl_to,
  COUNT(*)
FROM
  /* FIXME when categorylinks gets normalized as well */
  categorylinks
  JOIN linktarget ON lt_title = cl_to AND lt_namespace = 14
  JOIN pagelinks ON pl_target_id = lt_id
  JOIN page AS p1 ON pl_from = p1.page_id
  AND p1.page_namespace IN (0, 6, 10, 12, 14, 100)
  LEFT JOIN page AS p2 ON cl_to = p2.page_title
  AND p2.page_namespace = 14
WHERE
  p2.page_title IS NULL
GROUP BY
  1
LIMIT
  1000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(cl_to, count)| Row { cl_to, count })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category", "Links"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!(
                "[[Special:WhatLinksHere/Category:{}|{}]]",
                &row.cl_to, &row.cl_to
            ),
            row.count
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("linkedredlinkedcats.rs")
    }
}
