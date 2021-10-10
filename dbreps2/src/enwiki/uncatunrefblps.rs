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

pub struct UncatUnrefBLPs {}

#[async_trait::async_trait]
impl Report<Row> for UncatUnrefBLPs {
    fn title(&self) -> &'static str {
        "Uncategorized and unreferenced biographies of living people"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* uncatunrefblps.rs SLOW_OK */
SELECT
  DISTINCT page_title
FROM
  page
  JOIN categorylinks AS cl1 ON cl1.cl_from = page_id
  LEFT JOIN categorylinks AS cl2 ON cl2.cl_from = page_id
  AND cl2.cl_to NOT REGEXP '(Living_people|[0-9]+_births)'
  AND cl2.cl_to NOT IN (
    SELECT
      page_title
    FROM
      page
      JOIN categorylinks ON cl_from = page_id
    WHERE
      page_namespace = 14
      AND cl_to IN ('Wikipedia_maintenance', 'Hidden_categories')
  )
WHERE
  cl1.cl_to = 'All_unreferenced_BLPs'
  AND page_namespace = 0
  AND cl2.cl_from IS NULL;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Pages in [[:Category:All unreferenced BLPs]] in need of proper categorization"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("uncatunrefblps.rs")
    }
}
