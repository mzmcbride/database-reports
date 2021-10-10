/*
Copyright 2009, 2013 bjweeks, MZMcBride, Tim Landscheidt
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

pub struct Potenshblps1 {}

#[async_trait::async_trait]
impl Report<Row> for Potenshblps1 {
    fn title(&self) -> &'static str {
        "Potential biographies of living people (1)"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* potenshblps1.rs SLOW_OK */
SELECT
  pg1.page_title
FROM
  page AS pg1
  JOIN templatelinks ON pg1.page_id = tl_from
WHERE
  pg1.page_namespace = 0
  AND tl_namespace = 10
  AND tl_title = 'BLP_unsourced'
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg2
      JOIN categorylinks ON pg2.page_id = cl_from
    WHERE
      pg1.page_title = pg2.page_title
      AND pg2.page_namespace = 0
      AND cl_to = 'Living_people'
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg3
      JOIN categorylinks ON pg3.page_id = cl_from
    WHERE
      pg1.page_title = pg3.page_title
      AND pg3.page_namespace = 0
      AND cl_to = 'Possibly_living_people'
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS pg4
      JOIN categorylinks ON pg4.page_id = cl_from
    WHERE
      pg1.page_title = pg4.page_title
      AND pg4.page_namespace = 0
      AND cl_to RLIKE '^[0-9]{4}_deaths$'
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
        "Articles that transclude {{tl|BLP unsourced}} that are not \
        categorized in [[:Category:Living people]] or \
        [[:Category:Possibly living people]]"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("potenshblps1.rs")
    }
}
