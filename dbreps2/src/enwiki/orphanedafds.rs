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
    rev_timestamp: String,
}

pub struct OrphanedAfds {}

#[async_trait::async_trait]
impl Report<Row> for OrphanedAfds {
    fn title(&self) -> &'static str {
        "Orphaned article deletion discussions"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(1000)
    }

    fn query(&self) -> &'static str {
        r#"
/* orphanedafds.rs SLOW_OK */
SELECT
  page_title,
  rev_timestamp
FROM
  page
  JOIN revision ON page_id = rev_page
  LEFT JOIN pagelinks ON pl_title = page_title
  AND pl_namespace = page_namespace
  /* FIXME JOIN linktarget */
  LEFT JOIN templatelinks ON tl_title = page_title
  AND tl_namespace = page_namespace
WHERE
  page_namespace = 4
  AND page_is_redirect = 0
  AND page_title LIKE "Articles_for_deletion/%"
  AND rev_parent_id = 0
  AND ISNULL(pl_namespace)
  AND ISNULL(tl_namespace);
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let mut rows = conn
            .query_map(self.query(), |(page_title, rev_timestamp)| Row {
                page_title,
                rev_timestamp,
            })
            .await?;
        rows.sort_by(|a, b| b.rev_timestamp.cmp(&a.rev_timestamp));
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Subpages of [[Wikipedia:Articles for deletion]] that have no incoming links"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Creation time"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("{{{{pllh|1=Wikipedia:{}}}}}", &row.page_title),
            &row.rev_timestamp
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("orphanedafds.rs")
    }
}
