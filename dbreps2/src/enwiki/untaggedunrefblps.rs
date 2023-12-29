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
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;
use regex::Regex;

pub struct Row {
    page_title: String,
    categories: String,
}

pub struct UntaggedUnrefBLPs {}

impl Report<Row> for UntaggedUnrefBLPs {
    fn title(&self) -> &'static str {
        "Untagged and unreferenced biographies of living people"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* untaggedunrefblps.rs SLOW_OK */
SELECT
  p1.page_title,
  GROUP_CONCAT(cl2.cl_to SEPARATOR '|')
FROM
  page AS p1
  JOIN categorylinks AS cl1 ON cl1.cl_from = p1.page_id
  JOIN categorylinks AS cl2 ON cl2.cl_from = p1.page_id
WHERE
  cl1.cl_to = 'All_unreferenced_BLPs'
  AND p1.page_namespace = 0
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS p2
    WHERE
      p2.page_title = p1.page_title
      AND p2.page_namespace = 1
  )
GROUP BY
  p1.page_id;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title, categories)| Row {
                page_title,
                categories,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Pages in [[:Category:All unreferenced BLPs]] missing WikiProject tags"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography", "Categories"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        let exclude_cats = Regex::new(r"(?i)(\d{1,4}_births|living_people|all_unreferenced_blps|unreferenced_blps_from)").unwrap();
        let categories: Vec<_> = row
            .categories
            .split('|')
            .filter_map(|category| {
                if exclude_cats.is_match(category) {
                    None
                } else {
                    Some(format!("[[:Category:{category}|]]"))
                }
            })
            .collect();
        str_vec![
            format!("{{{{plat|1={}}}}}", row.page_title),
            categories.join(", ")
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("untaggedunrefblps.rs")
    }
}
