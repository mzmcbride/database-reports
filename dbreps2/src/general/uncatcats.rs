/*
Copyright 2008 bjweeks, MZMcBride
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
    page_len: u32,
    cat_pages: u32,
    rev_timestamp: String,
    actor_name: String,
}

pub struct UncatCats {}

#[async_trait::async_trait]
impl Report<Row> for UncatCats {
    fn title(&self) -> &'static str {
        "Project:Database reports/Uncategorized categories"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* uncatcats.rs SLOW_OK */
SELECT
  page_title,
  page_len,
  cat_pages,
  rev_timestamp,
  actor_name
FROM
  revision
  JOIN actor ON rev_actor = actor_id
  JOIN (
    SELECT
      page_id,
      page_title,
      page_len,
      cat_pages
    FROM
      category
      RIGHT JOIN page ON cat_title = page_title
      LEFT JOIN categorylinks ON page_id = cl_from
    WHERE
      cl_from IS NULL
      AND page_namespace = 14
      AND page_is_redirect = 0
  ) AS pagetmp ON rev_page = pagetmp.page_id
  AND rev_timestamp = (
    SELECT
      MAX(rev_timestamp)
    FROM
      revision AS last
    WHERE
      last.rev_page = pagetmp.page_id
  );
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(
                    page_title,
                    page_len,
                    cat_pages,
                    rev_timestamp,
                    actor_name,
                )| Row {
                    page_title,
                    page_len,
                    cat_pages,
                    rev_timestamp,
                    actor_name,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Uncategorized categories; {asof}."
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category", "Length", "Members", "Last edit", "Last user"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        // TODO: Improve this interface
        let mut fmt = vec![];
        fmt.push(format!("{{{{clh|1={}}}}}", &row.page_title));
        fmt.push(row.page_len.to_string());
        fmt.push(row.cat_pages.to_string());
        fmt.push(row.rev_timestamp.to_string());
        fmt.push(row.actor_name.to_string());

        fmt
    }
}
