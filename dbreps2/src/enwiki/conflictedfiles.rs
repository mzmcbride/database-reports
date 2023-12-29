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

pub struct ConflictedFiles {}

impl Report<Row> for ConflictedFiles {
    fn title(&self) -> &'static str {
        "Files with conflicting categorization"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* conflictedfiles.rs SLOW_OK */
SELECT
  page_title
FROM
  page
  JOIN categorylinks AS c1 ON c1.cl_from = page_id
  JOIN categorylinks AS c2 ON c2.cl_from = page_id
WHERE
  page_namespace = 6
  AND c1.cl_to = 'All_free_media'
  AND c2.cl_to = 'All_non-free_media';
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Files that are categorized in [[:Category:All non-free media]] and [[:Category:All free media]]"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["File"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[:File:{}|{}]]", row.page_title, row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("conflictedfiles.rs")
    }
}
