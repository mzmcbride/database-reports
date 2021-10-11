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

pub struct Row {
    page_title: String,
}

pub struct UnusedNonFree {}

#[async_trait::async_trait]
impl Report<Row> for UnusedNonFree {
    fn title(&self) -> &'static str {
        "Unused non-free files"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Daily
    }

    fn query(&self) -> &'static str {
        r#"
/* unusednonfree.rs SLOW_OK */
SELECT
  page_title
FROM
  page
  JOIN categorylinks AS cl1 ON cl1.cl_from = page_id
  LEFT JOIN imagelinks ON il_to = page_title
  AND page_namespace = 6
  LEFT JOIN categorylinks AS cl2 ON cl2.cl_from = page_id
  AND cl2.cl_to = 'All_orphaned_non-free_use_Wikipedia_files'
  LEFT JOIN redirect ON rd_title = page_title
  AND rd_namespace = 6
WHERE
  cl1.cl_to = 'All_non-free_media'
  AND il_from IS NULL
  AND cl2.cl_from IS NULL
  AND rd_from IS NULL
  AND page_is_redirect = 0
  AND page_namespace = 6;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["File"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[:File:{}|]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("unusednonfree.rs")
    }
}
