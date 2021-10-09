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
    img_size: u64,
}

pub struct LargeNonFree {}

#[async_trait::async_trait]
impl Report<Row> for LargeNonFree {
    fn title(&self) -> &'static str {
        "Large non-free files"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* largenonfree.rs SLOW_OK */
SELECT
  page_title,
  img_size
FROM
  page
  JOIN image ON img_name = page_title
  JOIN categorylinks ON cl_from = page_id
WHERE
  page_namespace = 6
  AND cl_to = 'All_non-free_media'
  AND img_size > 999999
  AND NOT EXISTS (
    SELECT
      1
    FROM
      categorylinks
    WHERE
      page_id = cl_from
      AND cl_to = 'Wikipedia_non-free_file_size_reduction_requests'
  );
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title, img_size)| Row {
                page_title,
                img_size,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Files in [[:Category:All non-free media]] that are larger than \
        999999 bytes and are not in [[:Category:Wikipedia non-free file size reduction requests]]"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["File", "Size"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[:File:{}]]", row.page_title), row.img_size]
    }

    fn code(&self) -> &'static str {
        include_str!("largenonfree.rs")
    }
}
